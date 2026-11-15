"""AI-03: content-hash planning, manifests, snapshot publication, and combination."""

from __future__ import annotations

import json
import threading
import time
from dataclasses import replace
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from tests.conftest import FIXTURE_DIR

from app.domain.enums import RelationType
from app.domain.errors import (
    MixedIndexContext,
    RetrievalSnapshotNotFound,
    RetrievalUnavailable,
)
from app.domain.models import TraceCandidate
from app.domain.retrieval_lifecycle import (
    CombineRequest,
    IndexRefreshObservation,
    ManifestListResponse,
    RetrievalConfig,
    SnapshotBoundBatch,
)
from app.ingestion.repository import GitRepository
from app.main import create_app
from app.persistence.ingested import IngestedStore
from app.retrieval.lifecycle import RetrievalLifecycle
from app.settings import Settings, SettingsError
from app.version import SCHEMA_VERSION


class NoCounterAdapter:
    """A deterministic adapter that cannot observe an embedding count."""

    def refresh(self, *, baseline, commit, plan, config):
        return IndexRefreshObservation(
            backend="deterministic",
            backend_binding="backend:test",
            items_embedded=None,
            items_embedded_availability="not_available",
            detail="backend exposes no embedding counter",
        )


class FailingAdapter:
    def refresh(self, *, baseline, commit, plan, config):
        raise TimeoutError("deterministic index adapter timed out")


class CountingAdapter:
    def refresh(self, *, baseline, commit, plan, config):
        return IndexRefreshObservation(
            backend="deterministic",
            backend_binding="backend:test",
            items_embedded=len(plan.changed) + len(plan.added),
            items_embedded_availability="measured",
            detail="test counter",
        )


def lifecycle(store: IngestedStore, settings: Settings, tmp_path: Path) -> RetrievalLifecycle:
    return RetrievalLifecycle(
        store,
        GitRepository(settings.fixture_repo),
        tmp_path / "retrieval-snapshots",
        repository_name="banking-demo",
    )


def config(weights: str = "sha256:" + "a" * 64) -> RetrievalConfig:
    return RetrievalConfig(
        provider="cocoindex",
        model_id="embeddinggemma-2-text-270m-q8_0",
        model_version="embeddinggemma-2-text-270m-q8_0@sha256:" + "b" * 12,
        weights_digest=weights,
        runtime="cocoindex 0.2.43",
        formatting_version="ai03-test-v1",
    )


def test_plan_matches_the_hand_labeled_change_set(
    store: IngestedStore, fixture_settings: Settings, tmp_path: Path
) -> None:
    service = lifecycle(store, fixture_settings, tmp_path)
    plan = service.plan("baseline-b", "baseline-a")
    assert plan.changed == ["CODE-001", "TEST-002"]
    assert plan.unchanged == ["CODE-002", "TEST-001"]
    assert plan.added == []
    assert plan.removed == []
    assert {artifact.artifact_id for artifact in plan.changed_artifacts} == {
        "CODE-001",
        "TEST-002",
    }
    assert {artifact.artifact_id for artifact in plan.unchanged_artifacts} == {
        "CODE-002",
        "TEST-001",
    }


