"""Capability probe for an optional OpenAI-compatible endpoint.

This module is called only from ``tools/probe_ai_capabilities.py --live`` or from tests with a
mocked transport. It sends synthetic canary text only; it never reads repository artifacts, and it
never writes a report by itself. A successful process exit is not evidence of capability: the
returned fields are the observation.
"""

from __future__ import annotations

import hashlib
import time
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from typing import Any

import httpx
from pydantic import BaseModel

from app.discovery.ai import (
    ChatMessage,
    ProviderError,
    parse_rate_limit_headers,
    parse_upstream_code,
    sanitize_capability_report,
    sanitize_text,
)
from app.settings import Settings

# Ask for a final answer explicitly. A reasoning model can spend a small budget entirely on
# reasoning and return no message content; the probe must not mistake that truncation for a
# missing chat capability.
CANARY_CHAT_PROMPT = "Reply with the single word: canary."
CANARY_EMBEDDING_TEXTS = ("CTA canary alpha", "CTA canary beta")
PROBE_TIMEOUT_SECONDS = 0.005
PROBE_SCHEMA_VERSION = "1"


class CanaryAnswer(BaseModel):
    ok: bool
    label: str


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _base_summary(settings: Settings) -> dict[str, Any]:
    summary = {
        "schema_version": PROBE_SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "mode": settings.ai_mode,
        "llm": {
            "base_url": settings.llm_base_url,
            "base_url_configured": settings.llm_base_url is not None,
            "model": settings.llm_model,
            "api_key_present": settings.llm_api_key_present,
        },
        "embeddings": {
            "base_url": settings.embed_base_url,
            "base_url_configured": settings.embed_base_url is not None,
            "model": settings.embed_model,
            "api_key_present": settings.embed_api_key_present,
            "configured": settings.embeddings_configured,
        },
        "vector_backend": settings.vector_backend,
        "live_tests_enabled": settings.ai_live_tests,
        "limits": {
            "configured_timeout_seconds": 10.0,
            "configured_max_retries": 1,
            "retry_after_cap_seconds": 5.0,
            "probe_timeout_seconds": PROBE_TIMEOUT_SECONDS,
            # No endpoint metadata or documentation supplies a concurrency limit here; do not
            # invent one by stress-testing a shared service.
            "concurrency_limit": "unknown",
        },
    }
    return sanitize_capability_report(
        summary, secrets=(settings.llm_api_key, settings.embed_api_key)
    )


def offline_summary(settings: Settings, *, reason: str) -> dict[str, Any]:
    """A report that explicitly did not contact an endpoint. No URL is included."""
    summary = _base_summary(settings)
    summary["probed"] = False
    summary["reason"] = reason
    summary["llm"].pop("base_url", None)
    summary["embeddings"].pop("base_url", None)
    return sanitize_capability_report(
        summary, secrets=(settings.llm_api_key, settings.embed_api_key)
    )


def _headers(api_key: str | None) -> dict[str, str]:
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    return headers


def _raw_request(
    method: str,
    url: str,
    *,
    transport: httpx.BaseTransport | None,
    timeout: float,
    api_key: str | None,
    json_body: Mapping[str, Any] | None = None,
) -> tuple[httpx.Response | None, float, str | None]:
    started = time.perf_counter()
    try:
        with httpx.Client(
            timeout=timeout,
            transport=transport,
            follow_redirects=False,
        ) as client:
            response = client.request(
                method,
                url,
                headers=_headers(api_key),
                json=dict(json_body) if json_body is not None else None,
            )
    except httpx.TimeoutException:
        return None, round((time.perf_counter() - started) * 1000, 3), "timeout"
    except httpx.TransportError:
        return None, round((time.perf_counter() - started) * 1000, 3), "transport"
    return response, round((time.perf_counter() - started) * 1000, 3), None


def _json_or_none(response: httpx.Response) -> Any:
    try:
        return response.json()
    except ValueError:
        return None


def _model_observation(response: httpx.Response, configured_model: str | None) -> dict[str, Any]:
    payload = _json_or_none(response)
    data = payload.get("data") if isinstance(payload, Mapping) else None
    if not isinstance(data, list):
        return {
            "model_ids": [],
            "configured_model_found": False,
            "context_lengths": {},
            "deployment_metadata": None,
        }

    model_ids: list[str] = []
    context_lengths: dict[str, int] = {}
    deployment: dict[str, Any] | None = None
    for item in data:
        if not isinstance(item, Mapping):
            continue
        model_id = item.get("id")
        if not isinstance(model_id, str) or not model_id:
            continue
        model_ids.append(model_id)
        for key in ("max_model_len", "context_length", "max_context_length", "max_input_tokens"):
            value = item.get(key)
            if isinstance(value, int) and value > 0:
                context_lengths[model_id] = value
                break
        if configured_model and model_id == configured_model:
            deployment = {
                key: item.get(key)
                for key in (
                    "id",
                    "object",
                    "created",
                    "owned_by",
                    "root",
                    "parent",
                    "max_model_len",
                )
                if key in item
            }
            for key in ("max_model_len", "context_length", "max_context_length"):
                value = item.get(key)
                if isinstance(value, int) and value > 0:
                    deployment["context_length"] = value
                    break
    return {
        "model_ids": sorted(model_ids),
        "configured_model_found": configured_model in model_ids if configured_model else False,
        "context_lengths": context_lengths,
        "deployment_metadata": deployment,
    }


