"""M4 report assembly, digesting, revision resolution, and finding-set comparison."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import tempfile
from collections.abc import Iterable, Sequence
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from pydantic import BaseModel, ValidationError

from app.domain.assurance_report import (
    DIFF_VERSION,
    POLICY,
    POLICY_VERSION,
    REPORT_VERSION,
    AssuranceReport,
    AssuranceScope,
    Coverage,
    DiffCounts,
    ExecutionReportProvenance,
    FailureStage,
    FindingsDiff,
    IdentityKind,
    InputManifest,
    NotComparableDiagnostic,
    ReportFinding,
    ReportInput,
    ToolOutcome,
    UnchangedFinding,
)
from app.domain.enums import RuleId
from app.domain.errors import ReportsNotComparable
from app.domain.executable import ExecutableFinding
from app.domain.models import Artifact, AssuranceFinding, finding_fingerprint
from app.version import PACKAGE_VERSION

REQUIREMENT_RULES: tuple[RuleId, ...] = (
    RuleId.MISSING_VERIFICATION_LINK,
    RuleId.MISSING_IMPLEMENTATION_LINK,
    RuleId.CANDIDATE_PENDING_REVIEW,
    RuleId.LIFECYCLE_SUPERSEDED,
    RuleId.VERIFICATION_FAILED,
    RuleId.REVERIFICATION_REQUIRED,
)
PORTABLE_RULES: tuple[RuleId, ...] = (
    RuleId.UNDEFINED_STEP,
    RuleId.AMBIGUOUS_STEP,
    RuleId.EXECUTION_FAILED,
)
_FULL_SHA = re.compile(r"^[0-9a-f]{40}$")


def canonical_json(value: BaseModel | dict | list) -> str:
    """Canonical JSON pinned by the report contract (UTF-8, sorted keys, compact)."""
    data = value.model_dump(mode="json") if isinstance(value, BaseModel) else value
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def digest_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def digest_value(value: BaseModel | dict | list) -> str:
    return digest_text(canonical_json(value))


def report_digest(report: AssuranceReport) -> str:
    return digest_text(canonical_json(report.model_dump(mode="json", exclude={"report_digest"})))


def finalize_report(report: AssuranceReport) -> AssuranceReport:
    return report.model_copy(update={"report_digest": report_digest(report)})


def _now() -> datetime:
    return datetime.now(UTC)


def _run_id() -> str:
    return str(uuid4())


def evaluator_revision(repo_root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
        commit = result.stdout.strip() if result.returncode == 0 else "unknown"
    except OSError:
        commit = "unknown"
    return f"cta@{PACKAGE_VERSION}+{commit or 'unknown'}"


def resolve_event_revision(event: dict) -> str:
    """Select the event's evaluated commit; never the synthetic test-merge commit."""
    pull_request = event.get("pull_request")
    if isinstance(pull_request, dict):
        head = pull_request.get("head")
        if isinstance(head, dict):
            sha = head.get("sha")
            if isinstance(sha, str) and _FULL_SHA.fullmatch(sha):
                return sha
    after = event.get("after")
    if isinstance(after, str) and after and set(after) != {"0"} and _FULL_SHA.fullmatch(after):
        return after
    github = event.get("github")
    if isinstance(github, dict):
        sha = github.get("sha")
        if isinstance(sha, str) and _FULL_SHA.fullmatch(sha):
            return sha
    sha = event.get("sha")
    if isinstance(sha, str) and _FULL_SHA.fullmatch(sha):
        return sha
    raise ValueError("event does not contain a full evaluated commit SHA")


def requirement_inputs(
    *,
    commit: str,
    artifacts: Iterable[Artifact],
    accepted_links: Iterable[object],
    proposed_links: Iterable[object],
    evidence: Iterable[object],
    historical_inputs: Iterable[ReportInput] = (),
    fixture_manifest_digest: str | None = None,
) -> list[ReportInput]:
    inputs: list[ReportInput] = [
        ReportInput(
            kind="artifact",
            id=artifact.artifact_id,
            path=artifact.locator,
            revision=commit,
            digest=artifact.content_hash,
        )
        for artifact in artifacts
    ]
    for kind, rows in (
        ("accepted_link_set", accepted_links),
        ("proposed_link_set", proposed_links),
        ("evidence_set", evidence),
    ):
        payload = [row.model_dump(mode="json") for row in rows]
        inputs.append(
            ReportInput(
                kind=kind,
                id=kind,
                revision=commit,
                digest=digest_value(payload),
            )
        )
    inputs.extend(historical_inputs)
    if fixture_manifest_digest:
        inputs.append(
            ReportInput(
                kind="fixture_manifest",
                id="baselines.json",
                path="fixtures/banking-demo/expected/baselines.json",
                revision=commit,
                digest=fixture_manifest_digest,
            )
        )
    inputs.append(
        ReportInput(
            kind="policy",
            id=POLICY,
            digest=digest_value({"policy": POLICY, "policy_version": POLICY_VERSION}),
        )
    )
    return sorted(inputs, key=lambda item: (item.kind, item.id or item.path or ""))


