"""M2 assurance: oracle equality, precedence, append-only evidence, and change impact.

The oracle is hand-labeled (``fixtures/banking-demo/expected/``). This module compares the rule
engine to it field by field; it never derives an expectation from the evaluator.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.assurance.rules import DeterministicAssuranceEvaluator
from app.domain.enums import EvidenceResult, FindingType
from app.domain.models import finding_fingerprint
from app.domain.oracle import ExpectedFindingsFile
from app.persistence.fixtures import load_model
from app.persistence.ingested import IngestedStore

REPO_ROOT = Path(__file__).resolve().parents[2]
EXPECTED = REPO_ROOT / "fixtures" / "banking-demo" / "expected"

BUSINESS_KEYS = (
    "rule_id",
    "finding_type",
    "severity",
    "artifact_ids",
    "evidence_ids",
    "explanation",
)


def _expected_file(baseline: str) -> ExpectedFindingsFile:
    return load_model(EXPECTED / f"{baseline}.json", ExpectedFindingsFile)


@pytest.mark.parametrize("baseline", ["baseline-a", "baseline-b"])
def test_evaluated_findings_equal_the_hand_labeled_oracle(
    store: IngestedStore, baseline: str
) -> None:
    expected = _expected_file(baseline)
    findings = DeterministicAssuranceEvaluator(store).evaluate(baseline)
    commit = store.commit_of(baseline)

    assert len(findings) == len(expected.findings)
    actual = sorted(
        [{key: getattr(finding, key) for key in BUSINESS_KEYS} for finding in findings],
        key=lambda item: (item["rule_id"], tuple(item["artifact_ids"])),
    )
    wanted = sorted(
        [{key: getattr(item, key) for key in BUSINESS_KEYS} for item in expected.findings],
        key=lambda item: (item["rule_id"], tuple(item["artifact_ids"])),
    )
    assert actual == wanted

    for finding in findings:
        assert finding.evaluated_baseline == commit
        assert finding.finding_id == finding_fingerprint(
            finding.rule_id, finding.finding_type, finding.artifact_ids
        )
        assert set(finding.artifact_revisions) == set(finding.artifact_ids)
        artifacts = {artifact.artifact_id: artifact for artifact in store.list_artifacts(baseline)}
        for artifact_id, revision in finding.artifact_revisions.items():
            assert revision == artifacts[artifact_id].revision


def test_reverification_and_failure_never_collapse(store: IngestedStore) -> None:
    findings = DeterministicAssuranceEvaluator(store).evaluate("baseline-b")
    reverification = {
        tuple(finding.artifact_ids)
        for finding in findings
        if finding.finding_type is FindingType.REVERIFICATION_REQUIRED
    }
    failures = {
        tuple(finding.artifact_ids)
        for finding in findings
        if finding.finding_type is FindingType.VERIFICATION_FAILED
    }
    assert reverification == {("CODE-001", "REQ-001", "SCN-001")}
    assert failures == {("REQ-003", "SCN-003", "TEST-002")}
    assert not reverification & failures
    assert all("REQ-001" not in item for item in failures)
    assert all("SCN-003" not in item for item in reverification)


def test_baseline_a_has_no_failure_or_reverification(store: IngestedStore) -> None:
    findings = DeterministicAssuranceEvaluator(store).evaluate("baseline-a")
    types = {finding.finding_type for finding in findings}
    assert FindingType.REVERIFICATION_REQUIRED not in types
    assert FindingType.VERIFICATION_FAILED not in types
    assert {
        finding.finding_type for finding in findings if "REQ-001" in finding.artifact_ids
    } == set()


def test_evidence_is_append_only_and_pinned_to_the_tested_commit(store: IngestedStore) -> None:
    evidence = {row.evidence_id: row for row in store.list_evidence("baseline-b")}
    assert sorted(evidence) == ["EV-001", "EV-002", "EV-003"]
    assert evidence["EV-001"].tested_commit == store.manifest.commits[0].commit
    assert evidence["EV-001"].result.value == "passed"
    assert evidence["EV-001"].run_uri == "ci://banking-demo/runs/1001"
    assert evidence["EV-001"].executed_at.isoformat() == "2026-10-01T09:12:00+00:00"
    assert evidence["EV-003"].tested_commit == store.manifest.commits[2].commit
    assert evidence["EV-003"].result.value == "failed"
    assert evidence["EV-003"].executed_at.isoformat() == "2026-10-15T14:05:00+00:00"
    assert evidence["EV-002"].tested_commit != evidence["EV-003"].tested_commit


def test_change_set_is_content_hash_based_and_matches_the_oracle(store: IngestedStore) -> None:
    expected = _expected_file("baseline-b")
    assert expected.change_summary is not None
    changed = store.changed_artifacts("baseline-b", "baseline-a")
    assert changed == expected.change_summary.changed_artifact_ids
    unchanged = sorted(
        artifact.artifact_id
        for artifact in store.list_artifacts("baseline-a")
        if artifact.artifact_id not in changed
    )
    assert unchanged == expected.change_summary.unchanged_artifact_ids
    # An evidence-only commit changes SHAs but not artifact content hashes.
    assert store.changed_artifacts("baseline-a", "baseline-a") == []


def test_impacted_links_reach_the_changed_artifacts(store: IngestedStore) -> None:
    impacted = store.impacted_links("baseline-b", "baseline-a")
    assert [link.link_id for link in impacted] == ["LNK-002", "LNK-006"]
    assert {link.target_id for link in impacted} == {"CODE-001", "TEST-002"}


class _StubRepository:
    """Minimal port implementation for counterfactual change cases.

    The built fixture is the source of artifacts/links/evidence; the stub only replaces the
    evaluated artifact set (content hashes) and, in one case, a recorded outcome.
    """

    def __init__(self, store, evaluated, *, tested_commit, evidence=None, links=None):
        self._store = store
        self._evaluated = evaluated
        self._tested_commit = tested_commit
        self._evidence = evidence if evidence is not None else store.list_evidence("baseline-b")
        self._links = links

    def resolve_baseline(self, baseline):
        return baseline

    def commit_of(self, baseline):
        return self._store.commit_of("baseline-b")

    def list_artifacts(self, baseline):
        return list(self._evaluated.values())

    def artifacts_at(self, revision):
        return self._store.artifacts_at(revision)

    def list_links(self, baseline, review_state=None):
        links = self._links if self._links is not None else self._store.list_links("baseline-b")
        if review_state is None:
            return list(links)
        return [link for link in links if link.review_state is review_state]

    def list_evidence(self, baseline):
        return list(self._evidence)

    def label_of(self, commit):
        return self._store.label_of(commit)


def _changed(artifacts, artifact_id):
    changed = dict(artifacts)
    changed[artifact_id] = changed[artifact_id].model_copy(
        update={"content_hash": "sha256:" + "0" * 64}
    )
    return changed


def _baseline_b_artifacts(store):
    return {artifact.artifact_id: artifact for artifact in store.list_artifacts("baseline-b")}


def test_a_changed_test_still_requires_reverification(store: IngestedStore) -> None:
    evaluated = _changed(_baseline_b_artifacts(store), "TEST-001")
    stub = _StubRepository(store, evaluated, tested_commit=store.manifest.commits[0].commit)
    findings = DeterministicAssuranceEvaluator(stub).evaluate("baseline-b")
    reverification = [
        finding
        for finding in findings
        if finding.finding_type is FindingType.REVERIFICATION_REQUIRED
        and "REQ-001" in finding.artifact_ids
    ]
    assert len(reverification) == 1
    assert "TEST-001" in reverification[0].artifact_ids


def test_a_changed_scenario_still_requires_reverification(store: IngestedStore) -> None:
    evaluated = _changed(_baseline_b_artifacts(store), "SCN-001")
    stub = _StubRepository(store, evaluated, tested_commit=store.manifest.commits[0].commit)
    findings = DeterministicAssuranceEvaluator(stub).evaluate("baseline-b")
    reverification = [
        finding
        for finding in findings
        if finding.finding_type is FindingType.REVERIFICATION_REQUIRED
        and "REQ-001" in finding.artifact_ids
    ]
    assert len(reverification) == 1
    assert "SCN-001" in reverification[0].artifact_ids


def test_an_old_failure_is_not_current_after_implementation_change(store: IngestedStore) -> None:
    evidence = [
        row.model_copy(update={"result": EvidenceResult.FAILED})
        if row.evidence_id == "EV-001"
        else row
        for row in store.list_evidence("baseline-b")
    ]
    stub = _StubRepository(
        store,
        _baseline_b_artifacts(store),
        tested_commit=store.manifest.commits[0].commit,
        evidence=evidence,
    )
    findings = DeterministicAssuranceEvaluator(stub).evaluate("baseline-b")
    assert not [
        finding
        for finding in findings
        if "REQ-001" in finding.artifact_ids
        and finding.finding_type is FindingType.VERIFICATION_FAILED
    ]
    assert not [
        finding
        for finding in findings
        if "REQ-001" in finding.artifact_ids
        and finding.finding_type is FindingType.REVERIFICATION_REQUIRED
    ]


def test_an_added_accepted_implementation_requires_reverification(store: IngestedStore) -> None:
    from datetime import UTC, datetime

    from app.domain.enums import ArtifactType, RelationType, ReviewState
    from app.domain.models import Artifact, TraceLink

    now = datetime(2026, 11, 13, tzinfo=UTC)
    evaluated = _baseline_b_artifacts(store)
    evaluated["CODE-999"] = Artifact(
        artifact_id="CODE-999",
        artifact_type=ArtifactType.SOURCE,
        title="Newly linked implementation",
        source_uri="fixture://banking-demo/src/new.py",
        repository="banking-demo",
        revision=store.commit_of("baseline-b"),
        content_hash="sha256:" + "1" * 64,
        locator="src/new.py",
    )
    links = [
        *store.list_links("baseline-b"),
        TraceLink(
            link_id="LNK-999",
            source_id="SCN-001",
            target_id="CODE-999",
            relation_type=RelationType.IMPLEMENTED_BY,
            review_state=ReviewState.ACCEPTED,
            provenance={"reviewer_id": "probe", "decided_at": now.isoformat()},
            created_at=now,
            updated_at=now,
        ),
    ]
    stub = _StubRepository(
        store,
        evaluated,
        tested_commit=store.manifest.commits[0].commit,
        links=links,
    )
    findings = DeterministicAssuranceEvaluator(stub).evaluate("baseline-b")
    reverification = [
        finding
        for finding in findings
        if finding.finding_type is FindingType.REVERIFICATION_REQUIRED
        and "REQ-001" in finding.artifact_ids
    ]
    assert len(reverification) == 1
    assert "CODE-999" in reverification[0].artifact_ids
    assert not [
        finding
        for finding in findings
        if finding.finding_type is FindingType.VERIFICATION_FAILED
        and "REQ-001" in finding.artifact_ids
    ]
