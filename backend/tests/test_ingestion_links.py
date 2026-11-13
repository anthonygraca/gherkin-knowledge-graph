"""DT-03 acceptance: declared links are typed, validated, and never merged by state."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from app.domain.oracle import FixtureSnapshot
from app.ingestion import GitRepository, IngestionError, ingest_revision
from app.version import SCHEMA_VERSION


def requirement(requirement_id: str) -> str:
    return f"---\nid: {requirement_id}\ntitle: A requirement\nstatus: active\n---\n\n# Body\n"


def feature(scenario_id: str) -> str:
    return f"Feature: Demo\n\n  @{scenario_id}\n  Scenario: A behaviour\n    Given a thing\n"


def source(artifact_id: str) -> str:
    return f"# cta:artifact {artifact_id}\nVALUE = 1\n"


def link(
    link_id: str,
    source_id: str,
    target_id: str,
    relation_type: str,
    *,
    review_state: str = "accepted",
) -> dict[str, object]:
    return {
        "link_id": link_id,
        "source_id": source_id,
        "target_id": target_id,
        "relation_type": relation_type,
        "review_state": review_state,
        "provenance": {
            "method": "manual-review",
            "reviewer_id": "rv-test",
            "decided_at": "2026-09-28T10:00:00+00:00",
        },
        "created_at": "2026-09-27T15:30:00+00:00",
        "updated_at": "2026-09-28T10:00:00+00:00",
    }


def link_file(review_state: str, links: list[dict[str, object]]) -> str:
    return json.dumps(
        {
            "schema_version": SCHEMA_VERSION,
            "repository": "demo",
            "review_state": review_state,
            "links": links,
        }
    )


def make_repo(tmp_path: Path, files: dict[str, str]) -> GitRepository:
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-q")
    for relative, text in files.items():
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    _git(root, "add", "-A")
    _git(
        root,
        "-c",
        "user.name=Link Test",
        "-c",
        "user.email=test@example.invalid",
        "-c",
        "commit.gpgsign=false",
        "commit",
        "-q",
        "-m",
        "fixture",
    )
    return GitRepository(root=root)


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)


def base_files() -> dict[str, str]:
    return {
        "requirements/REQ-900.md": requirement("REQ-900"),
        "features/demo.feature": feature("SCN-900"),
        "src/accounts.py": source("CODE-900"),
        "tests/test_demo.py": source("TEST-900"),
    }


def test_ingested_links_match_the_committed_snapshot(
    built_fixture, snapshot: FixtureSnapshot
) -> None:
    repository = GitRepository(root=built_fixture.repo)
    for entry in snapshot.baselines:
        revision = ingest_revision(repository, entry.commit, repository_name="banking-demo")
        assert revision.accepted_links == entry.accepted_links, entry.baseline
        assert revision.proposed_links == entry.proposed_links, entry.baseline


def test_proposals_are_ingested_separately(built_fixture) -> None:
    revision = ingest_revision(
        GitRepository(root=built_fixture.repo),
        "baseline-a",
        repository_name="banking-demo",
    )
    assert [link.link_id for link in revision.accepted_links if link.source_id == "REQ-002"] == []
    proposed = [link.link_id for link in revision.proposed_links]
    assert proposed == ["LNK-007"]
    assert revision.proposed_links[0].review_state.value == "proposed"


def test_wrong_relation_direction_is_rejected(tmp_path: Path) -> None:
    files = base_files()
    files["evidence/accepted-links.json"] = link_file(
        "accepted", [link("LNK-900", "CODE-900", "SCN-900", "verified_by")]
    )
    repository = make_repo(tmp_path, files)
    with pytest.raises(IngestionError, match="must connect requirement -> scenario"):
        ingest_revision(repository, repository.resolve(), repository_name="demo")


def test_link_to_unknown_artifact_is_rejected(tmp_path: Path) -> None:
    files = base_files()
    files["evidence/accepted-links.json"] = link_file(
        "accepted", [link("LNK-901", "REQ-900", "SCN-999", "verified_by")]
    )
    repository = make_repo(tmp_path, files)
    with pytest.raises(IngestionError, match="SCN-999"):
        ingest_revision(repository, repository.resolve(), repository_name="demo")


def test_file_with_the_wrong_review_state_is_rejected(tmp_path: Path) -> None:
    files = base_files()
    files["evidence/accepted-links.json"] = link_file(
        "proposed", [link("LNK-902", "REQ-900", "SCN-900", "verified_by", review_state="proposed")]
    )
    repository = make_repo(tmp_path, files)
    with pytest.raises(IngestionError) as failure:
        ingest_revision(repository, repository.resolve(), repository_name="demo")
    message = str(failure.value)
    assert "accepted-links.json" in message
    assert "LNK-902" in message


def test_a_proposed_member_in_an_accepted_file_is_rejected_naming_the_link(
    tmp_path: Path,
) -> None:
    files = base_files()
    files["evidence/accepted-links.json"] = link_file(
        "accepted", [link("LNK-908", "REQ-900", "SCN-900", "verified_by", review_state="proposed")]
    )
    repository = make_repo(tmp_path, files)
    with pytest.raises(IngestionError) as failure:
        ingest_revision(repository, repository.resolve(), repository_name="demo")
    assert "LNK-908" in str(failure.value)


def test_repeated_ingestion_returns_identical_links(tmp_path: Path) -> None:
    files = base_files()
    files["evidence/accepted-links.json"] = link_file(
        "accepted", [link("LNK-903", "REQ-900", "SCN-900", "verified_by")]
    )
    files["evidence/proposed-links.json"] = link_file(
        "proposed",
        [link("LNK-904", "SCN-900", "CODE-900", "implemented_by", review_state="proposed")],
    )
    repository = make_repo(tmp_path, files)
    first = ingest_revision(repository, repository.resolve(), repository_name="demo")
    second = ingest_revision(repository, repository.resolve(), repository_name="demo")
    assert first.accepted_links == second.accepted_links
    assert first.proposed_links == second.proposed_links
    assert first.accepted_links[0].provenance["decided_at"] == "2026-09-28T10:00:00+00:00"


def test_duplicate_link_ids_are_rejected(tmp_path: Path) -> None:
    files = base_files()
    files["evidence/accepted-links.json"] = link_file(
        "accepted",
        [
            link("LNK-905", "REQ-900", "SCN-900", "verified_by"),
            link("LNK-905", "SCN-900", "CODE-900", "implemented_by"),
        ],
    )
    repository = make_repo(tmp_path, files)
    with pytest.raises(IngestionError, match="link ids must be unique"):
        ingest_revision(repository, repository.resolve(), repository_name="demo")


def test_duplicate_link_ids_across_files_are_rejected(tmp_path: Path) -> None:
    files = base_files()
    files["evidence/accepted-links.json"] = link_file(
        "accepted", [link("LNK-907", "REQ-900", "SCN-900", "verified_by")]
    )
    files["evidence/proposed-links.json"] = link_file(
        "proposed",
        [link("LNK-907", "SCN-900", "CODE-900", "implemented_by", review_state="proposed")],
    )
    repository = make_repo(tmp_path, files)
    with pytest.raises(IngestionError, match="duplicate link id 'LNK-907'"):
        ingest_revision(repository, repository.resolve(), repository_name="demo")


def test_unsupported_link_schema_version_is_rejected(tmp_path: Path) -> None:
    files = base_files()
    payload = json.loads(
        link_file("accepted", [link("LNK-906", "REQ-900", "SCN-900", "verified_by")])
    )
    payload["schema_version"] = "999.0.0"
    files["evidence/accepted-links.json"] = json.dumps(payload)
    repository = make_repo(tmp_path, files)
    with pytest.raises(IngestionError, match="999.0.0"):
        ingest_revision(repository, repository.resolve(), repository_name="demo")


def test_absent_link_files_are_empty(tmp_path: Path) -> None:
    repository = make_repo(tmp_path, base_files())
    revision = ingest_revision(repository, repository.resolve(), repository_name="demo")
    assert revision.accepted_links == []
    assert revision.proposed_links == []
