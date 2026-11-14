"""Additive code-retrieval surface (AI-07).

The endpoint separates CTA's authoritative artifact identity from external retrieval: hits are
mapped to canonical artifacts at one commit, and the response carries path/lines/revision/hash plus
the CTA-computed snapshot binding. No link, review, evidence, or finding is written.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import SettingsDep, StoreDep
from app.discovery.cocoindex import CocoIndexError
from app.discovery.code_index import (
    CodeDiscovery,
    configured_model_version,
    live_client,
)
from app.domain.errors import RetrievalUnavailable
from app.domain.retrieval import CodeRetrievalRequest, CodeRetrievalResponse, RetrievalMethod
from app.ingestion.repository import GitRepository

router = APIRouter(prefix="/api/retrieval", tags=["retrieval"])


@router.post(
    "/code",
    response_model=CodeRetrievalResponse,
    responses={503: {"description": "The configured retrieval provider is unavailable."}},
    summary="Propose source/test artifacts for a scenario at one baseline",
)
def post_code_retrieval(
    payload: CodeRetrievalRequest, store: StoreDep, settings: SettingsDep
) -> CodeRetrievalResponse:
    client = None
    require_live_root = False
    wants_cocoindex = payload.method in (None, RetrievalMethod.COCOINDEX)
    if wants_cocoindex and settings.cocoindex_enabled:
        try:
            client = live_client(settings)
            require_live_root = True
        except CocoIndexError as exc:
            if payload.method is RetrievalMethod.COCOINDEX:
                raise RetrievalUnavailable(str(exc)) from exc
            # Auto mode falls back to lexical; the response limitations explain it.
    discovery = CodeDiscovery(
        repository=store,
        git=GitRepository(settings.fixture_repo),
        repository_name=settings.fixture,
        client=client,
        model_version=(
            configured_model_version(settings)
            if wants_cocoindex
            else "deterministic-token-overlap-v1"
        ),
        require_live_root=require_live_root,
    )
    try:
        return discovery.retrieve(payload)
    except CocoIndexError as exc:
        raise RetrievalUnavailable(str(exc)) from exc
