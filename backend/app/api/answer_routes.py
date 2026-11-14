"""Evidence-grounded answer surface (AI-08). Additive; no model required."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import SettingsDep, StoreDep
from app.discovery.code_index import CodeDiscovery
from app.domain.answers import AnswerRequest, AnswerResponse
from app.graphrag.context import AnswerService
from app.ingestion.repository import GitRepository

router = APIRouter(prefix="/api", tags=["answers"])


@router.post(
    "/answers",
    response_model=AnswerResponse,
    summary="Answer a requirement question from accepted links and recorded evidence",
)
def post_answer(payload: AnswerRequest, store: StoreDep, settings: SettingsDep) -> AnswerResponse:
    code = (
        CodeDiscovery(
            repository=store,
            git=GitRepository(settings.fixture_repo),
            repository_name=settings.fixture,
            model_version="deterministic-token-overlap-v1",
        )
        if payload.include_semantic_candidates
        else None
    )
    return AnswerService(store, code_discovery=code).answer(payload)
