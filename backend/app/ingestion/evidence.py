"""Ingest recorded verification evidence from a revision.

Evidence is read, never written here. DT-05/M2 owns freshness policy; this module only validates the
declared record and its artifact references.
"""

from __future__ import annotations

import json

from pydantic import ValidationError

from app.domain.enums import ArtifactType
from app.domain.models import Artifact, VerificationEvidence
from app.domain.oracle import FixtureEvidenceFile
from app.ingestion.errors import IngestionError
from app.ingestion.repository import GitRepository
from app.version import SCHEMA_VERSION

EVIDENCE_PATH = "evidence/verification-runs.json"


def load_evidence(
    repository: GitRepository, commit: str, *, artifacts: dict[str, Artifact]
) -> list[VerificationEvidence]:
    """Evidence runs at ``commit``, sorted by id; an absent file means no recorded runs."""
    paths = set(repository.list_paths(commit))
    if EVIDENCE_PATH not in paths:
        return []
    where = f"{commit}:{EVIDENCE_PATH}"
    raw = repository.read_blob(commit, EVIDENCE_PATH)
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise IngestionError(f"{where}: evidence file is not valid UTF-8 JSON: {exc}") from exc
    try:
        parsed = FixtureEvidenceFile.model_validate(payload)
    except ValidationError as exc:
        raise IngestionError(
            f"{where}: evidence file does not satisfy FixtureEvidenceFile:\n{exc}"
        ) from exc
    if parsed.schema_version != SCHEMA_VERSION:
        raise IngestionError(
            f"{where}: declares schema_version {parsed.schema_version!r}; this build implements "
            f"{SCHEMA_VERSION!r}"
        )
    for run in parsed.runs:
        test = artifacts.get(run.test_id)
        if test is None or test.artifact_type is not ArtifactType.TEST:
            raise IngestionError(
                f"{where}: evidence {run.evidence_id} references unknown test artifact "
                f"{run.test_id!r}"
            )
        if run.scenario_id is not None:
            scenario = artifacts.get(run.scenario_id)
            if scenario is None or scenario.artifact_type is not ArtifactType.SCENARIO:
                raise IngestionError(
                    f"{where}: evidence {run.evidence_id} references unknown scenario artifact "
                    f"{run.scenario_id!r}"
                )
    return sorted(parsed.runs, key=lambda run: run.evidence_id)
