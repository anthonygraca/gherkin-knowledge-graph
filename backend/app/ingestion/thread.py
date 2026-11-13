"""Assemble one artifact's digital thread from ingested facts.

One implementation is shared by the API store and the fixture generator, so a generated example and
a served response cannot drift. The thread contains only artifacts reachable through accepted
links; proposals and evidence are separate collections.
"""

from __future__ import annotations

from collections.abc import Sequence

from app.domain.api import ThreadResponse
from app.domain.models import Artifact, TraceLink, VerificationEvidence
from app.version import SCHEMA_VERSION


def assemble_thread(
    *,
    root_id: str,
    baseline: str,
    artifacts: Sequence[Artifact],
    accepted_links: Sequence[TraceLink],
    proposed_links: Sequence[TraceLink],
    evidence: Sequence[VerificationEvidence],
) -> ThreadResponse:
    """Build the thread rooted at ``root_id`` (the caller validates that the root exists)."""
    accepted_by_source: dict[str, list[TraceLink]] = {}
    for link in accepted_links:
        accepted_by_source.setdefault(link.source_id, []).append(link)

    visited = {root_id}
    frontier = [root_id]
    while frontier:
        following: list[str] = []
        for artifact_id in frontier:
            for link in accepted_by_source.get(artifact_id, []):
                if link.target_id not in visited:
                    visited.add(link.target_id)
                    following.append(link.target_id)
        frontier = following

    return ThreadResponse(
        schema_version=SCHEMA_VERSION,
        root_id=root_id,
        baseline=baseline,
        artifacts=sorted(
            (artifact for artifact in artifacts if artifact.artifact_id in visited),
            key=lambda artifact: artifact.artifact_id,
        ),
        accepted_links=sorted(
            (
                link
                for link in accepted_links
                if link.source_id in visited and link.target_id in visited
            ),
            key=lambda link: link.link_id,
        ),
        proposed_links=sorted(
            (
                link
                for link in proposed_links
                if link.source_id in visited or link.target_id in visited
            ),
            key=lambda link: link.link_id,
        ),
        evidence=sorted(
            (run for run in evidence if run.scenario_id in visited or run.test_id in visited),
            key=lambda run: run.evidence_id,
        ),
    )
