"""Request and response envelopes for the documented API (roadmap §4).

Baseline handling, stated once and relied on everywhere:

* Requests accept a baseline name (fixture tag) **or** a resolved commit SHA.
* Response-level ``baseline`` is the canonical baseline name when the requested revision
  resolves to a known baseline, otherwise the resolved commit SHA. Calling an endpoint
  with a tag and with that tag's SHA therefore yields byte-identical responses.
* Version-pinning fields — ``AssuranceFinding.evaluated_baseline`` and
  ``Artifact.revision`` — always carry the resolved commit SHA.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domain.enums import RelationType, ReviewDecision
from app.domain.models import (
    ARTIFACT_ID_PATTERN,
    Artifact,
    AssuranceFinding,
    TraceCandidate,
    TraceLink,
    VerificationEvidence,
    validate_link_partition,
)


class _FrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class HealthResponse(_FrozenModel):
    status: str
    package_version: str
    schema_version: str
    fixture: str
    baselines: list[str]
    baseline_commits: dict[str, str]
    discovery_providers: list[str]


class ThreadResponse(_FrozenModel):
    """One artifact's digital thread at one baseline.

    ``accepted_links`` and ``proposed_links`` are separate arrays on purpose: a proposal
    must never be read as an accepted relationship by a consumer that only walks
    ``accepted_links``.
    """

    schema_version: str
    root_id: str
    baseline: str
    artifacts: list[Artifact]
    accepted_links: list[TraceLink]
    proposed_links: list[TraceLink]
    evidence: list[VerificationEvidence]

    @model_validator(mode="after")
    def _link_partition(self) -> ThreadResponse:
        validate_link_partition(accepted=self.accepted_links, proposed=self.proposed_links)
        return self


class FindingsResponse(_FrozenModel):
    schema_version: str
    baseline: str
    findings: list[AssuranceFinding]


class ArtifactListResponse(_FrozenModel):
    """Artifact inventory at one baseline (additive in schema 0.2.0)."""

    schema_version: str
    baseline: str
    artifacts: list[Artifact]


class DiscoveryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    artifact_id: str = Field(pattern=ARTIFACT_ID_PATTERN)
    top_k: int = Field(default=5, ge=1, le=50)
    relation_types: list[RelationType] | None = Field(
        default=None, description="Restrict proposals to these relation types; null means all."
    )
    provider: str | None = Field(
        default=None, description="Discovery provider name; null uses the configured default."
    )


class DiscoveryResponse(_FrozenModel):
    """Candidate proposals for one source artifact. Contains no link ids and no review state."""

    schema_version: str
    artifact_id: str
    provider: str
    model_version: str
    index_revision: str
    candidates: list[TraceCandidate]


class ReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision: ReviewDecision
    reviewer_id: str = Field(min_length=1)
    reason: str | None = None


class EvaluateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    baseline: str = Field(min_length=1)
    policy: str | None = Field(
        default=None, description="Named policy; null uses the default policy."
    )


class IngestionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    repository: str = Field(min_length=1)
    revision: str | None = Field(
        default=None,
        description="Revision to ingest; null means the repository's default branch head.",
    )


class IngestionResponse(_FrozenModel):
    run_id: str
    repository: str
    baseline: str
    artifact_count: int
    accepted_link_count: int
    proposed_link_count: int
    evidence_count: int


class ProblemDetails(BaseModel):
    """RFC 9457 problem document.

    ``type`` is ``urn:cta:error:<code>`` for domain errors. Extension members: ``code``
    (machine-readable, so clients need not parse the URN); ``story`` and ``milestone`` are
    present on 501 responses and name the work that will implement the endpoint.
    """

    type: str
    title: str
    status: int
    detail: str
    instance: str
    code: str | None = None
    story: str | None = None
    milestone: str | None = None