def test_refresh_publishes_manifest_with_honest_counts(
    store: IngestedStore, fixture_settings: Settings, tmp_path: Path
) -> None:
    service = lifecycle(store, fixture_settings, tmp_path)
    first = service.refresh("baseline-a", config=config())
    assert first.schema_version == SCHEMA_VERSION
    assert first.config_digest.startswith("sha256:")
    assert first.corpus_cache_key.startswith("sha256:")
    assert first.snapshot_binding.startswith("snapshot:sha256:")
    assert first.items_embedded is None
    assert first.items_embedded_availability == "not_available"
    assert first.elapsed_ms >= 0
    assert {artifact.artifact_id for artifact in first.artifacts} == {
        "CODE-001",
        "CODE-002",
        "TEST-001",
        "TEST-002",
    }

    second = service.refresh(
        "baseline-b",
        previous_baseline="baseline-a",
        config=config(),
        adapter=NoCounterAdapter(),
    )
    assert second.changed == ["CODE-001", "TEST-002"]
    assert second.unchanged == ["CODE-002", "TEST-001"]
    assert second.snapshot_binding != first.snapshot_binding
    assert second.previous_snapshot_binding == first.snapshot_binding
    assert second.items_embedded is None
    assert second.items_embedded_availability == "not_available"
    assert second.backend_observation is not None
    assert second.backend_observation.items_embedded is None
    assert service.manifest_for("baseline-a").snapshot_binding == first.snapshot_binding
    assert service.manifest_for("baseline-b").snapshot_binding == second.snapshot_binding


def test_measured_counts_are_marked_measured(
    store: IngestedStore, fixture_settings: Settings, tmp_path: Path
) -> None:
    service = lifecycle(store, fixture_settings, tmp_path)
    manifest = service.refresh(
        "baseline-a",
        config=config(),
        adapter=CountingAdapter(),
    )
    assert manifest.items_embedded == 4
    assert manifest.items_embedded_availability == "measured"


def test_evidence_only_commit_reuses_content(fixture_settings: Settings, tmp_path: Path) -> None:
    import fixturectl

    repo = tmp_path / "repo"
    fixturectl.build_repo(FIXTURE_DIR, repo)
    fixturectl.git(["checkout", "--quiet", "baseline-a"], cwd=repo)
    fixturectl.git(["config", "user.name", "Test"], cwd=repo)
    fixturectl.git(["config", "user.email", "test@example.invalid"], cwd=repo)
    fixturectl.git(["commit", "--quiet", "--allow-empty", "-m", "evidence only"], cwd=repo)
    evidence_only = fixturectl.git(["rev-parse", "HEAD"], cwd=repo).strip()
    settings = replace(
        fixture_settings,
        fixture_repo_path=repo,
        retrieval_snapshot_dir=tmp_path / "snapshots",
    )
    store = IngestedStore.from_settings(settings)
    service = lifecycle(store, settings, tmp_path)
    first = service.refresh("baseline-a", config=config())
    second = service.refresh(
        evidence_only,
        previous_baseline="baseline-a",
        config=config(),
    )
    assert second.reused is True
    assert second.corpus_cache_key == first.corpus_cache_key
    assert second.config_digest == first.config_digest
    assert second.snapshot_binding != first.snapshot_binding
    assert second.changed == []
    assert second.added == []
    assert second.removed == []
    assert second.unchanged == ["CODE-001", "CODE-002", "TEST-001", "TEST-002"]
    assert second.items_embedded is None
    assert second.items_embedded_availability == "not_available"
    assert second.previous_snapshot_binding == first.snapshot_binding

    from app.assurance.rules import DeterministicAssuranceEvaluator

    evaluator = DeterministicAssuranceEvaluator(store)
    before = evaluator.evaluate("baseline-a")
    after = evaluator.evaluate(evidence_only)
    assert [
        (finding.finding_id, finding.finding_type, finding.artifact_ids) for finding in before
    ] == [(finding.finding_id, finding.finding_type, finding.artifact_ids) for finding in after]
    assert not any(finding.finding_type.value == "verification_failed" for finding in after)


def test_model_change_invalidates_cache_and_preserves_old_manifest(
    store: IngestedStore, fixture_settings: Settings, tmp_path: Path
) -> None:
    service = lifecycle(store, fixture_settings, tmp_path)
    old = service.refresh("baseline-a", config=config("sha256:" + "a" * 64))
    new = service.refresh(
        "baseline-a",
        previous_baseline="baseline-a",
        config=config("sha256:" + "b" * 64),
    )
    assert old.corpus_cache_key != new.corpus_cache_key
    assert old.config_digest != new.config_digest
    assert old.snapshot_binding != new.snapshot_binding
    assert service.get(old.snapshot_binding) == old
    assert service.manifest_for("baseline-a").snapshot_binding == new.snapshot_binding


