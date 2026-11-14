"""Executable traceability facts: relations and findings over portable repository data.

Three connection kinds stay separate, because collapsing them is how traceability tools start
lying:

* ``extracted`` — directly parsed from the Gherkin AST (scenario has step, outline expands to a
  concrete case). No claim about test implementation.
* ``matched`` — the framework itself resolved a Gherkin step to a registered step definition.
  A match is not an execution and says nothing about production code.
* ``observed`` — a trusted execution report shows a step actually ran and with what outcome.

Accepted :class:`~app.domain.models.TraceLink` relationships remain a fourth, human-approved kind
and are not represented here at all.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domain.enums import FindingStatus, FindingType, RuleId, Severity
from app.domain.models import _require_aware


class _FrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class RelationName(StrEnum):
    HAS_STEP = "HAS_STEP"
    EXPANDS_TO = "EXPANDS_TO"
    MATCHES_DEFINITION = "MATCHES_DEFINITION"
    HAS_STEP_EXECUTION = "HAS_STEP_EXECUTION"
    EXECUTED_DEFINITION = "EXECUTED_DEFINITION"


class RelationOrigin(StrEnum):
    EXTRACTED = "extracted"
    MATCHED = "matched"
    OBSERVED = "observed"


class ExecutableRelation(_FrozenModel):
    """One edge with its origin and provenance. Direction is ``source -> target``."""

    relation: RelationName
    origin: RelationOrigin
    source_key: str = Field(min_length=1)
    target_key: str = Field(min_length=1)
    provenance: dict[str, str] = Field(default_factory=dict)

    @field_validator("source_key", "target_key")
    @classmethod
    def _non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("relation endpoints must be non-empty")
        return value


class ExecutableFinding(_FrozenModel):
    """A deterministic finding about executability, not about requirement satisfaction."""

    finding_id: str = Field(pattern=r"^FND-[0-9a-f]{16}$")
    rule_id: RuleId
    finding_type: FindingType
    status: FindingStatus
    severity: Severity
    artifact_keys: list[str] = Field(min_length=1)
    evaluated_baseline: str = Field(min_length=7)
    execution_keys: list[str] = Field(default_factory=list)
    explanation: str = Field(min_length=1)

    @field_validator("artifact_keys", "execution_keys")
    @classmethod
    def _sorted_unique(cls, value: list[str]) -> list[str]:
        return sorted(set(value))


class ExecutableFindingResponse(_FrozenModel):
    schema_version: str
    repository_id: str
    revision: str
    tested_commit: str | None
    findings: list[ExecutableFinding]


class ExecutionCoverage(_FrozenModel):
    """Counts that make "no evidence" visible without pretending it is a defect."""

    scenarios_total: int = Field(ge=0)
    scenarios_executed: int = Field(ge=0)
    scenarios_without_execution: int = Field(ge=0)
    steps_total: int = Field(ge=0)
    steps_executed: int = Field(ge=0)


class RelationListResponse(_FrozenModel):
    schema_version: str
    repository_id: str
    revision: str
    tested_commit: str | None
    relations: list[ExecutableRelation]


class ReportProvenance(_FrozenModel):
    report_uri: str
    report_digest: str
    metadata_uri: str
    metadata_digest: str
    adapter: str
    runtime: str
    protocol_version: str
    tested_commit: str
    imported_at: datetime
    execution_count: int = Field(ge=0)

    @field_validator("imported_at")
    @classmethod
    def _aware(cls, value: datetime) -> datetime:
        return _require_aware(value)
