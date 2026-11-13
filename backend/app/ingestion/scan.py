"""Scan one repository revision into domain artifacts.

DT-01 covers requirements and Gherkin scenarios. Source and test annotations are added by
DT-02; the scan is deliberately not extensible ahead of a story that needs it.
"""

from __future__ import annotations

import hashlib

from pydantic import ValidationError

from app.domain.enums import ArtifactType
from app.domain.models import Artifact
from app.ingestion.errors import IngestionError
from app.ingestion.parsers import parse_front_matter, parse_scenarios
from app.ingestion.repository import GitRepository

REQUIREMENTS_PREFIX = "requirements/"
FEATURES_PREFIX = "features/"

#: ``artifact_id`` prefixes are part of the identity contract (docs/domain-contracts.md).
ARTIFACT_ID_PREFIX = {
    ArtifactType.REQUIREMENT: "REQ-",
    ArtifactType.SCENARIO: "SCN-",
    ArtifactType.SOURCE: "CODE-",
    ArtifactType.TEST: "TEST-",
}


def scan_artifacts(
    repository: GitRepository, revision: str | None, *, repository_name: str
) -> list[Artifact]:
    """Every declared artifact at one immutable commit, in tree order.

    The revision expression is resolved to a full commit SHA once; every read and every
    ``Artifact.revision`` uses that SHA, so a symbolic reference moving during the scan cannot
    mix revisions and abbreviated inputs cannot leak into provenance.

    Raises :class:`IngestionError` for unreadable content, malformed declarations, or duplicate
    artifact identities. A caller never receives a silently partial inventory.
    """
    commit = repository.resolve(revision)
    artifacts: list[Artifact] = []
    declared_at: dict[str, str] = {}

    for path in repository.list_paths(commit):
        blob = repository.read_blob(commit, path)
        if path.startswith(REQUIREMENTS_PREFIX) and path.endswith(".md"):
            found = [
                _requirement(blob, path=path, revision=commit, repository_name=repository_name)
            ]
        elif path.startswith(FEATURES_PREFIX) and path.endswith(".feature"):
            found = _scenarios(blob, path=path, revision=commit, repository_name=repository_name)
        else:
            continue

        for artifact in found:
            previous = declared_at.get(artifact.artifact_id)
            if previous is not None:
                raise IngestionError(
                    f"{commit}: duplicate artifact id {artifact.artifact_id!r}: declared by "
                    f"{previous} and {artifact.locator}"
                )
            declared_at[artifact.artifact_id] = artifact.locator
            artifacts.append(artifact)

    return artifacts


def _requirement(blob: bytes, *, path: str, revision: str, repository_name: str) -> Artifact:
    where = f"{revision}:{path}"
    fields = parse_front_matter(_decode(blob, where=where), where=where)
    missing = {"id", "title"} - fields.keys()
    if missing:
        raise IngestionError(f"{where}: missing front matter keys {sorted(missing)}")
    return _artifact(
        artifact_id=fields["id"],
        artifact_type=ArtifactType.REQUIREMENT,
        title=fields["title"],
        locator=path,
        blob=blob,
        revision=revision,
        repository_name=repository_name,
        metadata={"status": fields.get("status", "active")},
    )


def _scenarios(blob: bytes, *, path: str, revision: str, repository_name: str) -> list[Artifact]:
    where = f"{revision}:{path}"
    declarations = parse_scenarios(_decode(blob, where=where), where=where)
    return [
        _artifact(
            artifact_id=declaration.scenario_id,
            artifact_type=ArtifactType.SCENARIO,
            title=declaration.title,
            locator=f"{path}#{declaration.scenario_id}",
            blob=blob,
            revision=revision,
            repository_name=repository_name,
        )
        for declaration in declarations
    ]


def _artifact(
    *,
    artifact_id: str,
    artifact_type: ArtifactType,
    title: str,
    locator: str,
    blob: bytes,
    revision: str,
    repository_name: str,
    metadata: dict[str, str] | None = None,
) -> Artifact:
    path = locator.split("#", 1)[0]
    prefix = ARTIFACT_ID_PREFIX[artifact_type]
    if not artifact_id.startswith(prefix):
        raise IngestionError(
            f"{revision}:{locator}: a {artifact_type.value} artifact id must start with "
            f"{prefix!r}, got {artifact_id!r}"
        )
    try:
        return Artifact(
            artifact_id=artifact_id,
            artifact_type=artifact_type,
            title=title,
            source_uri=f"fixture://{repository_name}/{path}",
            repository=repository_name,
            revision=revision,
            content_hash=f"sha256:{hashlib.sha256(blob).hexdigest()}",
            locator=locator,
            metadata=metadata or {},
        )
    except ValidationError as exc:
        raise IngestionError(f"{revision}:{locator}: invalid artifact declaration:\n{exc}") from exc


def _decode(blob: bytes, *, where: str) -> str:
    try:
        return blob.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise IngestionError(f"{where}: artifact file is not UTF-8 text: {exc}") from exc
