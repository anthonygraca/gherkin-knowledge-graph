"""Semantic discovery (workstream A).

The candidate provider remains fixture-backed until a real ``CandidateDiscovery`` lands. The
optional AI provider protocols and their fake adapters are exported here; the HTTP adapters stay
behind :mod:`app.discovery.ai_http` so importing this package never imports ``httpx``.
"""

from app.discovery.ai import (
    ChatCompletion,
    ChatGenerationProvider,
    ChatMessage,
    EmbeddingBatch,
    EmbeddingProvider,
    ProviderError,
    TokenUsage,
)
from app.discovery.ai_fake import (
    FakeChatGenerationProvider,
    FakeEmbeddingProvider,
)
from app.discovery.fake import FakeCandidateDiscovery, compute_index_revision
from app.discovery.registry import REGISTERED_PROVIDERS, ProviderRegistry

__all__ = [
    "REGISTERED_PROVIDERS",
    "ChatCompletion",
    "ChatGenerationProvider",
    "ChatMessage",
    "EmbeddingBatch",
    "EmbeddingProvider",
    "FakeCandidateDiscovery",
    "FakeChatGenerationProvider",
    "FakeEmbeddingProvider",
    "ProviderError",
    "ProviderRegistry",
    "TokenUsage",
    "compute_index_revision",
]
