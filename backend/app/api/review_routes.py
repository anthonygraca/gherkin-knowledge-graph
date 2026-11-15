"""Trusted-local-operator review surface (AS-06).

Every route here is local-only. Reads project committed decisions over immutable baseline facts;
writes append to the application-owned journal and publish only after a committed pair exists.
"""

from __future__ import annotations

from typing import Annotated
from urllib.parse import urlsplit

from fastapi import APIRouter, Depends, Path, Query, Request, Response

from app.api.deps import ReviewDep, SettingsDep
from app.domain.api import ProblemDetails
from app.domain.errors import (
    ReviewIdentityMismatch,
    ReviewIdentityUnavailable,
    ReviewLoopbackRequired,
    ReviewOriginForbidden,
)
from app.domain.models import ARTIFACT_ID_PATTERN, LINK_ID_PATTERN, TraceLink
from app.domain.review import (
    LinkProposalResponse,
    ProposalCaptureRequest,
    ReviewConfigResponse,
    ReviewRequestPayload,
    WorkspaceHistoryResponse,
    WorkspaceProposalsResponse,
    WorkspaceThreadResponse,
)

router = APIRouter(prefix="/api", tags=["review"])

_LOOPBACK_PEERS = {
    "127.0.0.1",
    "::1",
    "localhost",
    "testclient",
    "::ffff:127.0.0.1",
}
_LOOPBACK_ORIGIN_HOSTS = {"127.0.0.1", "::1", "localhost"}

BASELINE_QUERY = Query(
    description="Baseline name or commit SHA; omitted means the latest tagged baseline."
)

_PROBLEM_403 = {"model": ProblemDetails, "description": "A local review write is required."}
_PROBLEM_404 = {"model": ProblemDetails, "description": "Unknown artifact, baseline, or proposal."}
_PROBLEM_409 = {"model": ProblemDetails, "description": "Conflicting or stale review state."}
_PROBLEM_422 = {"model": ProblemDetails, "description": "Invalid review or capture request."}
_PROBLEM_503 = {"model": ProblemDetails, "description": "Review identity or storage unavailable."}


def enforce_local_review(request: Request) -> None:
    """Loopback peer plus optional loopback browser origin.

    A missing ``Origin`` is allowed for local CLI/non-browser clients. Any present Origin must be
    an http(s) loopback origin; this is a CSRF boundary, not an authentication mechanism.
    """
    host = request.client.host if request.client else ""
    if host not in _LOOPBACK_PEERS:
        raise ReviewLoopbackRequired(
            f"Review access is limited to the local machine; peer {host!r} is not loopback."
        )
    origin = request.headers.get("origin")
    if origin is None:
        return
    try:
        parsed = urlsplit(origin)
    except ValueError as exc:
        raise ReviewOriginForbidden(
            f"Browser origin {origin!r} is malformed and outside the trusted local boundary."
        ) from exc
    if parsed.scheme not in {"http", "https"} or parsed.hostname not in _LOOPBACK_ORIGIN_HOSTS:
        raise ReviewOriginForbidden(
            f"Browser origin {origin!r} is outside the trusted local review boundary."
        )


async def review_local_guard(request: Request, settings: SettingsDep) -> None:
    """Transport and operator checks run before the request body is validated."""
    enforce_local_review(request)
    if settings.review_operator is None:
        raise ReviewIdentityUnavailable(
            "Review writes are disabled: no operator identity is configured (CTA_REVIEW_OPERATOR)."
        )


async def review_decision_guard(request: Request, settings: SettingsDep) -> None:
    await review_local_guard(request, settings)
    try:
        body = await request.json()
    except Exception:  # noqa: BLE001 - malformed JSON is left to body validation
        return
    reviewer = body.get("reviewer_id") if isinstance(body, dict) else None
    if isinstance(reviewer, str) and reviewer != settings.review_operator:
        raise ReviewIdentityMismatch(
            f"Reviewer {reviewer!r} is not the configured local operator "
            f"{settings.review_operator!r}. Review writes are server-assigned."
        )


@router.get(
    "/review/config",
    response_model=ReviewConfigResponse,
    responses={403: _PROBLEM_403},
    summary="Whether local review writes are enabled and which operator is assigned",
)
def get_review_config(request: Request, review: ReviewDep) -> ReviewConfigResponse:
    enforce_local_review(request)
    return review.config()


@router.post(
    "/link-proposals",
    response_model=LinkProposalResponse,
    status_code=201,
    dependencies=[Depends(review_local_guard)],
    responses={400: _PROBLEM_403, 409: _PROBLEM_409, 422: _PROBLEM_422, 503: _PROBLEM_503},
    summary="Capture a discovery candidate as a proposed link (never accepts it)",
)
def post_link_proposal(
    payload: ProposalCaptureRequest,
    response: Response,
    review: ReviewDep,
) -> LinkProposalResponse:
    result = review.capture(payload)
    if not result.created:
        response.status_code = 200
    return result


@router.post(
    "/links/{link_id}/review",
    response_model=TraceLink,
    dependencies=[Depends(review_decision_guard)],
    responses={
        403: _PROBLEM_403,
        404: _PROBLEM_404,
        409: _PROBLEM_409,
        422: _PROBLEM_422,
        503: _PROBLEM_503,
    },
    summary="Record an append-only reviewer decision on a proposed link",
)
def post_link_review(
    link_id: Annotated[str, Path(pattern=LINK_ID_PATTERN)],
    payload: ReviewRequestPayload,
    review: ReviewDep,
) -> TraceLink:
    return review.review(
        link_id,
        decision=payload.decision,
        reviewer_id=payload.reviewer_id,
        baseline=payload.baseline,
        reason=payload.reason,
        reason_present="reason" in payload.model_fields_set,
    )


@router.get(
    "/workspace/threads/{artifact_id}",
    response_model=WorkspaceThreadResponse,
    responses={403: _PROBLEM_403, 404: _PROBLEM_404},
    summary="Thread projection with committed review decisions applied",
)
def get_workspace_thread(
    artifact_id: Annotated[str, Path(pattern=ARTIFACT_ID_PATTERN)],
    request: Request,
    review: ReviewDep,
    baseline: Annotated[str | None, BASELINE_QUERY] = None,
) -> WorkspaceThreadResponse:
    enforce_local_review(request)
    return review.thread(artifact_id, baseline=baseline)


@router.get(
    "/workspace/proposals",
    response_model=WorkspaceProposalsResponse,
    responses={403: _PROBLEM_403, 404: _PROBLEM_404},
    summary="Pending review queue for a baseline",
)
def get_workspace_proposals(
    request: Request,
    review: ReviewDep,
    baseline: Annotated[str | None, BASELINE_QUERY] = None,
) -> WorkspaceProposalsResponse:
    enforce_local_review(request)
    return review.pending(baseline)


@router.get(
    "/workspace/history",
    response_model=WorkspaceHistoryResponse,
    responses={403: _PROBLEM_403, 404: _PROBLEM_404},
    summary="Capture and decision history applicable to a baseline",
)
def get_workspace_history(
    request: Request,
    review: ReviewDep,
    baseline: Annotated[str | None, BASELINE_QUERY] = None,
) -> WorkspaceHistoryResponse:
    enforce_local_review(request)
    return review.history(baseline)
