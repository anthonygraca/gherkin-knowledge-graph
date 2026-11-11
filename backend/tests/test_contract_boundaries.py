"""Boundary contracts that the independent M0 review found unenforced (R1, R2, R4).

Each test reproduces the reviewer's probe against a public surface: the shared port, the response
models, or the fixture loaders. They exist so those defects cannot come back silently.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.discovery.fake import FakeCandidateDiscovery
from app.domain.api import ThreadResponse
from app.domain.enums import ReviewState
from app.domain.errors import FixtureDataInvalid
from app.domain.oracle import CandidateIndexFile
from app.domain.ports import ArtifactRepository
from app.main import create_app
from app.persistence.fixtures import load_model
from app.persistence.store import FixtureStore
from app.settings import Settings


def fixture_copy(fixture_settings: Settings, tmp_path: Path) -> Path:
    """A writable copy of the fixture data, so probes never touch the committed files."""
    fixtures = tmp_path / "fixtures"
    shutil.copytree(fixture_settings.api_responses_dir, fixtures / "api-responses")
    shutil.copytree(fixture_settings.expected_dir, fixtures / "banking-demo" / "expected")
    return fixtures


def app_over(fixture_settings: Settings, fixtures: Path) -> TestClient:
    return TestClient(
        create_app(Settings(repo_root=fixture_settings.repo_root, fixtures_dir=fixtures))
    )


# ------------------------------------------------------------------ R1: port conformance


def test_store_satisfies_the_artifact_repository_port(fixture_settings: Settings) -> None:
    assert isinstance(FixtureStore.from_settings(fixture_settings), ArtifactRepository)


def test_consumer_can_read_everything_through_the_port_alone(fixture_settings: Settings) -> None:
    """R1's acceptance condition: one constructor path, port methods only, real data returned."""
    repository: ArtifactRepository = FixtureStore.from_settings(fixture_settings)

    assert repository.baselines() == ["baseline-a", "baseline-b"]
    assert repository.resolve_baseline("baseline-a") == "baseline-a"
    assert repository.resolve_baseline(None) == "baseline-b"

    artifact = repository.get_artifact("REQ-001", baseline="baseline-a")
    assert artifact.artifact_id == "REQ-001"
    assert repository.get_artifact("REQ-001", baseline="baseline-b").revision != artifact.revision

    accepted = repository.list_links("baseline-a", review_state=ReviewState.ACCEPTED)
    assert [link.link_id for link in accepted] == [
        "LNK-001",
        "LNK-002",
        "LNK-003",
        "LNK-004",
        "LNK-005",
        "LNK-006",
    ]
    proposed = repository.list_links("baseline-a", review_state=ReviewState.PROPOSED)
    assert [link.link_id for link in proposed] == ["LNK-007"]

    assert [item.evidence_id for item in repository.list_evidence("baseline-a")] == [
        "EV-001",
        "EV-002",
    ]
    assert repository.changed_artifacts("baseline-b", "baseline-a") == ["CODE-001", "TEST-002"]
    assert {item.artifact_id for item in repository.list_artifacts("baseline-b")} >= {
        "REQ-001",
        "REQ-003",
    }


def test_port_reads_raise_documented_errors(fixture_settings: Settings) -> None:
    from app.domain.errors import ArtifactNotFound, BaselineNotFound

    repository: ArtifactRepository = FixtureStore.from_settings(fixture_settings)
    with pytest.raises(ArtifactNotFound):
        repository.get_artifact("REQ-999", baseline="baseline-a")
    with pytest.raises(BaselineNotFound):
        repository.resolve_baseline("baseline-z")


# ------------------------------------------------- R2: link partitioning at the boundary


def test_thread_response_rejects_a_proposal_inside_accepted_links(client: TestClient) -> None:
    thread = client.get("/api/threads/REQ-002", params={"baseline": "baseline-a"}).json()
    thread["accepted_links"] = thread.pop("proposed_links")
    thread["proposed_links"] = []
    with pytest.raises(ValidationError) as failure:
        ThreadResponse.model_validate(thread)
    assert "accepted_links" in str(failure.value)


def test_thread_response_rejects_an_accepted_link_inside_proposals(client: TestClient) -> None:
    thread = client.get("/api/threads/REQ-001", params={"baseline": "baseline-a"}).json()
    thread["proposed_links"] = thread.pop("accepted_links")
    thread["accepted_links"] = []
    with pytest.raises(ValidationError) as failure:
        ThreadResponse.model_validate(thread)
    assert "proposed_links" in str(failure.value)


def test_loader_rejects_a_mispartitioned_thread_file(
    fixture_settings: Settings, tmp_path: Path
) -> None:
    fixtures = fixture_copy(fixture_settings, tmp_path)
    path = fixtures / "api-responses" / "threads" / "REQ-002.baseline-a.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["accepted_links"] = payload.pop("proposed_links")
    payload["proposed_links"] = []
    path.write_text(json.dumps(payload), encoding="utf-8")

    response = app_over(fixture_settings, fixtures).get(
        "/api/threads/REQ-002", params={"baseline": "baseline-a"}
    )
    assert response.status_code == 500
    assert response.json()["code"] == "fixture-data-invalid"


# ------------------------------------------------- R4: unsupported contract versions


@pytest.mark.parametrize(
    ("relative_path", "url"),
    [
        ("threads/REQ-001.baseline-a.json", "/api/threads/REQ-001?baseline=baseline-a"),
        ("findings.baseline-a.json", "/api/findings?baseline=baseline-a"),
    ],
)
def test_served_responses_reject_an_unsupported_schema_version(
    fixture_settings: Settings, tmp_path: Path, relative_path: str, url: str
) -> None:
    fixtures = fixture_copy(fixture_settings, tmp_path)
    path = fixtures / "api-responses" / relative_path
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["schema_version"] = "999.0.0"
    path.write_text(json.dumps(payload), encoding="utf-8")

    response = app_over(fixture_settings, fixtures).get(url)
    assert response.status_code == 500
    problem = response.json()
    assert problem["code"] == "fixture-data-invalid"
    assert "999.0.0" in problem["detail"]


def test_snapshot_and_index_versions_are_enforced(
    fixture_settings: Settings, tmp_path: Path
) -> None:
    fixtures = fixture_copy(fixture_settings, tmp_path)
    snapshot_path = fixtures / "api-responses" / "snapshot.json"
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    snapshot["schema_version"] = "999.0.0"
    snapshot_path.write_text(json.dumps(snapshot), encoding="utf-8")
    with pytest.raises(FixtureDataInvalid):
        create_app(Settings(repo_root=fixture_settings.repo_root, fixtures_dir=fixtures))

    index = load_model(fixture_settings.candidate_index_path, CandidateIndexFile)
    with pytest.raises(FixtureDataInvalid):
        FakeCandidateDiscovery(index.model_copy(update={"schema_version": "999.0.0"}))
