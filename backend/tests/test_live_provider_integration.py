"""Opt-in live integration test. It is NOT RUN by the default offline suite.

Enable only with ``CTA_AI_LIVE_TESTS=1`` and a valid ``CTA_AI_MODE=live`` configuration. The
test sends synthetic canary text only and never prints the endpoint, credentials, or a full
response. A missing configuration is a skip (NOT RUN), not a pass.
"""

from __future__ import annotations

import os

import pytest

from app.discovery.ai import ChatMessage
from app.discovery.registry import ProviderRegistry
from app.settings import SettingsError, load_settings


def _live_readiness() -> tuple[bool, str]:
    enabled = os.environ.get("CTA_AI_LIVE_TESTS", "").strip().lower()
    if enabled not in {"1", "true", "yes", "on"}:
        return False, "CTA_AI_LIVE_TESTS is not enabled"
    if os.environ.get("CTA_AI_MODE", "").strip().lower() != "live":
        return False, "CTA_AI_MODE is not live"
    try:
        load_settings()
    except SettingsError as exc:
        return False, f"configuration is incomplete: {exc}"
    return True, ""


_LIVE_READY, _LIVE_REASON = _live_readiness()
pytestmark = pytest.mark.skipif(not _LIVE_READY, reason=f"live provider NOT RUN: {_LIVE_REASON}")


def test_live_chat_completion_returns_an_observed_response() -> None:
    settings = load_settings()
    registry = ProviderRegistry(settings)
    completion = registry.chat().complete(
        [ChatMessage(role="user", content="Reply with the single word: canary.")],
        temperature=0.0,
        max_tokens=64,
    )
    assert completion.text.strip()
    assert completion.model
    assert completion.http_status == 200
    assert completion.latency_ms >= 0
    assert completion.provider == "openai-compatible"


def test_live_embeddings_when_configured() -> None:
    settings = load_settings()
    provider = ProviderRegistry(settings).embeddings()
    if provider is None:
        pytest.skip("live embeddings NOT RUN: CTA_EMBED_BASE_URL/CTA_EMBED_MODEL not configured")
    batch = provider.embed(["CTA live canary alpha", "CTA live canary beta"])
    assert batch.dimensions >= 1
    assert len(batch.vectors) == 2
    assert all(len(vector) == batch.dimensions for vector in batch.vectors)
    assert batch.model
    assert batch.http_status == 200
