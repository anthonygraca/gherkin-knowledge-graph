"""HTTP routes.

Endpoints are grouped by intent, which is also the honesty axis of the system:

* **reads** — real implementations over the ingested fixture repository.
* **ingestion** — parses the configured repository at a revision.
* **assurance** — deterministic rules over ingested facts; no model calls.
* **discovery** — proposals only; provider failure is a typed problem, never a finding.
* **review** — trusted-local-operator capture and append-only decisions (review_routes.py).
"""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Path, Query

from app.api.deps import (
    EvaluatorDep,
    ProvidersDep,
    RepositoryDep,
    SettingsDep,
    StoreDep,
)
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
    ProviderCatalogResponse,
    ProviderDescriptor,
    ThreadResponse,
)
from app.domain.enums import ArtifactType
from app.domain.errors import DomainError, ProviderUnavailable
from app.domain.models import ARTIFACT_ID_PATTERN, Artifact
from app.version import PACKAGE_VERSION, SCHEMA_VERSION

logger = logging.getLogger(__name__)

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
        "Both endpoints evaluate the deterministic rule set over the ingested revision: coverage "
        "gaps, unreviewed proposals, lifecycle review, confirmed execution failures, and "
        "change-driven reverification. Findings are compared against the hand-labeled oracle in "
        "`fixtures/banking-demo/expected/`; this endpoint no longer replays a recorded sample."
    ),
)
def get_findings(
    repository: RepositoryDep,
    evaluator: EvaluatorDep,
    baseline: Annotated[str | None, BASELINE_QUERY] = None,
) -> FindingsResponse:
    """Evaluated by the deterministic rule set, not replayed from a recorded sample."""
    canonical = repository.resolve_baseline(baseline)
    return FindingsResponse(
        schema_version=SCHEMA_VERSION,
        baseline=canonical,
        findings=evaluator.evaluate(canonical),
    )


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
    settings: SettingsDep,
) -> DiscoveryResponse:
    repository.get_artifact(payload.artifact_id)  # 404 when the source artifact is unknown
    resolved = payload.provider or settings.discovery_provider
    try:
        provider = providers.get(payload.provider)  # 400 when the provider name is unknown
    except DomainError:
        raise
    except Exception as exc:  # noqa: BLE001 - provider construction is an availability boundary
        logger.warning(
            "discovery provider %s could not be constructed for %s: %s",
            resolved,
            payload.artifact_id,
            exc,
        )
        raise ProviderUnavailable(
            f"Discovery provider {resolved!r} could not be constructed: {exc}",
            failed_provider=resolved,
        ) from exc
    try:
        candidates = provider.discover(
            payload.artifact_id,
            top_k=payload.top_k,
            relation_types=payload.relation_types,
            baseline=payload.baseline,
        )
    except DomainError:
        raise
    except Exception as exc:  # noqa: BLE001 - provider plugins are an availability boundary
        logger.warning(
            "discovery provider %s failed for %s at %s: %s",
            provider.provider_name,
            payload.artifact_id,
            payload.baseline,
            exc,
        )
        raise ProviderUnavailable(
            f"Discovery provider {provider.provider_name!r} could not execute for "
            f"{payload.artifact_id!r} at {payload.baseline or 'the latest baseline'}: {exc}",
            failed_provider=provider.provider_name,
        ) from exc
    return DiscoveryResponse(
        schema_version=SCHEMA_VERSION,
        artifact_id=payload.artifact_id,
        provider=provider.provider_name,
        model_version=provider.model_version,
        # Prefer the per-candidate binding for the requested baseline when one exists; the
        # provider-level attribute is only a construction-time default.
        index_revision=(
            candidates[0].index_revision
            if candidates
            else (
                provider.binding_for(payload.baseline)
                if hasattr(provider, "binding_for")
                else provider.index_revision
            )
        ),
        candidates=candidates,
    )


@router.get(
    "/api/discovery/providers",
    response_model=ProviderCatalogResponse,
    tags=["discovery"],
    summary="Effective discovery providers with presentation kind",
)
def get_discovery_providers(providers: ProvidersDep) -> ProviderCatalogResponse:
    catalog = providers.catalog()
    default = next((item["name"] for item in catalog if item["default"]), "fake")
    return ProviderCatalogResponse(
        schema_version=SCHEMA_VERSION,
        default=default,
        providers=[ProviderDescriptor.model_validate(item) for item in catalog],
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
    "/api/assurance/evaluate",
    response_model=FindingsResponse,
    tags=["assurance"],
    responses={400: _PROBLEM_400, 404: _PROBLEM_404, 422: {"model": ProblemDetails}},
    summary="Run the implemented deterministic assurance rules",
)
def post_assurance_evaluate(
    payload: EvaluateRequest, repository: RepositoryDep, evaluator: EvaluatorDep
) -> FindingsResponse:
    canonical = repository.resolve_baseline(payload.baseline)
    findings = evaluator.evaluate(canonical, policy=payload.policy)
    return FindingsResponse(
        schema_version=SCHEMA_VERSION,
        baseline=canonical,
        findings=findings,
    )
