"""Candidate-discovery provider lookup.

One provider is registered in M0: ``fake`` (fixture index). Local embedding providers
(AI-02, owner A) register here behind the same :class:`CandidateDiscovery` port; nothing
else in the codebase needs to change when they do.
"""

from __future__ import annotations

from app.discovery.fake import FakeCandidateDiscovery
from app.domain.errors import ProviderNotRegistered
from app.domain.ports import CandidateDiscovery
from app.settings import Settings

REGISTERED_PROVIDERS: tuple[str, ...] = ("fake",)


class ProviderRegistry:
    """Builds providers on demand and caches them per process."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._cache: dict[str, CandidateDiscovery] = {}

    @property
    def registered(self) -> list[str]:
        return list(REGISTERED_PROVIDERS)

    def get(self, name: str | None = None) -> CandidateDiscovery:
        resolved = name or self._settings.discovery_provider
        if resolved not in REGISTERED_PROVIDERS:
            raise ProviderNotRegistered(
                f"Unknown discovery provider '{resolved}'. Registered providers: "
                f"{', '.join(REGISTERED_PROVIDERS)}. Local model providers arrive with AI-02 (M3); "
                f"they are optional plugins and never required for tests."
            )
        if resolved not in self._cache:
            self._cache[resolved] = self._build(resolved)
        return self._cache[resolved]

    def _build(self, name: str) -> CandidateDiscovery:
        if name == "fake":
            return FakeCandidateDiscovery.from_fixture(self._settings.candidate_index_path)
        raise AssertionError(f"provider '{name}' is listed as registered but has no builder")