def requirement_report(
    *,
    repository: str,
    baseline: str,
    evaluated_revision: str,
    evaluator_revision_value: str,
    findings: Sequence[AssuranceFinding],
    inputs: Sequence[ReportInput],
    run_id: str | None = None,
    generated_at: datetime | None = None,
) -> AssuranceReport:
    payload = [
        ReportFinding(
            finding_id=finding.finding_id,
            rule_id=finding.rule_id,
            finding_type=finding.finding_type,
            severity=finding.severity,
            status=finding.status,
            artifact_ids=finding.artifact_ids,
            artifact_revisions=finding.artifact_revisions,
            evaluated_baseline=finding.evaluated_baseline,
            evidence_ids=finding.evidence_ids,
            explanation=finding.explanation,
        )
        for finding in findings
    ]
    report = AssuranceReport(
        report_version=REPORT_VERSION,
        run_id=run_id or _run_id(),
        generated_at=generated_at or _now(),
        scope=AssuranceScope.REQUIREMENT_ASSURANCE,
        repository=repository,
        identity_strategy="fixture",
        baseline=baseline,
        evaluated_revision=evaluated_revision,
        evaluator_revision=evaluator_revision_value,
        identity_kind=IdentityKind.STABLE_FINGERPRINT,
        rule_scope=list(REQUIREMENT_RULES),
        inputs=list(inputs),
        findings=sorted(payload, key=lambda item: item.finding_id),
        tool_outcome=ToolOutcome.COMPLETED,
        report_digest="sha256:" + "0" * 64,
    )
    return finalize_report(report)


def self_report(
    *,
    repository: str,
    tested_commit: str,
    evaluator_revision_value: str,
    findings: Sequence[ExecutableFinding],
    inputs: Sequence[ReportInput],
    coverage: Coverage,
    execution_report: ExecutionReportProvenance,
    run_id: str | None = None,
    generated_at: datetime | None = None,
) -> AssuranceReport:
    payload = [
        ReportFinding(
            finding_id=finding.finding_id,
            rule_id=finding.rule_id,
            finding_type=finding.finding_type,
            severity=finding.severity,
            status=finding.status,
            artifact_keys=finding.artifact_keys,
            evaluated_baseline=finding.evaluated_baseline,
            execution_keys=finding.execution_keys,
            explanation=finding.explanation,
        )
        for finding in findings
    ]
    report = AssuranceReport(
        report_version=REPORT_VERSION,
        run_id=run_id or _run_id(),
        generated_at=generated_at or _now(),
        scope=AssuranceScope.GHERKIN_EXECUTABILITY,
        repository=repository,
        identity_strategy="explicit",
        baseline=None,
        evaluated_revision=tested_commit,
        evaluator_revision=evaluator_revision_value,
        identity_kind=IdentityKind.SOURCE_LOCATOR,
        rule_scope=list(PORTABLE_RULES),
        inputs=list(inputs),
        coverage=coverage,
        findings=sorted(payload, key=lambda item: item.finding_id),
        tool_outcome=ToolOutcome.COMPLETED,
        report_digest="sha256:" + "0" * 64,
        execution_report=execution_report,
    )
    return finalize_report(report)


def incomplete_report(
    *,
    scope: AssuranceScope,
    repository: str,
    identity_strategy: str,
    baseline: str | None,
    evaluated_revision: str | None,
    evaluator_revision_value: str,
    rule_scope: Sequence[RuleId],
    inputs: Sequence[ReportInput],
    reason: str,
    stage: FailureStage,
    code: str,
    run_id: str | None = None,
    generated_at: datetime | None = None,
) -> AssuranceReport:
    report = AssuranceReport(
        report_version=REPORT_VERSION,
        run_id=run_id or _run_id(),
        generated_at=generated_at or _now(),
        scope=scope,
        repository=repository,
        identity_strategy=identity_strategy,
        baseline=baseline,
        evaluated_revision=evaluated_revision,
        evaluator_revision=evaluator_revision_value,
        rule_scope=list(rule_scope),
        inputs=list(inputs),
        findings=[],
        tool_outcome=ToolOutcome.INCOMPLETE,
        incomplete_reason=reason,
        failure_stage=stage,
        failure_code=code,
        report_digest="sha256:" + "0" * 64,
    )
    return finalize_report(report)