def test_failed_refresh_leaves_the_previous_snapshot_usable(
    store: IngestedStore, fixture_settings: Settings, tmp_path: Path
) -> None:
    service = lifecycle(store, fixture_settings, tmp_path)
    first = service.refresh("baseline-a", config=config())
    with pytest.raises(RetrievalUnavailable):
        service.refresh(
            "baseline-b",
            previous_baseline="baseline-a",
            config=config(),
            adapter=FailingAdapter(),
        )
    assert service.manifest_for("baseline-a").snapshot_binding == first.snapshot_binding
    with pytest.raises(RetrievalSnapshotNotFound):
        service.manifest_for("baseline-b")
    assert not (tmp_path / "retrieval-snapshots" / "baselines" / "baseline-b.json").exists()


def test_mixed_context_cannot_form_one_ranked_list(
    store: IngestedStore, fixture_settings: Settings, tmp_path: Path
) -> None:
    service = lifecycle(store, fixture_settings, tmp_path)

    def candidate(target: str, index: str, score: float) -> TraceCandidate:
        return TraceCandidate(
            source_id="SCN-001",
            target_id=target,
            proposed_relation_type=RelationType.IMPLEMENTED_BY,
            rank=1,
            score=score,
            discovery_provider="fake",
            model_version="fake-fixture-v1",
            index_revision=index,
        )

    request = CombineRequest(
        snapshot_binding="snapshot:sha256:aaa",
        batches=[
            SnapshotBoundBatch(
                snapshot_binding="snapshot:sha256:aaa",
                provider="fake",
                provider_index_revision="sha256:provider-a",
                model_version="fake-fixture-v1",
                candidates=[candidate("CODE-001", "snapshot:sha256:aaa", 0.9)],
            ),
            SnapshotBoundBatch(
                snapshot_binding="snapshot:sha256:bbb",
                provider="fake",
                provider_index_revision="sha256:provider-b",
                model_version="fake-fixture-v1",
                candidates=[candidate("CODE-002", "snapshot:sha256:bbb", 0.8)],
            ),
        ],
    )
    with pytest.raises(MixedIndexContext):
        service.combine(request)

    compatible = CombineRequest(
        snapshot_binding="snapshot:sha256:aaa",
        batches=[
            SnapshotBoundBatch(
                snapshot_binding="snapshot:sha256:aaa",
                provider="fake",
                provider_index_revision="sha256:provider-a",
                model_version="fake-fixture-v1",
                candidates=[candidate("CODE-002", "snapshot:sha256:aaa", 0.4)],
            ),
            SnapshotBoundBatch(
                snapshot_binding="snapshot:sha256:aaa",
                provider="fake",
                provider_index_revision="sha256:provider-a",
                model_version="fake-fixture-v1",
                candidates=[candidate("CODE-001", "snapshot:sha256:aaa", 0.9)],
            ),
        ],
    )
    combined = service.combine(compatible)
    assert [item.target_id for item in combined.candidates] == ["CODE-001", "CODE-002"]
    assert [item.rank for item in combined.candidates] == [1, 2]
    assert combined.provenance[0].provider_index_revision == "sha256:provider-a"


def test_bind_preserves_provider_provenance(
    store: IngestedStore, fixture_settings: Settings, tmp_path: Path
) -> None:
    from app.discovery.fake import FakeCandidateDiscovery

    service = lifecycle(store, fixture_settings, tmp_path)
    fake_config = RetrievalConfig(
        provider="fake",
        model_id="fake-fixture-v1",
        model_version="fake-fixture-v1",
        weights_digest="not_available",
        runtime="fixture",
        formatting_version="ai03-test-v1",
    )
    manifest = service.refresh("baseline-a", config=fake_config)
    provider = FakeCandidateDiscovery.from_fixture(fixture_settings.candidate_index_path)
    batch = service.bind(manifest, provider, "SCN-001", top_k=2)
    assert batch.snapshot_binding == manifest.snapshot_binding
    assert batch.provider_index_revision == provider.index_revision
    assert all(
        candidate.index_revision == manifest.snapshot_binding for candidate in batch.candidates
    )
    assert [candidate.target_id for candidate in batch.candidates] == ["CODE-001", "TEST-001"]


