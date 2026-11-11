"""Fixture-backed read model: the M0 mock implementation of :class:`ArtifactRepository`.

Data comes from ``fixtures/api-responses/snapshot.json`` plus precomputed thread responses. It is
deliberately dumb: look up, filter, return. All version awareness comes from the materialized
snapshot (content hashes and revisions), so nothing here needs git.

Method names and signatures follow the shared port (``app/domain/ports.py``) so an independently
written consumer — a rule engine, a UI client, or the future SQLite store — can use this mock
through ``ArtifactRepository`` alone. Two surfaces are explicitly *fixture-only* and are not part
of the port: ``thread`` (precomputed response replay, replaced by DT-04) and the sample-findings
source in :mod:`app.assurance.sample_findings` (replaced by AS-01…AS-03).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.domain.api import ThreadResponse
from app.domain.enums import ReviewState
from app.domain.errors import ArtifactNotFound, BaselineNotFound, ThreadNotFound
from app.domain.models import Artifact, TraceLink, VerificationEvidence
from app.domain.oracle import BaselineSnapshot, FixtureSnapshot
from app.persistence.fixtures import load_model, require_supported_schema_version
from app.settings import Settings


@dataclass(frozen=True)
class FixtureStore:
    """The fixtures exposed as an ``ArtifactRepository``."""

    snapshot_data: FixtureSnapshot
    responses_dir: Path

    # ----------------------------------------------------------- construction

    @classmethod
    def from_settings(cls, settings: Settings) -> FixtureStore:
        snapshot = load_model(settings.snapshot_path, FixtureSnapshot)
        require_supported_schema_version(snapshot.schema_version, settings.snapshot_path)
        return cls(snapshot_data=snapshot, responses_dir=settings.api_responses_dir)

    # --------------------------------------------------- ArtifactRepository port

    def baselines(self) -> list[str]:
        """Baseline names in fixture (chronological) order; the last entry is the latest."""
        return [entry.baseline for entry in self.snapshot_data.baselines]

    def resolve_baseline(self, baseline: str | None) -> str:
        """Canonical identifier for a baseline expression; ``None`` selects the latest."""
        return self._entry(baseline).baseline

    def get_artifact(self, artifact_id: str, *, baseline: str | None = None) -> Artifact:
        entry = self._entry(baseline)
        found = entry.artifact(artifact_id)
        if found is None:
            known = ", ".join(artifact.artifact_id for artifact in entry.artifacts)
            raise ArtifactNotFound(
                f"No artifact '{artifact_id}' at baseline '{entry.baseline}'. "
                f"Known artifacts: {known}"
            )
        return found

    def list_artifacts(self, baseline: str) -> list[Artifact]:
        return list(self._entry(baseline).artifacts)

    def list_links(
        self, baseline: str, *, review_state: ReviewState | None = None
    ) -> list[TraceLink]:
        entry = self._entry(baseline)
        links = [*entry.accepted_links, *entry.proposed_links]
        if review_state is not None:
            links = [link for link in links if link.review_state == review_state]
        return sorted(links, key=lambda link: link.link_id)

    def list_evidence(self, baseline: str) -> list[VerificationEvidence]:
        return sorted(self._entry(baseline).evidence, key=lambda item: item.evidence_id)

    def changed_artifacts(self, baseline: str, previous: str) -> list[str]:
        """Artifact ids whose content hash differs between two baselines (freshness key)."""
        current = {
            artifact.artifact_id: artifact.content_hash
            for artifact in self._entry(baseline).artifacts
        }
        before = {
            artifact.artifact_id: artifact.content_hash
            for artifact in self._entry(previous).artifacts
        }
        changed = {
            artifact_id
            for artifact_id in current.keys() | before.keys()
            if current.get(artifact_id) != before.get(artifact_id)
        }
        return sorted(changed)

    # ------------------------------------------- fixture-only surface (not the port)

    def baseline_commits(self) -> dict[str, str]:
        """Fixture addition used by ``/health``: baseline name -> resolved commit SHA."""
        return {entry.baseline: entry.commit for entry in self.snapshot_data.baselines}

    def thread(self, root_id: str, *, baseline: str | None = None) -> ThreadResponse:
        """Replay a precomputed thread response (requirement roots only; DT-04 replaces it)."""
        entry = self._entry(baseline)
        path = self.responses_dir / "threads" / f"{root_id}.{entry.baseline}.json"
        if not path.exists():
            self.get_artifact(root_id, baseline=entry.baseline)  # 404 when the artifact is unknown
            raise ThreadNotFound(
                f"No thread materialized for '{root_id}' at baseline '{entry.baseline}'. "
                f"M0 materializes threads for requirement roots only; thread assembly for every "
                f"artifact arrives with the ingestion work (DT-04, B-PR1)."
            )
        response = load_model(path, ThreadResponse)
        require_supported_schema_version(response.schema_version, path)
        return response

    # ------------------------------------------------------------- internals

    def _entry(self, baseline: str | None) -> BaselineSnapshot:
        if baseline is None:
            return self.snapshot_data.baselines[-1]
        for entry in self.snapshot_data.baselines:
            if baseline in (entry.baseline, entry.commit):
                return entry
        known = ", ".join(
            f"{entry.baseline} ({entry.commit})" for entry in self.snapshot_data.baselines
        )
        raise BaselineNotFound(f"Unknown baseline '{baseline}'. Known baselines: {known}")
