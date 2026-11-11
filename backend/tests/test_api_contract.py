"""AC-2.1 … AC-2.5: the mock API serves schema-valid fixture data and is honest about stubs."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.domain.api import (
    DiscoveryResponse,
    FindingsResponse,
    HealthResponse,
    ProblemDetails,
    ThreadResponse,
)
from app.domain.models import Artifact, finding_fingerprint
from app.domain.oracle import BaselinesManifest, ExpectedFindingsFile, FixtureSnapshot
from app.persistence.fixtures import load_model
from app.settings import Settings
from app.version import SCHEMA_VERSION

BASELINES = ("baseline-a", "baseline-b")

CONTRACTED_PATHS = {
    "/health",
    "/api/artifacts/{artifact_id}",
    "/api/threads/{artifact_id}",
    "/api/findings",
    "/api/discovery",
    "/api/ingestion/run",
    "/api/links/{link_id}/review",
    "/api/assurance/evaluate",
}


# ------------------------------------------------------------------------------------- health


def test_health_reports_contract_and_fixture_status(
    client: TestClient, snapshot: FixtureSnapshot, committed_manifest: BaselinesManifest
) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = HealthResponse.model_validate(response.json())
    assert body.status == "ok"
    assert body.schema_version == SCHEMA_VERSION
    assert body.fixture == snapshot.fixture
    assert body.baselines == [entry.baseline for entry in snapshot.baselines]
    assert body.baseline_commits == committed_manifest.tags
    assert body.discovery_providers == ["fake"]


# ---------------------------------------------------------------------------------- artifacts


def test_openapi_documents_every_contracted_endpoint(client: TestClient) -> None:
    document = client.get("/openapi.json").json()
    assert set(document["paths"]) == CONTRACTED_PATHS


def test_artifact_is_addressable_by_tag_or_commit(
    client: TestClient, committed_manifest: BaselinesManifest
) -> None:
    by_tag = client.get("/api/artifacts/REQ-001", params={"baseline": "baseline-a"})
    by_commit = client.get(
        "/api/artifacts/REQ-001", params={"baseline": committed_manifest.tags["baseline-a"]}
    )
    assert by_tag.status_code == by_commit.status_code == 200
    assert by_tag.json() == by_commit.json()

    artifact = Artifact.model_validate(by_tag.json())
    assert artifact.artifact_id == "REQ-001"
    assert artifact.artifact_type.value == "requirement"
    assert artifact.revision == committed_manifest.tags["baseline-a"]
    assert artifact.metadata["status"] == "active"


def test_artifact_revision_tracks_the_change(client: TestClient) -> None:
    at_a = client.get("/api/artifacts/CODE-001", params={"baseline": "baseline-a"}).json()
    at_b = client.get("/api/artifacts/CODE-001", params={"baseline": "baseline-b"}).json()
    assert at_a["content_hash"] != at_b["content_hash"]
    assert at_a["revision"] != at_b["revision"]


def test_unknown_artifact_returns_a_problem_document(client: TestClient) -> None:
    response = client.get("/api/artifacts/REQ-999")
    assert response.status_code == 404
    problem = ProblemDetails.model_validate(response.json())
    assert problem.type == "urn:cta:error:artifact-not-found"
    assert problem.code == "artifact-not-found"
    assert problem.instance == "/api/artifacts/REQ-999"
    assert "REQ-999" in problem.detail


def test_malformed_artifact_id_is_a_validation_problem(client: TestClient) -> None:
    response = client.get("/api/artifacts/not-an-id")
    assert response.status_code == 422
    assert response.json()["code"] == "request-validation"


def test_unknown_baseline_returns_a_problem_document(client: TestClient) -> None:
    response = client.get("/api/findings", params={"baseline": "baseline-z"})
    assert response.status_code == 404
    assert response.json()["code"] == "baseline-not-found"


# ------------------------------------------------------------------------------------ threads


def test_thread_keeps_proposals_out_of_accepted_links(client: TestClient) -> None:
    body = ThreadResponse.model_validate(
        client.get("/api/threads/REQ-002", params={"baseline": "baseline-a"}).json()
    )
    assert [artifact.artifact_id for artifact in body.artifacts] == ["REQ-002"]
    assert body.accepted_links == []
    assert [link.link_id for link in body.proposed_links] == ["LNK-007"]
    assert body.proposed_links[0].review_state.value == "proposed"
    assert body.evidence == []


def test_thread_carries_the_accepted_chain_with_evidence(client: TestClient) -> None:
    body = ThreadResponse.model_validate(
        client.get("/api/threads/REQ-001", params={"baseline": "baseline-b"}).json()
    )
    assert [artifact.artifact_id for artifact in body.artifacts] == [
        "CODE-001",
        "REQ-001",
        "SCN-001",
        "TEST-001",
    ]
    assert [link.link_id for link in body.accepted_links] == ["LNK-001", "LNK-002", "LNK-003"]
    assert [link.relation_type.value for link in body.accepted_links] == [
        "verified_by",
        "implemented_by",
        "exercised_by",
    ]
    assert [item.evidence_id for item in body.evidence] == ["EV-001"]
    assert body.baseline == "baseline-b"
    assert body.schema_version == SCHEMA_VERSION


def test_thread_reports_missing_roots_clearly(client: TestClient) -> None:
    unknown = client.get("/api/threads/REQ-999")
    assert unknown.status_code == 404
    assert unknown.json()["code"] == "artifact-not-found"

    # CODE-001 exists, but M0 materializes requirement roots only; say so instead of 500
    not_materialized = client.get("/api/threads/CODE-001")
    assert not_materialized.status_code == 404
    assert not_materialized.json()["code"] == "thread-not-found"


# ----------------------------------------------------------------------------------- findings


def test_default_baseline_is_the_latest(client: TestClient, snapshot: FixtureSnapshot) -> None:
    assert client.get("/api/findings").json()["baseline"] == snapshot.baselines[-1].baseline


@pytest.mark.parametrize("baseline", BASELINES)
def test_findings_match_the_oracle_exactly(
    client: TestClient, fixture_settings: Settings, baseline: str
) -> None:
    oracle = load_model(fixture_settings.expected_dir / f"{baseline}.json", ExpectedFindingsFile)
    body = FindingsResponse.model_validate(
        client.get("/api/findings", params={"baseline": baseline}).json()
    )

    actual = {
        (
            item.rule_id.value,
            item.finding_type.value,
            tuple(item.artifact_ids),
            tuple(item.evidence_ids),
        ): item
        for item in body.findings
    }
    expected = {
        (
            item.rule_id.value,
            item.finding_type.value,
            tuple(item.artifact_ids),
            tuple(item.evidence_ids),
        ): item
        for item in oracle.findings
    }
    assert set(actual) == set(expected)

    for key, expected_item in expected.items():
        item = actual[key]
        assert item.severity is expected_item.severity
        assert item.status is expected_item.status
        assert item.finding_id == finding_fingerprint(
            expected_item.rule_id, expected_item.finding_type, expected_item.artifact_ids
        )

    for artifact_id in oracle.healthy_artifact_ids:
        assert not [item for item in body.findings if artifact_id in item.artifact_ids]


@pytest.mark.parametrize("baseline", BASELINES)
def test_findings_are_pinned_to_the_evaluated_commit(
    client: TestClient, committed_manifest: BaselinesManifest, baseline: str
) -> None:
    body = client.get("/api/findings", params={"baseline": baseline}).json()
    assert body["baseline"] == baseline
    commit = committed_manifest.tags[baseline]
    assert body["findings"]
    assert {item["evaluated_baseline"] for item in body["findings"]} == {commit}
    for item in body["findings"]:
        assert set(item["artifact_revisions"].values()) == {commit}


def test_findings_by_sha_and_by_tag_are_identical(
    client: TestClient, committed_manifest: BaselinesManifest
) -> None:
    by_tag = client.get("/api/findings", params={"baseline": "baseline-b"}).json()
    by_commit = client.get(
        "/api/findings", params={"baseline": committed_manifest.tags["baseline-b"]}
    ).json()
    assert by_tag == by_commit


# ---------------------------------------------------------------------------------- discovery


def test_discovery_returns_a_proposal_and_never_an_accepted_link(
    client: TestClient, snapshot: FixtureSnapshot
) -> None:
    response = client.post("/api/discovery", json={"artifact_id": "SCN-001"})
    assert response.status_code == 200
    body = DiscoveryResponse.model_validate(response.json())
    assert body.provider == "fake"
    assert body.model_version == "fake-fixture-v1"
    assert body.index_revision.startswith("sha256:")
    assert body.schema_version == SCHEMA_VERSION

    top = body.candidates[0]
    assert (top.target_id, top.proposed_relation_type.value, top.rank) == (
        "CODE-001",
        "implemented_by",
        1,
    )
    assert top.index_revision == body.index_revision
    assert top.discovery_provider == body.provider
    assert {"link_id", "review_state"}.isdisjoint(response.json()["candidates"][0])

    for entry in snapshot.baselines:
        accepted = [link.link_id for link in entry.accepted_links if link.source_id == "SCN-001"]
        assert accepted == ["LNK-002", "LNK-003"]


def test_discovery_rejects_unknown_provider_and_artifact(client: TestClient) -> None:
    unknown_provider = client.post(
        "/api/discovery", json={"artifact_id": "SCN-001", "provider": "local-embeddinggemma"}
    )
    assert unknown_provider.status_code == 400
    assert unknown_provider.json()["code"] == "provider-not-registered"
    assert "fake" in unknown_provider.json()["detail"]

    unknown_artifact = client.post("/api/discovery", json={"artifact_id": "REQ-999"})
    assert unknown_artifact.status_code == 404
    assert unknown_artifact.json()["code"] == "artifact-not-found"


def test_discovery_top_k_and_relation_filter(client: TestClient) -> None:
    body = client.post(
        "/api/discovery",
        json={"artifact_id": "SCN-001", "top_k": 1, "relation_types": ["implemented_by"]},
    ).json()
    assert [candidate["target_id"] for candidate in body["candidates"]] == ["CODE-001"]
    assert [candidate["rank"] for candidate in body["candidates"]] == [1]


def test_discovery_validates_its_payload(client: TestClient) -> None:
    assert (
        client.post("/api/discovery", json={"artifact_id": "SCN-001", "top_k": 0}).status_code
        == 422
    )
    assert client.post("/api/discovery", json={}).status_code == 422


# ------------------------------------------------------------------- contract-only endpoints


@pytest.mark.parametrize(
    ("path", "payload", "story"),
    [
        ("/api/ingestion/run", {"repository": "banking-demo"}, "B-PR1"),
        ("/api/links/LNK-007/review", {"decision": "accept", "reviewer_id": "rv-ana"}, "AS-06"),
        ("/api/assurance/evaluate", {"baseline": "baseline-a"}, "AS-01"),
    ],
)
def test_contract_only_endpoints_are_honest(
    client: TestClient, path: str, payload: dict[str, object], story: str
) -> None:
    response = client.post(path, json=payload)
    assert response.status_code == 501
    problem = ProblemDetails.model_validate(response.json())
    assert problem.type == "urn:cta:error:not-implemented"
    assert problem.code == "not-implemented"
    assert problem.story is not None and story in problem.story
    assert problem.milestone


def test_contract_only_endpoints_still_validate_their_payloads(client: TestClient) -> None:
    assert client.post("/api/ingestion/run", json={}).status_code == 422
    assert (
        client.post(
            "/api/links/LNK-001/review", json={"decision": "maybe", "reviewer_id": "x"}
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/links/LNK-001/review", json={"decision": "accept", "reviewer_id": ""}
        ).status_code
        == 422
    )
    assert client.post("/api/assurance/evaluate", json={"baseline": ""}).status_code == 422


def test_unknown_path_returns_a_problem_document(client: TestClient) -> None:
    response = client.get("/api/nope")
    assert response.status_code == 404
    assert response.json()["code"] == "http-404"