def test_api_refresh_read_and_mixed_combination(fixture_settings: Settings, tmp_path: Path) -> None:
    settings = replace(
        fixture_settings,
        retrieval_snapshot_dir=tmp_path / "snapshots",
        review_journal_path=tmp_path / "journal.ndjson",
    )
    client = TestClient(create_app(settings))
    refreshed = client.post("/api/retrieval/refresh", json={"baseline": "baseline-a"})
    assert refreshed.status_code == 200, refreshed.text
    manifest = refreshed.json()
    assert manifest["snapshot_binding"].startswith("snapshot:sha256:")
    assert client.get("/api/retrieval/manifests").status_code == 200
    assert (
        client.get("/api/retrieval/manifests/baseline-a").json()["snapshot_binding"]
        == manifest["snapshot_binding"]
    )
    assert client.get("/api/retrieval/manifests/baseline-b").status_code == 404
    mixed = client.post(
        "/api/retrieval/combine",
        json={
            "snapshot_binding": "snapshot:sha256:aaa",
            "batches": [
                {
                    "snapshot_binding": "snapshot:sha256:bbb",
                    "provider": "fake",
                    "provider_index_revision": "sha256:provider-b",
                    "model_version": "fake-fixture-v1",
                    "candidates": [
                        {
                            "source_id": "SCN-001",
                            "target_id": "CODE-001",
                            "proposed_relation_type": "implemented_by",
                            "rank": 1,
                            "score": 0.9,
                            "discovery_provider": "fake",
                            "model_version": "fake-fixture-v1",
                            "index_revision": "snapshot:sha256:bbb",
                        }
                    ],
                }
            ],
        },
    )
    assert mixed.status_code == 409
    assert mixed.json()["code"] == "mixed-index-context"


def test_snapshot_directory_must_be_outside_the_fixture(fixture_settings: Settings) -> None:
    with pytest.raises(SettingsError):
        replace(
            fixture_settings,
            retrieval_snapshot_dir=fixture_settings.fixtures_dir / "snapshots",
        )
    with pytest.raises(SettingsError):
        replace(
            fixture_settings,
            retrieval_snapshot_dir=fixture_settings.fixture_repo / "snapshots",
        )


def test_corrupt_manifest_is_not_served(
    store: IngestedStore, fixture_settings: Settings, tmp_path: Path
) -> None:
    import json

    service = lifecycle(store, fixture_settings, tmp_path)
    manifest = service.refresh("baseline-a", config=config())
    path = next((tmp_path / "retrieval-snapshots" / "snapshots").glob("*.json"))
    payload = json.loads(path.read_text("utf-8"))
    payload["artifacts"][0]["content_hash"] = "sha256:" + "f" * 64
    path.write_text(json.dumps(payload), "utf-8")
    with pytest.raises(RetrievalSnapshotNotFound):
        service.get(manifest.snapshot_binding)
    with pytest.raises(RetrievalSnapshotNotFound):
        service.manifest_for("baseline-a")
    with pytest.raises(RetrievalSnapshotNotFound):
        service.refresh("baseline-a", config=config())

    payload["artifacts"][0]["content_hash"] = manifest.artifacts[0].content_hash
    payload["config"]["weights_digest"] = "sha256:" + "d" * 64
    path.write_text(json.dumps(payload), "utf-8")
    with pytest.raises(RetrievalSnapshotNotFound):
        service.get(manifest.snapshot_binding)


