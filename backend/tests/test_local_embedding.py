"""AI-02: the local provider behind the shared discovery contract, offline.

The optional ONNX runtime is exercised by the opt-in live test; these tests use a deterministic
runtime with the same boundary so the default suite never imports onnxruntime.
"""

from __future__ import annotations

import math
import sys
from dataclasses import replace
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.assurance.rules import DeterministicAssuranceEvaluator
from app.discovery.local_embedding import (
    LocalEmbeddingCandidateDiscovery,
    OnnxEmbeddingRuntime,
    validate_local_endpoint,
)
from app.discovery.registry import ProviderRegistry
from app.domain.enums import RelationType
from app.domain.errors import InvalidRequest, RetrievalUnavailable
from app.domain.ports import CandidateDiscovery
from app.ingestion.repository import GitRepository
from app.main import create_app
from app.persistence.ingested import IngestedStore
from app.settings import Settings, SettingsError


class KeywordRuntime:
    model_id = "embeddinggemma-2-text-270m-q8_0"
    weights_digest = "sha256:" + "a" * 64
    runtime_version = "deterministic-keyword-runtime"
    dimension = 3
    max_tokens = 512

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in texts:
            lowered = text.lower()
            vector = [0.0, 0.0, 0.0]
            if "withdraw" in lowered:
                vector[0] += 1.0
            if "transfer" in lowered:
                vector[1] += 1.0
            if "account" in lowered:
                vector[2] += 1.0
            if not any(vector):
                vector[2] = 1.0
            norm = math.sqrt(sum(value * value for value in vector))
            vectors.append([value / norm for value in vector])
        return vectors


class NaNKeywordRuntime(KeywordRuntime):
    def embed(self, texts: list[str]) -> list[list[float]]:
        return [[float("nan"), 0.0, 0.0] for _ in texts]


@pytest.fixture
def provider(store: IngestedStore, fixture_settings: Settings) -> LocalEmbeddingCandidateDiscovery:
    return LocalEmbeddingCandidateDiscovery(
        store,
        GitRepository(fixture_settings.fixture_repo),
        runtime=KeywordRuntime(),
    )


def test_provider_satisfies_the_port_and_has_no_write_surface(
    provider: LocalEmbeddingCandidateDiscovery,
) -> None:
    assert isinstance(provider, CandidateDiscovery)
    assert provider.provider_name == "local-embeddinggemma"
    assert provider.model_version.startswith("embeddinggemma-2-text-270m-q8_0@sha256:")
    public = {name for name in dir(provider) if not name.startswith("_")}
    write_like = {"accept", "approve", "reject", "record", "save", "store", "write", "review"}
    assert public.isdisjoint(write_like)


def test_contract_ranks_and_filters(provider: LocalEmbeddingCandidateDiscovery) -> None:
    candidates = provider.discover("SCN-001")
    assert candidates
    assert all(candidate.source_id == "SCN-001" for candidate in candidates)
    assert [candidate.rank for candidate in candidates] == list(range(1, len(candidates) + 1))
    assert candidates[0].target_id == "CODE-001"
    assert candidates[0].proposed_relation_type is RelationType.IMPLEMENTED_BY
    assert all(candidate.discovery_provider == "local-embeddinggemma" for candidate in candidates)
    assert all(candidate.index_revision == provider.index_revision for candidate in candidates)

    sources = provider.discover("SCN-001", relation_types=[RelationType.IMPLEMENTED_BY])
    assert sources and all(
        item.proposed_relation_type is RelationType.IMPLEMENTED_BY for item in sources
    )
    tests = provider.discover("SCN-001", relation_types=[RelationType.EXERCISED_BY])
    assert tests and all(item.proposed_relation_type is RelationType.EXERCISED_BY for item in tests)
    assert provider.discover("SCN-001", relation_types=[RelationType.VERIFIED_BY]) == []


