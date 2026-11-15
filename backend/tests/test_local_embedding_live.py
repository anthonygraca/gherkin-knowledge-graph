"""AI-02 live evidence: real same-machine EmbeddingGemma 2 inference.

Opt in with ``CTA_LOCAL_EMBEDDING_LIVE_TESTS=1``. The test is skipped by the default offline
suite and never downloads weights. Run it under an OS-level network denial (``unshare -rn``) to
prove the process tree has no non-loopback egress.
"""

from __future__ import annotations

import json
import os
import statistics
import time
from dataclasses import replace
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.assurance.rules import DeterministicAssuranceEvaluator
from app.discovery.registry import ProviderRegistry
from app.domain.enums import RelationType
from app.main import create_app
from app.persistence.ingested import IngestedStore
from app.settings import Settings

DEFAULT_MODEL_DIR = Path.home() / ".local/share/cta/models/embeddinggemma-2-text-270m-onnx"
pytestmark = pytest.mark.skipif(
    os.environ.get("CTA_LOCAL_EMBEDDING_LIVE_TESTS") != "1",
    reason="set CTA_LOCAL_EMBEDDING_LIVE_TESTS=1 to run real local inference",
)


def _rss_kib() -> int | None:
    try:
        for line in Path("/proc/self/status").read_text("utf-8").splitlines():
            if line.startswith("VmRSS:"):
                return int(line.split()[1])
    except OSError:
        return None
    return None


def test_local_embeddinggemma_live_contract(
    fixture_settings: Settings, store: IngestedStore, tmp_path: Path
) -> None:
    model_dir = Path(
        os.environ.get("CTA_LOCAL_EMBEDDING_MODEL_DIR", DEFAULT_MODEL_DIR)
    ).expanduser()
    if not model_dir.is_dir():
        pytest.skip(f"local model directory is absent: {model_dir}")
    settings = replace(
        fixture_settings,
        local_embedding_enabled=True,
        local_embedding_model_dir=model_dir,
    )
    rss_before = _rss_kib()
    evaluator = DeterministicAssuranceEvaluator(store)
    before = (
        store.list_links("baseline-a"),
        store.list_evidence("baseline-a"),
        evaluator.evaluate("baseline-a"),
    )
    started = time.perf_counter()
    provider = ProviderRegistry(settings, store).get("local-embeddinggemma")
    load_seconds = time.perf_counter() - started

    queries = ["SCN-001", "REQ-001", "SCN-002"]
    latencies: list[float] = []
    result_sets: dict[str, list[str]] = {}
    index_started = time.perf_counter()
    binding = provider.binding_for("baseline-a")
    index_seconds = time.perf_counter() - index_started
    for artifact_id in queries:
        query_started = time.perf_counter()
        candidates = provider.discover(artifact_id, top_k=10, baseline="baseline-a")
        latencies.append((time.perf_counter() - query_started) * 1_000.0)
        result_sets[artifact_id] = [candidate.target_id for candidate in candidates]
        assert all(candidate.source_id == artifact_id for candidate in candidates)
        assert [candidate.rank for candidate in candidates] == list(range(1, len(candidates) + 1))
        assert all(
            candidate.discovery_provider == "local-embeddinggemma" for candidate in candidates
        )
        assert all(candidate.model_version for candidate in candidates)
        assert all(candidate.index_revision == binding for candidate in candidates)
        assert all(
            not hasattr(candidate, "link_id") and not hasattr(candidate, "review_state")
            for candidate in candidates
        )

    scenario_candidates = provider.discover("SCN-001", top_k=10, baseline="baseline-a")
    assert "CODE-001" in {candidate.target_id for candidate in scenario_candidates}
    assert "TEST-001" in {candidate.target_id for candidate in scenario_candidates}
    assert all(
        candidate.proposed_relation_type is not RelationType.VERIFIED_BY
        for candidate in scenario_candidates
    )
    trimmed = provider.discover("SCN-001", top_k=1, baseline="baseline-a")
    assert len(trimmed) == 1
    assert trimmed[0].rank == 1
    implemented = provider.discover(
        "SCN-001", relation_types=[RelationType.IMPLEMENTED_BY], baseline="baseline-a"
    )
    exercised = provider.discover(
        "SCN-001", relation_types=[RelationType.EXERCISED_BY], baseline="baseline-a"
    )
    assert implemented and all(
        candidate.proposed_relation_type is RelationType.IMPLEMENTED_BY for candidate in implemented
    )
    assert exercised and all(
        candidate.proposed_relation_type is RelationType.EXERCISED_BY for candidate in exercised
    )
    incompatible = provider.discover(
        "SCN-001", relation_types=[RelationType.VERIFIED_BY], baseline="baseline-a"
    )
    assert incompatible == []
    requirements = provider.discover("REQ-001", baseline="baseline-a")
    assert requirements and all(
        candidate.proposed_relation_type is RelationType.VERIFIED_BY for candidate in requirements
    )
    assert provider.discover("CODE-001", baseline="baseline-a") == []

    api_settings = replace(settings, review_journal_path=tmp_path / "journal.ndjson")
    app = create_app(api_settings)
    registry = ProviderRegistry(api_settings, app.state.store)
    registry._cache["local-embeddinggemma"] = provider
    app.state.providers = registry
    empty = TestClient(app).post(
        "/api/discovery",
        json={
            "artifact_id": "CODE-001",
            "provider": "local-embeddinggemma",
            "baseline": "baseline-a",
        },
    )
    assert empty.status_code == 200, empty.text
    empty_body = empty.json()
    assert empty_body["candidates"] == []
    assert empty_body["provider"] == "local-embeddinggemma"
    assert empty_body["model_version"].startswith("embeddinggemma-2-text-270m-q8_0@sha256:")
    assert empty_body["index_revision"] == binding

    after = (
        store.list_links("baseline-a"),
        store.list_evidence("baseline-a"),
        evaluator.evaluate("baseline-a"),
    )
    assert before == after
    rss_after = _rss_kib()
    import socket

    try:
        socket.create_connection(("192.0.2.1", 9), timeout=1)
        external_egress = True
    except OSError:
        external_egress = False

    record = {
        "model_dir": str(model_dir),
        "model_version": provider.model_version,
        "index_revision": binding,
        "runtime": provider.runtime.runtime_version,
        "weights_digest": provider.runtime.weights_digest,
        "manifest_weights_digest": os.environ.get("CTA_LOCAL_EMBEDDING_WEIGHTS_DIGEST"),
        "formatting": provider.formatting_version,
        "load_seconds": round(load_seconds, 3),
        "index_seconds": round(index_seconds, 3),
        "query_latency_ms": [round(value, 1) for value in latencies],
        "median_query_latency_ms": round(statistics.median(latencies), 1),
        "rss_before_kib": rss_before,
        "rss_after_kib": rss_after,
        "rss_delta_kib": (rss_after - rss_before) if rss_before and rss_after else None,
        "results": result_sets,
        "external_egress": external_egress,
        "egress_denied_env": os.environ.get("CTA_EGRESS_DENIED") == "1",
        "network_namespace": os.readlink("/proc/self/ns/net"),
        "git": store.commit_of("baseline-a"),
    }
    print("LIVE_MEASUREMENT " + json.dumps(record, sort_keys=True))
