"""AS-01 acceptance: the missing-verification finding matches the hand-labeled oracle."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.domain.api import FindingsResponse
from app.domain.enums import FindingType
from app.domain.models import finding_fingerprint
from app.domain.oracle import ExpectedFindingsFile
from app.persistence.fixtures import load_model
from app.settings import Settings

BASELINES = ("baseline-a", "baseline-b")


def oracle(fixture_settings: Settings, baseline: str) -> ExpectedFindingsFile:
    return load_model(fixture_settings.expected_dir / f"{baseline}.json", ExpectedFindingsFile)


def evaluate(client: TestClient, baseline: str) -> FindingsResponse:
    response = client.post("/api/assurance/evaluate", json={"baseline": baseline})
    assert response.status_code == 200
    return FindingsResponse.model_validate(response.json())


@pytest.mark.parametrize("baseline", BASELINES)
def test_evaluate_matches_the_oracle_missing_verification_finding(
    client: TestClient, fixture_settings: Settings, committed_manifest, baseline: str
) -> None:
    body = evaluate(client, baseline)
    expected = [
        item
        for item in oracle(fixture_settings, baseline).findings
        if item.finding_type is FindingType.MISSING_VERIFICATION_LINK
    ]
    assert len(expected) == 1
    assert body.baseline == baseline
    findings = [
        finding
        for finding in body.findings
        if finding.finding_type is FindingType.MISSING_VERIFICATION_LINK
    ]
    assert len(findings) == 1

    finding = findings[0]
    item = expected[0]
    assert finding.rule_id == item.rule_id
    assert finding.finding_type == item.finding_type
    assert finding.severity == item.severity
    assert finding.status == item.status
    assert finding.artifact_ids == item.artifact_ids
    assert finding.evidence_ids == []
    assert finding.explanation == item.explanation
    assert finding.finding_id == finding_fingerprint(
        item.rule_id, item.finding_type, item.artifact_ids
    )
    expected_commit = committed_manifest.tags[baseline]
    assert finding.evaluated_baseline == expected_commit
    assert finding.artifact_revisions["REQ-002"] == expected_commit


def test_evaluate_does_not_count_proposals(client: TestClient) -> None:
    body = evaluate(client, "baseline-a")
    missing = [
        finding
        for finding in body.findings
        if finding.finding_type is FindingType.MISSING_VERIFICATION_LINK
    ]
    assert [finding.artifact_ids for finding in missing] == [["REQ-002"]]
    assert not [finding for finding in missing if "REQ-001" in finding.artifact_ids]
    assert not [finding for finding in missing if "REQ-003" in finding.artifact_ids]


def test_evaluate_leaves_a_covered_requirement_alone(client: TestClient) -> None:
    body = evaluate(client, "baseline-a")
    assert not [finding for finding in body.findings if "REQ-001" in finding.artifact_ids]


def test_evaluate_by_tag_and_sha_identical(client: TestClient, committed_manifest) -> None:
    by_tag = evaluate(client, "baseline-b")
    response = client.post(
        "/api/assurance/evaluate",
        json={"baseline": committed_manifest.tags["baseline-b"]},
    )
    assert response.status_code == 200
    assert FindingsResponse.model_validate(response.json()) == by_tag


def test_unknown_baseline_is_404(client: TestClient) -> None:
    response = client.post("/api/assurance/evaluate", json={"baseline": "baseline-z"})
    assert response.status_code == 404
    assert response.json()["code"] == "baseline-not-found"


def test_unknown_policy_is_400(client: TestClient) -> None:
    response = client.post(
        "/api/assurance/evaluate",
        json={"baseline": "baseline-a", "policy": "invented"},
    )
    assert response.status_code == 400
    assert response.json()["code"] == "invalid-request"
