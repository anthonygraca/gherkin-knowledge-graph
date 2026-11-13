"""Opt-in live integration test for the CocoIndex Code adapter. NOT RUN by the default suite.

Enable with ``CTA_CCC_LIVE_TESTS=1``, an initialized ``CTA_CCC_PROJECT_ROOT`` snapshot, live
opt-in, and an indexed CocoIndex project. The test sends one synthetic query only, prints no
credentials or endpoint URLs, and verifies every returned hit against the snapshot on disk.
A missing prerequisite is a skip (NOT RUN), never a pass.
"""

from __future__ import annotations

import os

import pytest

from app.discovery.cocoindex import (
    CocoIndexSearchClient,
    CocoIndexSearchResult,
    verify_hits_against_snapshot,
)
from app.discovery.cocoindex_mcp import (
    StdioMcpTransport,
    child_environment,
    validate_isolated_state,
)
from app.settings import SettingsError, load_settings


def _live_readiness() -> tuple[bool, str]:
    enabled = os.environ.get("CTA_CCC_LIVE_TESTS", "").strip().lower()
    if enabled not in {"1", "true", "yes", "on"}:
        return False, "CTA_CCC_LIVE_TESTS is not enabled"
    try:
        settings = load_settings()
    except SettingsError as exc:
        return False, f"configuration is incomplete: {exc}"
    if not settings.cocoindex_enabled:
        return False, "CTA_CCC_LIVE_OPT_IN/CTA_CCC_PROJECT_ROOT are not configured"
    try:
        validate_isolated_state(child_environment())
    except Exception as exc:  # noqa: BLE001 - readiness reports the reason
        return False, f"isolated CocoIndex state is not configured: {exc}"
    return True, ""


_LIVE_READY, _LIVE_REASON = _live_readiness()
pytestmark = pytest.mark.skipif(
    not _LIVE_READY, reason=f"live CocoIndex integration NOT RUN: {_LIVE_REASON}"
)


def test_live_search_returns_hits_that_match_the_snapshot() -> None:
    settings = load_settings()
    assert settings.ccc_project_root is not None
    transport = StdioMcpTransport(
        executable=settings.ccc_executable,
        project_root=settings.ccc_project_root,
        timeout=180.0,
    )
    capabilities = transport.capabilities(timeout=180.0)
    assert capabilities.server.name == "cocoindex-code"
    assert capabilities.search_tool().name == "search"

    result: CocoIndexSearchResult = CocoIndexSearchClient(transport).search(
        "withdraw whole dollar amounts",
        limit=3,
        languages=("python",),
        paths=("src/*",),
        timeout=180.0,
    )
    assert result.provider == "cocoindex-code"
    assert result.index_identity is None
    assert result.hits, "the live search returned no source hits"
    verify_hits_against_snapshot(settings.ccc_project_root, result.hits)
    assert all(hit.path.endswith(".py") for hit in result.hits)
    assert all(hit.start_line >= 1 and hit.end_line >= hit.start_line for hit in result.hits)
