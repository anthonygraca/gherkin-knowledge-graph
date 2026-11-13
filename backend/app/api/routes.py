"""HTTP routes.

Endpoints are grouped by intent, which is also the honesty axis of the system:

* **reads** — real implementations over the ingested fixture repository.
* **ingestion** — parses the configured repository at a revision.
* **discovery** — real implementation, fixture provider; returns proposals only.
* **contract-only** — the shape is frozen and documented, the implementation belongs to a
  later milestone; the response is 501 with the owning story, never fake success.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Path, Query

from app.api.deps import FindingsDep, ProvidersDep, RepositoryDep, SettingsDep, StoreDep
from app.domain.api import (
    ArtifactListResponse,
    DiscoveryRequest,
    DiscoveryResponse,
    EvaluateRequest,
    FindingsResponse,
    HealthResponse,
    IngestionRequest,
    IngestionResponse,
    ProblemDetails,
    ReviewRequest,
    ThreadResponse,
)
from app.domain.enums import ArtifactType
from app.domain.errors import FeatureNotImplemented
from app.domain.models import ARTIFACT_ID_PATTERN, LINK_ID_PATTERN, Artifact, TraceLink
from app.version import PACKAGE_VERSION, SCHEMA_VERSION

router = APIRouter()

BASELINE_QUERY = Query(
    description="Baseline name (fixture tag) or commit SHA; omitted means the latest baseline."
)

_PROBLEM_400: dict[str, object] = {
    "model": ProblemDetails,
    "description": "Unknown provider or invalid request.",
}
_PROBLEM_404: dict[str, object] = {
    "model": ProblemDetails,
    "description": "Unknown artifact, baseline, or thread.",
}
_PROBLEM_501: dict[str, object] = {
    "model": ProblemDetails,
    "description": "Contract-only endpoint; the problem document names the owning story.",
}


@router.get(
    "/health",
    response_model=HealthResponse,
    tags=["reads"],
    summary="Liveness, contract version, and fixture baseline status",
)
def get_health(settings: SettingsDep, store: StoreDep, providers: ProvidersDep) -> HealthResponse:
    """``baselines`` comes from the port; ``baseline_commits`` is a fixture-only convenience map."""
    return HealthResponse(
        status="ok",
        package_version=PACKAGE_VERSION,
        schema_version=SCHEMA_VERSION,
        fixture=settings.fixture,
        baselines=store.baselines(),
        baseline_commits=store.baseline_commits(),
        discovery_providers=providers.registered,
    )


@router.get(
    "/api/artifacts",
    response_model=ArtifactListResponse,
    tags=["reads"],
    responses={404: _PROBLEM_404},
    summary="Artifact inventory for a baseline",
)
def list_artifacts(
    repository: RepositoryDep,
    baseline: Annotated[str | None, BASELINE_QUERY] = None,
    artifact_type: Annotated[
        ArtifactType | None, Query(description="Restrict to one artifact type.")
    ] = None,
) -> ArtifactListResponse:
    canonical = repository.resolve_baseline(baseline)
    artifacts = repository.list_artifacts(canonical)
    if artifact_type is not None:
        artifacts = [artifact for artifact in artifacts if artifact.artifact_type is artifact_type]
    return ArtifactListResponse(
        schema_version=SCHEMA_VERSION,
        baseline=canonical,
        artifacts=sorted(artifacts, key=lambda artifact: artifact.artifact_id),
    )


@router.get(
    "/api/artifacts/{artifact_id}",
    response_model=Artifact,
    tags=["reads"],
    responses={404: _PROBLEM_404, 422: {"model": ProblemDetails}},
    summary="One artifact at one baseline",
)
def get_artifact(
    artifact_id: Annotated[str, Path(pattern=ARTIFACT_ID_PATTERN, description="e.g. REQ-001")],
    repository: RepositoryDep,
    baseline: Annotated[str | None, BASELINE_QUERY] = None,
) -> Artifact:
    return repository.get_artifact(artifact_id, baseline=baseline)


@router.get(
    "/api/threads/{artifact_id}",
    response_model=ThreadResponse,
    tags=["reads"],
    responses={404: _PROBLEM_404, 422: {"model": ProblemDetails}},
    summary="Digital thread for one artifact: accepted links, proposals kept separate, evidence",
)
def get_thread(
    artifact_id: Annotated[str, Path(pattern=ARTIFACT_ID_PATTERN, description="e.g. REQ-001")],
    store: StoreDep,
    baseline: Annotated[str | None, BASELINE_QUERY] = None,
) -> ThreadResponse:
    """Assembled from the ingested revision; proposals and evidence stay separate arrays."""
    return store.thread(artifact_id, baseline=baseline)


@router.get(
    "/api/findings",
    response_model=FindingsResponse,
    tags=["reads"],
    responses={404: _PROBLEM_404},
    summary="Assurance findings for a baseline",
    description=(
        "M1 replays the reviewed sample findings committed under `fixtures/api-responses/`, "
        "generated from the hand-labeled oracle in `fixtures/banking-demo/expected/`. "
        "`POST /api/assurance/evaluate` is contract-only in this snapshot (501; AS-01…AS-03). "
        "`GET` keeps the reviewed sample until the rule set is implemented, so M2 findings are not "
        "silently dropped."
    ),
)
def get_findings(
    repository: RepositoryDep,
    findings: FindingsDep,
    baseline: Annotated[str | None, BASELINE_QUERY] = None,
) -> FindingsResponse:
    return findings.findings(repository.resolve_baseline(baseline))


@router.post(
    "/api/discovery",
    response_model=DiscoveryResponse,
    tags=["discovery"],
    responses={400: _PROBLEM_400, 404: _PROBLEM_404, 422: {"model": ProblemDetails}},
    summary="Propose candidate links for a source artifact (never accepts them)",
)
def post_discovery(
    payload: DiscoveryRequest,
    repository: RepositoryDep,
    providers: ProvidersDep,
) -> DiscoveryResponse:
    repository.get_artifact(payload.artifact_id)  # 404 when the source artifact is unknown
    provider = providers.get(payload.provider)  # 400 when the provider name is unknown
    candidates = provider.discover(
        payload.artifact_id,
        top_k=payload.top_k,
        relation_types=payload.relation_types,
    )
    return DiscoveryResponse(
        schema_version=SCHEMA_VERSION,
        artifact_id=payload.artifact_id,
        provider=provider.provider_name,
        model_version=provider.model_version,
        index_revision=provider.index_revision,
        candidates=candidates,
    )


@router.post(
    "/api/ingestion/run",
    response_model=IngestionResponse,
    tags=["ingestion"],
    responses={400: _PROBLEM_400, 404: _PROBLEM_404, 422: {"model": ProblemDetails}},
    summary="Ingest the configured repository at a revision",
)
def post_ingestion_run(payload: IngestionRequest, store: StoreDep) -> IngestionResponse:
    revision = store.ingest(payload.repository, payload.revision)
    return IngestionResponse(
        run_id=f"ing-{revision.commit[:12]}",
        repository=payload.repository,
        baseline=store.label_of(revision.commit),
        artifact_count=len(revision.artifacts),
        accepted_link_count=len(revision.accepted_links),
        proposed_link_count=len(revision.proposed_links),
        evidence_count=len(revision.evidence),
    )


@router.post(
    "/api/links/{link_id}/review",
    response_model=TraceLink,
    tags=["contract-only"],
    responses={501: _PROBLEM_501, 422: {"model": ProblemDetails}},
    summary="Record a reviewer decision on a proposed link (contract only in M0)",
)
def post_link_review(
    link_id: Annotated[str, Path(pattern=LINK_ID_PATTERN)],
    payload: ReviewRequest,
) -> TraceLink:
    raise FeatureNotImplemented(
        story="AS-06 (C-PR1 onward)",
        milestone="M1/M2",
        detail=(
            "Link review with reviewer identity, timestamp, reason, and immutable decision "
            "history is implemented with AS-06. Accepting a link will not change verification "
            "status: an accepted link is not evidence of behaviour."
        ),
    )


@router.post(
    "/api/assurance/evaluate",
    response_model=FindingsResponse,
    tags=["contract-only"],
    responses={501: _PROBLEM_501, 404: _PROBLEM_404, 422: {"model": ProblemDetails}},
    summary="Run deterministic assurance rules (contract only in M0)",
)
def post_assurance_evaluate(payload: EvaluateRequest) -> FindingsResponse:
    raise FeatureNotImplemented(
        story="AS-01, AS-02, AS-03 (C-PR1)",
        milestone="M1/M2",
        detail=(
            "Deterministic rule evaluation is implemented with AS-01…AS-03 against the fixture "
            "oracle. GET /api/findings currently returns the reviewed sample findings."
        ),
    )
