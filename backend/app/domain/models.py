"""Core domain models (roadmap §4) plus the finding fingerprint rule.

Invariants enforced here, not by convention:

* Proposals, accepted relationships, and verification evidence are separate types.
  :class:`TraceCandidate` has no link id and no review state — a discovery provider has
  no vocabulary for "accepted".
* Every artifact carries an immutable ``revision`` and a ``content_hash`` (sha256 of the
  artifact bytes at that revision). Freshness decisions compare content hashes, never
  commit SHAs, so an evidence-only commit cannot look like a source change.
* Timestamps are timezone-aware; collections that feed fingerprints are sorted+unique.
* ``extra="forbid"`` everywhere: an unexpected key in a fixture file is an error, not
  silently ignored data.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.domain.enums import (
    ArtifactType,
    EvidenceResult,
    FindingStatus,
    FindingType,
    RelationType,
    ReviewState,
    RuleId,
    Severity,
)

ARTIFACT_ID_PATTERN = r"^(REQ|SCN|CODE|TEST)-\d{3}$"
EVIDENCE_ID_PATTERN = r"^EV-\d{3}$"
LINK_ID_PATTERN = r"^LNK-\d{3}$"
FINDING_ID_PATTERN = r"^FND-[0-9a-f]{16}$"
CONTENT_HASH_PATTERN = r"^sha256:[0-9a-f]{64}$"

#: JSON scalar values allowed in free-form ``metadata``/``provenance`` mappings.
ScalarValue = str | int | float | bool


class _FrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


def _require_aware(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamp must be timezone-aware (UTC)")
    return value


def _sorted_unique(values: list[str]) -> list[str]:
    return sorted(set(values))


class Artifact(_FrozenModel):
    """A versioned engineering artifact: requirement, scenario, source file, or test file."""

    artifact_id: str = Field(pattern=ARTIFACT_ID_PATTERN)
    artifact_type: ArtifactType
    title: str = Field(min_length=1)
    source_uri: str = Field(min_length=1)
    repository: str = Field(min_length=1)
    revision: str = Field(
        min_length=7,
        description="Immutable revision the artifact was read at (fixture: git commit SHA).",
    )
    content_hash: str = Field(
        pattern=CONTENT_HASH_PATTERN,
        description="sha256 of the artifact bytes at `revision`. Freshness is decided on this.",
    )
    locator: str = Field(
        min_length=1,
        description="'<path>' or '<path>#<anchor>' for artifacts inside a shared file.",
    )
    metadata: dict[str, ScalarValue] = Field(default_factory=dict)

    @field_validator("source_uri")
    @classmethod
    def _source_uri_has_scheme(cls, value: str) -> str:
        if "://" not in value:
            raise ValueError(
                "source_uri must be an absolute URI, e.g. fixture://banking-demo/src/accounts.py"
            )
        return value


class TraceLink(_FrozenModel):
    """A typed, provenance-aware link. ``proposed`` links are not accepted relationships."""

    link_id: str = Field(pattern=LINK_ID_PATTERN)
    source_id: str = Field(pattern=ARTIFACT_ID_PATTERN)
    target_id: str = Field(pattern=ARTIFACT_ID_PATTERN)
    relation_type: RelationType
    review_state: ReviewState
    provenance: dict[str, ScalarValue] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    @field_validator("created_at", "updated_at")
    @classmethod
    def _aware(cls, value: datetime) -> datetime:
        return _require_aware(value)

    @model_validator(mode="after")
    def _order(self) -> TraceLink:
        if self.updated_at < self.created_at:
            raise ValueError("updated_at must not precede created_at")
        if self.source_id == self.target_id:
            raise ValueError("a link must connect two different artifacts")
        return self


class VerificationEvidence(_FrozenModel):
    """One recorded execution of a test, pinned to the commit that was tested."""

    evidence_id: str = Field(pattern=EVIDENCE_ID_PATTERN)
    test_id: str = Field(pattern=ARTIFACT_ID_PATTERN)
    scenario_id: str | None = Field(default=None, pattern=ARTIFACT_ID_PATTERN)
    result: EvidenceResult
    tested_commit: str = Field(min_length=7)
    executed_at: datetime
    run_uri: str = Field(min_length=1)

    @field_validator("executed_at")
    @classmethod
    def _aware(cls, value: datetime) -> datetime:
        return _require_aware(value)


class TraceCandidate(_FrozenModel):
    """A *proposal* from semantic discovery. Never an accepted link, never evidence."""

    source_id: str = Field(pattern=ARTIFACT_ID_PATTERN)
    target_id: str = Field(pattern=ARTIFACT_ID_PATTERN)
    proposed_relation_type: RelationType
    rank: int = Field(ge=1, description="1-based rank within this response, after top_k trimming.")
    score: float = Field(ge=0.0, le=1.0)
    discovery_provider: str = Field(min_length=1)
    model_version: str = Field(min_length=1)
    index_revision: str = Field(
        min_length=1,
        description="Content fingerprint of the index that produced the candidate "
        "(convention: 'sha256:<hex>'). Never mix candidates from different index revisions.",
    )
    rationale: str | None = None

    @model_validator(mode="after")
    def _not_self(self) -> TraceCandidate:
        if self.source_id == self.target_id:
            raise ValueError("a candidate must connect two different artifacts")
        return self


class AssuranceFinding(_FrozenModel):
    """A deterministic assurance result. Findings explain; they do not mutate the thread."""

    finding_id: str = Field(pattern=FINDING_ID_PATTERN)
    finding_type: FindingType
    status: FindingStatus
    severity: Severity
    artifact_ids: list[str] = Field(min_length=1)
    evaluated_baseline: str = Field(
        min_length=1, description="Resolved revision the finding was evaluated at (commit SHA)."
    )
    evidence_ids: list[str] = Field(default_factory=list)
    explanation: str = Field(min_length=1)
    rule_id: RuleId
    artifact_revisions: dict[str, str] = Field(
        default_factory=dict,
        description="artifact_id -> resolved revision at `evaluated_baseline`.",
    )

    @field_validator("artifact_ids")
    @classmethod
    def _artifact_ids_sorted_unique(cls, value: list[str]) -> list[str]:
        return _sorted_unique(value)

    @field_validator("evidence_ids")
    @classmethod
    def _evidence_ids_sorted_unique(cls, value: list[str]) -> list[str]:
        return _sorted_unique(value)


def validate_link_partition(
    *, accepted: Iterable[TraceLink], proposed: Iterable[TraceLink]
) -> None:
    """Enforce the invariant that proposal and acceptance never share a container.

    Applied to every model that exposes both collections (snapshot and API response), so a
    mispartitioned file is rejected at the boundary instead of being served to a consumer that
    trusts ``accepted_links`` to contain only accepted relationships.
    """
    non_accepted = sorted(
        link.link_id for link in accepted if link.review_state is not ReviewState.ACCEPTED
    )
    if non_accepted:
        raise ValueError(
            "accepted_links may only contain links with review_state=accepted: "
            f"{', '.join(non_accepted)}"
        )
    promoted = sorted(
        link.link_id for link in proposed if link.review_state is ReviewState.ACCEPTED
    )
    if promoted:
        raise ValueError(f"proposed_links may not contain accepted links: {', '.join(promoted)}")


def finding_fingerprint(
    rule_id: RuleId | str, finding_type: FindingType | str, artifact_ids: Iterable[str]
) -> str:
    """Stable finding identity.

    Inputs: rule id, finding type, and the sorted set of artifact ids — nothing else.
    Deliberately excludes the baseline, the evidence set, and all prose so that the same
    underlying problem keeps one identity across baselines (required for M4 diffing of
    new/unchanged/resolved findings) and across edits to a finding's explanation.
    """
    payload = "|".join((str(rule_id), str(finding_type), ",".join(sorted(set(artifact_ids)))))
    return f"FND-{hashlib.sha256(payload.encode('utf-8')).hexdigest()[:16]}"


def make_finding(
    *,
    rule_id: RuleId,
    finding_type: FindingType,
    severity: Severity,
    artifact_ids: Iterable[str],
    evaluated_baseline: str,
    explanation: str,
    evidence_ids: Iterable[str] = (),
    artifact_revisions: dict[str, str] | None = None,
    status: FindingStatus = FindingStatus.OPEN,
) -> AssuranceFinding:
    """Assemble a finding with a computed fingerprint (single place that computes it)."""
    ids = sorted(set(artifact_ids))
    return AssuranceFinding(
        finding_id=finding_fingerprint(rule_id, finding_type, ids),
        finding_type=finding_type,
        status=status,
        severity=severity,
        artifact_ids=ids,
        evaluated_baseline=evaluated_baseline,
        evidence_ids=sorted(set(evidence_ids)),
        explanation=explanation,
        rule_id=rule_id,
        artifact_revisions=artifact_revisions or {},
    )
