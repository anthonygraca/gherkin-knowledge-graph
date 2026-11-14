"""Boundary interfaces (roadmap §3).

Fake and real adapters share these signatures, so contract tests written against the
fake adapters keep holding when a real implementation lands behind the same port.

Ownership: A owns ``CandidateDiscovery``, B owns ``ArtifactRepository``, C owns
``AssuranceEvaluator`` and ``ReviewService``. A change to a port requires review by the
owning workstream.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from app.domain.enums import RelationType, ReviewState
from app.domain.models import (
    Artifact,
    AssuranceFinding,
    TraceCandidate,
    TraceLink,
    VerificationEvidence,
)


@runtime_checkable
class CandidateDiscovery(Protocol):
    """Proposes candidate links. Has no vocabulary for accepting, storing, or verifying.

    ``discover`` returns candidates whose ``source_id`` is the requested artifact, ranked
    from 1, already trimmed to ``top_k``. Returning an empty list for a known artifact
    with no proposals is normal. Implementations MUST NOT write accepted links or
    verification evidence.
    """

    #: Stable provider name, e.g. ``"fake"`` or ``"local-embeddinggemma"``.
    provider_name: str
    #: Model identity; ``"fake-fixture-v1"`` for the fixture provider.
    model_version: str
    #: Content fingerprint of the index that produced the candidates.
    index_revision: str

    def discover(
        self,
        artifact_id: str,
        *,
        top_k: int = 5,
        relation_types: Sequence[RelationType] | None = None,
        baseline: str | None = None,
    ) -> list[TraceCandidate]: ...


@runtime_checkable
class ArtifactRepository(Protocol):
    """Read/write access to the artifact and link store (B; SQLite from B-PR1 onward)."""

    def baselines(self) -> list[str]: ...

    def resolve_baseline(self, baseline: str | None) -> str: ...

    def commit_of(self, baseline: str) -> str:
        """Resolved commit SHA that findings and evidence are pinned to."""
        ...

    def get_artifact(self, artifact_id: str, *, baseline: str | None = None) -> Artifact: ...

    def list_artifacts(self, baseline: str) -> list[Artifact]: ...

    def artifacts_at(self, revision: str) -> list[Artifact]:
        """Artifact versions at an arbitrary immutable commit (evidence's tested revision).

        Evidence is pinned to the commit that was tested, which is usually *not* a tagged
        baseline: the evidence-only commit has a different SHA but identical content. Comparing
        content hashes requires reading the tested commit itself.
        """
        ...

    def list_links(
        self, baseline: str, *, review_state: ReviewState | None = None
    ) -> list[TraceLink]: ...

    def list_evidence(self, baseline: str) -> list[VerificationEvidence]: ...

    def changed_artifacts(self, baseline: str, previous: str) -> list[str]:
        """Artifact ids whose content hash differs between two baselines."""
        ...

    def impacted_links(self, baseline: str, previous: str) -> list[TraceLink]:
        """Accepted links whose either endpoint changed between the two baselines.

        Impact is scoped to the accepted graph: proposals are not dependencies, and the rule
        engine must not re-implement change detection (DT-06 owns it).
        """
        ...


@runtime_checkable
class AssuranceEvaluator(Protocol):
    """Pure deterministic rules over a snapshot of the store. No model calls (C; AS-01…AS-03)."""

    def evaluate(self, baseline: str, *, policy: str | None = None) -> list[AssuranceFinding]: ...


@runtime_checkable
class ReviewService(Protocol):
    """Records reviewer decisions on proposed links, preserving history (C; AS-06).

    Accepting a link changes ``review_state`` only. It never changes verification status,
    because an accepted link is not evidence of behaviour.
    """

    def review(
        self,
        link_id: str,
        *,
        decision: str,
        reviewer_id: str,
        reason: str | None = None,
    ) -> TraceLink: ...
