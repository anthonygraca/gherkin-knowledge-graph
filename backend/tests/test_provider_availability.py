"""AS-07: provider availability, empty success, and structured problem extensions."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.discovery.registry import ProviderRegistry
from app.domain.api import ProviderCatalogResponse
from app.main import create_app
from app.settings import Settings


class FailingDiscovery:
    """A registered provider whose external transport is unavailable."""

    provider_name = "cocoindex"
    model_version = "recorded-embeddinggemma-2"
    index_revision = "sha256:" + "a" * 64

    def __init__(self) -> None:
        self.calls = 0

    def discover(self, artifact_id, *, top_k=5, relation_types=None, baseline=None):
        self.calls += 1
        raise TimeoutError("deterministic recorded transport timed out")


class CocoaRegistry(ProviderRegistry):
    @property
    def registered(self) -> list[str]:
        return ["fake", "cocoindex"]


def test_unregistered_provider_problem_names_the_registry(client: TestClient) -> None:
    response = client.post(
        "/api/discovery", json={"artifact_id": "REQ-001", "provider": "missing-provider"}
    )
    assert response.status_code == 400
    body = response.json()
    assert body["code"] == "provider-not-registered"
    assert body["failed_provider"] == "missing-provider"
    assert body["registered_providers"] == ["fake"]


def test_empty_result_retains_provenance(client: TestClient) -> None:
    response = client.post(
        "/api/discovery",
        json={"artifact_id": "REQ-003", "provider": "fake", "baseline": "baseline-a"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["candidates"] == []
    assert body["provider"] == "fake"
    assert body["model_version"] == "fake-fixture-v1"
    assert body["index_revision"].startswith("sha256:")


def test_registered_provider_failure_is_typed_and_creates_no_finding(
    fixture_settings: Settings,
) -> None:
    client = TestClient(create_app(fixture_settings))
    before = client.get("/api/findings", params={"baseline": "baseline-a"}).json()
    failing = FailingDiscovery()
    registry = CocoaRegistry(client.app.state.settings, client.app.state.store)
    registry._cache["cocoindex"] = failing
    client.app.state.providers = registry

    response = client.post(
        "/api/discovery",
        json={"artifact_id": "REQ-001", "provider": "cocoindex", "baseline": "baseline-a"},
    )
    assert response.status_code == 503
    body = response.json()
    assert body["code"] == "provider-unavailable"
    assert body["failed_provider"] == "cocoindex"
    assert failing.calls == 1
    assert client.get("/api/findings", params={"baseline": "baseline-a"}).json() == before
    assert client.get("/api/threads/REQ-001", params={"baseline": "baseline-a"}).status_code == 200


def test_registered_provider_construction_failure_is_typed(
    fixture_settings: Settings,
) -> None:
    from app.discovery.cocoindex import CocoIndexConfigurationError

    class BrokenConstructionRegistry(CocoaRegistry):
        def _build(self, name: str):
            if name == "cocoindex":
                raise CocoIndexConfigurationError("configured executable is missing")
            return super()._build(name)

    client = TestClient(create_app(fixture_settings))
    before_findings = client.get("/api/findings", params={"baseline": "baseline-a"}).json()
    before_thread = client.get("/api/threads/REQ-001", params={"baseline": "baseline-a"}).json()
    client.app.state.providers = BrokenConstructionRegistry(
        client.app.state.settings, client.app.state.store
    )
    response = client.post(
        "/api/discovery",
        json={"artifact_id": "REQ-001", "provider": "cocoindex", "baseline": "baseline-a"},
    )
    assert response.status_code == 503
    body = response.json()
    assert body["code"] == "provider-unavailable"
    assert body["failed_provider"] == "cocoindex"
    assert client.get("/api/findings", params={"baseline": "baseline-a"}).json() == before_findings
    assert (
        client.get("/api/threads/REQ-001", params={"baseline": "baseline-a"}).json()
        == before_thread
    )


def test_provider_catalogue_labels_kind_not_name(fixture_settings: Settings) -> None:
    client = TestClient(create_app(fixture_settings))
    response = client.get("/api/discovery/providers")
    assert response.status_code == 200
    catalog = ProviderCatalogResponse.model_validate(response.json())
    assert catalog.default == "fake"
    assert [(item.name, item.kind, item.default) for item in catalog.providers] == [
        ("fake", "fixture", True)
    ]


def test_catalogue_includes_an_enabled_optional_provider(
    fixture_settings: Settings, tmp_path: Path
) -> None:
    project = tmp_path / "cocoindex-project"
    (project / ".cocoindex_code").mkdir(parents=True)
    (project / ".cocoindex_code" / "settings.yml").write_text("version: 1\n", "utf-8")
    settings = Settings(
        repo_root=fixture_settings.repo_root,
        fixtures_dir=fixture_settings.fixtures_dir,
        fixture_repo_path=fixture_settings.fixture_repo_path,
        ccc_project_root=project,
        cocoindex_live_opt_in=True,
    )
    client = TestClient(create_app(settings))
    catalog = ProviderCatalogResponse.model_validate(client.get("/api/discovery/providers").json())
    assert catalog.default == "fake"
    assert [(item.name, item.kind) for item in catalog.providers] == [
        ("fake", "fixture"),
        ("cocoindex", "model"),
    ]
