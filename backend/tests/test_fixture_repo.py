"""FT-01 AC-1.1 (reproducible tagged history) and AC-1.8 (the labels are real)."""

from __future__ import annotations

import fixturectl
import pytest
from conftest import BuiltFixture

from app.domain.enums import EvidenceResult
from app.domain.oracle import ExpectedFindingsFile, FixtureSnapshot
from app.persistence.fixtures import load_model
from app.settings import Settings

EXPECTED_ARTIFACT_IDS = {
    "REQ-001",
    "REQ-002",
    "REQ-003",
    "SCN-001",
    "SCN-002",
    "SCN-003",
    "CODE-001",
    "CODE-002",
    "TEST-001",
    "TEST-002",
}


def test_generated_history_matches_the_committed_manifest(
    built_fixture: BuiltFixture, committed_manifest
) -> None:
    assert built_fixture.manifest.model_dump() == committed_manifest.model_dump()


def test_tags_exist_and_resolve_to_those_commits(
    built_fixture: BuiltFixture, committed_manifest
) -> None:
    for tag, sha in committed_manifest.tags.items():
        assert built_fixture.git(["rev-parse", f"refs/tags/{tag}"]) == sha
        assert built_fixture.git(["cat-file", "-t", sha]) == "commit"


def test_rebuilding_in_another_directory_is_reproducible(
    fixture_settings: Settings, tmp_path
) -> None:
    first = fixturectl.build_repo(fixture_settings.fixture_dir, tmp_path / "one")
    second = fixturectl.build_repo(fixture_settings.fixture_dir, tmp_path / "two")
    assert first.tags == second.tags
    assert [commit.commit for commit in first.commits] == [
        commit.commit for commit in second.commits
    ]


def test_history_is_linear_and_each_commit_has_one_parent(built_fixture: BuiltFixture) -> None:
    commits = [commit.commit for commit in built_fixture.manifest.commits]
    assert len(commits) == 4
    for parent, child in zip(commits, commits[1:], strict=False):
        assert built_fixture.git(["rev-parse", f"{child}^"]) == parent


def test_change_between_baselines_matches_the_hand_written_summary(
    built_fixture: BuiltFixture, fixture_settings: Settings
) -> None:
    oracle = load_model(fixture_settings.expected_dir / "baseline-b.json", ExpectedFindingsFile)
    assert oracle.change_summary is not None
    assert (
        built_fixture.changed_paths("baseline-a", "baseline-b")
        == oracle.change_summary.changed_paths
    )


def test_evidence_is_pinned_to_the_commit_that_was_executed(
    built_fixture: BuiltFixture, snapshot: FixtureSnapshot
) -> None:
    baselines = {entry.baseline: entry for entry in snapshot.baselines}
    at_a, at_b = baselines["baseline-a"], baselines["baseline-b"]

    def evidence(entry, evidence_id: str):
        return next(item for item in entry.evidence if item.evidence_id == evidence_id)

    assert evidence(at_a, "EV-001").result is EvidenceResult.PASSED
    assert evidence(at_a, "EV-002").result is EvidenceResult.PASSED
    assert evidence(at_b, "EV-003").result is EvidenceResult.FAILED

    assert evidence(at_a, "EV-001").tested_commit == built_fixture.commit("baseline-a-source")
    assert evidence(at_b, "EV-003").tested_commit == built_fixture.commit("baseline-b-change")
    for revision in (
        evidence(at_a, "EV-001").tested_commit,
        evidence(at_b, "EV-003").tested_commit,
    ):
        assert built_fixture.git(["cat-file", "-t", revision]) == "commit"

    # the tagged baseline is the evidence commit, one commit after the tested source revision
    assert built_fixture.tag("baseline-a") == built_fixture.commit("baseline-a-evidence")
    assert built_fixture.git(["rev-parse", "baseline-a"]) != evidence(at_a, "EV-001").tested_commit


