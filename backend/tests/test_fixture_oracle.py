"""Oracle consistency: labels, snapshot, index, and policy must agree with each other.

These tests never compare the code under test to itself. They check the hand-labeled oracle
files (the specification) against the materialized fixture data (the shared input).
"""

from __future__ import annotations

import itertools

import pytest

from app.discovery.fake import compute_index_revision
from app.domain.enums import FindingType, ReviewState
from app.domain.models import finding_fingerprint
from app.domain.oracle import (
    BaselineSnapshot,
    CandidateIndexFile,
    ExpectedFindingsFile,
    FixtureSnapshot,
)
from app.domain.policy import RULE_DEFAULT_SEVERITY, RULE_FINDING_TYPE
from app.persistence.fixtures import load_model
from app.persistence.store import FixtureStore
from app.settings import Settings

BASELINES = ("baseline-a", "baseline-b")


def oracle(fixture_settings: Settings, name: str) -> ExpectedFindingsFile:
    return load_model(fixture_settings.expected_dir / f"{name}.json", ExpectedFindingsFile)


def baseline_snapshot(snapshot: FixtureSnapshot, name: str) -> BaselineSnapshot:
    return next(entry for entry in snapshot.baselines if entry.baseline == name)


def findings_of_type(expected: ExpectedFindingsFile, finding_type: FindingType):
    return [item for item in expected.findings if item.finding_type is finding_type]


def fingerprint(expected) -> str:
    return finding_fingerprint(expected.rule_id, expected.finding_type, expected.artifact_ids)


# --------------------------------------------------------------------------- oracle hygiene


@pytest.mark.parametrize("name", BASELINES)
def test_oracle_declares_its_own_baseline(
    fixture_settings: Settings, snapshot: FixtureSnapshot, name: str
) -> None:
    parsed = oracle(fixture_settings, name)
    assert parsed.baseline == name
    assert parsed.fixture == snapshot.fixture
    assert parsed.findings


@pytest.mark.parametrize("name", BASELINES)
def test_oracle_references_existing_artifacts_and_evidence(
    fixture_settings: Settings, snapshot: FixtureSnapshot, name: str
) -> None:
    parsed = oracle(fixture_settings, name)
    entry = baseline_snapshot(snapshot, name)
    artifact_ids = {artifact.artifact_id for artifact in entry.artifacts}
    evidence_ids = {item.evidence_id for item in entry.evidence}
    for finding in parsed.findings:
        assert set(finding.artifact_ids) <= artifact_ids
        assert set(finding.evidence_ids) <= evidence_ids


@pytest.mark.parametrize("name", BASELINES)
def test_oracle_severity_and_type_follow_the_declared_policy(
    fixture_settings: Settings, name: str
) -> None:
    for finding in oracle(fixture_settings, name).findings:
        assert finding.severity is RULE_DEFAULT_SEVERITY[finding.rule_id]
        assert finding.finding_type is RULE_FINDING_TYPE[finding.rule_id]


@pytest.mark.parametrize("name", BASELINES)
def test_findings_have_unique_fingerprints(fixture_settings: Settings, name: str) -> None:
    identifiers = [fingerprint(item) for item in oracle(fixture_settings, name).findings]
    assert len(identifiers) == len(set(identifiers))


def test_persisting_findings_keep_their_identity_across_baselines(
    fixture_settings: Settings,
) -> None:
    """The property M4 diffing depends on: new/unchanged findings, not new ids every run."""
    at_a = {fingerprint(item) for item in oracle(fixture_settings, "baseline-a").findings}
    at_b = {fingerprint(item) for item in oracle(fixture_settings, "baseline-b").findings}
    assert at_a <= at_b
    assert len(at_b - at_a) == 2


@pytest.mark.parametrize("name", BASELINES)
def test_healthy_artifacts_have_no_finding(fixture_settings: Settings, name: str) -> None:
    parsed = oracle(fixture_settings, name)
    for artifact_id in parsed.healthy_artifact_ids:
        assert not [item for item in parsed.findings if artifact_id in item.artifact_ids]
    if name == "baseline-a":
        assert parsed.healthy_artifact_ids == ["REQ-001"]
    else:
        assert parsed.healthy_artifact_ids == []


# ------------------------------------------------------------------------------ case checks


