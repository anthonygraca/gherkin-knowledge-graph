"""Typed M4 assurance report and finding-diff contracts (CI-01/CI-02)."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.domain.enums import FindingStatus, FindingType, RuleId, Severity
from app.domain.models import _require_aware

REPORT_VERSION = "1.0"
DIFF_VERSION = "1.0"
POLICY = "default"
POLICY_VERSION = "1"

DIGEST_PATTERN = r"^sha256:[0-9a-f]{64}$"


REVISION_PATTERN = r"^[0-9a-f]{7,64}$"


class _FrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class AssuranceScope(StrEnum):
    REQUIREMENT_ASSURANCE = "requirement_assurance"
    GHERKIN_EXECUTABILITY = "gherkin_executability"


EVALUATED_INPUT_KINDS = frozenset(
    {
        "artifact",
        "accepted_link_set",
        "proposed_link_set",
        "evidence_set",
        "fixture_manifest",
        "feature",
        "execution_report",
        "provenance_sidecar",
    }
)

REQUIRED_INPUT_KINDS: dict[AssuranceScope, frozenset[str]] = {
    AssuranceScope.REQUIREMENT_ASSURANCE: frozenset(
        {
            "artifact",
            "accepted_link_set",
            "proposed_link_set",
            "evidence_set",
            "fixture_manifest",
            "policy",
        }
    ),
    AssuranceScope.GHERKIN_EXECUTABILITY: frozenset(
        {"execution_report", "provenance_sidecar", "feature", "policy"}
    ),
}


class IdentityKind(StrEnum):
    STABLE_FINGERPRINT = "stable_fingerprint"
    SOURCE_LOCATOR = "source_locator"


class ToolOutcome(StrEnum):
    COMPLETED = "completed"
    INCOMPLETE = "incomplete"


class FailureStage(StrEnum):
    RESOLUTION = "resolution"
    INPUT = "input"
    REPORT_PARSE = "report_parse"
    EVALUATION = "evaluation"
    WRITE = "write"
    PUBLICATION = "publication"


class ReportInput(_FrozenModel):
    kind: str = Field(min_length=1)
    id: str | None = None
    path: str | None = None
    revision: str | None = None
    digest: str | None = None
    available: bool = True
    required: bool = True

    @field_validator("digest")
    @classmethod
    def _digest(cls, value: str | None) -> str | None:
        if value is None:
            return None
        import re

        if not re.fullmatch(DIGEST_PATTERN, value):
            raise ValueError("digest must be 'sha256:<64 lowercase hex>' or null")
        return value


class Coverage(_FrozenModel):
    available: bool
    features_indexed: int = Field(ge=0)
    features_covered_by_report: int = Field(ge=0)
    scenarios_total: int = Field(ge=0)
    scenarios_executed: int = Field(ge=0)
    scenarios_skipped: int = Field(ge=0)
    scenarios_unknown: int = Field(ge=0)
    diagnostics: list[str] = Field(default_factory=list)


class ReportFinding(_FrozenModel):
    finding_id: str = Field(pattern=r"^FND-[0-9a-f]{16}$")
    rule_id: RuleId
    finding_type: FindingType
    severity: Severity
    status: FindingStatus = FindingStatus.OPEN
    artifact_ids: list[str] = Field(default_factory=list)
    artifact_keys: list[str] = Field(default_factory=list)
    artifact_revisions: dict[str, str] = Field(default_factory=dict)
    evaluated_baseline: str = Field(pattern=REVISION_PATTERN)
    evidence_ids: list[str] = Field(default_factory=list)
    execution_keys: list[str] = Field(default_factory=list)
    explanation: str = Field(min_length=1)


class SourceDigest(_FrozenModel):
    path: str = Field(min_length=1)
    digest: str = Field(pattern=DIGEST_PATTERN)


class ExecutionReportProvenance(_FrozenModel):
    report_digest: str = Field(pattern=DIGEST_PATTERN)
    tested_commit: str = Field(pattern=REVISION_PATTERN)
    adapter: str = Field(min_length=1)
    sources: list[SourceDigest] = Field(default_factory=list)
    metadata_digest: str | None = Field(default=None, pattern=DIGEST_PATTERN)


class AssuranceReport(_FrozenModel):
    report_version: Literal["1.0"] = "1.0"
    run_id: str = Field(min_length=1)
    generated_at: datetime
    scope: AssuranceScope
    repository: str = Field(min_length=1)
    identity_strategy: str = Field(min_length=1)
    baseline: str | None = None
    evaluated_revision: str | None = Field(default=None, pattern=REVISION_PATTERN)
    evaluator_revision: str = Field(min_length=1)
    policy: str = POLICY
    policy_version: str = POLICY_VERSION
    identity_kind: IdentityKind = IdentityKind.STABLE_FINGERPRINT
    rule_scope: list[RuleId] = Field(default_factory=list)
    artifact_ids: list[str] = Field(default_factory=list)
    feature_ids: list[str] = Field(default_factory=list)
    historical_ids: list[str] = Field(default_factory=list)
    inputs: list[ReportInput] = Field(default_factory=list)
    coverage: Coverage | None = None
    findings: list[ReportFinding] = Field(default_factory=list)
    tool_outcome: ToolOutcome = ToolOutcome.COMPLETED
    incomplete_reason: str | None = None
    failure_stage: FailureStage | None = None
    failure_code: str | None = None
    report_digest: str = Field(pattern=DIGEST_PATTERN)
    execution_report: ExecutionReportProvenance | None = None

    @field_validator("generated_at")
    @classmethod
    def _aware(cls, value: datetime) -> datetime:
        return _require_aware(value)

    @field_validator("rule_scope")
    @classmethod
    def _rules_sorted(cls, value: list[RuleId]) -> list[RuleId]:
        return sorted(set(value))

    @field_validator("artifact_ids", "feature_ids", "historical_ids")
    @classmethod
    def _coverage_sorted(cls, value: list[str]) -> list[str]:
        return sorted(set(value))

    @field_validator("findings")
    @classmethod
    def _finding_ids_unique(cls, value: list[ReportFinding]) -> list[ReportFinding]:
        ids = [finding.finding_id for finding in value]
        if len(ids) != len(set(ids)):
            raise ValueError("finding identities must be unique within one report")
        return value

    @model_validator(mode="after")
    def _consistent(self) -> AssuranceReport:
        if self.tool_outcome is ToolOutcome.COMPLETED:
            if self.evaluated_revision is None:
                raise ValueError("a completed report requires evaluated_revision")
            for entry in self.inputs:
                if entry.required and (not entry.available or entry.digest is None):
                    raise ValueError(
                        "a completed report requires every required input to be available "
                        "and digested"
                    )
            provided = {entry.kind for entry in self.inputs if entry.required}
            missing = REQUIRED_INPUT_KINDS[self.scope] - provided
            if missing:
                raise ValueError(
                    "a completed report is missing mandatory input kinds: "
                    + ", ".join(sorted(missing))
                )
            for entry in self.inputs:
                if not entry.required:
                    continue
                if entry.kind in EVALUATED_INPUT_KINDS:
                    if entry.revision != self.evaluated_revision:
                        raise ValueError(f"input {entry.kind} must bind to the evaluated revision")
                elif entry.kind == "historical_artifact":
                    if entry.revision != entry.id:
                        raise ValueError(
                            "historical input must bind to its declared historical revision"
                        )
            if self.scope is AssuranceScope.REQUIREMENT_ASSURANCE:
                artifact_inputs = {
                    entry.id
                    for entry in self.inputs
                    if entry.kind == "artifact"
                    and entry.required
                    and entry.available
                    and entry.digest is not None
                    and entry.id is not None
                }
                if set(self.artifact_ids) != artifact_inputs:
                    raise ValueError(
                        "a completed requirement report requires one artifact input per "
                        "evaluated artifact"
                    )
                historical_inputs = {
                    entry.id
                    for entry in self.inputs
                    if entry.kind == "historical_artifact"
                    and entry.required
                    and entry.available
                    and entry.digest is not None
                    and entry.id is not None
                }
                if set(self.historical_ids) != historical_inputs:
                    raise ValueError(
                        "a completed requirement report requires one historical input per "
                        "consulted historical revision"
                    )
            else:
                feature_inputs = {
                    entry.path
                    for entry in self.inputs
                    if entry.kind == "feature"
                    and entry.required
                    and entry.available
                    and entry.digest is not None
                    and entry.path is not None
                }
                if set(self.feature_ids) != feature_inputs:
                    raise ValueError(
                        "a completed self-assurance report requires one feature input per "
                        "indexed feature"
                    )
            if self.incomplete_reason is not None:
                raise ValueError("a completed report cannot have incomplete_reason")
            if self.failure_stage is not None or self.failure_code is not None:
                raise ValueError("a completed report cannot have failure fields")
            if self.scope is AssuranceScope.GHERKIN_EXECUTABILITY:
                if self.execution_report is None:
                    raise ValueError("gherkin_executability requires execution_report")
                if self.coverage is None:
                    raise ValueError("gherkin_executability requires coverage")
        else:
            if not self.incomplete_reason:
                raise ValueError("an incomplete diagnostic requires incomplete_reason")
            if self.failure_stage is None or self.failure_code is None:
                raise ValueError("an incomplete diagnostic requires failure_stage/code")
            if self.findings:
                raise ValueError("an incomplete diagnostic cannot contain findings")
            if self.execution_report is not None:
                raise ValueError("an incomplete diagnostic cannot claim execution_report")
        return self


class DiffCounts(_FrozenModel):
    new: int = Field(ge=0)
    unchanged: int = Field(ge=0)
    resolved: int = Field(ge=0)


class UnchangedFinding(_FrozenModel):
    finding_id: str = Field(pattern=r"^FND-[0-9a-f]{16}$")
    before: ReportFinding
    after: ReportFinding


class FindingsDiff(_FrozenModel):
    diff_version: str = DIFF_VERSION
    previous_revision: str = Field(pattern=REVISION_PATTERN)
    current_revision: str = Field(pattern=REVISION_PATTERN)
    previous_report_digest: str = Field(pattern=DIGEST_PATTERN)
    current_report_digest: str = Field(pattern=DIGEST_PATTERN)
    repository: str = Field(min_length=1)
    scope: AssuranceScope
    policy: str = POLICY
    policy_version: str = POLICY_VERSION
    evaluator_revision: str = Field(min_length=1)
    rule_scope: list[RuleId] = Field(default_factory=list)
    new: list[ReportFinding] = Field(default_factory=list)
    unchanged: list[UnchangedFinding] = Field(default_factory=list)
    resolved: list[ReportFinding] = Field(default_factory=list)
    counts: DiffCounts

    @field_validator("rule_scope")
    @classmethod
    def _rules_sorted(cls, value: list[RuleId]) -> list[RuleId]:
        return sorted(set(value))


class NotComparableDiagnostic(BaseModel):
    """The only public shape for a refused comparison."""

    model_config = ConfigDict(extra="forbid")

    diff_version: str = DIFF_VERSION
    tool_outcome: str = "incomplete"
    code: str = "findings-not-comparable"
    invalid_input: str
    reason: str
    classifications: None = None


class InputManifest(BaseModel):
    """Separately published input manifest for one assurance report."""

    model_config = ConfigDict(extra="forbid")

    manifest_version: Literal["1.0"] = "1.0"
    report_digest: str = Field(pattern=DIGEST_PATTERN)
    scope: AssuranceScope
    repository: str = Field(min_length=1)
    baseline: str | None = None
    evaluated_revision: str | None = Field(default=None, pattern=REVISION_PATTERN)
    entries: list[ReportInput] = Field(default_factory=list)
    diagnostics: list[str] = Field(default_factory=list)
