"""In-memory portable repository registry: indexes, imported reports, and derived facts.

Scope rules that prevent silent mixups:

* an index is keyed by ``(repository_id, resolved commit)``; a query never substitutes another
  repository's data;
* importing a report requires the tested commit to be an indexed snapshot of *that* repository;
* the same report bytes imported twice is idempotent; a different report for the same run is a
  separate, append-only record;
* everything here is derived state. Nothing writes to the indexed repository.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from app.assurance.executable_rules import evaluate_executable_findings
from app.domain.errors import ReportNotApplicable, RepositoryNotIndexed
from app.domain.executable import (
    ExecutableFinding,
    ExecutableRelation,
    ExecutionCoverage,
    RelationName,
    RelationOrigin,
    ReportProvenance,
)
from app.domain.portable import (
    BindingAvailability,
    ExecutionImportRequest,
    ExecutionOutcome,
    PortableIndexSummary,
    PortableSnapshot,
    ScenarioExecutionRecord,
    StepDefinitionRecord,
    StepResolutionRecord,
)
from app.ingestion.cucumber_messages import CucumberMessagesAdapter, CucumberReportData
from app.ingestion.portable import PortableIndexer, summarize
from app.ingestion.repository import GitRepository

#: Outcomes that mean the step body actually ran. SKIPPED/PENDING/UNDEFINED/AMBIGUOUS do not.
_INVOKED = {ExecutionOutcome.PASSED, ExecutionOutcome.FAILED}


@dataclass
class RepositoryState:
    repository_id: str
    path: Path
    snapshots: dict[str, PortableSnapshot] = field(default_factory=dict)
    refs: dict[str, str] = field(default_factory=dict)
    reports: dict[str, CucumberReportData] = field(default_factory=dict)
    ingested_at: dict[str, datetime] = field(default_factory=dict)
    metadata: dict[str, tuple[str, str]] = field(default_factory=dict)

    def latest_commit(self) -> str:
        return next(reversed(self.snapshots))


@dataclass
class PortableRegistry:
    """All portable state for this process. Built empty; no default repository is inferred."""

    indexer: PortableIndexer = field(default_factory=PortableIndexer)
    adapter: CucumberMessagesAdapter = field(default_factory=CucumberMessagesAdapter)
    repositories: dict[str, RepositoryState] = field(default_factory=dict)

    # ------------------------------------------------------------------ indexing

    def index(
        self, path: str | Path, *, repository_id: str | None = None, revision: str | None = None
    ) -> PortableIndexSummary:
        snapshot = self.indexer.index(Path(path), repository_id=repository_id, revision=revision)
        state = self.repositories.setdefault(
            snapshot.repository_id,
            RepositoryState(repository_id=snapshot.repository_id, path=Path(path)),
        )
        for name, commit in GitRepository(Path(path)).tags().items():
            if commit in state.snapshots or commit == snapshot.revision:
                state.refs.setdefault(name, commit)
        if revision is not None:
            state.refs.setdefault(revision, snapshot.revision)
        existing = state.snapshots.get(snapshot.revision)
        if existing is not None and existing.source_digest != snapshot.source_digest:
            raise RepositoryNotIndexed(
                f"re-indexing {snapshot.repository_id}@{snapshot.revision} produced a different "
                "tree digest; the snapshot is not reproducible and must not be mixed"
            )
        state.snapshots[snapshot.revision] = existing or snapshot
        counts = summarize(snapshot)
        return PortableIndexSummary(
            repository_id=snapshot.repository_id,
            identity_strategy=snapshot.identity_strategy,
            revision=snapshot.revision,
            source_digest=snapshot.source_digest,
            parser=snapshot.parser,
            counts=counts,
            files_modified=0,
            hooks_executed=False,
        )

    def summaries(self) -> list[PortableIndexSummary]:
        summaries: list[PortableIndexSummary] = []
        for state in self.repositories.values():
            for snapshot in state.snapshots.values():
                summaries.append(
                    PortableIndexSummary(
                        repository_id=snapshot.repository_id,
                        identity_strategy=snapshot.identity_strategy,
                        revision=snapshot.revision,
                        source_digest=snapshot.source_digest,
                        parser=snapshot.parser,
                        counts=summarize(snapshot),
                        files_modified=0,
                        hooks_executed=False,
                    )
                )
        return sorted(summaries, key=lambda item: (item.repository_id, item.revision))

    # ------------------------------------------------------------------- queries

    def state(self, repository_id: str) -> RepositoryState:
        state = self.repositories.get(repository_id)
        if state is None:
            known = ", ".join(sorted(self.repositories)) or "none"
            raise RepositoryNotIndexed(
                f"repository {repository_id!r} has not been indexed in this process; "
                f"indexed repositories: {known}"
            )
        return state

    def snapshot(self, repository_id: str, revision: str | None = None) -> PortableSnapshot:
        state = self.state(repository_id)
        if revision is None:
            return state.snapshots[state.latest_commit()]
        if revision in state.snapshots:
            return state.snapshots[revision]
        pinned = state.refs.get(revision)
        if pinned is not None and pinned in state.snapshots:
            return state.snapshots[pinned]
        matches = [commit for commit in state.snapshots if commit.startswith(revision)]
        if len(matches) == 1:
            return state.snapshots[matches[0]]
        if not matches:
            raise RepositoryNotIndexed(
                f"revision {revision!r} of {repository_id!r} is not indexed; index it explicitly"
            )
        raise RepositoryNotIndexed(f"revision {revision!r} is ambiguous in {repository_id!r}")

    # ------------------------------------------------------------------- reports

    def import_report(
        self, repository_id: str, request: ExecutionImportRequest
    ) -> tuple[CucumberReportData, bool]:
        state = self.state(repository_id)
        snapshot = self.snapshot(repository_id, request.tested_commit)
        if snapshot.revision != request.tested_commit and not snapshot.revision.startswith(
            request.tested_commit
        ):
            raise ReportNotApplicable(
                f"tested commit {request.tested_commit!r} does not match indexed revision "
                f"{snapshot.revision!r}"
            )
        if request.adapter != "cucumber-messages":
            raise ReportNotApplicable(
                f"adapter {request.adapter!r} is not supported; supported: cucumber-messages"
            )
        if not request.metadata_path:
            raise ReportNotApplicable(
                "report provenance metadata is required: it must name the tested commit and "
                "repository, because a messages stream alone cannot establish which revision ran"
            )
        metadata_path = Path(request.metadata_path)
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise ReportNotApplicable(
                f"report metadata {metadata_path} does not exist; it must name the tested commit"
            ) from exc
        except json.JSONDecodeError as exc:
            raise ReportNotApplicable(
                f"report metadata {metadata_path} is not valid JSON: {exc}"
            ) from exc
        if not isinstance(metadata, dict):
            raise ReportNotApplicable(f"report metadata {metadata_path} must be an object")
        if metadata.get("tested_commit") != snapshot.revision:
            raise ReportNotApplicable(
                f"report metadata names tested commit {metadata.get('tested_commit')!r}, but the "
                f"import was requested for {snapshot.revision!r}; refusing to relabel a run"
            )
        if metadata.get("repository_id") not in (None, repository_id):
            raise ReportNotApplicable(
                f"report metadata names repository {metadata.get('repository_id')!r}, not "
                f"{repository_id!r}"
            )
        report = self.adapter.parse(
            Path(request.report_path),
            repository_id=repository_id,
            tested_commit=snapshot.revision,
        )
        by_path = {feature.path: feature for feature in snapshot.features}
        for uri, digest in report.sources:
            feature = by_path.get(uri)
            if feature is None:
                raise ReportNotApplicable(
                    f"report covers {uri!r}, which is not a feature file at "
                    f"{repository_id}@{snapshot.revision}; the run did not test this revision"
                )
            if feature.content_hash != digest:
                raise ReportNotApplicable(
                    f"report parsed {uri!r} with content {digest}, but that file differs at "
                    f"{repository_id}@{snapshot.revision} ({feature.content_hash}); the run did "
                    "not test this revision"
                )
        for existing_key, existing in state.reports.items():
            if existing.report_digest == report.report_digest and not existing_key.startswith(
                f"{snapshot.revision}:"
            ):
                raise ReportNotApplicable(
                    f"this exact report is already attributed to "
                    f"{existing_key.split(':', 1)[0]!r}; a run cannot be rebased onto another "
                    "revision"
                )
        key = f"{snapshot.revision}:{report.report_digest}"
        already = key in state.reports
        state.reports.setdefault(key, report)
        state.ingested_at.setdefault(key, datetime.now(UTC))
        state.metadata.setdefault(
            key,
            (
                str(metadata_path),
                f"sha256:{hashlib.sha256(metadata_path.read_bytes()).hexdigest()}",
            ),
        )
        return state.reports[key], already

    def reports_for(self, repository_id: str, revision: str) -> list[CucumberReportData]:
        state = self.state(repository_id)
        snapshot = self.snapshot(repository_id, revision)
        return sorted(
            (
                report
                for key, report in state.reports.items()
                if key.startswith(f"{snapshot.revision}:") and report.executions
            ),
            key=lambda report: report.report_digest,
        )

    def bindings(
        self, repository_id: str, revision: str | None = None
    ) -> tuple[
        BindingAvailability,
        str,
        list[StepDefinitionRecord],
        list[StepResolutionRecord],
        list[CucumberReportData],
    ]:
        snapshot = self.snapshot(repository_id, revision)
        reports = self.reports_for(repository_id, snapshot.revision)
        if not reports:
            return (
                BindingAvailability.NOT_AVAILABLE,
                "no trusted framework matching report has been imported for this revision; "
                "step matching is unknown, not undefined",
                [],
                [],
                [],
            )
        definitions: dict[str, StepDefinitionRecord] = {}
        resolutions: dict[tuple[str, str | None, str], StepResolutionRecord] = {}
        for report in reports:
            for definition in report.step_definitions:
                definitions.setdefault(definition.definition_key, definition)
            for resolution in report.resolutions:
                resolutions.setdefault(
                    (resolution.scenario_key, resolution.instance_key, resolution.step_key),
                    resolution,
                )
        return (
            BindingAvailability.AVAILABLE,
            "framework-reported step definitions and matches",
            sorted(definitions.values(), key=lambda item: item.definition_key),
            sorted(
                resolutions.values(),
                key=lambda item: (item.scenario_key, item.instance_key or "", item.step_key),
            ),
            reports,
        )

    def executions(
        self, repository_id: str, revision: str | None = None
    ) -> tuple[list[ScenarioExecutionRecord], list[CucumberReportData]]:
        snapshot = self.snapshot(repository_id, revision)
        reports = self.reports_for(repository_id, snapshot.revision)
        executions = [execution for report in reports for execution in report.executions]
        return (
            sorted(
                executions,
                key=lambda item: (item.scenario_key, item.executed_at, item.execution_key),
            ),
            reports,
        )

    def coverage(self, repository_id: str, revision: str | None = None) -> ExecutionCoverage:
        snapshot = self.snapshot(repository_id, revision)
        executions, _ = self.executions(repository_id, snapshot.revision)
        scenarios = [scenario for feature in snapshot.features for scenario in feature.scenarios]
        executed = {
            execution.scenario_key
            for execution in executions
            if any(step.outcome in _INVOKED for step in execution.steps)
        }
        declared_steps = {step.step_key for scenario in scenarios for step in scenario.steps}
        executed_steps = {
            step.step_key
            for execution in executions
            for step in execution.steps
            if step.outcome in _INVOKED
        } & declared_steps
        return ExecutionCoverage(
            scenarios_total=len(scenarios),
            scenarios_executed=len(executed & {scenario.scenario_key for scenario in scenarios}),
            scenarios_without_execution=len(
                {scenario.scenario_key for scenario in scenarios} - executed
            ),
            steps_total=len(declared_steps),
            steps_executed=len(executed_steps),
        )

    def provenance(self, repository_id: str, revision: str | None = None) -> list[ReportProvenance]:
        """Report provenance, restricted to one tested revision when one is named."""
        state = self.state(repository_id)
        snapshot = self.snapshot(repository_id, revision) if revision is not None else None
        provenance: list[ReportProvenance] = []
        for key, report in sorted(state.reports.items()):
            if snapshot is not None and not key.startswith(f"{snapshot.revision}:"):
                continue
            metadata_uri, metadata_digest = state.metadata[key]
            provenance.append(
                ReportProvenance(
                    report_uri=report.report_uri,
                    report_digest=report.report_digest,
                    metadata_uri=metadata_uri,
                    metadata_digest=metadata_digest,
                    adapter=report.adapter,
                    runtime=report.runtime,
                    protocol_version=report.protocol_version,
                    tested_commit=report.executions[0].tested_commit,
                    imported_at=state.ingested_at[key],
                    execution_count=len(report.executions),
                )
            )
        return provenance

    # ----------------------------------------------------------------- graph edges

    def relations(
        self, repository_id: str, revision: str | None = None
    ) -> list[ExecutableRelation]:
        snapshot = self.snapshot(repository_id, revision)
        relations: list[ExecutableRelation] = []
        for feature in snapshot.features:
            for scenario in feature.scenarios:
                for step in scenario.steps:
                    if step.from_background:
                        continue
                    relations.append(
                        ExecutableRelation(
                            relation=RelationName.HAS_STEP,
                            origin=RelationOrigin.EXTRACTED,
                            source_key=scenario.scenario_key,
                            target_key=step.step_key,
                            provenance={"parser": snapshot.parser, "revision": snapshot.revision},
                        )
                    )
                for instance in scenario.instances:
                    relations.append(
                        ExecutableRelation(
                            relation=RelationName.EXPANDS_TO,
                            origin=RelationOrigin.EXTRACTED,
                            source_key=scenario.scenario_key,
                            target_key=instance.instance_key,
                            provenance={"parser": snapshot.parser, "revision": snapshot.revision},
                        )
                    )
        status, _, _, resolutions, reports = self.bindings(repository_id, snapshot.revision)
        if status is BindingAvailability.AVAILABLE:
            digests = ",".join(sorted(report.report_digest for report in reports))
            for resolution in resolutions:
                if resolution.status.value == "matched":
                    for definition_key in resolution.definition_keys:
                        relations.append(
                            ExecutableRelation(
                                relation=RelationName.MATCHES_DEFINITION,
                                origin=RelationOrigin.MATCHED,
                                source_key=resolution.step_key,
                                target_key=definition_key,
                                provenance={
                                    "report_digest": digests,
                                    "adapter": "cucumber-messages",
                                },
                            )
                        )
        executions, _ = self.executions(repository_id, snapshot.revision)
        for execution in executions:
            for step in execution.steps:
                if step.outcome not in _INVOKED:
                    continue
                relations.append(
                    ExecutableRelation(
                        relation=RelationName.HAS_STEP_EXECUTION,
                        origin=RelationOrigin.OBSERVED,
                        source_key=execution.execution_key,
                        target_key=step.step_key,
                        provenance={
                            "report_digest": execution.report_digest,
                            "tested_commit": execution.tested_commit,
                        },
                    )
                )
                if step.definition_keys:
                    for definition_key in step.definition_keys:
                        relations.append(
                            ExecutableRelation(
                                relation=RelationName.EXECUTED_DEFINITION,
                                origin=RelationOrigin.OBSERVED,
                                source_key=step.step_key,
                                target_key=definition_key,
                                provenance={
                                    "report_digest": execution.report_digest,
                                    "execution_key": execution.execution_key,
                                },
                            )
                        )
        return sorted(
            relations,
            key=lambda item: (
                item.relation.value,
                item.source_key,
                item.target_key,
                item.origin.value,
            ),
        )

    # ------------------------------------------------------------------ findings

    def findings(
        self, repository_id: str, revision: str | None = None
    ) -> tuple[list[ExecutableFinding], str | None]:
        snapshot = self.snapshot(repository_id, revision)
        status, _, definitions, resolutions, reports = self.bindings(
            repository_id, snapshot.revision
        )
        executions, _ = self.executions(repository_id, snapshot.revision)
        if status is BindingAvailability.NOT_AVAILABLE:
            return [], None
        if not reports:
            return [], None
        findings = evaluate_executable_findings(
            repository_id=snapshot.repository_id,
            revision=snapshot.revision,
            resolutions=resolutions,
            executions=executions,
            definition_paths={
                definition.definition_key: definition.source_path for definition in definitions
            },
        )
        return findings, reports[0].executions[0].tested_commit
