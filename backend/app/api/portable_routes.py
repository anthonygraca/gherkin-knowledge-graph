"""Repository-scoped query surface for repositories CTA did not create.

These routes never touch the strict fixture artifacts: no requirement nodes are manufactured, and a
repository with no requirements is not "broken". Every response carries the repository id, the
resolved commit, and the tree digest it describes, so a caller can pin exactly what it read.

Query-time honesty rules enforced here:

* no report imported -> bindings answer ``not_available`` with a reason, never an undefined step;
* an unindexed repository or revision -> 404, never an implicit index of a different ref;
* a report whose tested commit is not the indexed snapshot -> 400, never a silent reattribution.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Request

from app.domain.errors import InvalidRequest, ScenarioNotFound
from app.domain.executable import (
    ExecutableFindingResponse,
    RelationListResponse,
)
from app.domain.portable import (
    BatchIndexRequest,
    BindingAvailability,
    BindingResponse,
    ExecutionImportRequest,
    ExecutionImportResponse,
    ExecutionListResponse,
    PortableIndexSummary,
    PortableScenario,
    RepositoryListResponse,
    ScenarioListResponse,
    StepListResponse,
    StepMatchStatus,
)
from app.ingestion.portable import PortableIndexError
from app.persistence.portable import PortableRegistry
from app.version import SCHEMA_VERSION

router = APIRouter(prefix="/api/repositories", tags=["portable"])

REPOSITORY_ID = Path(pattern=r"^[a-z0-9][a-z0-9._-]{0,127}$", description="Repository id")
REVISION_QUERY = Query(
    description="Pinned commit (full or unique prefix). Omitted means the latest indexed commit."
)


def provide_registry(request: Request) -> PortableRegistry:
    return request.app.state.portable


RegistryDep = Annotated[PortableRegistry, Depends(provide_registry)]


@router.post(
    "/index",
    response_model=PortableIndexSummary,
    summary="Index a local Git repository at a pinned commit (read-only, no hooks)",
)
def index_repository(payload: BatchIndexRequest, registry: RegistryDep) -> PortableIndexSummary:
    try:
        return registry.index(
            payload.path, repository_id=payload.repository_id, revision=payload.revision
        )
    except PortableIndexError as exc:
        raise InvalidRequest(str(exc)) from exc


@router.get(
    "",
    response_model=RepositoryListResponse,
    summary="Repositories indexed in this process, with their pinned revisions",
)
def list_repositories(registry: RegistryDep) -> RepositoryListResponse:
    return RepositoryListResponse(schema_version=SCHEMA_VERSION, repositories=registry.summaries())


@router.get(
    "/{repository_id}/scenarios",
    response_model=ScenarioListResponse,
    responses={404: {"description": "Repository or revision not indexed"}},
    summary="Scenarios at a pinned revision, filtered by path or tag",
)
def list_scenarios(
    repository_id: Annotated[str, REPOSITORY_ID],
    registry: RegistryDep,
    revision: Annotated[str | None, REVISION_QUERY] = None,
    path: Annotated[str | None, Query(description="Exact feature path")] = None,
    tag: Annotated[str | None, Query(description="Tag name, with or without '@'")] = None,
) -> ScenarioListResponse:
    snapshot = registry.snapshot(repository_id, revision)
    wanted_tag = f"@{tag.lstrip('@')}" if tag else None
    scenarios = [scenario for feature in snapshot.features for scenario in feature.scenarios]
    if path is not None:
        scenarios = [scenario for scenario in scenarios if scenario.path == path]
    if wanted_tag is not None:
        scenarios = [scenario for scenario in scenarios if wanted_tag in scenario.tags]
    return ScenarioListResponse(
        schema_version=SCHEMA_VERSION,
        repository_id=snapshot.repository_id,
        revision=snapshot.revision,
        source_digest=snapshot.source_digest,
        parser=snapshot.parser,
        scenarios=scenarios,
    )


@router.get(
    "/{repository_id}/scenario",
    response_model=PortableScenario,
    responses={404: {"description": "Repository, revision, or scenario not indexed"}},
    summary="One scenario with its steps and Scenario Outline instances",
)
def get_scenario(
    repository_id: Annotated[str, REPOSITORY_ID],
    registry: RegistryDep,
    scenario_key: Annotated[str, Query(min_length=1)],
    revision: Annotated[str | None, REVISION_QUERY] = None,
) -> PortableScenario:
    snapshot = registry.snapshot(repository_id, revision)
    scenario = snapshot.scenario(scenario_key)
    if scenario is None:
        raise ScenarioNotFound(
            f"scenario key {scenario_key!r} is not present at {snapshot.revision}; "
            "query /scenarios for the keys at this revision"
        )
    return scenario


@router.get(
    "/{repository_id}/steps",
    response_model=StepListResponse,
    summary="Steps at a pinned revision, filtered by scenario or step text",
)
def list_steps(
    repository_id: Annotated[str, REPOSITORY_ID],
    registry: RegistryDep,
    revision: Annotated[str | None, REVISION_QUERY] = None,
    scenario_key: Annotated[str | None, Query()] = None,
    text: Annotated[str | None, Query(description="Substring match on step text")] = None,
) -> StepListResponse:
    snapshot = registry.snapshot(repository_id, revision)
    scenarios = [scenario for feature in snapshot.features for scenario in feature.scenarios]
    if scenario_key is not None:
        scenarios = [scenario for scenario in scenarios if scenario.scenario_key == scenario_key]
    steps = [step for scenario in scenarios for step in scenario.steps]
    if text is not None:
        steps = [step for step in steps if text in step.text]
    seen: set[str] = set()
    unique = []
    for step in steps:
        if step.step_key in seen:
            continue
        seen.add(step.step_key)
        unique.append(step)
    return StepListResponse(
        schema_version=SCHEMA_VERSION,
        repository_id=snapshot.repository_id,
        revision=snapshot.revision,
        source_digest=snapshot.source_digest,
        parser=snapshot.parser,
        steps=unique,
    )


@router.get(
    "/{repository_id}/bindings",
    response_model=BindingResponse,
    summary="Framework-reported step definitions and resolutions (or an explicit not_available)",
)
def get_bindings(
    repository_id: Annotated[str, REPOSITORY_ID],
    registry: RegistryDep,
    revision: Annotated[str | None, REVISION_QUERY] = None,
) -> BindingResponse:
    snapshot = registry.snapshot(repository_id, revision)
    availability, reason, definitions, resolutions, reports = registry.bindings(
        repository_id, snapshot.revision
    )
    tested_commit = reports[0].executions[0].tested_commit if reports else None
    return BindingResponse(
        schema_version=SCHEMA_VERSION,
        repository_id=snapshot.repository_id,
        revision=snapshot.revision,
        source_digest=snapshot.source_digest,
        parser=snapshot.parser,
        availability=availability,
        reason=reason,
        adapter=reports[0].adapter if reports else None,
        tested_commit=tested_commit,
        report_uri=reports[0].report_uri if reports else None,
        step_definitions=list(definitions),
        resolutions=list(resolutions),
    )


@router.get(
    "/{repository_id}/unresolved-steps",
    response_model=BindingResponse,
    summary="Steps the framework reported as undefined or ambiguous (requires a report)",
)
def get_unresolved_steps(
    repository_id: Annotated[str, REPOSITORY_ID],
    registry: RegistryDep,
    revision: Annotated[str | None, REVISION_QUERY] = None,
) -> BindingResponse:
    snapshot = registry.snapshot(repository_id, revision)
    availability, reason, definitions, resolutions, reports = registry.bindings(
        repository_id, snapshot.revision
    )
    unresolved = [
        resolution
        for resolution in resolutions
        if resolution.status in (StepMatchStatus.UNDEFINED, StepMatchStatus.AMBIGUOUS)
    ]
    return BindingResponse(
        schema_version=SCHEMA_VERSION,
        repository_id=snapshot.repository_id,
        revision=snapshot.revision,
        source_digest=snapshot.source_digest,
        parser=snapshot.parser,
        availability=availability,
        reason=(
            reason
            if availability is BindingAvailability.NOT_AVAILABLE
            else f"{len(unresolved)} step(s) reported undefined or ambiguous"
        ),
        adapter=reports[0].adapter if reports else None,
        tested_commit=reports[0].executions[0].tested_commit if reports else None,
        report_uri=reports[0].report_uri if reports else None,
        step_definitions=list(definitions) if availability is BindingAvailability.AVAILABLE else [],
        resolutions=unresolved,
    )


@router.post(
    "/{repository_id}/reports",
    response_model=ExecutionImportResponse,
    responses={400: {"description": "Report does not apply to the indexed revision"}},
    summary="Import an existing Cucumber Messages report for the indexed commit",
)
def import_report(
    repository_id: Annotated[str, REPOSITORY_ID],
    payload: ExecutionImportRequest,
    registry: RegistryDep,
) -> ExecutionImportResponse:
    snapshot = registry.snapshot(repository_id, payload.tested_commit)
    report, already = registry.import_report(repository_id, payload)
    return ExecutionImportResponse(
        schema_version=SCHEMA_VERSION,
        repository_id=snapshot.repository_id,
        revision=snapshot.revision,
        source_digest=snapshot.source_digest,
        parser=snapshot.parser,
        report_uri=report.report_uri,
        report_digest=report.report_digest,
        tested_commit=snapshot.revision,
        adapter=report.adapter,
        imported=not already,
        execution_count=len(report.executions),
        step_definition_count=len(report.step_definitions),
    )


@router.get(
    "/{repository_id}/executions",
    response_model=ExecutionListResponse,
    summary="Observed scenario executions at a pinned revision",
)
def list_executions(
    repository_id: Annotated[str, REPOSITORY_ID],
    registry: RegistryDep,
    revision: Annotated[str | None, REVISION_QUERY] = None,
) -> ExecutionListResponse:
    snapshot = registry.snapshot(repository_id, revision)
    executions, _ = registry.executions(repository_id, snapshot.revision)
    return ExecutionListResponse(
        schema_version=SCHEMA_VERSION,
        repository_id=snapshot.repository_id,
        revision=snapshot.revision,
        source_digest=snapshot.source_digest,
        parser=snapshot.parser,
        executions=executions,
        coverage=registry.coverage(repository_id, snapshot.revision),
        reports=registry.provenance(repository_id, snapshot.revision),
    )


@router.get(
    "/{repository_id}/relations",
    response_model=RelationListResponse,
    summary="Extracted, matched, and observed executable relations",
)
def list_relations(
    repository_id: Annotated[str, REPOSITORY_ID],
    registry: RegistryDep,
    revision: Annotated[str | None, REVISION_QUERY] = None,
) -> RelationListResponse:
    snapshot = registry.snapshot(repository_id, revision)
    _, reports = registry.executions(repository_id, snapshot.revision)
    return RelationListResponse(
        schema_version=SCHEMA_VERSION,
        repository_id=snapshot.repository_id,
        revision=snapshot.revision,
        tested_commit=reports[0].executions[0].tested_commit if reports else None,
        relations=registry.relations(repository_id, snapshot.revision),
    )


@router.get(
    "/{repository_id}/executable-findings",
    response_model=ExecutableFindingResponse,
    summary="Executability findings derived only from framework evidence",
)
def list_executable_findings(
    repository_id: Annotated[str, REPOSITORY_ID],
    registry: RegistryDep,
    revision: Annotated[str | None, REVISION_QUERY] = None,
) -> ExecutableFindingResponse:
    snapshot = registry.snapshot(repository_id, revision)
    findings, tested_commit = registry.findings(repository_id, snapshot.revision)
    return ExecutableFindingResponse(
        schema_version=SCHEMA_VERSION,
        repository_id=snapshot.repository_id,
        revision=snapshot.revision,
        tested_commit=tested_commit,
        findings=findings,
    )
