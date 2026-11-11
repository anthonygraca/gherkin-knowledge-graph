"""Contract tests for the shared domain models (no fixtures, no services)."""

from __future__ import annotations

import os
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.domain.enums import (
    ArtifactType,
    EvidenceResult,
    FindingStatus,
    FindingType,
    RelationType,
    ReviewState,
    RuleId,
    Severity,
)
from app.domain.models import (
    Artifact,
    TraceCandidate,
    TraceLink,
    VerificationEvidence,
    finding_fingerprint,
    make_finding,
)
from app.domain.policy import RULE_DEFAULT_SEVERITY, RULE_FINDING_TYPE
from app.domain.ports import CandidateDiscovery
from app.settings import ENV_DISCOVERY_PROVIDER, ENV_FIXTURES_DIR, load_settings

AWARE = datetime(2026, 10, 1, 9, 0, tzinfo=UTC)


def artifact(**overrides: object) -> Artifact:
    payload: dict[str, object] = {
        "artifact_id": "CODE-001",
        "artifact_type": ArtifactType.SOURCE,
        "title": "src/accounts.py",
        "source_uri": "fixture://banking-demo/src/accounts.py",
        "repository": "banking-demo",
        "revision": "0" * 40,
        "content_hash": "sha256:" + "a" * 64,
        "locator": "src/accounts.py",
    }
    payload.update(overrides)
    return Artifact.model_validate(payload)


# ------------------------------------------------------------------------------- artifacts


def test_artifact_rejects_malformed_content_hash() -> None:
    with pytest.raises(ValidationError):
        artifact(content_hash="deadbeef")


def test_artifact_rejects_unknown_keys() -> None:
    with pytest.raises(ValidationError):
        artifact(verified=True)


def test_artifact_rejects_non_uri_source() -> None:
    with pytest.raises(ValidationError):
        artifact(source_uri="src/accounts.py")


def test_artifact_accepts_status_metadata() -> None:
    superseded = artifact(metadata={"status": "superseded"})
    assert superseded.metadata["status"] == "superseded"


# ----------------------------------------------------------------------------------- links


def test_link_rejects_self_loop_and_reversed_timestamps() -> None:
    base: dict[str, object] = {
        "link_id": "LNK-001",
        "source_id": "REQ-001",
        "target_id": "SCN-001",
        "relation_type": RelationType.VERIFIED_BY,
        "review_state": ReviewState.PROPOSED,
        "created_at": AWARE,
        "updated_at": AWARE,
    }
    assert TraceLink.model_validate(base).review_state is ReviewState.PROPOSED
    with pytest.raises(ValidationError):
        TraceLink.model_validate({**base, "target_id": "REQ-001"})
    with pytest.raises(ValidationError):
        TraceLink.model_validate({**base, "created_at": datetime(2026, 10, 2, tzinfo=UTC)})


def test_link_requires_timezone_aware_timestamps() -> None:
    with pytest.raises(ValidationError):
        TraceLink.model_validate(
            {
                "link_id": "LNK-001",
                "source_id": "REQ-001",
                "target_id": "SCN-001",
                "relation_type": RelationType.VERIFIED_BY,
                "review_state": ReviewState.ACCEPTED,
                "created_at": datetime(2026, 10, 1, 9, 0),
                "updated_at": datetime(2026, 10, 1, 9, 0),
            }
        )


# -------------------------------------------------------------------------------- evidence


def test_evidence_requires_aware_timestamps_and_a_test_id() -> None:
    payload: dict[str, object] = {
        "evidence_id": "EV-001",
        "test_id": "TEST-001",
        "scenario_id": "SCN-001",
        "result": EvidenceResult.PASSED,
        "tested_commit": "0" * 40,
        "executed_at": AWARE,
        "run_uri": "ci://banking-demo/runs/1001",
    }
    evidence = VerificationEvidence.model_validate(payload)
    assert evidence.result is EvidenceResult.PASSED
    with pytest.raises(ValidationError):
        VerificationEvidence.model_validate({**payload, "executed_at": datetime(2026, 10, 1)})
    with pytest.raises(ValidationError):
        VerificationEvidence.model_validate({**payload, "test_id": "accounts"})


# ------------------------------------------------------------------ candidates vs acceptance


def test_candidate_has_no_acceptance_vocabulary() -> None:
    """A proposal must have no field in which an accepted state could be smuggled."""
    forbidden = {"link_id", "review_state", "accepted_at", "evidence_id", "verified"}
    assert forbidden.isdisjoint(TraceCandidate.model_fields)


def test_candidate_rejects_self_loop_and_out_of_range_score() -> None:
    payload: dict[str, object] = {
        "source_id": "SCN-001",
        "target_id": "CODE-001",
        "proposed_relation_type": RelationType.IMPLEMENTED_BY,
        "rank": 1,
        "score": 0.9,
        "discovery_provider": "fake",
        "model_version": "fake-fixture-v1",
        "index_revision": "sha256:" + "b" * 64,
    }
    assert TraceCandidate.model_validate(payload).rank == 1
    with pytest.raises(ValidationError):
        TraceCandidate.model_validate({**payload, "target_id": "SCN-001"})
    with pytest.raises(ValidationError):
        TraceCandidate.model_validate({**payload, "score": 1.5})


def test_candidate_discovery_port_surface_is_minimal() -> None:
    assert set(CandidateDiscovery.__protocol_attrs__) == {
        "provider_name",
        "model_version",
        "index_revision",
        "discover",
    }


# -------------------------------------------------------------------------------- findings


