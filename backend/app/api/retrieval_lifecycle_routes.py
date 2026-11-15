"""CTA-owned retrieval snapshot lifecycle endpoints (AI-03)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Path

from app.api.deps import RetrievalLifecycleDep
from app.domain.api import ProblemDetails
from app.domain.retrieval_lifecycle import (
    CombinedCandidatesResponse,
    CombineRequest,
    ManifestListResponse,
    RetrievalManifest,
    RetrievalRefreshRequest,
)

router = APIRouter(prefix="/api/retrieval", tags=["retrieval"])

_PROBLEM_404 = {"model": ProblemDetails, "description": "No published snapshot."}
_PROBLEM_409 = {"model": ProblemDetails, "description": "Mixed index context."}
_PROBLEM_503 = {"model": ProblemDetails, "description": "Refresh adapter unavailable."}


@router.post(
    "/refresh",
    response_model=RetrievalManifest,
    responses={404: _PROBLEM_404, 503: _PROBLEM_503},
    summary="Plan and publish a CTA retrieval manifest for a baseline",
)
def post_retrieval_refresh(
    payload: RetrievalRefreshRequest, lifecycle: RetrievalLifecycleDep
) -> RetrievalManifest:
    return lifecycle.refresh(
        payload.baseline,
        previous_baseline=payload.previous_baseline,
        config=payload.config,
    )


@router.get(
    "/manifests",
    response_model=ManifestListResponse,
    summary="All published retrieval manifests",
)
def get_retrieval_manifests(lifecycle: RetrievalLifecycleDep) -> ManifestListResponse:
    return lifecycle.manifests()


@router.get(
    "/manifests/{baseline}",
    response_model=RetrievalManifest,
    responses={404: _PROBLEM_404},
    summary="The current published manifest for a baseline",
)
def get_retrieval_manifest(
    baseline: Annotated[str, Path(min_length=1)],
    lifecycle: RetrievalLifecycleDep,
) -> RetrievalManifest:
    return lifecycle.manifest_for(baseline)


@router.post(
    "/combine",
    response_model=CombinedCandidatesResponse,
    responses={409: _PROBLEM_409},
    summary="Combine candidate batches only when every batch shares one snapshot binding",
)
def post_retrieval_combine(
    payload: CombineRequest, lifecycle: RetrievalLifecycleDep
) -> CombinedCandidatesResponse:
    return lifecycle.combine(payload)
