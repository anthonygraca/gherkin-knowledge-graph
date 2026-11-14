"""Evidence-grounded answer contracts (AI-08 / PR 3).

The response separates three things that must never be conflated:

* authoritative accepted-graph context (artifacts, accepted links, evidence, deterministic
  findings);
* proposed links (labelled, never traversed as accepted);
* semantic retrieval candidates (CocoIndex/lexical code proposals, never graph facts).

Answer text is deterministic and built only from the retrieved context. No chat model is required;
when one is not configured the response says so rather than fabricating an explanation.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domain.enums import RelationType
from app.domain.models import (
    ARTIFACT_ID_PATTERN,
    Artifact,
    AssuranceFinding,
    TraceLink,
    VerificationEvidence,
)
from app.domain.retrieval import RetrievalHit, RetrievalMethod


class AnswerStatus(StrEnum):
    ANSWERED = "answered"
    ABSTAINED = "abstained"
    NOT_FOUND = "not_found"


class EvidenceSummary(StrEnum):
    PASSED = "passed"
    FAILED = "failed"
    MISSING = "missing"
    UNKNOWN = "unknown"
    NONE = "none"


class AnswerRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    requirement_id: str | None = Field(default=None, pattern=ARTIFACT_ID_PATTERN)
    question: str | None = Field(default=None, min_length=1, max_length=500)
    baseline: str | None = None
    include_semantic_candidates: bool = False
    semantic_method: RetrievalMethod | None = None

    @model_validator(mode="after")
    def _one_locator(self) -> AnswerRequest:
        if not self.requirement_id and not self.question:
            raise ValueError("one of requirement_id or question is required")
        return self


class GraphPath(BaseModel):
    """One accepted path, from the requirement to a leaf artifact."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    artifact_ids: list[str] = Field(min_length=2)
    link_ids: list[str] = Field(min_length=1)
    evidence_ids: list[str] = Field(default_factory=list)
    review_state: str = "accepted"


class AnswerReferences(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    artifact_ids: list[str] = Field(default_factory=list)
    link_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    finding_ids: list[str] = Field(default_factory=list)


class AnswerResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str
    question: str
    requirement_id: str | None = Field(default=None, pattern=ARTIFACT_ID_PATTERN)
    baseline: str | None = None
    revision: str | None = None
    status: AnswerStatus
    answer: str
    evidence_state: EvidenceSummary
    accepted_links: list[TraceLink] = Field(default_factory=list)
    proposed_links: list[TraceLink] = Field(default_factory=list)
    artifacts: list[Artifact] = Field(default_factory=list)
    evidence: list[VerificationEvidence] = Field(default_factory=list)
    graph_paths: list[GraphPath] = Field(default_factory=list)
    findings: list[AssuranceFinding] = Field(default_factory=list)
    semantic_candidates: list[RetrievalHit] = Field(default_factory=list)
    semantic_method: RetrievalMethod | None = None
    references: AnswerReferences = Field(default_factory=AnswerReferences)
    explanation_method: str = "deterministic"
    chat_model: str | None = None
    uncertainties: list[str] = Field(default_factory=list)


class RetrievalLabelling(BaseModel):
    """Non-authoritative semantic candidate context, kept outside graph paths."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    relation_type: RelationType
    hits: list[RetrievalHit] = Field(default_factory=list)
    method: RetrievalMethod
    index_binding: str