def test_findings_are_sorted_and_deduplicated() -> None:
    finding = make_finding(
        rule_id=RuleId.MISSING_VERIFICATION_LINK,
        finding_type=FindingType.MISSING_VERIFICATION_LINK,
        severity=Severity.HIGH,
        artifact_ids=["SCN-001", "REQ-002", "SCN-001"],
        evaluated_baseline="f" * 40,
        explanation="gap",
        evidence_ids=["EV-002", "EV-001", "EV-001"],
    )
    assert finding.artifact_ids == ["REQ-002", "SCN-001"]
    assert finding.evidence_ids == ["EV-001", "EV-002"]


def test_finding_fingerprint_ignores_baseline_evidence_and_prose() -> None:
    first = make_finding(
        rule_id=RuleId.REVERIFICATION_REQUIRED,
        finding_type=FindingType.REVERIFICATION_REQUIRED,
        severity=Severity.MEDIUM,
        artifact_ids=["REQ-001", "SCN-001", "CODE-001"],
        evaluated_baseline="a" * 40,
        explanation="first wording",
        evidence_ids=["EV-001"],
    )
    second = make_finding(
        rule_id=RuleId.REVERIFICATION_REQUIRED,
        finding_type=FindingType.REVERIFICATION_REQUIRED,
        severity=Severity.MEDIUM,
        artifact_ids=["CODE-001", "SCN-001", "REQ-001"],
        evaluated_baseline="b" * 40,
        explanation="different wording entirely",
        evidence_ids=["EV-009"],
    )
    assert first.finding_id == second.finding_id
    assert first.evaluated_baseline != second.evaluated_baseline


def test_finding_fingerprint_depends_on_artifacts_rules_and_type() -> None:
    def fingerprint(rule: RuleId, finding_type: FindingType, artifacts: list[str]) -> str:
        return finding_fingerprint(rule, finding_type, artifacts)

    baseline = fingerprint(
        RuleId.MISSING_IMPLEMENTATION_LINK, FindingType.MISSING_IMPLEMENTATION_LINK, ["SCN-002"]
    )
    assert baseline == fingerprint(
        RuleId.MISSING_IMPLEMENTATION_LINK, FindingType.MISSING_IMPLEMENTATION_LINK, ["SCN-002"]
    )
    assert baseline != fingerprint(
        RuleId.MISSING_IMPLEMENTATION_LINK, FindingType.MISSING_IMPLEMENTATION_LINK, ["SCN-003"]
    )
    assert baseline != fingerprint(
        RuleId.MISSING_VERIFICATION_LINK, FindingType.MISSING_IMPLEMENTATION_LINK, ["SCN-002"]
    )
    assert baseline != fingerprint(
        RuleId.MISSING_IMPLEMENTATION_LINK, FindingType.MISSING_VERIFICATION_LINK, ["SCN-002"]
    )


def test_finding_fingerprint_format() -> None:
    value = finding_fingerprint(
        RuleId.VERIFICATION_FAILED, FindingType.VERIFICATION_FAILED, ["TEST-002"]
    )
    assert value.startswith("FND-")
    assert len(value) == len("FND-") + 16
    assert set(value[4:]) <= set("0123456789abcdef")


def test_policy_tables_cover_every_rule_and_agree_on_types() -> None:
    assert set(RULE_DEFAULT_SEVERITY) == set(RuleId)
    assert set(RULE_FINDING_TYPE) == set(RuleId)
    assert RULE_FINDING_TYPE[RuleId.LIFECYCLE_SUPERSEDED] is FindingType.LIFECYCLE_REVIEW_REQUIRED


# Expected values computed independently from ``finding_fingerprint`` (review finding R6): if the
# test took its expectation from the production helper, switching the hash function would pass.
# Vectors deliberately include duplicate and out-of-order artifact ids.
INDEPENDENT_FINGERPRINT_VECTORS = [
    (
        "RULE-MISSING-IMPLEMENTATION-LINK",
        "missing_implementation_link",
        ["SCN-002", "SCN-002"],
        "FND-b48266a397c838c9",
    ),
    (
        "RULE-REVERIFICATION-REQUIRED",
        "reverification_required",
        ["SCN-001", "CODE-001", "REQ-001"],
        "FND-c458a6d4a5494d67",
    ),
    (
        "RULE-LIFECYCLE-SUPERSEDED",
        "lifecycle_review_required",
        ["REQ-003"],
        "FND-4a4f24555531acf3",
    ),
]


@pytest.mark.parametrize(
    ("rule_id", "finding_type", "artifact_ids", "expected"),
    INDEPENDENT_FINGERPRINT_VECTORS,
)
def test_fingerprint_matches_an_independently_computed_vector(
    rule_id: str, finding_type: str, artifact_ids: list[str], expected: str
) -> None:
    assert finding_fingerprint(RuleId(rule_id), FindingType(finding_type), artifact_ids) == expected


def test_finding_status_default_is_open() -> None:
    finding = make_finding(
        rule_id=RuleId.CANDIDATE_PENDING_REVIEW,
        finding_type=FindingType.CANDIDATE_PENDING_REVIEW,
        severity=Severity.LOW,
        artifact_ids=["REQ-002"],
        evaluated_baseline="c" * 40,
        explanation="pending",
    )
    assert finding.status is FindingStatus.OPEN


# -------------------------------------------------------------------------------- settings


def test_settings_env_overrides(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setenv(ENV_FIXTURES_DIR, str(tmp_path / "fixtures"))
    monkeypatch.setenv(ENV_DISCOVERY_PROVIDER, "fake")
    settings = load_settings()
    assert settings.fixtures_dir == (tmp_path / "fixtures")
    assert settings.fixture_dir == tmp_path / "fixtures" / "banking-demo"
    assert settings.discovery_provider == "fake"
    assert os.fspath(settings.snapshot_path).endswith("api-responses/snapshot.json")
