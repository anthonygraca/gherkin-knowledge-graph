"""Provider lookup.

Candidate discovery is still fixture-backed (``fake``); real providers register behind the same
:class:`CandidateDiscovery` port in a later story. The optional chat and embedding providers are
built lazily from :class:`app.settings.Settings`: fake mode returns deterministic fakes, live mode
builds the HTTP adapters only when asked, and a live configuration without an embeddings endpoint
reports embeddings as unavailable rather than substituting chat completions.
"""

from __future__ import annotations

from app.discovery.ai import ChatGenerationProvider, EmbeddingProvider
from app.discovery.ai_fake import FakeChatGenerationProvider, FakeEmbeddingProvider
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
        self._chat: ChatGenerationProvider | None = None
        self._embeddings: EmbeddingProvider | None = None
        self._embeddings_resolved = False

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

    def chat(self) -> ChatGenerationProvider:
        """The configured chat provider. Construction never contacts the endpoint."""
        if self._chat is None:
            if self._settings.ai_mode == "fake":
                self._chat = FakeChatGenerationProvider()
            else:
                from app.discovery.ai_http import OpenAICompatibleChatProvider

                self._chat = OpenAICompatibleChatProvider(
                    base_url=self._settings.llm_base_url or "",
                    model=self._settings.llm_model or "",
                    api_key=self._settings.llm_api_key,
                )
        return self._chat

    def embeddings(self) -> EmbeddingProvider | None:
        """The configured embedding provider, or ``None`` when none is available.

        A live mode without ``CTA_EMBED_BASE_URL``/``CTA_EMBED_MODEL`` is a valid configuration;
        callers must treat the missing provider as "embeddings unavailable", never as a reason to
        use chat output.
        """
        if not self._embeddings_resolved:
            if self._settings.ai_mode == "fake":
                self._embeddings = FakeEmbeddingProvider()
            elif self._settings.embeddings_configured:
                from app.discovery.ai_http import OpenAICompatibleEmbeddingProvider

                self._embeddings = OpenAICompatibleEmbeddingProvider(
                    base_url=self._settings.embed_base_url or "",
                    model=self._settings.embed_model or "",
                    api_key=self._settings.embed_api_key,
                )
            else:
                self._embeddings = None
            self._embeddings_resolved = True
        return self._embeddings

    def _build(self, name: str) -> CandidateDiscovery:
        if name == "fake":
            return FakeCandidateDiscovery.from_fixture(self._settings.candidate_index_path)
        raise AssertionError(f"provider '{name}' is listed as registered but has no builder")
