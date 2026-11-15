"""AS-06: review journal, proposal capture, workspace projection, and restart recovery."""

from __future__ import annotations

import hashlib
import json
import threading
from dataclasses import replace
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from tests.conftest import BuiltFixture

from app.domain.enums import ReviewDecision
from app.domain.errors import ReviewConflict
from app.domain.review import make_proposal_snapshot
from app.main import create_app
from app.persistence.review import ReviewJournal, ReviewWorkspace
from app.settings import Settings, SettingsError

FIXED_SNAPSHOT_DIGEST = "sha256:4fd8412568cb2f1ee67bc8708efd7ebb6c5f371fa10f2a2fff2f28640eaa1c24"


def independent_snapshot_digest(
    *,
    source_id: str,
    target_id: str,
    relation_type: str,
    baseline: str,
    baseline_commit: str,
    source_content_hash: str,
    target_content_hash: str,
    provider: str | None,
    model_version: str | None,
    index_revision: str | None,
) -> str:
    """The reviewed identity-field set, hashed without the production helper."""
    payload = {
        "source_id": source_id,
        "target_id": target_id,
        "relation_type": relation_type,
        "baseline": baseline,
        "baseline_commit": baseline_commit,
        "source_content_hash": source_content_hash,
        "target_content_hash": target_content_hash,
        "provider": provider,
        "model_version": model_version,
        "index_revision": index_revision,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return f"sha256:{hashlib.sha256(canonical.encode('utf-8')).hexdigest()}"


def review_settings(
    base: Settings,
    tmp_path: Path,
    *,
    operator: str | None = "rv-ana",
    journal: Path | None = None,
) -> Settings:
    return replace(
        base,
        review_operator=operator,
        review_journal_path=journal or (tmp_path / "review-journal.ndjson"),
    )


def capture_payload(client: TestClient, **overrides: object) -> dict[str, object]:
    return capture_payload_for(client, "baseline-a", **overrides)


def capture_payload_for(
    client: TestClient, baseline: str, **overrides: object
) -> dict[str, object]:
    artifacts = {
        artifact["artifact_id"]: artifact
        for artifact in client.get("/api/artifacts", params={"baseline": baseline}).json()[
            "artifacts"
        ]
    }
    payload: dict[str, object] = {
        "source_id": "SCN-002",
        "target_id": "CODE-001",
        "relation_type": "implemented_by",
        "baseline": baseline,
        "source_content_hash": artifacts["SCN-002"]["content_hash"],
        "target_content_hash": artifacts["CODE-001"]["content_hash"],
        "provider": "fake",
        "model_version": "fake-fixture-v1",
        "index_revision": "sha256:" + "a" * 64,
        "score": 0.71,
    }
    payload.update(overrides)
    return payload


def capture(client: TestClient, **overrides: object) -> dict[str, object]:
    response = client.post("/api/link-proposals", json=capture_payload(client, **overrides))
    assert response.status_code == 201, response.text
    return response.json()


def accept(client: TestClient, link_id: str, baseline: str = "baseline-a") -> dict[str, object]:
    response = client.post(
        f"/api/links/{link_id}/review",
        json={"decision": "accept", "reviewer_id": "rv-ana", "baseline": baseline},
    )
    assert response.status_code == 200, response.text
    return response.json()


def reject(
    client: TestClient, link_id: str, reason: str, baseline: str = "baseline-a"
) -> dict[str, object]:
    response = client.post(
        f"/api/links/{link_id}/review",
        json={
            "decision": "reject",
            "reviewer_id": "rv-ana",
            "baseline": baseline,
            "reason": reason,
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


@pytest.fixture
def app_client(fixture_settings: Settings, tmp_path: Path) -> tuple[TestClient, Settings]:
    settings = review_settings(fixture_settings, tmp_path)
    return TestClient(create_app(settings)), settings


# ------------------------------------------------------------------ capture


def test_capture_is_only_a_proposal_and_does_not_mutate_fixture(
    app_client: tuple[TestClient, Settings], built_fixture: BuiltFixture
) -> None:
    client, _ = app_client
    before_head = built_fixture.git(["rev-parse", "HEAD"])
    before_status = built_fixture.git(["status", "--porcelain"])
    before_findings = client.get("/api/findings", params={"baseline": "baseline-a"}).json()
    before_thread = client.get("/api/threads/REQ-002", params={"baseline": "baseline-a"}).json()

    body = capture(client)

    assert body["created"] is True
    assert body["link"]["review_state"] == "proposed"
    assert body["link"]["link_id"] == "LNK-008"
    assert body["snapshot"]["provider"] == "fake"
    assert body["snapshot"]["model_version"] == "fake-fixture-v1"
    assert body["snapshot"]["baseline"] == "baseline-a"
    assert body["snapshot"]["source_content_hash"].startswith("sha256:")
    assert body["snapshot"]["snapshot_digest"] == independent_snapshot_digest(
        source_id="SCN-002",
        target_id="CODE-001",
        relation_type="implemented_by",
        baseline="baseline-a",
        baseline_commit=body["snapshot"]["baseline_commit"],
        source_content_hash=body["snapshot"]["source_content_hash"],
        target_content_hash=body["snapshot"]["target_content_hash"],
        provider="fake",
        model_version="fake-fixture-v1",
        index_revision="sha256:" + "a" * 64,
    )

    assert client.get("/api/findings", params={"baseline": "baseline-a"}).json() == before_findings
    after_thread = client.get("/api/threads/REQ-002", params={"baseline": "baseline-a"}).json()
    assert after_thread == before_thread
    assert built_fixture.git(["rev-parse", "HEAD"]) == before_head
    assert built_fixture.git(["status", "--porcelain"]) == before_status


def test_capture_validates_endpoints_direction_and_hashes(
    app_client: tuple[TestClient, Settings],
) -> None:
    client, _ = app_client
    unknown = client.post("/api/link-proposals", json=capture_payload(client, target_id="SCN-999"))
    assert unknown.status_code == 422
    assert unknown.json()["code"] == "proposal-invalid"

    wrong_direction = client.post(
        "/api/link-proposals",
        json=capture_payload(
            client,
            source_id="CODE-001",
            target_id="SCN-002",
            source_content_hash=capture_payload(client)["target_content_hash"],
            target_content_hash=capture_payload(client)["source_content_hash"],
        ),
    )
    assert wrong_direction.status_code == 422
    assert wrong_direction.json()["code"] == "proposal-invalid"

    stale_hash = client.post(
        "/api/link-proposals",
        json=capture_payload(client, source_content_hash="sha256:" + "b" * 64),
    )
    assert stale_hash.status_code == 409
    assert stale_hash.json()["code"] == "proposal-stale"
    pending = client.get("/api/workspace/proposals").json()["proposals"]
    assert pending[0]["link"]["link_id"] == "LNK-007"


def test_capture_identity_is_explicit(app_client: tuple[TestClient, Settings]) -> None:
    client, settings = app_client
    body = capture(client)
    link_id = body["link"]["link_id"]

    duplicate = client.post("/api/link-proposals", json=capture_payload(client))
    assert duplicate.status_code == 200
    assert duplicate.json()["created"] is False
    assert duplicate.json()["link"]["link_id"] == link_id

    conflict = client.post(
        "/api/link-proposals", json=capture_payload(client, provider="cocoindex")
    )
    assert conflict.status_code == 409
    assert conflict.json()["code"] == "proposal-conflict"

    accept(client, link_id)
    terminal = client.post("/api/link-proposals", json=capture_payload(client))
    assert terminal.status_code == 409
    assert terminal.json()["code"] == "review-conflict"

    journal_lines = settings.review_journal.read_text("utf-8").splitlines()
    assert len(journal_lines) == 4  # capture payload+commit, decision payload+commit


# ---------------------------------------------------------------- decisions


def test_accept_projects_workspace_and_preserves_baseline(
    app_client: tuple[TestClient, Settings],
) -> None:
    client, settings = app_client
    before_findings = client.get("/api/findings", params={"baseline": "baseline-a"}).json()
    before_evidence = client.get("/api/threads/REQ-002", params={"baseline": "baseline-a"}).json()[
        "evidence"
    ]

    decided = accept(client, "LNK-007")

    assert decided["review_state"] == "accepted"
    assert decided["provenance"]["reviewed_by"] == "rv-ana"
    assert decided["provenance"]["decision"] == "accept"
    assert decided["provenance"]["snapshot_digest"].startswith("sha256:")

    thread = client.get("/api/workspace/threads/REQ-002", params={"baseline": "baseline-a"}).json()
    assert [link["link_id"] for link in thread["accepted_links"]] == ["LNK-007"]
    assert thread["proposed_links"] == []

    pending = client.get("/api/workspace/proposals", params={"baseline": "baseline-a"}).json()
    assert pending["proposals"] == []

    history = client.get("/api/workspace/history", params={"baseline": "baseline-a"}).json()
    assert [(event["event"], event.get("decision")) for event in history["events"]] == [
        ("decision_recorded", "accept")
    ]
    assert history["events"][0]["operator"] == "rv-ana"
    assert history["events"][0]["recorded_at"].endswith("Z")

    assert client.get("/api/findings", params={"baseline": "baseline-a"}).json() == before_findings
    assert (
        client.get("/api/threads/REQ-002", params={"baseline": "baseline-a"}).json()["evidence"]
        == before_evidence
    )
    assert (
        client.get("/api/threads/REQ-002", params={"baseline": "baseline-a"}).json()[
            "accepted_links"
        ]
        == []
    )
    assert settings.review_journal.exists()


def test_rejection_retains_reason_and_excludes_proposal(
    app_client: tuple[TestClient, Settings],
) -> None:
    client, _ = app_client
    reason = "The scenario does not cover the requirement"
    decided = reject(client, "LNK-007", reason)
    assert decided["review_state"] == "rejected"

    history = client.get("/api/workspace/history", params={"baseline": "baseline-a"}).json()
    assert history["events"][0]["decision"] == "reject"
    assert history["events"][0]["reason"] == reason

    thread = client.get("/api/workspace/threads/REQ-002", params={"baseline": "baseline-a"}).json()
    assert thread["accepted_links"] == []
    assert thread["proposed_links"] == []
    assert client.get("/api/workspace/proposals").json()["proposals"] == []


def test_identity_and_reason_errors_append_nothing(
    app_client: tuple[TestClient, Settings],
) -> None:
    client, settings = app_client
    mismatch = client.post(
        "/api/links/LNK-007/review",
        json={"decision": "accept", "reviewer_id": "rv-mallory", "baseline": "baseline-a"},
    )
    assert mismatch.status_code == 403
    assert mismatch.json()["code"] == "review-identity-mismatch"

    absent = client.post(
        "/api/links/LNK-007/review",
        json={"decision": "reject", "reviewer_id": "rv-ana", "baseline": "baseline-a"},
    )
    assert absent.status_code == 422
    assert absent.json()["code"] == "request-validation"

    null = client.post(
        "/api/links/LNK-007/review",
        json={
            "decision": "reject",
            "reviewer_id": "rv-ana",
            "baseline": "baseline-a",
            "reason": None,
        },
    )
    assert null.status_code == 422
    assert null.json()["code"] == "request-validation"

    for blank in ("", "   "):
        response = client.post(
            "/api/links/LNK-007/review",
            json={
                "decision": "reject",
                "reviewer_id": "rv-ana",
                "baseline": "baseline-a",
                "reason": blank,
            },
        )
        assert response.status_code == 422
        assert response.json()["code"] == "review-reason-required"

    assert not settings.review_journal.exists()


def test_unset_operator_disables_writes(fixture_settings: Settings, tmp_path: Path) -> None:
    settings = review_settings(fixture_settings, tmp_path, operator=None)
    client = TestClient(create_app(settings))
    response = client.post(
        "/api/links/LNK-007/review",
        json={"decision": "accept", "reviewer_id": "rv-ana", "baseline": "baseline-a"},
    )
    assert response.status_code == 503
    assert response.json()["code"] == "review-identity-unavailable"
    assert client.get("/api/review/config").json()["enabled"] is False


def test_second_terminal_decision_preserves_original_bytes(
    app_client: tuple[TestClient, Settings],
) -> None:
    client, settings = app_client
    accept(client, "LNK-007")
    before = settings.review_journal.read_bytes()

    second = client.post(
        "/api/links/LNK-007/review",
        json={
            "decision": "reject",
            "reviewer_id": "rv-ana",
            "baseline": "baseline-a",
            "reason": "Changed my mind",
        },
    )
    assert second.status_code == 409
    assert second.json()["code"] == "review-conflict"
    assert settings.review_journal.read_bytes() == before


def test_stale_acceptance_is_refused(app_client: tuple[TestClient, Settings]) -> None:
    client, settings = app_client
    body = capture(client)
    link_id = body["link"]["link_id"]
    before = settings.review_journal.read_bytes()

    response = client.post(
        f"/api/links/{link_id}/review",
        json={"decision": "accept", "reviewer_id": "rv-ana", "baseline": "baseline-b"},
    )
    assert response.status_code == 409
    assert response.json()["code"] == "proposal-stale"
    assert settings.review_journal.read_bytes() == before
    assert client.get("/api/findings", params={"baseline": "baseline-b"}).json()["findings"]


def test_missing_proposal_is_a_typed_404(app_client: tuple[TestClient, Settings]) -> None:
    client, _ = app_client
    response = client.post(
        "/api/links/LNK-999/review",
        json={"decision": "accept", "reviewer_id": "rv-ana", "baseline": "baseline-a"},
    )
    assert response.status_code == 404
    assert response.json()["code"] == "proposal-not-found"


# ---------------------------------------------------------------- durability


def test_pending_capture_and_rejection_survive_restart(
    app_client: tuple[TestClient, Settings],
) -> None:
    client, settings = app_client
    captured = capture(client)
    reject(client, "LNK-007", "Not this scenario")
    before = settings.review_journal.read_bytes()

    restarted = TestClient(create_app(settings))
    pending = restarted.get("/api/workspace/proposals", params={"baseline": "baseline-a"}).json()
    assert [record["link"]["link_id"] for record in pending["proposals"]] == [
        captured["link"]["link_id"]
    ]
    assert pending["proposals"][0]["snapshot"]["provider"] == "fake"
    assert pending["proposals"][0]["binding"] == "captured"
    history = restarted.get("/api/workspace/history", params={"baseline": "baseline-a"}).json()
    assert [(event["event"], event.get("decision")) for event in history["events"]] == [
        ("proposal_captured", None),
        ("decision_recorded", "reject"),
    ]
    assert history["events"][1]["reason"] == "Not this scenario"
    assert settings.review_journal.read_bytes() == before


def test_concurrent_decisions_serialize(app_client: tuple[TestClient, Settings]) -> None:
    client, _ = app_client
    workspace: ReviewWorkspace = client.app.state.review
    outcomes: list[str] = []

    def decide(decision: ReviewDecision) -> None:
        try:
            workspace.review(
                "LNK-007",
                decision=decision,
                reviewer_id="rv-ana",
                baseline="baseline-a",
                reason=None if decision is ReviewDecision.ACCEPT else "concurrent rejection",
            )
            outcomes.append("ok")
        except ReviewConflict:
            outcomes.append("conflict")

    threads = [
        threading.Thread(target=decide, args=(ReviewDecision.ACCEPT,)),
        threading.Thread(target=decide, args=(ReviewDecision.REJECT,)),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert sorted(outcomes) == ["conflict", "ok"]
    history = client.get("/api/workspace/history", params={"baseline": "baseline-a"}).json()
    assert len([event for event in history["events"] if event["event"] == "decision_recorded"]) == 1


class _FailSecondFsync(ReviewJournal):
    def __init__(self, path: Path) -> None:
        self.calls = 0
        super().__init__(path)

    def _fsync(self, fd: int) -> None:
        self.calls += 1
        if self.calls == 2:
            raise OSError("injected fsync failure")
        super()._fsync(fd)


class _FailRollback(_FailSecondFsync):
    def _truncate(self, fd: int, size: int) -> None:
        raise OSError("injected truncate failure")


def _workspace_with_journal(
    client: TestClient, settings: Settings, journal: ReviewJournal
) -> ReviewWorkspace:
    workspace = ReviewWorkspace(client.app.state.store, settings, journal=journal)
    client.app.state.review = workspace
    return workspace


def test_confirmed_rollback_does_not_publish(
    app_client: tuple[TestClient, Settings], tmp_path: Path
) -> None:
    client, settings = app_client
    _workspace_with_journal(client, settings, _FailSecondFsync(settings.review_journal))
    response = client.post(
        "/api/links/LNK-007/review",
        json={"decision": "accept", "reviewer_id": "rv-ana", "baseline": "baseline-a"},
    )
    assert response.status_code == 503
    assert response.json()["code"] == "review-storage-unavailable"
    assert response.json()["durability"] == "not_committed"
    pending = client.get("/api/workspace/proposals").json()["proposals"]
    assert pending[0]["link"]["link_id"] == "LNK-007"
    assert settings.review_journal.read_bytes() == b""

    restarted = TestClient(create_app(settings))
    history = restarted.get("/api/workspace/history", params={"baseline": "baseline-a"}).json()
    assert history["events"] == []


def test_indeterminate_commit_is_reported_and_replayed(
    app_client: tuple[TestClient, Settings],
) -> None:
    client, settings = app_client
    _workspace_with_journal(client, settings, _FailRollback(settings.review_journal))
    response = client.post(
        "/api/links/LNK-007/review",
        json={"decision": "accept", "reviewer_id": "rv-ana", "baseline": "baseline-a"},
    )
    assert response.status_code == 503
    assert response.json()["code"] == "review-storage-unavailable"
    assert response.json()["durability"] == "indeterminate"
    pending = client.get("/api/workspace/proposals").json()["proposals"]
    assert pending[0]["link"]["link_id"] == "LNK-007"

    restarted = TestClient(create_app(settings))
    history = restarted.get("/api/workspace/history", params={"baseline": "baseline-a"}).json()
    assert [(event["event"], event["decision"]) for event in history["events"]] == [
        ("decision_recorded", "accept")
    ]


def test_uncommitted_tail_is_ignored_and_blocks_mutation(
    fixture_settings: Settings, tmp_path: Path
) -> None:
    journal = tmp_path / "review-journal.ndjson"
    journal.write_text('{"event": {}, "record_digest": "sha256:' + "a" * 64 + '"}\n', "utf-8")
    settings = review_settings(fixture_settings, tmp_path, journal=journal)
    client = TestClient(create_app(settings))

    assert client.get("/api/workspace/history").json()["events"] == []
    response = client.post(
        "/api/links/LNK-007/review",
        json={"decision": "accept", "reviewer_id": "rv-ana", "baseline": "baseline-a"},
    )
    assert response.status_code == 503
    assert response.json()["code"] == "review-storage-unavailable"
    assert journal.read_text("utf-8").startswith('{"event": {}')


def test_loopback_origin_boundary(app_client: tuple[TestClient, Settings]) -> None:
    client, settings = app_client
    before = settings.review_journal.read_bytes() if settings.review_journal.exists() else b""

    forbidden = client.post(
        "/api/links/LNK-007/review",
        headers={"Origin": "https://example.invalid"},
        json={"decision": "accept", "reviewer_id": "rv-ana", "baseline": "baseline-a"},
    )
    assert forbidden.status_code == 403
    assert forbidden.json()["code"] == "review-origin-forbidden"
    assert (
        settings.review_journal.read_bytes() if settings.review_journal.exists() else b""
    ) == before

    allowed = client.post(
        "/api/links/LNK-007/review",
        headers={"Origin": "http://127.0.0.1:5173"},
        json={"decision": "accept", "reviewer_id": "rv-ana", "baseline": "baseline-a"},
    )
    assert allowed.status_code == 200
    assert allowed.json()["review_state"] == "accepted"


def test_journal_must_be_outside_the_fixture(fixture_settings: Settings, tmp_path: Path) -> None:
    with pytest.raises(SettingsError):
        replace(
            fixture_settings,
            review_operator="rv-ana",
            review_journal_path=fixture_settings.fixtures_dir / "journal.ndjson",
        )
    with pytest.raises(SettingsError):
        replace(
            fixture_settings,
            review_operator="rv-ana",
            review_journal_path=fixture_settings.fixture_repo / "journal.ndjson",
        )


# -------------------------------------------------------------------- domain


def test_snapshot_digest_excludes_presentation_metadata() -> None:
    from datetime import UTC, datetime

    now = datetime(2026, 11, 14, 12, 0, tzinfo=UTC)
    one = make_proposal_snapshot(
        source_id="SCN-002",
        target_id="CODE-001",
        relation_type="implemented_by",
        baseline="baseline-a",
        baseline_commit="0" * 40,
        source_content_hash="sha256:" + "a" * 64,
        target_content_hash="sha256:" + "b" * 64,
        provider="fake",
        model_version="fake-fixture-v1",
        index_revision="sha256:" + "c" * 64,
        score=0.1,
        rationale="one",
        captured_at=now,
    )
    two = make_proposal_snapshot(
        source_id="SCN-002",
        target_id="CODE-001",
        relation_type="implemented_by",
        baseline="baseline-a",
        baseline_commit="0" * 40,
        source_content_hash="sha256:" + "a" * 64,
        target_content_hash="sha256:" + "b" * 64,
        provider="fake",
        model_version="fake-fixture-v1",
        index_revision="sha256:" + "c" * 64,
        score=0.9,
        rationale="two",
        captured_at=now,
    )
    assert one.snapshot_digest == two.snapshot_digest


def test_proposal_snapshot_rejects_a_tampered_digest() -> None:
    from datetime import UTC, datetime

    from app.domain.review import ProposalSnapshot

    valid = make_proposal_snapshot(
        source_id="SCN-002",
        target_id="CODE-001",
        relation_type="implemented_by",
        baseline="baseline-a",
        baseline_commit="0" * 40,
        source_content_hash="sha256:" + "a" * 64,
        target_content_hash="sha256:" + "b" * 64,
        provider="fake",
        model_version="fake-fixture-v1",
        index_revision="sha256:" + "c" * 64,
        score=None,
        rationale=None,
        captured_at=datetime(2026, 11, 14, tzinfo=UTC),
    )
    with pytest.raises(ValidationError):
        ProposalSnapshot.model_validate(
            {**valid.model_dump(mode="python"), "snapshot_digest": "sha256:" + "d" * 64}
        )


def test_arbitrary_commit_is_a_resolvable_baseline(store, built_fixture: BuiltFixture) -> None:
    source_commit = built_fixture.commit("baseline-a-source")
    assert store.resolve_baseline(source_commit) == source_commit
    assert store.commit_of(source_commit) == source_commit
    assert store.list_artifacts(source_commit)


def test_error_precedence_combines_identity_reason_and_missing_proposal(
    fixture_settings: Settings, tmp_path: Path
) -> None:
    no_operator = TestClient(create_app(review_settings(fixture_settings, tmp_path, operator=None)))
    response = no_operator.post(
        "/api/links/LNK-999/review",
        json={
            "decision": "reject",
            "reviewer_id": "rv-mallory",
            "baseline": "baseline-a",
            "reason": "",
        },
    )
    assert response.status_code == 503
    assert response.json()["code"] == "review-identity-unavailable"

    mismatch = TestClient(create_app(review_settings(fixture_settings, tmp_path)))
    response = mismatch.post(
        "/api/links/LNK-999/review",
        json={
            "decision": "reject",
            "reviewer_id": "rv-mallory",
            "baseline": "baseline-a",
            "reason": "",
        },
    )
    assert response.status_code == 403
    assert response.json()["code"] == "review-identity-mismatch"

    missing = TestClient(create_app(review_settings(fixture_settings, tmp_path)))
    response = missing.post(
        "/api/links/LNK-999/review",
        json={
            "decision": "reject",
            "reviewer_id": "rv-ana",
            "baseline": "baseline-a",
            "reason": "",
        },
    )
    assert response.status_code == 404
    assert response.json()["code"] == "proposal-not-found"

    valid = TestClient(create_app(review_settings(fixture_settings, tmp_path)))
    response = valid.post(
        "/api/links/LNK-007/review",
        json={
            "decision": "reject",
            "reviewer_id": "rv-ana",
            "baseline": "baseline-a",
            "reason": "   ",
        },
    )
    assert response.status_code == 422
    assert response.json()["code"] == "review-reason-required"

    invalid_body = TestClient(create_app(review_settings(fixture_settings, tmp_path)))
    response = invalid_body.post("/api/links/LNK-007/review", json={"reviewer_id": "rv-mallory"})
    assert response.status_code == 403
    assert response.json()["code"] == "review-identity-mismatch"

    no_identity_invalid_body = TestClient(
        create_app(review_settings(fixture_settings, tmp_path, operator=None))
    )
    response = no_identity_invalid_body.post(
        "/api/links/LNK-007/review", json={"decision": "maybe"}
    )
    assert response.status_code == 503
    assert response.json()["code"] == "review-identity-unavailable"


def test_capture_conflicts_are_scoped_to_the_capture_baseline(
    app_client: tuple[TestClient, Settings],
) -> None:
    client, _ = app_client
    first = capture(client)
    second = client.post("/api/link-proposals", json=capture_payload_for(client, "baseline-b"))
    assert second.status_code == 201, second.text
    assert second.json()["link"]["link_id"] != first["link"]["link_id"]
    accept(client, first["link"]["link_id"])
    duplicate_b = client.post("/api/link-proposals", json=capture_payload_for(client, "baseline-b"))
    assert duplicate_b.status_code == 200
    assert duplicate_b.json()["link"]["link_id"] == second.json()["link"]["link_id"]


def test_origin_policy_rejects_testclient_host_and_malformed_origin(
    app_client: tuple[TestClient, Settings],
) -> None:
    client, settings = app_client
    before = settings.review_journal.read_bytes() if settings.review_journal.exists() else b""
    for origin in ("http://testclient", "http://["):
        for path, body in (
            (
                "/api/links/LNK-007/review",
                {
                    "decision": "accept",
                    "reviewer_id": "rv-ana",
                    "baseline": "baseline-a",
                },
            ),
            ("/api/link-proposals", capture_payload(client)),
        ):
            response = client.post(path, headers={"Origin": origin}, json=body)
            assert response.status_code == 403, response.text
            assert response.json()["code"] == "review-origin-forbidden"
    assert (
        settings.review_journal.read_bytes() if settings.review_journal.exists() else b""
    ) == before


def test_snapshot_digest_matches_an_independent_fixed_vector() -> None:
    from datetime import UTC, datetime

    snapshot = make_proposal_snapshot(
        source_id="SCN-002",
        target_id="CODE-001",
        relation_type="implemented_by",
        baseline="baseline-a",
        baseline_commit="0" * 40,
        source_content_hash="sha256:" + "a" * 64,
        target_content_hash="sha256:" + "b" * 64,
        provider="fake",
        model_version="fake-fixture-v1",
        index_revision="sha256:" + "c" * 64,
        score=0.1,
        rationale="one",
        captured_at=datetime(2026, 11, 14, 12, 0, tzinfo=UTC),
    )
    assert snapshot.snapshot_digest == FIXED_SNAPSHOT_DIGEST
    assert snapshot.snapshot_digest == independent_snapshot_digest(
        source_id="SCN-002",
        target_id="CODE-001",
        relation_type="implemented_by",
        baseline="baseline-a",
        baseline_commit="0" * 40,
        source_content_hash="sha256:" + "a" * 64,
        target_content_hash="sha256:" + "b" * 64,
        provider="fake",
        model_version="fake-fixture-v1",
        index_revision="sha256:" + "c" * 64,
    )
    other = make_proposal_snapshot(
        source_id="SCN-002",
        target_id="CODE-001",
        relation_type="implemented_by",
        baseline="baseline-a",
        baseline_commit="0" * 40,
        source_content_hash="sha256:" + "a" * 64,
        target_content_hash="sha256:" + "b" * 64,
        provider="fake",
        model_version="fake-fixture-v1",
        index_revision="sha256:" + "c" * 64,
        score=0.9,
        rationale="different presentation metadata",
        captured_at=datetime(2026, 11, 14, 13, 0, tzinfo=UTC),
    )
    assert other.snapshot_digest == FIXED_SNAPSHOT_DIGEST
