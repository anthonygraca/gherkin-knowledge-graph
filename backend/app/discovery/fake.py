"""Deterministic fixture-backed candidate discovery (provider name ``"fake"``).

The index is a hand-labeled JSON file (``fixtures/<fixture>/expected/candidate-links.json``).
It exists so A, B, and C can build retrieval, review, and UI flows with no GPU, model
download, or network access, and so retrieval evaluation (AI-05) has a labeled dataset.

Fixture discipline: scores and rationales are *labels*, never measurements of a model.
The negative-labeled entries are returned like any other candidate — the system must be
able to surface a plausible-but-wrong suggestion for a human to reject.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from pathlib import Path

from app.domain.enums import RelationType
from app.domain.models import TraceCandidate
from app.domain.oracle import CandidateIndexFile
from app.persistence.fixtures import load_model, require_supported_schema_version


def canonical_index_payload(index: CandidateIndexFile) -> dict[str, object]:
    """The exact payload hashed into ``index_revision``.

    The evaluation ``label`` is excluded: it is harness metadata for AI-05, not part of
    the retrieval index. Everything that can change a returned candidate is included.
    """
    return {
        "provider": index.provider,
        "model_version": index.model_version,
        "candidates": [
            {
                "source_id": candidate.source_id,
                "target_id": candidate.target_id,
                "proposed_relation_type": str(candidate.proposed_relation_type),
                "score": candidate.score,
                "rationale": candidate.rationale,
            }
            for candidate in index.candidates
        ],
    }


def compute_index_revision(index: CandidateIndexFile) -> str:
    """Content fingerprint of an index, so candidates are never mixed across revisions."""
    canonical = json.dumps(canonical_index_payload(index), sort_keys=True, separators=(",", ":"))
    return f"sha256:{hashlib.sha256(canonical.encode('utf-8')).hexdigest()}"


class FakeCandidateDiscovery:
    """Implements :class:`app.domain.ports.CandidateDiscovery` over a labeled fixture index.

    Has no repository, database, or writer of any kind: it cannot create links, and
    :class:`~app.domain.models.TraceCandidate` has no field in which an accepted state
    could be smuggled.
    """

    def __init__(
        self, index: CandidateIndexFile, *, source: Path | str = "candidate index"
    ) -> None:
        require_supported_schema_version(index.schema_version, source)
        self._index = index
        self.provider_name: str = index.provider
        self.model_version: str = index.model_version
        self.index_revision: str = compute_index_revision(index)

    @classmethod
    def from_fixture(cls, path: Path) -> FakeCandidateDiscovery:
        return cls(load_model(path, CandidateIndexFile), source=path)

    @property
    def candidate_count(self) -> int:
        return len(self._index.candidates)

    def discover(
        self,
        artifact_id: str,
        *,
        top_k: int = 5,
        relation_types: Sequence[RelationType] | None = None,
    ) -> list[TraceCandidate]:
        if top_k < 1:
            raise ValueError("top_k must be >= 1")
        allowed = (
            None if relation_types is None else {RelationType(item) for item in relation_types}
        )
        matches = [
            candidate
            for candidate in self._index.candidates
            if candidate.source_id == artifact_id
            and (allowed is None or candidate.proposed_relation_type in allowed)
        ]
        ordered = sorted(
            matches, key=lambda c: (-c.score, c.target_id, str(c.proposed_relation_type))
        )
        return [
            TraceCandidate(
                source_id=candidate.source_id,
                target_id=candidate.target_id,
                proposed_relation_type=candidate.proposed_relation_type,
                rank=position,
                score=candidate.score,
                discovery_provider=self.provider_name,
                model_version=self.model_version,
                index_revision=self.index_revision,
                rationale=candidate.rationale,
            )
            for position, candidate in enumerate(ordered[:top_k], start=1)
        ]