def test_pointer_failure_rolls_back_the_unpublished_snapshot(
    store: IngestedStore,
    fixture_settings: Settings,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import app.retrieval.lifecycle as lifecycle_module

    service = lifecycle(store, fixture_settings, tmp_path)
    first = service.refresh("baseline-a", config=config())
    original = lifecycle_module._atomic_write

    def failing_pointer(path: Path, content: str) -> None:
        if path.parent.name == "baselines" and path.name == "baseline-b.json":
            raise OSError("injected pointer publication failure")
        original(path, content)

    monkeypatch.setattr(lifecycle_module, "_atomic_write", failing_pointer)
    with pytest.raises(RetrievalUnavailable):
        service.refresh("baseline-b", previous_baseline="baseline-a", config=config())
    with pytest.raises(RetrievalSnapshotNotFound):
        service.manifest_for("baseline-b")
    snapshot_files = sorted(
        path.name for path in (tmp_path / "retrieval-snapshots" / "snapshots").glob("*.json")
    )
    assert snapshot_files == [f"{first.snapshot_binding.replace(':', '-')}.json"]

    monkeypatch.setattr(lifecycle_module, "_atomic_write", original)
    retried = service.refresh("baseline-b", previous_baseline="baseline-a", config=config())
    assert retried.baseline == "baseline-b"


def test_cross_baseline_pointer_is_rejected(
    store: IngestedStore, fixture_settings: Settings, tmp_path: Path
) -> None:
    import json

    service = lifecycle(store, fixture_settings, tmp_path)
    manifest = service.refresh("baseline-a", config=config())
    pointer = tmp_path / "retrieval-snapshots" / "baselines" / "baseline-b.json"
    pointer.write_text(
        json.dumps(
            {
                "snapshot_binding": manifest.snapshot_binding,
                "config_digest": manifest.config_digest,
            }
        ),
        "utf-8",
    )
    with pytest.raises(RetrievalSnapshotNotFound):
        service.manifest_for("baseline-b")


def test_elapsed_includes_key_construction(
    store: IngestedStore, fixture_settings: Settings, tmp_path: Path
) -> None:
    ticks = iter([0.0, 1.0])
    service = RetrievalLifecycle(
        store,
        GitRepository(fixture_settings.fixture_repo),
        tmp_path / "retrieval-snapshots",
        repository_name="banking-demo",
        clock=lambda: next(ticks),
    )
    manifest = service.refresh("baseline-a", config=config())
    assert manifest.elapsed_ms == 1_000.0


def test_repository_and_mislabeled_baseline_are_not_served(
    store: IngestedStore, fixture_settings: Settings, tmp_path: Path
) -> None:
    service = lifecycle(store, fixture_settings, tmp_path)
    manifest = service.refresh("baseline-a", config=config())
    path = next((tmp_path / "retrieval-snapshots" / "snapshots").glob("snapshot-*.json"))
    payload = json.loads(path.read_text("utf-8"))

    payload["repository"] = "another-repository"
    path.write_text(json.dumps(payload), "utf-8")
    with pytest.raises(RetrievalSnapshotNotFound):
        service.get(manifest.snapshot_binding)
    with pytest.raises(RetrievalSnapshotNotFound):
        service.manifest_for("baseline-a")
    with pytest.raises(RetrievalSnapshotNotFound):
        service.refresh("baseline-a", config=config())

    payload["repository"] = "banking-demo"
    payload["baseline"] = "baseline-b"
    path.write_text(json.dumps(payload), "utf-8")
    pointer = tmp_path / "retrieval-snapshots" / "baselines" / "baseline-b.json"
    pointer.write_text(
        json.dumps(
            {
                "snapshot_binding": manifest.snapshot_binding,
                "config_digest": manifest.config_digest,
            }
        ),
        "utf-8",
    )
    with pytest.raises(RetrievalSnapshotNotFound):
        service.get(manifest.snapshot_binding)
    with pytest.raises(RetrievalSnapshotNotFound):
        service.manifest_for("baseline-b")


def test_arbitrary_snapshot_filename_is_not_listed_or_served(
    store: IngestedStore, fixture_settings: Settings, tmp_path: Path
) -> None:
    service = lifecycle(store, fixture_settings, tmp_path)
    manifest = service.refresh("baseline-a", config=config())
    original = next((tmp_path / "retrieval-snapshots" / "snapshots").glob("snapshot-*.json"))
    original.rename(original.with_name("arbitrary.json"))

    listed = service.manifests()
    assert manifest.snapshot_binding not in {item.snapshot_binding for item in listed.manifests}
    with pytest.raises(RetrievalSnapshotNotFound):
        service.manifest_for("baseline-a")
    with pytest.raises(RetrievalSnapshotNotFound):
        service.get(manifest.snapshot_binding)


def test_publication_is_invisible_until_pointer_commit(
    store: IngestedStore,
    fixture_settings: Settings,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import app.retrieval.lifecycle as lifecycle_module

    service = lifecycle(store, fixture_settings, tmp_path)
    first = service.refresh("baseline-a", config=config())
    original = lifecycle_module._atomic_write
    entered = threading.Event()
    release = threading.Event()

    def paused_pointer(path: Path, content: str) -> None:
        if path.parent.name == "baselines" and path.name == "baseline-b.json":
            entered.set()
            assert release.wait(5)
            raise OSError("injected pointer publication failure")
        original(path, content)

    monkeypatch.setattr(lifecycle_module, "_atomic_write", paused_pointer)
    failures: list[BaseException] = []

    def do_refresh() -> None:
        try:
            service.refresh("baseline-b", previous_baseline="baseline-a", config=config())
        except RetrievalUnavailable:
            pass
        except BaseException as exc:  # noqa: BLE001 - the worker reports any unexpected failure
            failures.append(exc)

    worker = threading.Thread(target=do_refresh)
    worker.start()
    assert entered.wait(5)
    reader_result: list[ManifestListResponse | BaseException] = []

    def do_read() -> None:
        try:
            reader_result.append(service.manifests())
        except BaseException as exc:  # noqa: BLE001 - the worker reports any unexpected failure
            reader_result.append(exc)

    reader = threading.Thread(target=do_read)
    reader.start()
    time.sleep(0.1)
    assert reader.is_alive(), "a reader observed the pending publication before commit"
    release.set()
    worker.join(5)
    reader.join(5)
    assert not worker.is_alive() and not reader.is_alive()
    assert failures == []
    assert len(reader_result) == 1
    listed = reader_result[0]
    assert isinstance(listed, ManifestListResponse)
    assert [item.baseline for item in listed.manifests] == ["baseline-a"]
    assert service.manifest_for("baseline-a").snapshot_binding == first.snapshot_binding
    with pytest.raises(RetrievalSnapshotNotFound):
        service.manifest_for("baseline-b")
    assert not list((tmp_path / "retrieval-snapshots" / "staging").glob("*.json"))


def test_snapshot_write_failure_is_typed(
    store: IngestedStore,
    fixture_settings: Settings,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import app.retrieval.lifecycle as lifecycle_module

    service = lifecycle(store, fixture_settings, tmp_path)
    original = lifecycle_module._atomic_write

    def failing_snapshot(path: Path, content: str) -> None:
        if path.parent.name == "staging":
            raise OSError("injected snapshot storage failure")
        original(path, content)

    monkeypatch.setattr(lifecycle_module, "_atomic_write", failing_snapshot)
    with pytest.raises(RetrievalUnavailable):
        service.refresh("baseline-a", config=config())
    with pytest.raises(RetrievalSnapshotNotFound):
        service.manifest_for("baseline-a")
    assert not list((tmp_path / "retrieval-snapshots" / "snapshots").glob("*.json"))
    assert not list((tmp_path / "retrieval-snapshots" / "baselines").glob("*.json"))
