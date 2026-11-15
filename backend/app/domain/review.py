"""Review-workspace contracts (AS-06).

A discovery candidate is not a link until an explicit capture; a capture is not accepted until a
durable human decision. These models keep the three states separate and make the audit fields
explicit: the proposal snapshot, the selected baseline and hashes, the server-assigned operator,
and the append-only journal event.

Nothing here derives an expected result from model output. Provenance is *reported* provenance,
stored verbatim; missing values stay null and are rendered as "not recorded".
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domain.api import ThreadResponse
from app.domain.enums import RelationType, ReviewDecision
from app.domain.models import (
    ARTIFACT_ID_PATTERN,
    CONTENT_HASH_PATTERN,
    TraceLink,
    _FrozenModel,
)


class ProposalCaptureRequest(BaseModel):
    """Explicit capture of a discovery candidate as a proposed link."""

    model_config = ConfigDict(extra="forbid")

    source_id: str = Field(pattern=ARTIFACT_ID_PATTERN)
    target_id: str = Field(pattern=ARTIFACT_ID_PATTERN)
    relation_type: RelationType
    baseline: str = Field(min_length=1)
    source_content_hash: str = Field(pattern=CONTENT_HASH_PATTERN)
    target_content_hash: str = Field(pattern=CONTENT_HASH_PATTERN)
    provider: str | None = Field(default=None, min_length=1)
    model_version: str | None = Field(default=None, min_length=1)
    index_revision: str | None = Field(default=None, min_length=1)
    score: float | None = Field(default=None, ge=0.0, le=1.0)
    rationale: str | None = None


def snapshot_identity_payload(
    *,
    source_id: str,
    target_id: str,
    relation_type: RelationType,
    baseline: str,
    baseline_commit: str,
    source_content_hash: str,
    target_content_hash: str,
    provider: str | None,
    model_version: str | None,
    index_revision: str | None,
) -> dict[str, object]:
    """The exact fields hashed into ``snapshot_digest``.

    Presentation metadata (``score``, ``rationale``, ``captured_at``) is excluded: editing a
    rationale must not manufacture a different proposal identity.
    """
    return {
        "source_id": source_id,
        "target_id": target_id,
        "relation_type": str(relation_type),
        "baseline": baseline,
        "baseline_commit": baseline_commit,
        "source_content_hash": source_content_hash,
        "target_content_hash": target_content_hash,
        "provider": provider,
        "model_version": model_version,
        "index_revision": index_revision,
    }


def compute_snapshot_digest(payload: dict[str, object]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return f"sha256:{hashlib.sha256(canonical.encode('utf-8')).hexdigest()}"


class ProposalSnapshot(_FrozenModel):
    """Immutable identity and provenance of one proposal at one baseline."""

    snapshot_digest: str = Field(pattern=CONTENT_HASH_PATTERN)
    source_id: str = Field(pattern=ARTIFACT_ID_PATTERN)
    target_id: str = Field(pattern=ARTIFACT_ID_PATTERN)
    relation_type: RelationType
    baseline: str = Field(min_length=1)
    baseline_commit: str = Field(min_length=7)
    source_content_hash: str = Field(pattern=CONTENT_HASH_PATTERN)
    target_content_hash: str = Field(pattern=CONTENT_HASH_PATTERN)
    provider: str | None = None
    model_version: str | None = None
    index_revision: str | None = None
    score: float | None = Field(default=None, ge=0.0, le=1.0)
    rationale: str | None = None
    captured_at: datetime

    @model_validator(mode="after")
    def _digest_matches(self) -> ProposalSnapshot:
        expected = compute_snapshot_digest(
            snapshot_identity_payload(
                source_id=self.source_id,
                target_id=self.target_id,
                relation_type=self.relation_type,
                baseline=self.baseline,
                baseline_commit=self.baseline_commit,
                source_content_hash=self.source_content_hash,
                target_content_hash=self.target_content_hash,
                provider=self.provider,
                model_version=self.model_version,
                index_revision=self.index_revision,
            )
        )
        if self.snapshot_digest != expected:
            raise ValueError("snapshot_digest does not match the snapshot identity fields")
        return self

    @model_validator(mode="after")
    def _different_endpoints(self) -> ProposalSnapshot:
        if self.source_id == self.target_id:
            raise ValueError("a proposal must connect two different artifacts")
        return self


def make_proposal_snapshot(
    *,
    source_id: str,
    target_id: str,
    relation_type: RelationType,
    baseline: str,
    baseline_commit: str,
    source_content_hash: str,
    target_content_hash: str,
    provider: str | None,
    model_version: str | None,
    index_revision: str | None,
    score: float | None,
    rationale: str | None,
    captured_at: datetime,
) -> ProposalSnapshot:
    payload = snapshot_identity_payload(
        source_id=source_id,
        target_id=target_id,
        relation_type=relation_type,
        baseline=baseline,
        baseline_commit=baseline_commit,
        source_content_hash=source_content_hash,
        target_content_hash=target_content_hash,
        provider=provider,
        model_version=model_version,
        index_revision=index_revision,
    )
    return ProposalSnapshot(
        snapshot_digest=compute_snapshot_digest(payload),
        source_id=source_id,
        target_id=target_id,
        relation_type=relation_type,
        baseline=baseline,
        baseline_commit=baseline_commit,
        source_content_hash=source_content_hash,
        target_content_hash=target_content_hash,
        provider=provider,
        model_version=model_version,
        index_revision=index_revision,
        score=score,
        rationale=rationale,
        captured_at=captured_at,
    )


class LinkProposalResponse(_FrozenModel):
    schema_version: str
    link: TraceLink
    snapshot: ProposalSnapshot
    review_revision: int = Field(ge=0)
    created: bool


class ProposalRecord(_FrozenModel):
    """One pending proposal; legacy proposals have no capture snapshot yet."""

    link: TraceLink
    snapshot: ProposalSnapshot | None = None
    binding: Literal["captured", "legacy"]


class WorkspaceProposalsResponse(_FrozenModel):
    schema_version: str
    baseline: str
    review_revision: int = Field(ge=0)
    proposals: list[ProposalRecord]


class ReviewEvent(_FrozenModel):
    """One committed journal event: a capture or a terminal decision."""

    review_revision: int = Field(ge=1)
    event: Literal["proposal_captured", "decision_recorded"]
    recorded_at: datetime
    operator: str = Field(min_length=1)
    baseline: str = Field(min_length=1)
    baseline_commit: str = Field(min_length=7)
    link: TraceLink
    snapshot: ProposalSnapshot
    decision: ReviewDecision | None = None
    reason: str | None = None

    @model_validator(mode="after")
    def _consistent(self) -> ReviewEvent:
        if self.event == "proposal_captured" and self.decision is not None:
            raise ValueError("a capture event cannot carry a decision")
        if self.event == "decision_recorded" and self.decision is None:
            raise ValueError("a decision event must carry a decision")
        return self


class JournalPayload(_FrozenModel):
    event: ReviewEvent
    record_digest: str = Field(pattern=CONTENT_HASH_PATTERN)


class JournalCommit(_FrozenModel):
    commit: str = Field(pattern=CONTENT_HASH_PATTERN)


def compute_record_digest(event: ReviewEvent) -> str:
    canonical = json.dumps(event.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
    return f"sha256:{hashlib.sha256(canonical.encode('utf-8')).hexdigest()}"


class WorkspaceThreadResponse(ThreadResponse):
    """Thread projection with the journal revision that produced it."""

    review_revision: int = Field(default=0, ge=0)


class WorkspaceHistoryResponse(_FrozenModel):
    schema_version: str
    baseline: str
    review_revision: int = Field(ge=0)
    events: list[ReviewEvent]


class ReviewConfigResponse(_FrozenModel):
    schema_version: str
    enabled: bool
    operator: str | None = None
    loopback_only: bool = True


class ReviewRequestPayload(BaseModel):
    """Request body for ``POST /api/links/{link_id}/review``.

    ``reason`` is optional at the type level so the route can distinguish an absent/null field
    (``request-validation``) from an empty/whitespace value (``review-reason-required``).
    """

    model_config = ConfigDict(extra="forbid")

    decision: ReviewDecision
    reviewer_id: str = Field(min_length=1)
    baseline: str = Field(min_length=1)
    reason: str | None = None


__all__ = [
    "JournalCommit",
    "JournalPayload",
    "LinkProposalResponse",
    "ProposalCaptureRequest",
    "ProposalRecord",
    "ProposalSnapshot",
    "ReviewConfigResponse",
    "ReviewEvent",
    "ReviewRequestPayload",
    "WorkspaceHistoryResponse",
    "WorkspaceProposalsResponse",
    "WorkspaceThreadResponse",
    "compute_record_digest",
    "compute_snapshot_digest",
    "make_proposal_snapshot",
    "snapshot_identity_payload",
]
