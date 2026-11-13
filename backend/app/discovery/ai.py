"""Typed provider boundary for optional AI capabilities (workstream A).

These protocols are deliberately separate from :class:`app.domain.ports.CandidateDiscovery`.
A discovery provider may use a chat or embedding provider internally, but this module has no
vocabulary for links, review states, evidence, or assurance policy: an adapter can generate text
or vectors and nothing else.

The fake providers in :mod:`app.discovery.ai_fake` and the HTTP adapters in
:mod:`app.discovery.ai_http` implement the same protocols.
"""

from __future__ import annotations

import math
import re
from collections.abc import Mapping, Sequence
from typing import Any, Literal, Protocol, runtime_checkable
from urllib.parse import urlsplit, urlunsplit

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

ChatRole = Literal["system", "user", "assistant"]

REDACTED = "<redacted>"
#: Headers that are safe and useful to retain as provenance. Everything else is dropped.
RATE_LIMIT_HEADERS = frozenset(
    {
        "retry-after",
        "x-ratelimit-limit-requests",
        "x-ratelimit-remaining-requests",
        "x-ratelimit-reset-requests",
        "x-ratelimit-limit-tokens",
        "x-ratelimit-remaining-tokens",
        "x-ratelimit-reset-tokens",
    }
)


class ChatMessage(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    role: ChatRole
    content: str = Field(min_length=1)


class TokenUsage(BaseModel):
    """Token counts reported by an endpoint. Missing fields stay ``None`` (unavailable)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    prompt_tokens: int | None = Field(default=None, ge=0)
    completion_tokens: int | None = Field(default=None, ge=0)
    total_tokens: int | None = Field(default=None, ge=0)


class ChatCompletion(BaseModel):
    """One completion plus the provenance needed to explain where it came from."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    text: str
    model: str
    #: True only when the endpoint itself reported the model identifier.
    model_observed: bool = False
    provider: str
    usage: TokenUsage | None = None
    latency_ms: float = Field(ge=0)
    finish_reason: str | None = None
    response_id: str | None = None
    request_id: str | None = None
    http_status: int | None = Field(default=None, ge=200, lt=300)
    rate_limit_headers: dict[str, str] = Field(default_factory=dict)
    #: Validated JSON object when the caller supplied a ``response_model``.
    parsed: dict[str, Any] | None = None


class EmbeddingBatch(BaseModel):
    """Vectors for one batch. Every vector has the reported dimension."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    vectors: tuple[tuple[float, ...], ...]
    model: str
    #: True only when the endpoint itself reported the model identifier.
    model_observed: bool = False
    provider: str
    dimensions: int = Field(ge=1)
    usage: TokenUsage | None = None
    latency_ms: float = Field(ge=0)
    request_id: str | None = None
    http_status: int | None = Field(default=None, ge=200, lt=300)
    rate_limit_headers: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _vector_shape(self) -> EmbeddingBatch:
        if not self.vectors:
            raise ValueError("an embedding batch must contain at least one vector")
        if any(len(vector) != self.dimensions for vector in self.vectors):
            raise ValueError("every vector must have the reported dimensions")
        return self


@runtime_checkable
class ChatGenerationProvider(Protocol):
    """Text generation only. No link, review, or evidence operation is part of this contract."""

    provider_name: str
    model_version: str

    def complete(
        self,
        messages: Sequence[ChatMessage],
        *,
        temperature: float = 0.0,
        max_tokens: int | None = None,
        response_model: type[BaseModel] | None = None,
        timeout: float | None = None,
    ) -> ChatCompletion: ...


@runtime_checkable
class EmbeddingProvider(Protocol):
    """Embedding generation only. It never substitutes chat output for a vector."""

    provider_name: str
    model_version: str
    dimensions: int | None

    def embed(self, texts: Sequence[str], *, timeout: float | None = None) -> EmbeddingBatch: ...


class ProviderError(Exception):
    """Sanitized provider failure. Details never include headers, payloads, or credentials."""

    code = "provider-error"
    retryable = False

    def __init__(
        self,
        detail: str,
        *,
        provider: str,
        status: int | None = None,
        retry_after: float | None = None,
        upstream_code: str | None = None,
    ) -> None:
        super().__init__(detail)
        self.detail = detail
        self.provider = provider
        self.status = status
        self.retry_after = retry_after
        self.upstream_code = upstream_code


class ProviderConfigurationError(ProviderError):
    code = "provider-configuration-error"


class ProviderAuthenticationError(ProviderError):
    code = "provider-authentication-error"


class ProviderRateLimitError(ProviderError):
    code = "provider-rate-limit"
    retryable = True


class ProviderServerError(ProviderError):
    code = "provider-server-error"
    retryable = True


class ProviderTimeoutError(ProviderError):
    code = "provider-timeout"
    retryable = True


class ProviderTransportError(ProviderError):
    code = "provider-transport-error"
    retryable = True


class ProviderResponseError(ProviderError):
    code = "provider-response-error"


class ProviderCapabilityError(ProviderError):
    code = "provider-capability-error"


class ProviderRequestError(ProviderError):
    code = "provider-request-error"


def validate_temperature(temperature: float) -> float:
    if not math.isfinite(temperature) or not 0.0 <= temperature <= 2.0:
        raise ValueError("temperature must be a finite value between 0 and 2")
    return temperature


def validate_max_tokens(max_tokens: int | None) -> int | None:
    if max_tokens is not None and max_tokens < 1:
        raise ValueError("max_tokens must be >= 1 when provided")
    return max_tokens


def validate_timeout(timeout: float) -> float:
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("timeout must be a finite value greater than zero")
    return timeout


def parse_usage(payload: Any) -> TokenUsage | None:
    """Parse OpenAI-style usage without turning missing fields into zero."""
    if not isinstance(payload, Mapping):
        return None
    fields = ("prompt_tokens", "completion_tokens", "total_tokens")
    values: dict[str, int | None] = {}
    for field in fields:
        value = payload.get(field)
        values[field] = (
            value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else None
        )
    if all(value is None for value in values.values()):
        return None
    return TokenUsage(**values)


def parse_rate_limit_headers(headers: Mapping[str, str]) -> dict[str, str]:
    """Retain only allow-listed, non-secret rate-limit response headers."""
    selected: dict[str, str] = {}
    for name, value in headers.items():
        lowered = name.lower()
        if lowered in RATE_LIMIT_HEADERS or lowered.startswith("ratelimit-"):
            selected[lowered] = str(value)[:80]
    return dict(sorted(selected.items()))


def parse_upstream_code(payload: Any) -> str | None:
    """Extract a short machine-readable error code; never the upstream message."""
    if not isinstance(payload, Mapping):
        return None
    error = payload.get("error")
    if not isinstance(error, Mapping):
        return None
    for key in ("code", "type"):
        value = error.get(key)
        if isinstance(value, (str, int)) and str(value).strip():
            return str(value).strip()[:80]
    return None


def redact_secrets(value: str, secrets: Sequence[str | None]) -> str:
    redacted = value
    for secret in secrets:
        if secret:
            redacted = redacted.replace(secret, REDACTED)
    return redacted


def sanitize_url(value: str) -> str:
    """Drop userinfo, query, and fragment, which could carry a credential."""
    try:
        parsed = urlsplit(value)
    except ValueError:
        return "<invalid-url>"
    netloc = parsed.netloc.rsplit("@", 1)[-1]
    return urlunsplit((parsed.scheme, netloc, parsed.path, "", ""))


_URL_PATTERN = re.compile(r"https?://[^\s\"'<>]+", re.IGNORECASE)


def sanitize_text(value: str, secrets: Sequence[str | None] = ()) -> str:
    """Remove URL credentials/query and known secret values from arbitrary text."""
    without_credentials = _URL_PATTERN.sub(lambda match: sanitize_url(match.group(0)), value)
    return redact_secrets(without_credentials, secrets)


def sanitize_capability_report(value: Any, *, secrets: Sequence[str | None] = ()) -> Any:
    """Recursively sanitize report values **and dynamic keys**.

    Keys can be data, not just field names: a model catalogue can use a URL as a model id,
    which becomes a key in ``models.context_lengths``. Both keys and values therefore pass
    through URL credential removal and configured-secret replacement.
    """
    if isinstance(value, dict):
        sanitized: dict[str, Any] = {}
        for key, item in value.items():
            sanitized_key = sanitize_text(str(key), secrets)
            if sanitized_key in sanitized:
                suffix = 2
                candidate = f"{sanitized_key}#{suffix}"
                while candidate in sanitized:
                    suffix += 1
                    candidate = f"{sanitized_key}#{suffix}"
                sanitized_key = candidate
            lowered = str(key).lower()
            sensitive = lowered in {
                "api_key",
                "authorization",
                "password",
                "secret",
                "token",
                "access_token",
            } or lowered.endswith(("_api_key", "_secret", "_password"))
            if sensitive:
                sanitized[sanitized_key] = "<redacted>" if item else item
            else:
                sanitized[sanitized_key] = sanitize_capability_report(item, secrets=secrets)
        return sanitized
    if isinstance(value, list):
        return [sanitize_capability_report(item, secrets=secrets) for item in value]
    if isinstance(value, tuple):
        return tuple(sanitize_capability_report(item, secrets=secrets) for item in value)
    if isinstance(value, str):
        return sanitize_text(value, secrets)
    return value


def validate_response_model(
    text: str, response_model: type[BaseModel], *, provider: str
) -> dict[str, Any]:
    """Validate schema-constrained output; fail without echoing the model's text."""
    try:
        validated = response_model.model_validate_json(text)
    except ValidationError as exc:
        raise ProviderResponseError(
            f"response failed {response_model.__name__} validation "
            f"({exc.error_count()} validation error(s))",
            provider=provider,
        ) from None
    return validated.model_dump(mode="json")