def _error_record(error: ProviderError, secrets: tuple[str | None, ...]) -> dict[str, Any]:
    return {
        "available": False,
        "error_code": error.code,
        "status": error.status,
        "retryable": error.retryable,
        "upstream_code": sanitize_text(error.upstream_code or "", secrets) or None,
        "detail": sanitize_text(str(error), secrets),
    }


def _usage(completion: Any) -> dict[str, Any] | None:
    return None if completion.usage is None else completion.usage.model_dump(mode="json")


def probe_capabilities(
    settings: Settings,
    *,
    transport: httpx.BaseTransport | None = None,
    sleep: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    """Probe the configured endpoint with synthetic text; return a sanitized observation."""
    report = _base_summary(settings)
    report["probed"] = True
    report["reason"] = "live probe requested"
    if settings.ai_mode != "live":
        report["probed"] = False
        report["reason"] = "CTA_AI_MODE is not live; no endpoint was contacted"
        return sanitize_capability_report(
            report, secrets=(settings.llm_api_key, settings.embed_api_key)
        )

    from app.discovery.ai_http import (
        DEFAULT_MAX_RETRIES,
        DEFAULT_TIMEOUT_SECONDS,
        OpenAICompatibleChatProvider,
        OpenAICompatibleEmbeddingProvider,
    )

    secrets = (settings.llm_api_key, settings.embed_api_key)
    base_url = settings.llm_base_url or ""
    chat = OpenAICompatibleChatProvider(
        base_url=base_url,
        model=settings.llm_model or "",
        api_key=settings.llm_api_key,
        timeout=DEFAULT_TIMEOUT_SECONDS,
        max_retries=DEFAULT_MAX_RETRIES,
        transport=transport,
        sleep=sleep,
    )

    # 1. Endpoint model catalogue, including provenance and any context-window facts it exposes.
    models_response, models_latency, models_error = _raw_request(
        "GET",
        f"{base_url}/models",
        transport=transport,
        timeout=DEFAULT_TIMEOUT_SECONDS,
        api_key=settings.llm_api_key,
    )
    if models_response is None:
        report["models"] = {
            "available": False,
            "error": models_error,
            "latency_ms": models_latency,
        }
        report["context_window"] = "unknown"
        report["deployment_identifiable"] = False
    else:
        observation = _model_observation(models_response, settings.llm_model)
        report["models"] = {
            "available": 200 <= models_response.status_code < 300,
            "status": models_response.status_code,
            "latency_ms": models_latency,
            "rate_limit_headers": parse_rate_limit_headers(models_response.headers),
            **observation,
        }
        if models_response.status_code >= 400:
            payload = _json_or_none(models_response)
            report["models"]["upstream_code"] = parse_upstream_code(payload)
        report["context_window"] = (
            observation["context_lengths"].get(settings.llm_model or "", "unknown")
            if observation["context_lengths"]
            else "unknown"
        )
        report["deployment_identifiable"] = bool(
            observation["configured_model_found"] and observation["deployment_metadata"]
        )

    # 2. One real chat completion with canary text.
    try:
        completion = chat.complete(
            [ChatMessage(role="user", content=CANARY_CHAT_PROMPT)],
            temperature=0.0,
            max_tokens=64,
        )
        report["chat"] = {
            "available": True,
            "provider": completion.provider,
            "configured_model": settings.llm_model,
            "observed_model": completion.model if completion.model_observed else None,
            "model_observed": completion.model_observed,
            "http_status": completion.http_status,
            "latency_ms": completion.latency_ms,
            "usage": _usage(completion),
            "usage_available": completion.usage is not None,
            "finish_reason": completion.finish_reason,
            "response_id": completion.response_id,
            "request_id": completion.request_id,
            "rate_limit_headers": completion.rate_limit_headers,
            "text": completion.text[:200],
            "text_sha256": hashlib.sha256(completion.text.encode("utf-8")).hexdigest(),
            "text_length": len(completion.text),
        }
    except ProviderError as error:
        report["chat"] = _error_record(error, secrets)

    # 3. Schema-constrained JSON support, if offered.
    try:
        structured = chat.complete(
            [
                ChatMessage(
                    role="user", content="Return a JSON object with ok=true and label=canary."
                )
            ],
            temperature=0.0,
            max_tokens=64,
            response_model=CanaryAnswer,
        )
        report["json_schema"] = {
            "supported": True,
            "http_status": structured.http_status,
            "observed_model": structured.model if structured.model_observed else None,
            "model_observed": structured.model_observed,
            "usage": _usage(structured),
            "parsed": structured.parsed,
        }
    except ProviderError as error:
        report["json_schema"] = {**_error_record(error, secrets), "supported": False}

    # 4. Embeddings are a distinct API. If no embedding endpoint is configured or it is absent,
    #    the provider stays unavailable; chat output is never treated as an embedding.
    if not settings.embeddings_configured:
        report["embeddings"]["available"] = False
        report["embeddings"]["reason"] = "CTA_EMBED_BASE_URL/CTA_EMBED_MODEL not configured"
    else:
        embedding = OpenAICompatibleEmbeddingProvider(
            base_url=settings.embed_base_url or "",
            model=settings.embed_model or "",
            api_key=settings.embed_api_key,
            timeout=DEFAULT_TIMEOUT_SECONDS,
            max_retries=DEFAULT_MAX_RETRIES,
            transport=transport,
            sleep=sleep,
        )
        try:
            batch = embedding.embed(CANARY_EMBEDDING_TEXTS)
            first = batch.vectors[0]
            report["embeddings"].update(
                {
                    "available": True,
                    "provider": batch.provider,
                    "configured_model": settings.embed_model,
                    "observed_model": batch.model if batch.model_observed else None,
                    "model_observed": batch.model_observed,
                    "http_status": batch.http_status,
                    "latency_ms": batch.latency_ms,
                    "dimensions": batch.dimensions,
                    "count": len(batch.vectors),
                    "usage": _usage(batch),
                    "usage_available": batch.usage is not None,
                    "request_id": batch.request_id,
                    "rate_limit_headers": batch.rate_limit_headers,
                    "first_vector_head": [round(value, 6) for value in first[:3]],
                    "all_finite": all(
                        all(isinstance(value, float) for value in vector)
                        for vector in batch.vectors
                    ),
                }
            )
        except ProviderError as error:
            report["embeddings"].update(_error_record(error, secrets))

    # 5. Timeout behavior: a deliberately tiny deadline, never a stress test.
    _, timeout_latency, timeout_error = _raw_request(
        "GET",
        f"{base_url}/models",
        transport=transport,
        timeout=PROBE_TIMEOUT_SECONDS,
        api_key=settings.llm_api_key,
    )
    report["timeout"] = {
        "observed": (
            "timeout"
            if timeout_error == "timeout"
            else "completed"
            if timeout_error is None
            else "transport_error"
        ),
        "latency_ms": timeout_latency,
        "configured_timeout_seconds": DEFAULT_TIMEOUT_SECONDS,
        "probe_timeout_seconds": PROBE_TIMEOUT_SECONDS,
    }

    # 6. Error format from one deliberately invalid request. Record shape only, never the message.
    error_response, error_latency, error_transport = _raw_request(
        "POST",
        f"{base_url}/chat/completions",
        transport=transport,
        timeout=DEFAULT_TIMEOUT_SECONDS,
        api_key=settings.llm_api_key,
        json_body={"model": settings.llm_model, "messages": []},
    )
    if error_response is None:
        report["error_format"] = {
            "observed": False,
            "transport_error": error_transport,
            "latency_ms": error_latency,
        }
    else:
        payload = _json_or_none(error_response)
        error_object = payload.get("error") if isinstance(payload, Mapping) else None
        report["error_format"] = {
            "observed": True,
            "status": error_response.status_code,
            "content_type": error_response.headers.get("content-type"),
            "json_object": isinstance(payload, Mapping),
            "error_keys": sorted(error_object) if isinstance(error_object, Mapping) else [],
            "upstream_code": parse_upstream_code(payload),
            "rate_limit_headers": parse_rate_limit_headers(error_response.headers),
            "latency_ms": error_latency,
        }

    report["capability_matrix"] = {
        "chat_available": bool(report.get("chat", {}).get("available")),
        "embeddings_available": bool(report["embeddings"].get("available")),
        "json_schema_supported": bool(report.get("json_schema", {}).get("supported")),
        "models_available": bool(report.get("models", {}).get("available")),
        "context_window": report["context_window"],
        "deployment_identifiable": report["deployment_identifiable"],
    }
    return sanitize_capability_report(report, secrets=secrets)