def test_case_2_and_3_coverage_gaps_are_labeled(fixture_settings: Settings) -> None:
    parsed = oracle(fixture_settings, "baseline-a")
    missing_verification = findings_of_type(parsed, FindingType.MISSING_VERIFICATION_LINK)
    missing_implementation = findings_of_type(parsed, FindingType.MISSING_IMPLEMENTATION_LINK)
    assert [item.artifact_ids for item in missing_verification] == [["REQ-002"]]
    assert [item.artifact_ids for item in missing_implementation] == [["SCN-002"]]


def test_case_6_proposal_is_pending_and_not_accepted(
    fixture_settings: Settings, snapshot: FixtureSnapshot
) -> None:
    parsed = oracle(fixture_settings, "baseline-a")
    pending = findings_of_type(parsed, FindingType.CANDIDATE_PENDING_REVIEW)
    assert [item.artifact_ids for item in pending] == [["REQ-002", "SCN-002"]]

    entry = baseline_snapshot(snapshot, "baseline-a")
    pair = ("REQ-002", "SCN-002")
    assert not [link for link in entry.accepted_links if (link.source_id, link.target_id) == pair]
    proposed = [link for link in entry.proposed_links if (link.source_id, link.target_id) == pair]
    assert [link.link_id for link in proposed] == ["LNK-007"]
    assert proposed[0].review_state is ReviewState.PROPOSED


def test_case_6_proposal_provenance_matches_the_index_candidate(
    fixture_settings: Settings, snapshot: FixtureSnapshot
) -> None:
    index = load_model(fixture_settings.expected_dir / "candidate-links.json", CandidateIndexFile)
    link = next(
        link
        for link in baseline_snapshot(snapshot, "baseline-a").proposed_links
        if link.link_id == "LNK-007"
    )
    matches = [
        candidate
        for candidate in index.candidates
        if (candidate.source_id, candidate.target_id, candidate.proposed_relation_type)
        == (link.source_id, link.target_id, link.relation_type)
    ]
    assert len(matches) == 1
    assert link.provenance["score"] == matches[0].score
    assert link.provenance["index_revision"] == compute_index_revision(index)
    assert link.provenance["model_version"] == index.model_version
    assert link.provenance["discovery_provider"] == index.provider


def test_case_7_superseded_requirement_is_flagged_for_lifecycle_review(
    fixture_settings: Settings, snapshot: FixtureSnapshot
) -> None:
    for name in BASELINES:
        lifecycle = findings_of_type(
            oracle(fixture_settings, name), FindingType.LIFECYCLE_REVIEW_REQUIRED
        )
        assert [item.artifact_ids for item in lifecycle] == [["REQ-003"]]
    superseded = baseline_snapshot(snapshot, "baseline-a").artifact("REQ-003")
    assert superseded is not None
    assert superseded.metadata["status"] == "superseded"
    assert baseline_snapshot(snapshot, "baseline-a").accepted_links  # still has live relationships


def test_case_4_reverification_identifies_both_baselines_and_the_change(
    fixture_settings: Settings, snapshot: FixtureSnapshot, built_fixture
) -> None:
    parsed = oracle(fixture_settings, "baseline-b")
    reverification = findings_of_type(parsed, FindingType.REVERIFICATION_REQUIRED)
    assert len(reverification) == 1
    finding = reverification[0]
    assert finding.artifact_ids == ["CODE-001", "REQ-001", "SCN-001"]
    assert finding.evidence_ids == ["EV-001"]

    at_a, at_b = (
        baseline_snapshot(snapshot, "baseline-a"),
        baseline_snapshot(snapshot, "baseline-b"),
    )
    evidence = next(item for item in at_a.evidence if item.evidence_id == "EV-001")
    assert evidence.result.value == "passed"

    # both baselines are identifiable, and the attributed change is real: compare the content
    # hash of CODE-001 at the evaluated baseline with the bytes that were actually executed
    assert evidence.tested_commit != at_b.commit
    code_at_a = at_a.artifact("CODE-001")
    code_at_b = at_b.artifact("CODE-001")
    assert (
        built_fixture.blob_sha256(evidence.tested_commit, code_at_a.locator)
        == code_at_a.content_hash
    )
    assert built_fixture.blob_sha256(at_b.commit, code_at_b.locator) == code_at_b.content_hash
    assert code_at_a.content_hash != code_at_b.content_hash
    test_at_a, test_at_b = at_a.artifact("TEST-001"), at_b.artifact("TEST-001")
    assert (
        built_fixture.blob_sha256(evidence.tested_commit, test_at_a.locator)
        == test_at_a.content_hash
    )
    assert test_at_a.content_hash == test_at_b.content_hash

    # the only evidence for SCN-001 is the baseline-a run: nothing was executed after the change
    scn001 = [item for item in at_b.evidence if item.scenario_id == "SCN-001"]
    assert [item.evidence_id for item in scn001] == ["EV-001"]

    # and the requirement is not reported as failed
    assert not [
        item
        for item in parsed.findings
        if item.finding_type is FindingType.VERIFICATION_FAILED and "REQ-001" in item.artifact_ids
    ]