def input_manifest(report: AssuranceReport, diagnostics: Sequence[str] = ()) -> InputManifest:
    return InputManifest(
        report_digest=report.report_digest,
        scope=report.scope,
        repository=report.repository,
        baseline=report.baseline,
        evaluated_revision=report.evaluated_revision,
        entries=list(report.inputs),
        diagnostics=list(diagnostics),
    )


def write_atomic(path: Path, content: str) -> None:
    path = path.expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def write_report(report: AssuranceReport, report_path: Path, manifest_path: Path) -> None:
    write_atomic(report_path, canonical_json(report) + "\n")
    write_atomic(manifest_path, canonical_json(input_manifest(report)) + "\n")


def load_report(path: Path, *, side: str) -> AssuranceReport:
    try:
        raw = json.loads(path.read_text("utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReportsNotComparable(
            f"The {side} report is not readable JSON: {exc}", invalid_input=side
        ) from exc
    try:
        report = AssuranceReport.model_validate(raw)
    except ValidationError as exc:
        raise ReportsNotComparable(
            f"The {side} report does not follow the report contract: {exc}",
            invalid_input=side,
        ) from exc
    if report.report_digest != report_digest(report):
        raise ReportsNotComparable(
            f"The {side} report digest does not match its contents.", invalid_input=side
        )
    return report


def _validate_finding(finding: ReportFinding, *, side: str) -> None:
    keys = finding.artifact_ids or finding.artifact_keys
    expected = finding_fingerprint(finding.rule_id, finding.finding_type, keys)
    if finding.finding_id != expected:
        raise ReportsNotComparable(
            f"The {side} finding {finding.finding_id} does not match its stable identity.",
            invalid_input=side,
        )


def _validate_report(report: AssuranceReport, *, side: str) -> None:
    if report.tool_outcome is not ToolOutcome.COMPLETED:
        raise ReportsNotComparable(f"The {side} evaluation is incomplete.", invalid_input=side)
    if report.evaluated_revision is None:
        raise ReportsNotComparable(f"The {side} resolved revision is absent.", invalid_input=side)
    if report.identity_kind is IdentityKind.SOURCE_LOCATOR:
        raise ReportsNotComparable(
            f"The {side} uses source-locator identities; stable cross-revision identity is "
            "unavailable and no reviewed continuity mapping is implemented.",
            invalid_input=side,
        )
    seen: set[str] = set()
    for finding in report.findings:
        if finding.evaluated_baseline != report.evaluated_revision:
            raise ReportsNotComparable(
                f"The {side} finding {finding.finding_id} has a baseline that contradicts its "
                "report's evaluated revision.",
                invalid_input=side,
            )
        if finding.finding_id in seen:
            raise ReportsNotComparable(
                f"The {side} report contains duplicate finding identities.", invalid_input=side
            )
        seen.add(finding.finding_id)
        _validate_finding(finding, side=side)


def compare_reports(previous: AssuranceReport, current: AssuranceReport) -> FindingsDiff:
    _validate_report(previous, side="previous")
    _validate_report(current, side="current")
    for field in (
        "scope",
        "repository",
        "policy",
        "policy_version",
        "evaluator_revision",
        "rule_scope",
    ):
        if getattr(previous, field) != getattr(current, field):
            raise ReportsNotComparable(
                f"The reports differ by {field}; findings are not comparable.",
                invalid_input="both",
            )
    assert previous.evaluated_revision is not None
    assert current.evaluated_revision is not None
    before = {finding.finding_id: finding for finding in previous.findings}
    after = {finding.finding_id: finding for finding in current.findings}
    new = [after[key] for key in sorted(after.keys() - before.keys())]
    resolved = [before[key] for key in sorted(before.keys() - after.keys())]
    unchanged = [
        UnchangedFinding(finding_id=key, before=before[key], after=after[key])
        for key in sorted(before.keys() & after.keys())
    ]
    return FindingsDiff(
        diff_version=DIFF_VERSION,
        previous_revision=previous.evaluated_revision,
        current_revision=current.evaluated_revision,
        previous_report_digest=previous.report_digest,
        current_report_digest=current.report_digest,
        repository=current.repository,
        scope=current.scope,
        policy=current.policy,
        policy_version=current.policy_version,
        evaluator_revision=current.evaluator_revision,
        rule_scope=list(current.rule_scope),
        new=new,
        unchanged=unchanged,
        resolved=resolved,
        counts=DiffCounts(new=len(new), unchanged=len(unchanged), resolved=len(resolved)),
    )


def refusal_diagnostic(exc: ReportsNotComparable) -> NotComparableDiagnostic:
    return NotComparableDiagnostic(
        diff_version=DIFF_VERSION,
        invalid_input=exc.invalid_input,
        reason=exc.detail,
    )
