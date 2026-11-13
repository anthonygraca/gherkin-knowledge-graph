"""One revision's ingested facts: artifacts and declared links.

Evidence joins this record with DT-04 (thread assembly needs it); DT-05/M2 owns evidence policy.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.models import Artifact, TraceLink
from app.ingestion.links import load_links
from app.ingestion.repository import GitRepository
from app.ingestion.scan import scan_artifacts


@dataclass(frozen=True)
class IngestedRevision:
    """Everything ingestion has read at one immutable commit."""

    commit: str
    artifacts: list[Artifact]
    accepted_links: list[TraceLink]
    proposed_links: list[TraceLink]

    def artifact(self, artifact_id: str) -> Artifact | None:
        return next(
            (artifact for artifact in self.artifacts if artifact.artifact_id == artifact_id),
            None,
        )


def ingest_revision(
    repository: GitRepository, revision: str | None, *, repository_name: str
) -> IngestedRevision:
    """Resolve once, scan artifacts, and read the declared links at that commit."""
    commit = repository.resolve(revision)
    artifacts = scan_artifacts(repository, commit, repository_name=repository_name)
    by_id = {artifact.artifact_id: artifact for artifact in artifacts}
    accepted, proposed = load_links(repository, commit, artifacts=by_id)
    return IngestedRevision(
        commit=commit,
        artifacts=artifacts,
        accepted_links=accepted,
        proposed_links=proposed,
    )
