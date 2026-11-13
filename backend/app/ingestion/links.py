"""Ingest declared traceability links from a repository revision.

Links are read, never written here: accepted and proposed relationships live in separate files,
ingestion validates them, and no code path can promote a proposal. Review decisions are AS-06.
"""

from __future__ import annotations

import json

from pydantic import ValidationError

from app.domain.enums import RELATION_DIRECTION, ReviewState
from app.domain.models import Artifact, TraceLink
from app.domain.oracle import FixtureLinkFile
from app.ingestion.errors import IngestionError
from app.ingestion.repository import GitRepository
from app.version import SCHEMA_VERSION

ACCEPTED_LINKS_PATH = "evidence/accepted-links.json"
PROPOSED_LINKS_PATH = "evidence/proposed-links.json"


def load_links(
    repository: GitRepository, commit: str, *, artifacts: dict[str, Artifact]
) -> tuple[list[TraceLink], list[TraceLink]]:
    """Accepted and proposed links at ``commit``, sorted by id.

    A missing file means the repository declares no links of that state. Present files are
    validated for contract version, declared state, duplicate ids, endpoints, and direction.
    """
    paths = set(repository.list_paths(commit))
    accepted = _read(repository, commit, paths, ACCEPTED_LINKS_PATH, ReviewState.ACCEPTED)
    proposed = _read(repository, commit, paths, PROPOSED_LINKS_PATH, ReviewState.PROPOSED)

    declared_at: dict[str, str] = {}
    for where, links in ((ACCEPTED_LINKS_PATH, accepted), (PROPOSED_LINKS_PATH, proposed)):
        for link in links:
            previous = declared_at.get(link.link_id)
            if previous is not None:
                raise IngestionError(
                    f"{commit}:{where}: duplicate link id {link.link_id!r}; "
                    f"already declared in {previous}"
                )
            declared_at[link.link_id] = where
            _validate_link(link, artifacts, where=f"{commit}:{where}")

    return (
        sorted(accepted, key=lambda link: link.link_id),
        sorted(proposed, key=lambda link: link.link_id),
    )


def _read(
    repository: GitRepository,
    commit: str,
    paths: set[str],
    path: str,
    expected_state: ReviewState,
) -> list[TraceLink]:
    if path not in paths:
        return []
    where = f"{commit}:{path}"
    raw = repository.read_blob(commit, path)
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise IngestionError(f"{where}: link file is not valid UTF-8 JSON: {exc}") from exc
    try:
        parsed = FixtureLinkFile.model_validate(payload)
    except ValidationError as exc:
        raise IngestionError(
            f"{where}: link file does not satisfy FixtureLinkFile:\n{exc}"
        ) from exc

    if parsed.schema_version != SCHEMA_VERSION:
        raise IngestionError(
            f"{where}: declares schema_version {parsed.schema_version!r}; this build implements "
            f"{SCHEMA_VERSION!r}"
        )
    if parsed.review_state != expected_state:
        affected = ", ".join(sorted(link.link_id for link in parsed.links)) or "none"
        raise IngestionError(
            f"{where}: declares review_state {parsed.review_state.value!r} but should be "
            f"{expected_state.value!r}; affected links: {affected}"
        )
    return list(parsed.links)


def _validate_link(link: TraceLink, artifacts: dict[str, Artifact], *, where: str) -> None:
    source = artifacts.get(link.source_id)
    target = artifacts.get(link.target_id)
    if source is None:
        raise IngestionError(
            f"{where}: link {link.link_id} references unknown source artifact {link.source_id!r}"
        )
    if target is None:
        raise IngestionError(
            f"{where}: link {link.link_id} references unknown target artifact {link.target_id!r}"
        )
    expected_source, expected_target = RELATION_DIRECTION[link.relation_type]
    if (source.artifact_type, target.artifact_type) != (expected_source, expected_target):
        raise IngestionError(
            f"{where}: link {link.link_id} relation {link.relation_type.value!r} must connect "
            f"{expected_source.value} -> {expected_target.value}, got "
            f"{source.artifact_type.value} -> {target.artifact_type.value}"
        )
