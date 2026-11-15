"""BDD-only ASGI app: the real CTA app with a deterministic CocoIndex provider.

Only the provider's external transport is replaced. `POST /api/discovery`, the problem mapping,
the provider catalogue, and the dashboard consumption are the production surfaces.
"""

from __future__ import annotations

import os
from pathlib import Path

from app.discovery.cocoindex import (
    CocoIndexSearchClient,
    CocoIndexTimeoutError,
    FakeCocoIndexTransport,
)
from app.discovery.code_index import CocoIndexCandidateDiscovery, CodeDiscovery
from app.discovery.registry import ProviderRegistry
from app.ingestion.repository import GitRepository
from app.main import create_app

ROOT = Path(__file__).resolve().parents[2]
CAPTURE = ROOT / "backend" / "tests" / "fixtures" / "cocoindex-search-response.json"
MODEL_VERSION = "embeddinggemma-2-text-270m-q8_0@sha256:278a7ff1248c"


class StatefulTimeoutTransport:
    """Real recorded transport on the first search; a transport timeout afterwards."""

    def __init__(self, captured: Path, *, project_root: Path) -> None:
        self._inner = FakeCocoIndexTransport.from_fixture(captured, project_root=project_root)
        self.project_root = project_root
        self.calls = 0

    def capabilities(self, *, timeout: float | None = None):
        return self._inner.capabilities(timeout=timeout)

    def search(self, request, *, timeout: float | None = None):
        self.calls += 1
        if self.calls > 1:
            raise CocoIndexTimeoutError("deterministic recorded CocoIndex transport timed out")
        return self._inner.search(request, timeout=timeout)


def recorded_discovery(registry: ProviderRegistry, transport=None) -> CocoIndexCandidateDiscovery:
    settings = registry._settings
    store = registry._repository
    client = CocoIndexSearchClient(
        transport
        or FakeCocoIndexTransport.from_fixture(CAPTURE, project_root=settings.fixture_repo)
    )
    discovery = CodeDiscovery(
        repository=store,
        git=GitRepository(settings.fixture_repo),
        repository_name=settings.fixture,
        client=client,
        model_version=MODEL_VERSION,
        require_live_root=False,
    )
    return CocoIndexCandidateDiscovery(discovery, model_version=MODEL_VERSION)


class DemoRegistry(ProviderRegistry):
    @property
    def registered(self) -> list[str]:
        if os.environ.get("CTA_BDD_PROVIDER_MODE", "recorded") == "fake-only":
            return ["fake"]
        return ["fake", "cocoindex"]

    def _build(self, name: str):
        if name == "cocoindex":
            mode = os.environ.get("CTA_BDD_PROVIDER_MODE", "recorded")
            if mode == "timeout":
                return recorded_discovery(
                    self,
                    StatefulTimeoutTransport(CAPTURE, project_root=self._settings.fixture_repo),
                )
            return recorded_discovery(self)
        return super()._build(name)


app = create_app()
app.state.providers = DemoRegistry(app.state.settings, app.state.store)
