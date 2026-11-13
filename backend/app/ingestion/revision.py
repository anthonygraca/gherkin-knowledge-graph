"""One revision's ingested facts: artifacts, declared links, and recorded evidence.

Freshness policy is DT-05/M2; this record only holds what the repository declares at one commit.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.models import Artifact, TraceLink, VerificationEvidence
from app.ingestion.evidence import load_evidence
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
    evidence: list[VerificationEvidence]

    def artifact(self, artifact_id: str) -> Artifact | None:
        return next(
            (artifact for artifact in self.artifacts if artifact.artifact_id == artifact_id),
            None,
        )


def ingest_revision(
    repository: GitRepository, revision: str | None, *, repository_name: str
) -> IngestedRevision:
    """Resolve once, then read artifacts, links, and evidence at that commit."""
    commit = repository.resolve(revision)
    artifacts = scan_artifacts(repository, commit, repository_name=repository_name)
    by_id = {artifact.artifact_id: artifact for artifact in artifacts}
    accepted, proposed = load_links(repository, commit, artifacts=by_id)
    evidence = load_evidence(repository, commit, artifacts=by_id)
    return IngestedRevision(
        commit=commit,
        artifacts=artifacts,
        accepted_links=accepted,
        proposed_links=proposed,
        evidence=evidence,
    )