def test_content_hashes_are_the_bytes_of_that_revision(
    built_fixture: BuiltFixture, snapshot: FixtureSnapshot
) -> None:
    baselines = {entry.baseline: entry for entry in snapshot.baselines}
    for name in ("baseline-a", "baseline-b"):
        entry = baselines[name]
        code = entry.artifact("CODE-001")
        assert code is not None
        assert code.revision == built_fixture.tag(name)
        assert code.content_hash == built_fixture.blob_sha256(name, "src/accounts.py")

    scenario = baselines["baseline-a"].artifact("SCN-001")
    assert scenario is not None
    assert scenario.content_hash == built_fixture.blob_sha256(
        "baseline-a", "features/withdrawals.feature"
    )
    assert scenario.locator == "features/withdrawals.feature#SCN-001"


def test_only_the_intended_artifacts_changed_between_baselines(snapshot: FixtureSnapshot) -> None:
    baselines = {entry.baseline: entry for entry in snapshot.baselines}
    at_a, at_b = baselines["baseline-a"], baselines["baseline-b"]

    def hashes(entry) -> dict[str, str]:
        return {artifact.artifact_id: artifact.content_hash for artifact in entry.artifacts}

    before, after = hashes(at_a), hashes(at_b)
    assert set(before) == set(after) == EXPECTED_ARTIFACT_IDS
    changed = sorted(
        artifact_id for artifact_id in before if before[artifact_id] != after[artifact_id]
    )
    assert changed == ["CODE-001", "TEST-002"]
    # TEST-001 is unchanged, which is what makes the missing re-run a reverification finding
    assert before["TEST-001"] == after["TEST-001"]


def test_unannotated_files_are_not_artifacts(snapshot: FixtureSnapshot) -> None:
    locators = {artifact.locator for entry in snapshot.baselines for artifact in entry.artifacts}
    assert locators == {
        "requirements/REQ-001.md",
        "requirements/REQ-002.md",
        "requirements/REQ-003.md",
        "features/withdrawals.feature#SCN-001",
        "features/transfers.feature#SCN-002",
        "features/transfers.feature#SCN-003",
        "src/accounts.py",
        "src/transfers.py",
        "tests/test_accounts.py",
        "tests/test_transfers.py",
    }
    assert not any("conftest" in locator or locator.endswith("__init__.py") for locator in locators)


def test_fixture_test_suite_reproduces_the_labeled_evidence(
    built_fixture: BuiltFixture, tmp_path
) -> None:
    at_baseline_a = built_fixture.run_fixture_tests("baseline-a", tmp_path)
    assert at_baseline_a.exit_code == 0, at_baseline_a.output
    assert at_baseline_a.failed == []
    assert at_baseline_a.passed == 5

    at_baseline_b = built_fixture.run_fixture_tests("baseline-b", tmp_path)
    assert at_baseline_b.exit_code != 0
    assert at_baseline_b.failed == [
        "tests/test_accounts.py::test_withdraw_allows_fractional_amounts",
        "tests/test_transfers.py::test_transfer_exactly_at_limit_is_permitted",
    ]


@pytest.mark.parametrize("tag", ["baseline-a", "baseline-b"])
def test_baseline_tag_tree_contains_the_expected_paths(
    built_fixture: BuiltFixture, tag: str
) -> None:
    listed = built_fixture.git(["ls-tree", "-r", "--name-only", tag]).splitlines()
    assert "evidence/verification-runs.json" in listed
    assert "evidence/accepted-links.json" in listed
    assert "requirements/REQ-001.md" in listed
    assert "src/accounts.py" in listed


def test_generator_pins_the_object_format(
    fixture_settings: Settings, tmp_path, monkeypatch: pytest.MonkeyPatch, committed_manifest
) -> None:
    """Review R5: an inherited GIT_DEFAULT_HASH must not change the baseline SHAs."""
    monkeypatch.setenv("GIT_DEFAULT_HASH", "sha256")
    manifest = fixturectl.build_repo(fixture_settings.fixture_dir, tmp_path / "sha256-host")
    assert manifest.tags == committed_manifest.tags