def test_case_5_failure_is_distinct_from_staleness(
    fixture_settings: Settings, snapshot: FixtureSnapshot
) -> None:
    parsed = oracle(fixture_settings, "baseline-b")
    failed = findings_of_type(parsed, FindingType.VERIFICATION_FAILED)
    assert len(failed) == 1
    assert failed[0].artifact_ids == ["REQ-003", "SCN-003", "TEST-002"]
    assert failed[0].evidence_ids == ["EV-003"]

    at_b = baseline_snapshot(snapshot, "baseline-b")
    evidence = next(item for item in at_b.evidence if item.evidence_id == "EV-003")
    assert evidence.result.value == "failed"
    assert evidence.tested_commit != at_b.commit  # recorded by CI against the source revision

    assert not [
        item
        for item in parsed.findings
        if item.finding_type is FindingType.REVERIFICATION_REQUIRED
        and "SCN-003" in item.artifact_ids
    ]
    assert not [
        item
        for item in parsed.findings
        if item.finding_type is FindingType.VERIFICATION_FAILED and "REQ-002" in item.artifact_ids
    ]


def test_change_summary_matches_content_hash_comparison(
    store: FixtureStore, fixture_settings: Settings
) -> None:
    parsed = oracle(fixture_settings, "baseline-b")
    assert parsed.change_summary is not None
    changed = store.changed_artifacts("baseline-b", "baseline-a")
    assert changed == sorted(parsed.change_summary.changed_artifact_ids)

    all_ids = {artifact.artifact_id for artifact in store.list_artifacts("baseline-b")}
    assert sorted(all_ids - set(changed)) == sorted(parsed.change_summary.unchanged_artifact_ids)


# -------------------------------------------------------------------------- candidate index


def test_candidate_index_is_labeled_for_evaluation(fixture_settings: Settings) -> None:
    index = load_model(fixture_settings.expected_dir / "candidate-links.json", CandidateIndexFile)
    assert {candidate.label for candidate in index.candidates} == {"positive", "negative"}
    assert index.provider == "fake"
    assert index.model_version


def test_candidate_index_lists_candidates_in_descending_score_order(
    fixture_settings: Settings,
) -> None:
    index = load_model(fixture_settings.expected_dir / "candidate-links.json", CandidateIndexFile)
    grouped = itertools.groupby(
        sorted(index.candidates, key=lambda candidate: candidate.source_id),
        key=lambda candidate: candidate.source_id,
    )
    for source_id, group in grouped:
        scores = [candidate.score for candidate in group]
        assert scores == sorted(scores, reverse=True), f"{source_id} is not in rank order"


def test_candidate_index_references_known_artifacts(
    fixture_settings: Settings, snapshot: FixtureSnapshot
) -> None:
    index = load_model(fixture_settings.expected_dir / "candidate-links.json", CandidateIndexFile)
    known = {artifact.artifact_id for entry in snapshot.baselines for artifact in entry.artifacts}
    assert {candidate.source_id for candidate in index.candidates} <= known
    assert {candidate.target_id for candidate in index.candidates} <= known


def test_a_negative_labeled_candidate_was_never_accepted(
    fixture_settings: Settings, snapshot: FixtureSnapshot
) -> None:
    index = load_model(fixture_settings.expected_dir / "candidate-links.json", CandidateIndexFile)
    negatives = {
        (candidate.source_id, candidate.target_id, candidate.proposed_relation_type)
        for candidate in index.candidates
        if candidate.label == "negative"
    }
    assert negatives
    accepted = {
        (link.source_id, link.target_id, link.relation_type)
        for entry in snapshot.baselines
        for link in entry.accepted_links
    }
    assert negatives.isdisjoint(accepted)


def test_lifecycle_metadata_is_only_used_for_superseded_requirements(
    snapshot: FixtureSnapshot,
) -> None:
    statuses = {
        artifact.artifact_id: artifact.metadata.get("status")
        for entry in snapshot.baselines
        for artifact in entry.artifacts
        if artifact.artifact_type.value == "requirement"
    }
    assert statuses == {"REQ-001": "active", "REQ-002": "active", "REQ-003": "superseded"}
