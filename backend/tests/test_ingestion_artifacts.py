"""DT-01 acceptance: requirements and Gherkin scenarios become stable artifacts.

Expectations come from the committed snapshot (shared fixture input) and from independently
computed Git blob hashes, never from the scanner's own output.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from app.domain.enums import ArtifactType
from app.domain.oracle import FixtureSnapshot
from app.ingestion import GitRepository, IngestionError, scan_artifacts

KEPT_TYPES = {ArtifactType.REQUIREMENT, ArtifactType.SCENARIO}


def make_repo(tmp_path: Path, files: dict[str, str]) -> GitRepository:
    """A throwaway repository whose committed content is exactly ``files``."""
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
        "user.name=Ingestion Test",
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


def requirement(requirement_id: str, title: str = "A title", status: str = "active") -> str:
    return f"---\nid: {requirement_id}\ntitle: {title}\nstatus: {status}\n---\n\n# Body\n"


def feature(*, tag: str, title: str, untagged: bool = False) -> str:
    body = f"Feature: Demo\n\n  @{tag}\n  Scenario: {title}\n    Given a thing\n"
    if untagged:
        body += "\n  Scenario: Anonymous\n    Given another thing\n"
    return body


# ------------------------------------------------------------------------ SCN-501, SCN-502


def test_requirement_document_is_parsed_into_an_artifact(
    built_fixture, snapshot: FixtureSnapshot
) -> None:
    repository = GitRepository(root=built_fixture.repo)
    revision = built_fixture.tag("baseline-a")
    artifacts = {
        item.artifact_id: item
        for item in scan_artifacts(repository, revision, repository_name="banking-demo")
    }

    artifact = artifacts["REQ-001"]
    expected = next(
        item
        for entry in snapshot.baselines
        if entry.baseline == "baseline-a"
        for item in entry.artifacts
        if item.artifact_id == "REQ-001"
    )
    assert artifact == expected
    assert artifact.artifact_type is ArtifactType.REQUIREMENT
    assert artifact.title == "Instant withdrawal availability"
    assert artifact.locator == "requirements/REQ-001.md"
    assert artifact.metadata == {"status": "active"}
    assert artifact.revision == revision
    assert artifact.content_hash == built_fixture.blob_sha256(revision, "requirements/REQ-001.md")


def test_scenario_identity_comes_from_the_gherkin_tag(
    built_fixture, snapshot: FixtureSnapshot
) -> None:
    repository = GitRepository(root=built_fixture.repo)
    revision = built_fixture.tag("baseline-a")
    artifacts = scan_artifacts(repository, revision, repository_name="banking-demo")
    by_id = {item.artifact_id: item for item in artifacts}

    scenario = by_id["SCN-001"]
    expected = next(
        item
        for entry in snapshot.baselines
        if entry.baseline == "baseline-a"
        for item in entry.artifacts
        if item.artifact_id == "SCN-001"
    )
    assert scenario == expected
    assert scenario.artifact_type is ArtifactType.SCENARIO
    assert scenario.locator == "features/withdrawals.feature#SCN-001"
    assert scenario.title == "Successful instant withdrawal"
    assert scenario.content_hash == built_fixture.blob_sha256(
        revision, "features/withdrawals.feature"
    )

    # Unannotated files are not artifacts: this revision declares none of them.
    assert not [item for item in artifacts if item.locator.startswith(("src/", "tests/"))]


def test_parsed_artifacts_match_the_committed_snapshot_for_requirements_and_scenarios(
    built_fixture, snapshot: FixtureSnapshot
) -> None:
    repository = GitRepository(root=built_fixture.repo)
    for entry in snapshot.baselines:
        expected = {
            item.artifact_id: item for item in entry.artifacts if item.artifact_type in KEPT_TYPES
        }
        actual = {
            item.artifact_id: item
            for item in scan_artifacts(repository, entry.commit, repository_name="banking-demo")
        }
        assert actual == expected, entry.baseline


# ------------------------------------------------------------------- SCN-507 revision pinning


def test_tag_and_sha_ingestion_return_identical_artifacts(built_fixture) -> None:
    repository = GitRepository(root=built_fixture.repo)
    sha = built_fixture.tag("baseline-a")
    by_tag = scan_artifacts(repository, "baseline-a", repository_name="banking-demo")
    by_sha = scan_artifacts(repository, sha, repository_name="banking-demo")
    assert by_tag == by_sha
    assert {artifact.revision for artifact in by_tag} == {sha}


def test_abbreviated_sha_is_pinned_to_the_full_commit(built_fixture) -> None:
    sha = built_fixture.tag("baseline-a")
    artifacts = scan_artifacts(
        GitRepository(root=built_fixture.repo), sha[:9], repository_name="banking-demo"
    )
    assert artifacts
    assert {artifact.revision for artifact in artifacts} == {sha}


def test_every_read_uses_the_resolved_commit(built_fixture) -> None:
    sha = built_fixture.tag("baseline-a")
    inner = GitRepository(root=built_fixture.repo)
    listed: list[str] = []

    class RecordingRepository:
        def resolve(self, revision: str | None) -> str:
            return inner.resolve(revision)

        def list_paths(self, commit: str) -> list[str]:
            listed.append(commit)
            assert commit == sha
            return inner.list_paths(commit)

        def read_blob(self, commit: str, path: str) -> bytes:
            assert commit == sha
            return inner.read_blob(commit, path)

    scan_artifacts(RecordingRepository(), "baseline-a", repository_name="banking-demo")
    assert listed == [sha]


# ---------------------------------------------------------------- SCN-503 … SCN-506 failures


def test_requirement_without_front_matter_is_rejected(tmp_path: Path) -> None:
    repository = make_repo(
        tmp_path,
        {
            "requirements/GOOD.md": requirement("REQ-901"),
            "requirements/BROKEN.md": "# Missing front matter\n",
        },
    )
    with pytest.raises(IngestionError, match="requirements/BROKEN.md"):
        scan_artifacts(repository, repository.resolve(), repository_name="demo")


def test_untagged_scenario_creates_no_artifact(tmp_path: Path) -> None:
    repository = make_repo(
        tmp_path,
        {
            "features/demo.feature": feature(
                tag="SCN-903", title="Only the tagged one", untagged=True
            )
        },
    )
    artifacts = scan_artifacts(repository, repository.resolve(), repository_name="demo")
    assert [item.artifact_id for item in artifacts] == ["SCN-903"]
    assert not [item for item in artifacts if item.title == "Anonymous"]


def test_dangling_scenario_tag_is_rejected(tmp_path: Path) -> None:
    repository = make_repo(
        tmp_path,
        {"features/demo.feature": "Feature: Demo\n\n  @SCN-999\n  Rule: broken\n"},
    )
    with pytest.raises(IngestionError, match="@SCN-999"):
        scan_artifacts(repository, repository.resolve(), repository_name="demo")


def test_duplicate_artifact_identities_are_rejected(tmp_path: Path) -> None:
    repository = make_repo(
        tmp_path,
        {
            "requirements/one.md": requirement("REQ-900", title="First"),
            "requirements/two.md": requirement("REQ-900", title="Second"),
        },
    )
    with pytest.raises(IngestionError, match="REQ-900"):
        scan_artifacts(repository, repository.resolve(), repository_name="demo")


def test_requirement_id_with_the_wrong_type_prefix_is_rejected(tmp_path: Path) -> None:
    repository = make_repo(
        tmp_path, {"requirements/one.md": requirement("CODE-001", title="Wrong kind")}
    )
    with pytest.raises(IngestionError, match="must start with 'REQ-'"):
        scan_artifacts(repository, repository.resolve(), repository_name="demo")


def test_quoted_front_matter_values_are_parsed(tmp_path: Path) -> None:
    repository = make_repo(
        tmp_path,
        {
            "requirements/one.md": (
                "---\n"
                'id: "REQ-900"\n'
                'title: "A quoted title"\n'
                "status: superseded # historical\n"
                "---\n"
            )
        },
    )
    [artifact] = scan_artifacts(repository, repository.resolve(), repository_name="demo")
    assert artifact.artifact_id == "REQ-900"
    assert artifact.title == "A quoted title"
    assert artifact.metadata == {"status": "superseded"}


def test_invalid_yaml_is_rejected_by_the_scanner(tmp_path: Path) -> None:
    repository = make_repo(
        tmp_path,
        {"requirements/broken.md": '---\nid: REQ-900\ntitle: "unterminated\n---\n'},
    )
    with pytest.raises(IngestionError, match="not valid YAML"):
        scan_artifacts(repository, repository.resolve(), repository_name="demo")


def test_block_scalar_with_indented_separator_preserves_title_and_status(tmp_path: Path) -> None:
    repository = make_repo(
        tmp_path,
        {
            "requirements/one.md": (
                "---\n"
                "id: REQ-900\n"
                "title: |-\n"
                "  Before delimiter\n"
                "  ---\n"
                "  After delimiter\n"
                "status: superseded\n"
                "---\n"
            )
        },
    )
    [artifact] = scan_artifacts(repository, repository.resolve(), repository_name="demo")
    assert artifact.title == "Before delimiter\n---\nAfter delimiter"
    assert artifact.metadata == {"status": "superseded"}


def test_control_character_in_front_matter_is_rejected_by_the_scanner(tmp_path: Path) -> None:
    repository = make_repo(
        tmp_path,
        {"requirements/bad.md": ("---\nid: REQ-900\ntitle: |-\n  Before\x0b  After\n---\n")},
    )
    with pytest.raises(IngestionError, match="not valid YAML"):
        scan_artifacts(repository, repository.resolve(), repository_name="demo")


def test_unicode_line_separator_title_is_preserved_by_the_scanner(tmp_path: Path) -> None:
    repository = make_repo(
        tmp_path,
        {"requirements/one.md": '---\nid: REQ-900\ntitle: "Before\u2028  After"\n---\n'},
    )
    [artifact] = scan_artifacts(repository, repository.resolve(), repository_name="demo")
    assert artifact.title == "Before\u2028After"
