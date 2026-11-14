"""Portable repository contracts: annotation-free Gherkin facts and binding evidence.

This module is deliberately separate from :mod:`app.domain.models`, which describes CTA's own
strict fixture artifacts (``@SCN-nnn`` tags, ``# cta:artifact`` annotations, requirement front
matter). An external project must not be forced to adopt those declarations to be indexed, so the
portable path has its own identity scheme:

* Every identity is prefixed with a repository id, so two repositories that both use
  ``features/login.feature`` and ``@SCN-001`` never collide.
* Identity is derived from the pinned commit plus the source locator, and the strategy is recorded
  (``source_locator``). Nothing claims continuity across edits, renames, or reordering.
* Directly parsed facts, framework-resolved matches, observed executions, and unknown information
  are different fields with different types. There is no field that means "probably works".

The models carry ``extra="forbid"`` so a query response cannot smuggle an undocumented claim.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.domain.executable import ExecutionCoverage, ReportProvenance
from app.domain.models import _require_aware

REPOSITORY_ID_PATTERN = r"^[a-z0-9][a-z0-9._-]{0,127}$"
PORTABLE_KEY_PATTERN = r"^[^\r\n]+$"
CONTENT_DIGEST_PATTERN = r"^sha256:[0-9a-f]{64}$"


class _FrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class IdentityStrategy(StrEnum):
    """Where the repository id came from. Recorded, because confidence differs."""

    EXPLICIT = "explicit"
    REMOTE_URL = "remote_url"
    ROOT_COMMIT = "root_commit"


class ScenarioKind(StrEnum):
    SCENARIO = "scenario"
    SCENARIO_OUTLINE = "scenario_outline"


class StepMatchStatus(StrEnum):
    """Resolution of one Gherkin step against the selected framework adapter.

    ``UNKNOWN`` and ``NOT_AVAILABLE`` are not defects. Only ``UNDEFINED``/``AMBIGUOUS`` assert
    something about the repository, and only a trusted framework report can establish them.
    """

    MATCHED = "matched"
    UNDEFINED = "undefined"
    AMBIGUOUS = "ambiguous"
    UNKNOWN = "unknown"
    NOT_AVAILABLE = "not_available"


class ExecutionOutcome(StrEnum):
    """Observed outcome. ``UNKNOWN`` is used when the report does not say."""

    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    PENDING = "pending"
    UNDEFINED = "undefined"
    AMBIGUOUS = "ambiguous"
    UNKNOWN = "unknown"


class PortableStep(_FrozenModel):
    """One Gherkin step, directly parsed from the pinned commit."""

    step_key: str = Field(pattern=PORTABLE_KEY_PATTERN)
    keyword: str = Field(min_length=1)
    text: str
    line: int = Field(ge=1)
    column: int = Field(ge=1)
    from_background: bool = False
    doc_string: str | None = None
    data_table: list[list[str]] | None = None

    @field_validator("data_table")
    @classmethod
    def _rectangular(cls, value: list[list[str]] | None) -> list[list[str]] | None:
        if value is not None and any(len(row) != len(value[0]) for row in value):
            raise ValueError("data table rows must have equal length")
        return value


class PortableScenarioInstance(_FrozenModel):
    """A concrete executable case for a Scenario Outline (one ``Examples`` row)."""

    instance_key: str = Field(pattern=PORTABLE_KEY_PATTERN)
    scenario_key: str = Field(pattern=PORTABLE_KEY_PATTERN)
    name: str = Field(min_length=1)
    example_row: int = Field(ge=1, description="1-based data row within the Examples table.")
    example_values: dict[str, str]
    steps: list[PortableStep] = Field(default_factory=list)


class PortableScenario(_FrozenModel):
    scenario_key: str = Field(pattern=PORTABLE_KEY_PATTERN)
    feature_key: str = Field(pattern=PORTABLE_KEY_PATTERN)
    path: str = Field(min_length=1)
    line: int = Field(ge=1)
    keyword: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = ""
    tags: list[str] = Field(default_factory=list)
    rule_name: str | None = None
    kind: ScenarioKind = ScenarioKind.SCENARIO
    steps: list[PortableStep] = Field(default_factory=list)
    instances: list[PortableScenarioInstance] = Field(default_factory=list)

    @field_validator("tags")
    @classmethod
    def _tags_unique(cls, value: list[str]) -> list[str]:
        return sorted(set(value))


class PortableFeature(_FrozenModel):
    feature_key: str = Field(pattern=PORTABLE_KEY_PATTERN)
    path: str = Field(min_length=1)
    line: int = Field(ge=1)
    language: str = Field(min_length=2)
    name: str = Field(min_length=1)
    description: str = ""
    tags: list[str] = Field(default_factory=list)
    background_steps: list[PortableStep] = Field(default_factory=list)
    scenarios: list[PortableScenario] = Field(default_factory=list)
    content_hash: str = Field(pattern=CONTENT_DIGEST_PATTERN)

    @field_validator("tags")
    @classmethod
    def _tags_unique(cls, value: list[str]) -> list[str]:
        return sorted(set(value))


class PortableDiagnostic(_FrozenModel):
    """A file that could not be fully indexed. Never silently dropped."""

    path: str
    code: str = Field(min_length=1)
    detail: str = Field(min_length=1)
    line: int | None = None


class PortableSnapshot(_FrozenModel):
    """Everything directly parsed from one pinned commit. No requirement metadata involved."""

    repository_id: str = Field(pattern=REPOSITORY_ID_PATTERN)
    identity_strategy: IdentityStrategy
    revision: str = Field(min_length=7)
    source_digest: str = Field(pattern=CONTENT_DIGEST_PATTERN)
    parser: str = Field(min_length=1)
    indexed_at: datetime
    features: list[PortableFeature] = Field(default_factory=list)
    diagnostics: list[PortableDiagnostic] = Field(default_factory=list)
    annotation_dependency: bool = Field(
        default=False,
        description="False: parsing needs no @SCN tags, cta:artifact annotations, or YAML.",
    )

    @field_validator("indexed_at")
    @classmethod
    def _aware(cls, value: datetime) -> datetime:
        return _require_aware(value)

    @model_validator(mode="after")
    def _unique_keys(self) -> PortableSnapshot:
        scenario_keys = [s.scenario_key for f in self.features for s in f.scenarios]
        if len(scenario_keys) != len(set(scenario_keys)):
            raise ValueError("scenario keys must be unique within one snapshot")
        feature_keys = [f.feature_key for f in self.features]
        if len(feature_keys) != len(set(feature_keys)):
            raise ValueError("feature keys must be unique within one snapshot")
        return self

    def scenario(self, scenario_key: str) -> PortableScenario | None:
        return next(
            (s for f in self.features for s in f.scenarios if s.scenario_key == scenario_key),
            None,
        )


class PortableCounts(_FrozenModel):
    features: int = Field(ge=0)
    scenarios: int = Field(ge=0)
    scenario_outlines: int = Field(ge=0)
    example_instances: int = Field(ge=0)
    steps: int = Field(ge=0)
    untagged_scenarios: int = Field(ge=0)
    diagnostics: int = Field(ge=0)


class PortableIndexSummary(_FrozenModel):
    """Result of one read-only index operation over a pinned commit."""

    repository_id: str = Field(pattern=REPOSITORY_ID_PATTERN)
    identity_strategy: IdentityStrategy
    revision: str = Field(min_length=7)
    source_digest: str = Field(pattern=CONTENT_DIGEST_PATTERN)
    parser: str = Field(min_length=1)
    counts: PortableCounts
    files_modified: int = Field(
        ge=0, description="Tracked files changed by indexing. Must be 0; asserted by tests."
    )
    hooks_executed: bool = Field(default=False)


class _PortableEnvelope(_FrozenModel):
    schema_version: str
    repository_id: str = Field(pattern=REPOSITORY_ID_PATTERN)
    revision: str = Field(min_length=7)
    source_digest: str = Field(pattern=CONTENT_DIGEST_PATTERN)
    parser: str = Field(min_length=1)


class RepositoryListResponse(_FrozenModel):
    schema_version: str
    repositories: list[PortableIndexSummary]


class ScenarioListResponse(_PortableEnvelope):
    scenarios: list[PortableScenario]


class StepListResponse(_PortableEnvelope):
    steps: list[PortableStep]


class StepDefinitionRecord(_FrozenModel):
    """A definition the selected framework registered, with its source locator.

    Registration is a fact about the test suite. It is not proof that a particular step resolved
    to it: that lives in :class:`StepResolutionRecord`.
    """

    definition_key: str = Field(pattern=PORTABLE_KEY_PATTERN)
    framework_definition_id: str = Field(min_length=1)
    pattern: str = Field(min_length=1)
    pattern_type: str = Field(min_length=1)
    source_path: str = Field(min_length=1)
    line: int = Field(ge=1)
    runtime: str = Field(min_length=1)


class StepResolutionRecord(_FrozenModel):
    scenario_key: str = Field(pattern=PORTABLE_KEY_PATTERN)
    instance_key: str | None = Field(
        default=None, description="Concrete Scenario Outline example instance, when one applies."
    )
    step_key: str = Field(pattern=PORTABLE_KEY_PATTERN)
    step_text: str
    status: StepMatchStatus
    definition_keys: list[str] = Field(default_factory=list)

    @field_validator("definition_keys")
    @classmethod
    def _sorted_unique(cls, value: list[str]) -> list[str]:
        return sorted(set(value))

    @model_validator(mode="after")
    def _status_matches_definitions(self) -> StepResolutionRecord:
        count = len(self.definition_keys)
        if self.status is StepMatchStatus.MATCHED and count != 1:
            raise ValueError("matched requires exactly one definition")
        if self.status is StepMatchStatus.AMBIGUOUS and count < 2:
            raise ValueError("ambiguous requires at least two definitions")
        if self.status is StepMatchStatus.UNDEFINED and count != 0:
            raise ValueError("undefined requires no definitions")
        return self


class StepExecutionRecord(_FrozenModel):
    step_key: str
    text: str
    outcome: ExecutionOutcome
    definition_keys: list[str] = Field(default_factory=list)
    duration_ms: float | None = Field(default=None, ge=0)


class ScenarioExecutionRecord(_FrozenModel):
    execution_key: str = Field(pattern=PORTABLE_KEY_PATTERN)
    scenario_key: str = Field(pattern=PORTABLE_KEY_PATTERN)
    instance_key: str | None = Field(
        default=None, description="Concrete Scenario Outline example instance, when one applies."
    )
    scenario_name: str = Field(min_length=1)
    feature_path: str = Field(min_length=1)
    outcome: ExecutionOutcome
    tested_commit: str = Field(min_length=7)
    executed_at: datetime
    runtime: str = Field(min_length=1)
    report_uri: str = Field(min_length=1)
    report_digest: str = Field(pattern=CONTENT_DIGEST_PATTERN)
    steps: list[StepExecutionRecord] = Field(default_factory=list)

    @field_validator("executed_at")
    @classmethod
    def _aware(cls, value: datetime) -> datetime:
        return _require_aware(value)


class BindingAvailability(StrEnum):
    AVAILABLE = "available"
    NOT_AVAILABLE = "not_available"


class BindingResponse(_PortableEnvelope):
    """Definitions and resolutions, or an explicit statement that no report was supplied."""

    availability: BindingAvailability
    reason: str = Field(min_length=1)
    adapter: str | None = None
    tested_commit: str | None = None
    report_uri: str | None = None
    step_definitions: list[StepDefinitionRecord] = Field(default_factory=list)
    resolutions: list[StepResolutionRecord] = Field(default_factory=list)


class ExecutionListResponse(_PortableEnvelope):
    executions: list[ScenarioExecutionRecord]
    coverage: ExecutionCoverage
    reports: list[ReportProvenance] = Field(default_factory=list)


class BatchIndexRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: str = Field(min_length=1, description="Local path to the repository (read-only).")
    repository_id: str | None = Field(default=None, pattern=REPOSITORY_ID_PATTERN)
    revision: str | None = Field(
        default=None, description="Git revision to pin; null means the current HEAD."
    )


class ExecutionImportRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    report_path: str = Field(min_length=1, description="Cucumber Messages NDJSON file.")
    metadata_path: str | None = Field(
        default=None,
        description="Provenance sidecar naming the tested commit. Required: a report alone cannot "
        "prove which revision its step definitions and implementation belonged to.",
    )
    tested_commit: str = Field(
        min_length=7,
        description="Commit the report's run actually tested. Required: a commit that merely "
        "stores the report is not the tested commit.",
    )
    adapter: str = Field(default="cucumber-messages", min_length=1)


class ExecutionImportResponse(_PortableEnvelope):
    report_uri: str
    report_digest: str = Field(pattern=CONTENT_DIGEST_PATTERN)
    tested_commit: str
    adapter: str
    imported: bool = Field(description="False when this exact report was already imported.")
    execution_count: int = Field(ge=0)
    step_definition_count: int = Field(ge=0)
