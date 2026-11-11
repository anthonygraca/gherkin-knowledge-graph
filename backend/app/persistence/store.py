"""Fixture-backed read model: the M0 mock implementation of :class:`ArtifactRepository`.

Data comes from ``fixtures/api-responses/snapshot.json`` plus precomputed thread responses.
It is deliberately dumb: look up, filter, return. All version awareness comes from the
materialized snapshot (content hashes and revisions), so nothing here needs git.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.domain.api import ThreadResponse
from app.domain.enums import ReviewState
from app.domain.errors import ArtifactNotFound, BaselineNotFound, ThreadNotFound
from app.domain.models import Artifact, TraceLink, VerificationEvidence
from app.domain.oracle import BaselineSnapshot, FixtureSnapshot
from app.persistence.fixtures import load_model
from app.settings import Settings
from app.version import SCHEMA_VERSION


@dataclass(frozen=True)
class FixtureStore:
    snapshot: FixtureSnapshot
    responses_dir: Path

    # ---------------------------------------------------------------- construction

    @classmethod
    def from_settings(cls, settings: Settings) -> FixtureStore:
        snapshot = load_model(settings.snapshot_path, FixtureSnapshot)
        if snapshot.schema_version != SCHEMA_VERSION:
            raise ValueError(
                f"snapshot.json declares schema_version {snapshot.schema_version!r} but the "
                f"contracts are {SCHEMA_VERSION!r}; regenerate fixtures with "
                f"'tools/fixturectl.py materialize' and review the contract change."
            )
        return cls(snapshot=snapshot, responses_dir=settings.api_responses_dir)

    # ---------------------------------------------------------------- baselines

    def baselines(self) -> list[str]:
        """Baseline names in fixture (chronological) order; the last entry is the latest."""
        return [b.baseline for b in self.snapshot.baselines]

    def baseline_commits(self) -> dict[str, str]:
        return {b.baseline: b.commit for b in self.snapshot.baselines}

    def resolve(self, baseline: str | None) -> BaselineSnapshot:
        """Resolve a baseline name or commit SHA; ``None`` selects the latest baseline."""
        if baseline is None:
            return self.snapshot.baselines[-1]
        for entry in self.snapshot.baselines:
            if baseline in (entry.baseline, entry.commit):
                return entry
        known = ", ".join(f"{b.baseline} ({b.commit})" for b in self.snapshot.baselines)
        raise BaselineNotFound(f"Unknown baseline '{baseline}'. Known baselines: {known}")

    # ---------------------------------------------------------------- artifacts, links, evidence

    def artifact(self, artifact_id: str, *, baseline: str | None = None) -> Artifact:
        entry = self.resolve(baseline)
        found = entry.artifact(artifact_id)
        if found is None:
            known = ", ".join(a.artifact_id for a in entry.artifacts)
            raise ArtifactNotFound(
                f"No artifact '{artifact_id}' at baseline '{entry.baseline}'. "
                f"Known artifacts: {known}"
            )
        return found

    def artifacts(self, baseline: str | None = None) -> list[Artifact]:
        return list(self.resolve(baseline).artifacts)

    def links(
        self, baseline: str | None = None, *, review_state: ReviewState | None = None
    ) -> list[TraceLink]:
        entry = self.resolve(baseline)
        links = [*entry.accepted_links, *entry.proposed_links]
        if review_state is not None:
            links = [link for link in links if link.review_state == review_state]
        return sorted(links, key=lambda link: link.link_id)

    def evidence(self, baseline: str | None = None) -> list[VerificationEvidence]:
        return sorted(self.resolve(baseline).evidence, key=lambda item: item.evidence_id)

    def changed_artifact_ids(self, baseline: str, previous: str) -> list[str]:
        """Artifact ids whose content hash differs between two baselines (by path identity)."""
        current_map = {a.artifact_id: a.content_hash for a in self.resolve(baseline).artifacts}
        previous_map = {a.artifact_id: a.content_hash for a in self.resolve(previous).artifacts}
        changed = {
            artifact_id
            for artifact_id in current_map.keys() | previous_map.keys()
            if current_map.get(artifact_id) != previous_map.get(artifact_id)
        }
        return sorted(changed)

    # ---------------------------------------------------------------- precomputed responses

    def thread(self, root_id: str, *, baseline: str | None = None) -> ThreadResponse:
        entry = self.resolve(baseline)
        path = self.responses_dir / "threads" / f"{root_id}.{entry.baseline}.json"
        if not path.exists():
            self.artifact(root_id, baseline=entry.baseline)  # raises ArtifactNotFound if unknown
            raise ThreadNotFound(
                f"No thread materialized for '{root_id}' at baseline '{entry.baseline}'. "
                f"M0 materializes threads for requirement roots only; thread assembly for every "
                f"artifact arrives with the ingestion work (DT-04, B-PR1)."
            )
        response = load_model(path, ThreadResponse)
        return response