def test_top_k_and_rank_trimming(provider: LocalEmbeddingCandidateDiscovery) -> None:
    assert [candidate.rank for candidate in provider.discover("SCN-001", top_k=1)] == [1]
    assert provider.discover("SCN-001", top_k=1)[0].target_id == "CODE-001"
    with pytest.raises(ValueError):
        provider.discover("SCN-001", top_k=0)


def test_requirement_discovery_and_source_no_candidates(
    provider: LocalEmbeddingCandidateDiscovery,
) -> None:
    candidates = provider.discover("REQ-001")
    assert candidates
    assert candidates[0].target_id == "SCN-001"
    assert candidates[0].proposed_relation_type is RelationType.VERIFIED_BY
    assert provider.discover("CODE-001") == []


def test_index_binding_tracks_content_and_model(provider: LocalEmbeddingCandidateDiscovery) -> None:
    first = provider.binding_for("baseline-a")
    second = provider.binding_for("baseline-b")
    assert first.startswith("sha256:")
    assert second.startswith("sha256:")
    assert first != second


def test_discovery_does_not_write_links_evidence_or_findings(
    provider: LocalEmbeddingCandidateDiscovery, store: IngestedStore
) -> None:
    evaluator = DeterministicAssuranceEvaluator(store)
    before = (
        store.list_links("baseline-a"),
        store.list_evidence("baseline-a"),
        evaluator.evaluate("baseline-a"),
    )
    provider.discover("SCN-001")
    provider.discover("REQ-001")
    after = (
        store.list_links("baseline-a"),
        store.list_evidence("baseline-a"),
        evaluator.evaluate("baseline-a"),
    )
    assert before == after


def test_malformed_embedding_is_a_typed_failure(
    store: IngestedStore, fixture_settings: Settings
) -> None:
    malformed = LocalEmbeddingCandidateDiscovery(
        store,
        GitRepository(fixture_settings.fixture_repo),
        runtime=NaNKeywordRuntime(),
    )
    with pytest.raises(RetrievalUnavailable):
        malformed.discover("SCN-001")


def test_remote_endpoint_is_refused_before_any_connection(fixture_settings: Settings) -> None:
    settings = replace(
        fixture_settings,
        local_embedding_enabled=True,
        local_embedding_endpoint="http://192.0.2.10:11434",
    )
    registry = ProviderRegistry(settings, IngestedStore.from_settings(fixture_settings))
    with pytest.raises(InvalidRequest):
        registry.get("local-embeddinggemma")
    validate_local_endpoint("http://127.0.0.1:11434")
    validate_local_endpoint(None)


def test_missing_model_directory_is_unavailable(fixture_settings: Settings) -> None:
    settings = replace(
        fixture_settings,
        local_embedding_enabled=True,
        local_embedding_model_dir=None,
    )
    registry = ProviderRegistry(settings, IngestedStore.from_settings(fixture_settings))
    with pytest.raises(RetrievalUnavailable):
        registry.get("local-embeddinggemma")


def test_onnx_runtime_refuses_missing_weights(tmp_path: Path) -> None:
    with pytest.raises(RetrievalUnavailable):
        OnnxEmbeddingRuntime(tmp_path / "missing-model")


