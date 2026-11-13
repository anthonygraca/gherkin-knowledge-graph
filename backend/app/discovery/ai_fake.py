"""Deterministic fake chat and embedding providers for offline contract tests.

The fake providers are deliberately not a model: the chat provider returns a fixed or scripted
string and reports no token usage, and the embedding provider derives a stable vector from a hash.
They exist so the protocol and its consumers can be tested with no network, GPU, model download,
or vector database.
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable, Sequence

from pydantic import BaseModel

from app.discovery.ai import (
    ChatCompletion,
    ChatMessage,
    EmbeddingBatch,
    ProviderConfigurationError,
    validate_max_tokens,
    validate_response_model,
    validate_temperature,
)

FAKE_CHAT_PROVIDER = "fake"
FAKE_CHAT_MODEL = "fake-chat-v1"
FAKE_EMBED_PROVIDER = "fake"
FAKE_EMBED_MODEL = "fake-embedding-v1"
FAKE_EMBED_DIMENSIONS = 8


class FakeChatGenerationProvider:
    """Scriptable completion source. It has no link, review, or evidence method."""

    provider_name = FAKE_CHAT_PROVIDER
    model_version = FAKE_CHAT_MODEL

    def __init__(
        self,
        responses: Sequence[str] | None = None,
        responder: Callable[[Sequence[ChatMessage]], str] | None = None,
    ) -> None:
        if responses is not None and responder is not None:
            raise ValueError("supply either scripted responses or a responder, not both")
        self._responses = list(responses) if responses is not None else None
        self._responder = responder
        self._index = 0

    def complete(
        self,
        messages: Sequence[ChatMessage],
        *,
        temperature: float = 0.0,
        max_tokens: int | None = None,
        response_model: type[BaseModel] | None = None,
        timeout: float | None = None,
    ) -> ChatCompletion:
        if not messages:
            raise ValueError("at least one message is required")
        validate_temperature(temperature)
        validate_max_tokens(max_tokens)
        if timeout is not None and timeout <= 0:
            raise ValueError("timeout must be positive")

        if self._responses is not None:
            if self._index >= len(self._responses):
                raise ProviderConfigurationError(
                    "scripted fake completion responses are exhausted",
                    provider=self.provider_name,
                )
            text = self._responses[self._index]
            self._index += 1
        elif self._responder is not None:
            text = self._responder(messages)
        else:
            text = "fake chat completion"

        parsed = (
            None
            if response_model is None
            else validate_response_model(text, response_model, provider=self.provider_name)
        )
        return ChatCompletion(
            text=text,
            model=self.model_version,
            provider=self.provider_name,
            usage=None,
            latency_ms=0.0,
            finish_reason="stop",
            response_id=None,
            request_id=None,
            http_status=None,
            parsed=parsed,
        )


class FakeEmbeddingProvider:
    """Hash-derived, dimension-stable vectors. Never used as retrieval-quality evidence."""

    provider_name = FAKE_EMBED_PROVIDER
    model_version = FAKE_EMBED_MODEL

    def __init__(self, dimensions: int = FAKE_EMBED_DIMENSIONS) -> None:
        if dimensions < 1:
            raise ValueError("dimensions must be >= 1")
        self.dimensions = dimensions

    def embed(self, texts: Sequence[str], *, timeout: float | None = None) -> EmbeddingBatch:
        if not texts:
            raise ValueError("at least one text is required")
        if timeout is not None and timeout <= 0:
            raise ValueError("timeout must be positive")
        vectors = tuple(self._vector(text) for text in texts)
        return EmbeddingBatch(
            vectors=vectors,
            model=self.model_version,
            provider=self.provider_name,
            dimensions=self.dimensions,
            usage=None,
            latency_ms=0.0,
            request_id=None,
            http_status=None,
        )

    def _vector(self, text: str) -> tuple[float, ...]:
        chunks: list[bytes] = []
        total = 0
        counter = 0
        while total < self.dimensions:
            chunk = hashlib.sha256(f"{self.model_version}\0{text}\0{counter}".encode()).digest()
            chunks.append(chunk)
            total += len(chunk)
            counter += 1
        digest = b"".join(chunks)
        return tuple((byte / 127.5) - 1.0 for byte in digest[: self.dimensions])
