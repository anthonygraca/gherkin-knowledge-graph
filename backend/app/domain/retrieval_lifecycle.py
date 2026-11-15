"""CTA-owned retrieval snapshot and cache lifecycle (AI-03).

CTA owns content-hash change planning, corpus cache keys, configuration manifests, isolated
snapshot publication, compatibility checks, and honest refresh reporting. CocoIndex owns code
chunking, embeddings, and its internal index; CTA never claims an internal embedding count that
the backend does not expose.

No model, network, vector database, or CocoIndex daemon is required to build or validate these
manifests. A refresh adapter is an optional hook; the default publication records the CTA corpus
snapshot and reports backend embedding counts as `not_available`.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.domain.models import (
    CONTENT_HASH_PATTERN,
    TraceCandidate,
    _FrozenModel,
    _require_aware,
)


class RetrievalConfig(_FrozenModel):
    """Identity of the retrieval configuration a snapshot was built with."""

    provider: str = Field(default="cocoindex", min_length=1)
    model_id: str = Field(min_length=1)
    model_version: str = Field(min_length=1)
    weights_digest: str = Field(min_length=1)
    runtime: str = Field(min_length=1)
    formatting_version: str = Field(min_length=1)
    dimension: int = Field(default=768, ge=1)
    max_tokens: int = Field(default=512, ge=1)
    chunking_owner: Literal["cocoindex"] = "cocoindex"
    embedding_owner: Literal["cocoindex"] = "cocoindex"


class RetrievalArtifact(_FrozenModel):
    """One eligible source/test artifact at the snapshot commit."""

    artifact_id: str = Field(pattern=r"^(CODE|TEST)-\d{3}$")
    artifact_type: str = Field(pattern=r"^(source|test)$")
    locator: str = Field(min_length=1)
    revision: str = Field(min_length=7)
    content_hash: str = Field(pattern=CONTENT_HASH_PATTERN)


class ContentChangePlan(_FrozenModel):
    repository: str
    baseline: str
    previous_baseline: str | None = None
    commit: str = Field(min_length=7)
    previous_commit: str | None = None
    changed: list[str] = Field(default_factory=list)
    added: list[str] = Field(default_factory=list)
    removed: list[str] = Field(default_factory=list)
    unchanged: list[str] = Field(default_factory=list)
    changed_artifacts: list[RetrievalArtifact] = Field(default_factory=list)
    unchanged_artifacts: list[RetrievalArtifact] = Field(default_factory=list)


class IndexRefreshObservation(_FrozenModel):
    """What the optional index adapter could actually observe."""

    backend: str = Field(min_length=1)
    backend_binding: str | None = None
    items_embedded: int | None = Field(default=None, ge=0)
    items_embedded_availability: Literal["measured", "not_available"] = "not_available"
    detail: str | None = None


class RetrievalManifest(_FrozenModel):
    schema_version: str
    repository: str
    baseline: str
    commit: str = Field(min_length=7)
    config: RetrievalConfig
    config_digest: str = Field(pattern=CONTENT_HASH_PATTERN)
    corpus_cache_key: str = Field(pattern=CONTENT_HASH_PATTERN)
    snapshot_binding: str = Field(min_length=1)
    artifacts: list[RetrievalArtifact]
    changed: list[str] = Field(default_factory=list)
    added: list[str] = Field(default_factory=list)
    removed: list[str] = Field(default_factory=list)
    unchanged: list[str] = Field(default_factory=list)
    added_count: int = Field(default=0, ge=0)
    changed_count: int = Field(default=0, ge=0)
    removed_count: int = Field(default=0, ge=0)
    unchanged_count: int = Field(default=0, ge=0)
    items_embedded: int | None = Field(default=None, ge=0)
    items_embedded_availability: Literal["measured", "not_available"] = "not_available"
    elapsed_ms: float = Field(ge=0)
    previous_snapshot_binding: str | None = None
    reused: bool = False
    published_at: datetime
    backend_observation: IndexRefreshObservation | None = None

    @field_validator("published_at")
    @classmethod
    def _aware(cls, value: datetime) -> datetime:
        return _require_aware(value)


class ManifestListResponse(_FrozenModel):
    schema_version: str
    manifests: list[RetrievalManifest]


class RetrievalRefreshRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    baseline: str = Field(min_length=1)
    previous_baseline: str | None = None
    config: RetrievalConfig | None = None


class SnapshotBoundBatch(_FrozenModel):
    """A provider response adapted to one CTA snapshot binding.

    ``provider_index_revision`` preserves the provider's own (possibly unavailable) index identity.
    Candidates carry the CTA snapshot binding in their existing ``index_revision`` field, which is
    the only field the combination service compares.
    """

    snapshot_binding: str = Field(min_length=1)
    provider: str = Field(min_length=1)
    provider_index_revision: str = Field(min_length=1)
    model_version: str = Field(min_length=1)
    candidates: list[TraceCandidate]

    @model_validator(mode="after")
    def _candidates_are_bound(self) -> SnapshotBoundBatch:
        mismatched = [
            candidate.target_id
            for candidate in self.candidates
            if candidate.index_revision != self.snapshot_binding
        ]
        if mismatched:
            raise ValueError(
                "snapshot-bound batch candidates must carry its snapshot_binding: "
                + ", ".join(sorted(mismatched))
            )
        return self


class BatchProvenance(_FrozenModel):
    snapshot_binding: str
    provider: str
    provider_index_revision: str
    model_version: str


class CombineRequest(_FrozenModel):
    snapshot_binding: str = Field(min_length=1)
    batches: list[SnapshotBoundBatch]


class CombinedCandidatesResponse(_FrozenModel):
    schema_version: str
    snapshot_binding: str
    provenance: list[BatchProvenance] = Field(default_factory=list)
    candidates: list[TraceCandidate]


def config_digest(config: RetrievalConfig) -> str:
    payload = config.model_dump(mode="json")
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return f"sha256:{hashlib.sha256(canonical.encode('utf-8')).hexdigest()}"


def corpus_cache_key(
    *,
    repository: str,
    config_digest_value: str,
    artifacts: list[RetrievalArtifact],
) -> str:
    """Content-addressed cache key: commits are deliberately excluded."""
    payload = {
        "repository": repository,
        "config_digest": config_digest_value,
        "artifacts": [
            {
                "artifact_id": artifact.artifact_id,
                "artifact_type": artifact.artifact_type,
                "locator": artifact.locator,
                "content_hash": artifact.content_hash,
            }
            for artifact in sorted(artifacts, key=lambda item: item.artifact_id)
        ],
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return f"sha256:{hashlib.sha256(canonical.encode('utf-8')).hexdigest()}"


def snapshot_binding(
    *,
    repository: str,
    commit: str,
    cache_key: str,
    config_digest_value: str,
) -> str:
    payload = {
        "repository": repository,
        "commit": commit,
        "corpus_cache_key": cache_key,
        "config_digest": config_digest_value,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return f"snapshot:sha256:{digest}"


__all__ = [
    "BatchProvenance",
    "CombineRequest",
    "CombinedCandidatesResponse",
    "ContentChangePlan",
    "IndexRefreshObservation",
    "ManifestListResponse",
    "RetrievalArtifact",
    "RetrievalConfig",
    "RetrievalManifest",
    "RetrievalRefreshRequest",
    "SnapshotBoundBatch",
    "config_digest",
    "corpus_cache_key",
    "snapshot_binding",
]
