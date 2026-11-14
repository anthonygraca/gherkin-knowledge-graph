"""Typed, read-only code-retrieval contracts (AI-07).

These models describe a *proposal* view: semantic or lexical code hits mapped to canonical
engineering artifacts. They deliberately have no link id, review state, evidence, or finding field.
A hit is not an accepted relationship and not verification evidence.

Provenance rules:

* ``revision`` and ``content_hash`` come from the authoritative artifact record at the requested
  baseline, never from the search hit.
* ``index_binding`` is a CTA-computed binding over the requested commit and the artifact paths and
  hashes. CocoIndex 0.2.43 does not report an index identity over MCP; this field is therefore named
  a binding, not a server index revision.
* ``raw_score`` is the value the retrieval method reported. ``score`` is the same value clamped to
  the existing candidate contract's 0..1 range and is not a probability.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domain.enums import RelationType
from app.domain.models import (
    ARTIFACT_ID_PATTERN,
    CONTENT_HASH_PATTERN,
    _FrozenModel,
    _require_aware,
)


class RetrievalMethod(StrEnum):
    LEXICAL = "lexical"
    COCOINDEX = "cocoindex"


class RetrievalStatus(StrEnum):
    OK = "ok"
    NOT_AVAILABLE = "not_available"


class RetrievalHit(_FrozenModel):
    rank: int = Field(ge=1)
    score: float = Field(ge=0.0, le=1.0, description="Clamped reported score; not a probability.")
    raw_score: float = Field(description="Score exactly as reported by the retrieval method.")
    artifact_id: str = Field(pattern=ARTIFACT_ID_PATTERN)
    relation_type: RelationType
    path: str = Field(min_length=1)
    start_line: int = Field(ge=1)
    end_line: int = Field(ge=1)
    revision: str = Field(min_length=7)
    content_hash: str = Field(pattern=CONTENT_HASH_PATTERN)
    method: RetrievalMethod

    @field_validator("end_line")
    @classmethod
    def _ordered(cls, value: int, info) -> int:
        start = info.data.get("start_line")
        if start is not None and value < start:
            raise ValueError("end_line must not precede start_line")
        return value


class UnresolvedHit(_FrozenModel):
    path: str = Field(min_length=1)
    start_line: int = Field(ge=1)
    end_line: int = Field(ge=1)
    raw_score: float
    reason: str = Field(min_length=1)


class CodeRetrievalRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    artifact_id: str = Field(pattern=ARTIFACT_ID_PATTERN)
    baseline: str | None = Field(
        default=None, description="Baseline tag/SHA; null means the repository's latest baseline."
    )
    top_k: int = Field(default=5, ge=1, le=50)
    method: RetrievalMethod | None = Field(
        default=None, description="null selects CocoIndex when configured, else lexical."
    )
    relation_types: list[RelationType] | None = None
    include_unresolved: bool = True


class CodeRetrievalResponse(_FrozenModel):
    schema_version: str
    artifact_id: str = Field(pattern=ARTIFACT_ID_PATTERN)
    baseline: str = Field(min_length=1)
    revision: str = Field(min_length=7)
    status: RetrievalStatus
    method: RetrievalMethod
    provider: str = Field(min_length=1)
    model_version: str = Field(min_length=1)
    index_binding: str = Field(min_length=1)
    hits: list[RetrievalHit] = Field(default_factory=list)
    unresolved: list[UnresolvedHit] = Field(default_factory=list)
    latency_ms: float = Field(ge=0)
    limitations: list[str] = Field(default_factory=list)


class RetrievalProvenanceRecord(_FrozenModel):
    """Durable record of one retrieval observation; no repository mutation."""

    artifact_id: str = Field(pattern=ARTIFACT_ID_PATTERN)
    baseline: str
    revision: str
    method: RetrievalMethod
    provider: str
    model_version: str
    index_binding: str
    observed_at: datetime

    @field_validator("observed_at")
    @classmethod
    def _aware(cls, value: datetime) -> datetime:
        return _require_aware(value)