def test_empty_discovery_retains_provenance(
    fixture_settings: Settings, tmp_path: Path, store: IngestedStore
) -> None:
    settings = replace(
        fixture_settings,
        local_embedding_enabled=True,
        local_embedding_model_dir=None,
        review_journal_path=tmp_path / "journal.ndjson",
    )
    app = create_app(settings)
    registry = ProviderRegistry(settings, app.state.store)
    registry._cache["local-embeddinggemma"] = LocalEmbeddingCandidateDiscovery(
        store,
        GitRepository(fixture_settings.fixture_repo),
        runtime=KeywordRuntime(),
    )
    app.state.providers = registry
    response = TestClient(app).post(
        "/api/discovery",
        json={
            "artifact_id": "CODE-001",
            "provider": "local-embeddinggemma",
            "baseline": "baseline-a",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["candidates"] == []
    assert body["provider"] == "local-embeddinggemma"
    assert body["model_version"].startswith("embeddinggemma-2-text-270m-q8_0@")
    assert body["index_revision"].startswith("sha256:")


def test_unavailable_provenance_fails_explicitly(
    store: IngestedStore, fixture_settings: Settings
) -> None:
    class NoProvenanceRuntime:
        dimension = 3
        max_tokens = 512
        runtime_version = "no-provenance"

        def embed(self, texts: list[str]) -> list[list[float]]:
            return [[1.0, 0.0, 0.0] for _ in texts]

    with pytest.raises(RetrievalUnavailable):
        LocalEmbeddingCandidateDiscovery(
            store,
            GitRepository(fixture_settings.fixture_repo),
            runtime=NoProvenanceRuntime(),
        )


def test_digest_mismatch_is_unavailable(tmp_path: Path) -> None:
    model_dir = tmp_path / "model"
    (model_dir / "onnx").mkdir(parents=True)
    (model_dir / "onnx" / "model_quantized.onnx").write_bytes(b"graph")
    (model_dir / "onnx" / "model_quantized.onnx_data").write_bytes(b"data")
    (model_dir / "tokenizer.json").write_text("{}", "utf-8")
    with pytest.raises(RetrievalUnavailable):
        OnnxEmbeddingRuntime(
            model_dir,
            expected_weights_digest="sha256:" + "a" * 64,
        )


def test_missing_runtime_package_is_unavailable(tmp_path: Path, monkeypatch) -> None:
    model_dir = tmp_path / "model"
    (model_dir / "onnx").mkdir(parents=True)
    (model_dir / "onnx" / "model_quantized.onnx").write_bytes(b"graph")
    (model_dir / "onnx" / "model_quantized.onnx_data").write_bytes(b"data")
    (model_dir / "tokenizer.json").write_text("{}", "utf-8")
    monkeypatch.setitem(sys.modules, "onnxruntime", None)
    monkeypatch.setitem(sys.modules, "tokenizers", None)
    with pytest.raises(RetrievalUnavailable):
        OnnxEmbeddingRuntime(model_dir)


def test_remote_endpoint_route_is_a_400(fixture_settings: Settings, tmp_path: Path) -> None:
    settings = replace(
        fixture_settings,
        local_embedding_enabled=True,
        local_embedding_endpoint="http://192.0.2.10:11434",
        review_journal_path=tmp_path / "journal.ndjson",
    )
    client = TestClient(create_app(settings))
    response = client.post(
        "/api/discovery",
        json={"artifact_id": "SCN-001", "provider": "local-embeddinggemma"},
    )
    assert response.status_code == 400
    assert response.json()["code"] == "invalid-request"
    assert "no connection was attempted" in response.json()["detail"]


def test_missing_model_route_is_a_503(fixture_settings: Settings, tmp_path: Path) -> None:
    settings = replace(
        fixture_settings,
        local_embedding_enabled=True,
        local_embedding_model_dir=None,
        review_journal_path=tmp_path / "journal.ndjson",
    )
    client = TestClient(create_app(settings))
    response = client.post(
        "/api/discovery",
        json={"artifact_id": "SCN-001", "provider": "local-embeddinggemma"},
    )
    assert response.status_code == 503
    assert response.json()["code"] == "retrieval-unavailable"


def test_default_registry_does_not_include_local(
    fixture_settings: Settings, store: IngestedStore
) -> None:
    assert ProviderRegistry(fixture_settings, store).registered == ["fake"]


def test_invalid_weights_digest_configuration(fixture_settings: Settings) -> None:
    with pytest.raises(SettingsError):
        replace(
            fixture_settings,
            local_embedding_enabled=True,
            local_embedding_weights_digest="not-a-digest",
        )
