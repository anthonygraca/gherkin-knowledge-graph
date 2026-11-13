"""Offline contract tests for the optional chat and embedding providers.

Every HTTP test uses ``httpx.MockTransport``. No test in this module opens a socket, downloads a
model, or requires an API key. The live integration test lives in
``test_live_provider_integration.py`` and skips unless explicitly enabled.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import httpx
import pytest
from probe_ai_capabilities import main as probe_cli_main
from pydantic import BaseModel

from app.discovery.ai import (
    ChatGenerationProvider,
    ChatMessage,
    EmbeddingProvider,
    ProviderAuthenticationError,
    ProviderCapabilityError,
    ProviderConfigurationError,
    ProviderResponseError,
    ProviderServerError,
    ProviderTimeoutError,
    sanitize_capability_report,
    sanitize_url,
)
from app.discovery.ai_fake import FakeChatGenerationProvider, FakeEmbeddingProvider
from app.discovery.ai_http import (
    OpenAICompatibleChatProvider,
    OpenAICompatibleEmbeddingProvider,
)
from app.discovery.capabilities import offline_summary, probe_capabilities
from app.discovery.registry import ProviderRegistry
from app.settings import Settings, SettingsError, load_settings

REPO_ROOT = Path(__file__).resolve().parents[2]


def _settings(tmp_path: Path, **overrides: object) -> Settings:
    values: dict[str, object] = {
        "repo_root": tmp_path,
        "fixtures_dir": tmp_path / "fixtures",
    }
    values.update(overrides)
    return Settings(**values)  # type: ignore[arg-type]


def _completion_response() -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "id": "chatcmpl-1",
            "model": "test-model-2026",
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": "hello"},
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 4, "completion_tokens": 2, "total_tokens": 6},
        },
        headers={"x-request-id": "req-1", "x-ratelimit-remaining-requests": "9"},
    )


def _chat_provider(
    handler: Callable[[httpx.Request], httpx.Response],
    **overrides: object,
) -> OpenAICompatibleChatProvider:
    values: dict[str, object] = {
        "base_url": "http://llm.test/v1/",
        "model": "test-model",
        "api_key": "secret-key",
        "transport": httpx.MockTransport(handler),
        "sleep": lambda _: None,
    }
    values.update(overrides)
    return OpenAICompatibleChatProvider(**values)  # type: ignore[arg-type]


def _embedding_provider(
    handler: Callable[[httpx.Request], httpx.Response],
    **overrides: object,
) -> OpenAICompatibleEmbeddingProvider:
    values: dict[str, object] = {
        "base_url": "http://embed.test/v1",
        "model": "embed-model",
        "api_key": "embed-secret",
        "transport": httpx.MockTransport(handler),
        "sleep": lambda _: None,
    }
    values.update(overrides)
    return OpenAICompatibleEmbeddingProvider(**values)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------------- fakes


def test_fake_chat_is_deterministic_and_reports_unavailable_usage() -> None:
    provider = FakeChatGenerationProvider()
    assert isinstance(provider, ChatGenerationProvider)
    first = provider.complete([ChatMessage(role="user", content="hello")])
    second = provider.complete([ChatMessage(role="user", content="hello")])
    assert first.text == second.text == "fake chat completion"
    assert first.model == "fake-chat-v1"
    assert first.model_observed is False
    assert first.provider == "fake"
    assert first.usage is None
    assert first.http_status is None
    assert first.latency_ms == 0.0


def test_fake_chat_validates_a_requested_schema() -> None:
    class Answer(BaseModel):
        ok: bool

    valid = FakeChatGenerationProvider(responses=['{"ok": true}'])
    completion = valid.complete([ChatMessage(role="user", content="json")], response_model=Answer)
    assert completion.parsed == {"ok": True}

    invalid = FakeChatGenerationProvider(responses=["not json"])
    with pytest.raises(ProviderResponseError):
        invalid.complete([ChatMessage(role="user", content="json")], response_model=Answer)


def test_fake_embeddings_are_deterministic_and_dimensioned() -> None:
    provider = FakeEmbeddingProvider()
    assert isinstance(provider, EmbeddingProvider)
    first = provider.embed(["alpha", "beta"])
    second = provider.embed(["alpha", "beta"])
    assert first.vectors == second.vectors
    assert first.dimensions == 8
    assert [len(vector) for vector in first.vectors] == [8, 8]
    assert first.model == "fake-embedding-v1"
    assert first.usage is None
    assert first.http_status is None
    assert len(FakeEmbeddingProvider(dimensions=40).embed(["alpha"]).vectors[0]) == 40


def test_fake_providers_have_no_link_or_review_surface() -> None:
    public = {name for name in dir(FakeChatGenerationProvider) if not name.startswith("_")} | {
        name for name in dir(FakeEmbeddingProvider) if not name.startswith("_")
    }
    assert public.isdisjoint(
        {"accept", "approve", "reject", "store", "write", "review", "link", "evidence"}
    )


# ---------------------------------------------------------------------------------- chat HTTP


def test_chat_request_uses_configured_model_key_and_observes_response() -> None:
    captured: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        return _completion_response()

    provider = _chat_provider(handler)
    result = provider.complete(
        [ChatMessage(role="system", content="s"), ChatMessage(role="user", content="u")],
        temperature=0.2,
        max_tokens=16,
    )

    request = captured[0]
    assert str(request.url) == "http://llm.test/v1/chat/completions"
    assert request.headers["authorization"] == "Bearer secret-key"
    assert json.loads(request.content) == {
        "model": "test-model",
        "messages": [
            {"role": "system", "content": "s"},
            {"role": "user", "content": "u"},
        ],
        "temperature": 0.2,
        "max_tokens": 16,
    }
    assert result.text == "hello"
    assert result.model == "test-model-2026"
    assert result.model_observed is True
    assert result.usage is not None and result.usage.total_tokens == 6
    assert result.http_status == 200
    assert result.request_id == "req-1"
    assert result.rate_limit_headers == {"x-ratelimit-remaining-requests": "9"}
    assert result.latency_ms >= 0


def test_chat_retries_a_rate_limit_and_honors_retry_after() -> None:
    calls: list[httpx.Request] = []
    sleeps: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        if len(calls) == 1:
            return httpx.Response(
                429,
                json={"error": {"code": "rate_limit"}},
                headers={"retry-after": "0"},
            )
        return _completion_response()

    provider = _chat_provider(handler, max_retries=1, sleep=sleeps.append)
    result = provider.complete([ChatMessage(role="user", content="hello")])
    assert result.text == "hello"
    assert len(calls) == 2
    assert sleeps == [0.0]


def test_retry_after_is_capped() -> None:
    calls: list[httpx.Request] = []
    sleeps: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        if len(calls) == 1:
            return httpx.Response(
                429, json={"error": {"code": "rate_limit"}}, headers={"retry-after": "120"}
            )
        return _completion_response()

    provider = _chat_provider(handler, max_retries=1, sleep=sleeps.append)
    provider.complete([ChatMessage(role="user", content="hello")])
    assert sleeps == [5.0]


def test_bounded_retry_stops_after_the_budget() -> None:
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(503, json={"error": {"code": "unavailable"}})

    provider = _chat_provider(handler, max_retries=2)
    with pytest.raises(ProviderServerError) as raised:
        provider.complete([ChatMessage(role="user", content="hello")])
    assert len(calls) == 3
    assert raised.value.retryable is True


def test_authentication_failure_is_not_retried_and_does_not_echo_the_key(
    caplog: pytest.LogCaptureFixture,
) -> None:
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(
            401,
            json={
                "error": {
                    "code": "invalid_api_key",
                    "message": "credential secret-key was rejected",
                }
            },
        )

    provider = _chat_provider(handler, logger=logging.getLogger("test.ai.provider"))
    with caplog.at_level(logging.INFO):
        with pytest.raises(ProviderAuthenticationError) as raised:
            provider.complete([ChatMessage(role="user", content="hello")])
    assert len(calls) == 1
    assert raised.value.upstream_code == "invalid_api_key"
    assert "secret-key" not in str(raised.value)
    assert "secret-key" not in caplog.text


def test_timeout_is_retryable_and_bounded() -> None:
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        raise httpx.ReadTimeout("timed out", request=request)

    provider = _chat_provider(handler, max_retries=1)
    with pytest.raises(ProviderTimeoutError):
        provider.complete([ChatMessage(role="user", content="hello")])
    assert len(calls) == 2


def test_malformed_success_is_not_retried() -> None:
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(200, json={"choices": []})

    provider = _chat_provider(handler, max_retries=2)
    with pytest.raises(ProviderResponseError):
        provider.complete([ChatMessage(role="user", content="hello")])
    assert len(calls) == 1


class _Answer(BaseModel):
    ok: bool
    label: str


def test_schema_constrained_completion_sends_and_validates_json_schema() -> None:
    captured: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        return httpx.Response(
            200,
            json={
                "id": "chatcmpl-2",
                "model": "test-model",
                "choices": [
                    {
                        "message": {"content": '{"ok": true, "label": "canary"}'},
                        "finish_reason": "stop",
                    }
                ],
            },
        )

    provider = _chat_provider(handler)
    completion = provider.complete(
        [ChatMessage(role="user", content="json")], response_model=_Answer
    )
    request_body = json.loads(captured[0].content)
    assert request_body["response_format"]["type"] == "json_schema"
    assert request_body["response_format"]["json_schema"]["name"] == "_Answer"
    assert completion.parsed == {"ok": True, "label": "canary"}


def test_schema_violation_is_a_response_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "choices": [
                    {"message": {"content": '{"ok": "not-a-bool"}'}, "finish_reason": "stop"}
                ]
            },
        )

    provider = _chat_provider(handler)
    with pytest.raises(ProviderResponseError):
        provider.complete([ChatMessage(role="user", content="json")], response_model=_Answer)


def test_schema_rejection_is_a_capability_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json={"error": {"code": "unsupported_response_format"}})

    provider = _chat_provider(handler)
    with pytest.raises(ProviderCapabilityError) as raised:
        provider.complete([ChatMessage(role="user", content="json")], response_model=_Answer)
    assert raised.value.upstream_code == "unsupported_response_format"


def test_adapter_configuration_bounds() -> None:
    with pytest.raises(ProviderConfigurationError):
        OpenAICompatibleChatProvider("http://user:pass@host/v1", "m")
    with pytest.raises(ProviderConfigurationError):
        OpenAICompatibleChatProvider("http://host/v1", "m", max_retries=99)
    with pytest.raises(ValueError):
        OpenAICompatibleChatProvider("http://host/v1", "m").complete([])


# ---------------------------------------------------------------------------------- embeddings


def test_embeddings_use_the_embeddings_endpoint_and_report_dimensions() -> None:
    captured: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        return httpx.Response(
            200,
            json={
                "model": "embed-model-2026",
                "data": [
                    {"index": 1, "embedding": [4.0, 5.0]},
                    {"index": 0, "embedding": [1.0, 2.0]},
                ],
                "usage": {"prompt_tokens": 2, "total_tokens": 2},
            },
            headers={"x-request-id": "embed-req"},
        )

    provider = _embedding_provider(handler)
    batch = provider.embed(["alpha", "beta"])
    assert str(captured[0].url) == "http://embed.test/v1/embeddings"
    assert json.loads(captured[0].content) == {
        "model": "embed-model",
        "input": ["alpha", "beta"],
    }
    assert batch.vectors == ((1.0, 2.0), (4.0, 5.0))
    assert batch.dimensions == 2
    assert batch.model == "embed-model-2026"
    assert batch.model_observed is True
    assert batch.usage is not None and batch.usage.total_tokens == 2
    assert batch.request_id == "embed-req"
    assert batch.http_status == 200


@pytest.mark.parametrize("indices", [("1", "0"), (True, False)])
def test_embedding_rejects_invalid_index_types(indices: tuple[object, object]) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "data": [
                    {"index": indices[0], "embedding": [1.0, 2.0]},
                    {"index": indices[1], "embedding": [3.0, 4.0]},
                ]
            },
        )

    provider = _embedding_provider(handler)
    with pytest.raises(ProviderResponseError):
        provider.embed(["alpha", "beta"])


def test_embedding_rejects_unrepresentable_numbers() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"data": [{"index": 0, "embedding": [10**400]}]})

    provider = _embedding_provider(handler)
    with pytest.raises(ProviderResponseError):
        provider.embed(["alpha"])


def test_embedding_rejects_mixed_index_shapes() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "data": [
                    {"index": 0, "embedding": [1.0, 2.0]},
                    {"embedding": [3.0, 4.0]},
                ]
            },
        )

    provider = _embedding_provider(handler)
    with pytest.raises(ProviderResponseError):
        provider.embed(["alpha", "beta"])


def test_embedding_rejects_a_chat_shaped_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return _completion_response()

    provider = _embedding_provider(handler)
    with pytest.raises(ProviderResponseError):
        provider.embed(["alpha"])


def test_embedding_404_is_a_capability_error_and_is_not_retried() -> None:
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(404, json={"error": {"code": "not_found"}})

    provider = _embedding_provider(handler, max_retries=2)
    with pytest.raises(ProviderCapabilityError):
        provider.embed(["alpha"])
    assert len(calls) == 1


def test_embedding_dimension_mismatch_is_a_response_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"data": [{"index": 0, "embedding": [1.0, 2.0, 3.0]}]})

    provider = _embedding_provider(handler, dimensions=2)
    with pytest.raises(ProviderResponseError):
        provider.embed(["alpha"])


def test_embedding_rejects_empty_input_without_a_request() -> None:
    def handler(request: httpx.Request) -> httpx.Response:  # pragma: no cover - must not run
        raise AssertionError("no request should be made")

    provider = _embedding_provider(handler)
    with pytest.raises(ValueError):
        provider.embed([])


# ---------------------------------------------------------------------------------- settings


def _clear_ai_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
        "CTA_AI_MODE",
        "CTA_LLM_BASE_URL",
        "CTA_LLM_MODEL",
        "CTA_LLM_API_KEY",
        "CTA_EMBED_BASE_URL",
        "CTA_EMBED_MODEL",
        "CTA_EMBED_API_KEY",
        "CTA_VECTOR_BACKEND",
        "CTA_AI_LIVE_TESTS",
    ):
        monkeypatch.delenv(name, raising=False)


def test_default_settings_are_fake_and_offline(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_ai_env(monkeypatch)
    settings = load_settings()
    assert settings.ai_mode == "fake"
    assert settings.vector_backend == "memory"
    assert settings.embeddings_configured is False
    assert settings.llm_api_key_present is False


def test_live_mode_requires_llm_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_ai_env(monkeypatch)
    monkeypatch.setenv("CTA_AI_MODE", "live")
    with pytest.raises(SettingsError):
        load_settings()


def test_embedding_configuration_must_be_complete(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_ai_env(monkeypatch)
    monkeypatch.setenv("CTA_EMBED_BASE_URL", "http://embed.test/v1")
    with pytest.raises(SettingsError):
        load_settings()


def test_unknown_mode_and_vector_backend_are_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_ai_env(monkeypatch)
    monkeypatch.setenv("CTA_AI_MODE", "hosted")
    with pytest.raises(SettingsError):
        load_settings()
    monkeypatch.setenv("CTA_AI_MODE", "fake")
    monkeypatch.setenv("CTA_VECTOR_BACKEND", "qdrant")
    with pytest.raises(SettingsError):
        load_settings()


def test_api_keys_are_excluded_from_repr(tmp_path: Path) -> None:
    settings = _settings(
        tmp_path,
        ai_mode="live",
        llm_base_url="http://llm.test/v1",
        llm_model="test-model",
        llm_api_key="top-secret",
    )
    assert "top-secret" not in repr(settings)
    assert settings.llm_api_key_present is True


def test_fake_registry_returns_offline_providers(tmp_path: Path) -> None:
    registry = ProviderRegistry(_settings(tmp_path))
    assert isinstance(registry.chat(), FakeChatGenerationProvider)
    assert isinstance(registry.embeddings(), FakeEmbeddingProvider)


def test_live_registry_builds_adapters_without_network(tmp_path: Path) -> None:
    registry = ProviderRegistry(
        _settings(
            tmp_path,
            ai_mode="live",
            llm_base_url="http://llm.test/v1",
            llm_model="test-model",
            embed_base_url="http://embed.test/v1",
            embed_model="embed-model",
        )
    )
    chat = registry.chat()
    embeddings = registry.embeddings()
    assert chat.__class__.__name__ == "OpenAICompatibleChatProvider"
    assert chat.model_version == "test-model"
    assert embeddings is not None
    assert embeddings.__class__.__name__ == "OpenAICompatibleEmbeddingProvider"
    assert embeddings.model_version == "embed-model"


def test_live_registry_without_embeddings_reports_unavailable(tmp_path: Path) -> None:
    registry = ProviderRegistry(
        _settings(
            tmp_path,
            ai_mode="live",
            llm_base_url="http://llm.test/v1",
            llm_model="test-model",
        )
    )
    assert registry.embeddings() is None


def test_fake_mode_import_does_not_import_the_http_transport() -> None:
    code = (
        "import sys; import app.discovery.registry; "
        "print('app.discovery.ai_http' in sys.modules); "
        "print('httpx' in sys.modules)"
    )
    environment = {**os.environ, "PYTHONPATH": str(REPO_ROOT / "backend")}
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=REPO_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == ["False", "False"]


# ---------------------------------------------------------------------------- capability probe


def _probe_settings(tmp_path: Path, **overrides: object) -> Settings:
    values: dict[str, object] = {
        "repo_root": tmp_path,
        "fixtures_dir": tmp_path / "fixtures",
        "ai_mode": "live",
        "llm_base_url": "http://llm.test/v1",
        "llm_model": "test-model",
        "embed_base_url": "http://embed.test/v1",
        "embed_model": "embed-model",
    }
    values.update(overrides)
    return Settings(**values)  # type: ignore[arg-type]


def _probe_handler(
    *,
    schema_status: int = 200,
    embedding_status: int = 200,
    models: list[dict[str, object]] | None = None,
    include_chat_model: bool = True,
) -> Callable[[httpx.Request], httpx.Response]:
    catalogue = (
        models
        if models is not None
        else [
            {
                "id": "test-model",
                "created": 1,
                "owned_by": "local",
                "max_model_len": 8192,
            }
        ]
    )

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if request.method == "GET" and path.endswith("/models"):
            return httpx.Response(200, json={"data": catalogue})
        if path.endswith("/embeddings"):
            if embedding_status != 200:
                return httpx.Response(embedding_status, json={"error": {"code": "not_found"}})
            return httpx.Response(
                200,
                json={
                    "model": "embed-model",
                    "data": [
                        {"index": 0, "embedding": [0.1, 0.2]},
                        {"index": 1, "embedding": [0.3, 0.4]},
                    ],
                },
            )
        body = json.loads(request.content) if request.content else {}
        if body.get("messages") == []:
            return httpx.Response(
                400, json={"error": {"code": "invalid_request_error", "type": "bad_request"}}
            )
        if "response_format" in body:
            if schema_status != 200:
                return httpx.Response(
                    schema_status, json={"error": {"code": "unsupported_response_format"}}
                )
            content = '{"ok": true, "label": "canary"}'
        else:
            content = "canary"
        response_body: dict[str, object] = {
            "id": "chatcmpl-probe",
            "choices": [{"message": {"content": content}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 3, "completion_tokens": 1, "total_tokens": 4},
        }
        if include_chat_model:
            response_body["model"] = "test-model"
        return httpx.Response(
            200,
            json=response_body,
            headers={"x-request-id": "probe-request"},
        )

    return handler


def test_probe_cli_offline_import_does_not_import_the_transport() -> None:
    code = (
        "import sys; import probe_ai_capabilities; "
        "print('app.discovery.ai_http' in sys.modules); "
        "print('httpx' in sys.modules)"
    )
    environment = {
        **os.environ,
        "PYTHONPATH": f"{REPO_ROOT / 'backend'}:{REPO_ROOT / 'tools'}",
    }
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=REPO_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == ["False", "False"]


def test_probe_offline_fake_mode_never_contacts_the_endpoint(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:  # pragma: no cover - must not run
        raise AssertionError("fake mode must not contact an endpoint")

    settings = _settings(tmp_path)
    report = probe_capabilities(settings, transport=httpx.MockTransport(handler))
    assert report["probed"] is False
    assert report["reason"].startswith("CTA_AI_MODE is not live")
    assert "models" not in report


def test_probe_records_observed_capabilities(tmp_path: Path) -> None:
    settings = _probe_settings(tmp_path)
    report = probe_capabilities(
        settings,
        transport=httpx.MockTransport(_probe_handler()),
        sleep=lambda _: None,
    )
    assert report["probed"] is True
    assert report["models"]["available"] is True
    assert report["models"]["model_ids"] == ["test-model"]
    assert report["models"]["context_lengths"] == {"test-model": 8192}
    assert report["context_window"] == 8192
    assert report["deployment_identifiable"] is True
    assert report["chat"]["available"] is True
    assert report["chat"]["observed_model"] == "test-model"
    assert report["chat"]["usage"]["total_tokens"] == 4
    assert report["chat"]["request_id"] == "probe-request"
    assert report["json_schema"]["supported"] is True
    assert report["json_schema"]["parsed"] == {"ok": True, "label": "canary"}
    assert report["embeddings"]["available"] is True
    assert report["embeddings"]["dimensions"] == 2
    assert report["embeddings"]["count"] == 2
    assert report["timeout"]["observed"] == "completed"
    assert report["error_format"]["status"] == 400
    assert report["error_format"]["error_keys"] == ["code", "type"]
    assert report["capability_matrix"] == {
        "chat_available": True,
        "embeddings_available": True,
        "json_schema_supported": True,
        "models_available": True,
        "context_window": 8192,
        "deployment_identifiable": True,
    }
    assert "secret" not in json.dumps(report)


def test_probe_sanitizes_urls_in_model_metadata(tmp_path: Path) -> None:
    settings = _probe_settings(tmp_path, llm_api_key="top-secret")
    report = probe_capabilities(
        settings,
        transport=httpx.MockTransport(
            _probe_handler(
                models=[
                    {
                        "id": "test-model",
                        "root": "https://account:password@example.test/model"
                        "?access_token=hidden&key=top-secret",
                        "max_model_len": 8192,
                    }
                ]
            )
        ),
        sleep=lambda _: None,
    )
    text = json.dumps(report)
    assert "password" not in text
    assert "access_token" not in text
    assert "top-secret" not in text
    assert report["models"]["deployment_metadata"]["root"].startswith("https://example.test/model")


def test_fake_mode_probe_report_is_sanitized(tmp_path: Path) -> None:
    model_url = "https://account:password@example.test/model?access_token=hidden&key=review-key"
    settings = _settings(
        tmp_path,
        ai_mode="fake",
        llm_model=model_url,
        llm_api_key="review-key",
    )

    def handler(request: httpx.Request) -> httpx.Response:  # pragma: no cover - must not run
        raise AssertionError("fake mode must not contact an endpoint")

    report = probe_capabilities(settings, transport=httpx.MockTransport(handler))
    text = json.dumps(report)
    assert report["probed"] is False
    assert "password" not in text
    assert "access_token" not in text
    assert "review-key" not in text


def test_offline_summary_is_sanitized(tmp_path: Path) -> None:
    model_url = "https://account:password@example.test/model?access_token=hidden&key=review-key"
    settings = _settings(
        tmp_path,
        ai_mode="fake",
        llm_model=model_url,
        llm_api_key="review-key",
    )
    summary = offline_summary(settings, reason="not requested")
    text = json.dumps(summary)
    assert "password" not in text
    assert "access_token" not in text
    assert "review-key" not in text


@pytest.mark.parametrize("status", [200, 401])
def test_logs_sanitize_url_credentials(status: int, caplog: pytest.LogCaptureFixture) -> None:
    model_url = "https://account:password@example.test/model?access_token=hidden&key=review-key"

    def handler(request: httpx.Request) -> httpx.Response:
        if status == 401:
            return httpx.Response(401, json={"error": {"code": "invalid_api_key"}})
        return _completion_response()

    provider = _chat_provider(
        handler,
        model=model_url,
        api_key="review-key",
        logger=logging.getLogger(f"test.ai.url.{status}"),
    )
    with caplog.at_level(logging.INFO):
        if status == 401:
            with pytest.raises(ProviderAuthenticationError):
                provider.complete([ChatMessage(role="user", content="hello")])
        else:
            provider.complete([ChatMessage(role="user", content="hello")])
    assert "password" not in caplog.text
    assert "access_token" not in caplog.text
    assert "review-key" not in caplog.text


def test_probe_sanitizes_dynamic_model_id_keys(tmp_path: Path) -> None:
    model_url = "https://account:password@example.test/model?access_token=hidden&key=review-key"
    settings = _probe_settings(tmp_path, llm_model=model_url, llm_api_key="review-key")
    report = probe_capabilities(
        settings,
        transport=httpx.MockTransport(
            _probe_handler(
                models=[{"id": model_url, "max_model_len": 4096}],
                include_chat_model=False,
            )
        ),
        sleep=lambda _: None,
    )
    text = json.dumps(report)
    assert "password" not in text
    assert "access_token" not in text
    assert "review-key" not in text
    assert "https://example.test/model" in text


def test_probe_does_not_claim_identity_from_an_unrelated_catalogue(tmp_path: Path) -> None:
    settings = _probe_settings(tmp_path, llm_model="configured-alias")
    report = probe_capabilities(
        settings,
        transport=httpx.MockTransport(
            _probe_handler(
                models=[{"id": "other-model"}],
                include_chat_model=False,
            )
        ),
        sleep=lambda _: None,
    )
    assert report["models"]["model_ids"] == ["other-model"]
    assert report["models"]["configured_model_found"] is False
    assert report["deployment_identifiable"] is False
    assert report["chat"]["observed_model"] is None
    assert report["json_schema"]["observed_model"] is None


def test_probe_reports_embeddings_unavailable_without_substituting_chat(tmp_path: Path) -> None:
    settings = _probe_settings(tmp_path, embed_base_url=None, embed_model=None)
    report = probe_capabilities(
        settings,
        transport=httpx.MockTransport(_probe_handler()),
        sleep=lambda _: None,
    )
    assert report["embeddings"]["available"] is False
    assert "not configured" in report["embeddings"]["reason"]
    assert report["capability_matrix"]["chat_available"] is True
    assert report["capability_matrix"]["embeddings_available"] is False


def test_probe_reports_an_absent_embedding_endpoint(tmp_path: Path) -> None:
    settings = _probe_settings(tmp_path)
    report = probe_capabilities(
        settings,
        transport=httpx.MockTransport(_probe_handler(embedding_status=404)),
        sleep=lambda _: None,
    )
    assert report["embeddings"]["available"] is False
    assert report["embeddings"]["error_code"] == "provider-capability-error"
    assert report["embeddings"]["status"] == 404


def test_probe_reports_json_schema_unsupported(tmp_path: Path) -> None:
    settings = _probe_settings(tmp_path)
    report = probe_capabilities(
        settings,
        transport=httpx.MockTransport(_probe_handler(schema_status=400)),
        sleep=lambda _: None,
    )
    assert report["json_schema"]["supported"] is False
    assert report["json_schema"]["error_code"] == "provider-capability-error"
    assert report["capability_matrix"]["json_schema_supported"] is False


def test_probe_cli_offline_makes_no_probe(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _clear_ai_env(monkeypatch)
    monkeypatch.setenv("CTA_REPO_ROOT", str(tmp_path))
    assert probe_cli_main([]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["probed"] is False
    assert "base_url" not in json.dumps(report)


def test_probe_cli_offline_sanitizes_model_credentials(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _clear_ai_env(monkeypatch)
    monkeypatch.setenv("CTA_REPO_ROOT", str(tmp_path))
    monkeypatch.setenv(
        "CTA_LLM_MODEL",
        "https://account:password@example.test/model?access_token=hidden&key=review-key",
    )
    monkeypatch.setenv("CTA_LLM_API_KEY", "review-key")
    assert probe_cli_main([]) == 0
    output = capsys.readouterr().out
    assert "password" not in output
    assert "access_token" not in output
    assert "review-key" not in output
    assert "https://example.test/model" in output


def test_probe_cli_refuses_a_repository_report(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _clear_ai_env(monkeypatch)
    monkeypatch.setenv("CTA_REPO_ROOT", str(tmp_path))
    target = tmp_path / "capabilities.json"
    assert probe_cli_main(["--report", str(target)]) == 2
    assert not target.exists()


def test_offline_summary_omits_the_base_url(tmp_path: Path) -> None:
    summary = offline_summary(_probe_settings(tmp_path), reason="not requested")
    assert summary["probed"] is False
    assert "base_url" not in summary["llm"]
    assert "base_url" not in summary["embeddings"]


def test_sanitizer_redacts_dynamic_dictionary_keys() -> None:
    report = {
        "https://user:pass@host/path?token=secret": 1,
        "nested": {"https://user:pass@host/other?key=secret": 2},
    }
    sanitized = sanitize_capability_report(report, secrets=("secret",))
    text = json.dumps(sanitized)
    assert "pass" not in text
    assert "token" not in text
    assert "secret" not in text
    assert "https://host/path" in text
    assert "https://host/other" in text


def test_sanitizer_redacts_credentials_and_url_query() -> None:
    report = {
        "api_key": "top-secret",
        "base_url": "http://user:password@host/v1?key=top-secret",
        "nested": {"authorization": "Bearer top-secret", "total_tokens": 5},
    }
    sanitized = sanitize_capability_report(report, secrets=("top-secret",))
    assert sanitized["api_key"] == "<redacted>"
    assert sanitized["nested"]["authorization"] == "<redacted>"
    assert sanitized["nested"]["total_tokens"] == 5
    assert "top-secret" not in json.dumps(sanitized)
    assert "password" not in json.dumps(sanitized)
    assert sanitize_url("http://user:pass@host/v1?key=secret") == "http://host/v1"
