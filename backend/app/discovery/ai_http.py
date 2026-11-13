"""Minimal OpenAI-compatible HTTP adapters for chat and embeddings.

Compatibility is asserted only when a probe or a caller observes it. The adapters use the
``/chat/completions`` and ``/embeddings`` shapes; they do not guess at vendor-specific fields.
Every call has an explicit timeout, a bounded retry budget, response-shape validation, and an
error type that never renders headers, payloads, or credentials.

``httpx`` is imported here, not by :mod:`app.discovery.registry`; fake mode therefore works
without importing the transport.
"""

from __future__ import annotations

import json
import logging
import math
import time
from collections.abc import Callable, Mapping, Sequence
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from typing import Any

import httpx
from pydantic import BaseModel

from app.discovery.ai import (
    ChatCompletion,
    ChatMessage,
    EmbeddingBatch,
    ProviderAuthenticationError,
    ProviderCapabilityError,
    ProviderConfigurationError,
    ProviderError,
    ProviderRateLimitError,
    ProviderRequestError,
    ProviderResponseError,
    ProviderServerError,
    ProviderTimeoutError,
    ProviderTransportError,
    parse_rate_limit_headers,
    parse_upstream_code,
    parse_usage,
    sanitize_text,
    validate_max_tokens,
    validate_response_model,
    validate_temperature,
    validate_timeout,
)
from app.settings import validate_base_url

DEFAULT_TIMEOUT_SECONDS = 10.0
DEFAULT_MAX_RETRIES = 1
MAX_RETRIES_LIMIT = 5
DEFAULT_BACKOFF_SECONDS = 0.25
MAX_RETRY_AFTER_SECONDS = 5.0
OPENAI_COMPATIBLE_PROVIDER = "openai-compatible"


def _retry_after_seconds(value: str | None) -> float | None:
    """Parse Retry-After seconds or HTTP-date; cap it so a hostile header cannot stall a run."""
    if not value:
        return None
    try:
        seconds = float(value)
    except ValueError:
        try:
            when = parsedate_to_datetime(value)
        except (TypeError, ValueError):
            return None
        if when.tzinfo is None:
            when = when.replace(tzinfo=UTC)
        seconds = (when - datetime.now(UTC)).total_seconds()
    return max(0.0, min(seconds, MAX_RETRY_AFTER_SECONDS))


class _OpenAICompatibleProvider:
    provider_name = OPENAI_COMPATIBLE_PROVIDER

    def __init__(
        self,
        base_url: str,
        model: str,
        *,
        api_key: str | None = None,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        max_retries: int = DEFAULT_MAX_RETRIES,
        backoff_seconds: float = DEFAULT_BACKOFF_SECONDS,
        transport: httpx.BaseTransport | None = None,
        sleep: Callable[[float], None] = time.sleep,
        logger: logging.Logger | None = None,
    ) -> None:
        try:
            normalized = validate_base_url("base_url", base_url)
        except ValueError as exc:
            raise ProviderConfigurationError(str(exc), provider=self.provider_name) from None
        if normalized is None:
            raise ProviderConfigurationError("base_url is required", provider=self.provider_name)
        model = model.strip()
        if not model:
            raise ProviderConfigurationError("model is required", provider=self.provider_name)
        if not 0 <= max_retries <= MAX_RETRIES_LIMIT:
            raise ProviderConfigurationError(
                f"max_retries must be between 0 and {MAX_RETRIES_LIMIT}",
                provider=self.provider_name,
            )
        if not math.isfinite(backoff_seconds) or backoff_seconds < 0:
            raise ProviderConfigurationError(
                "backoff_seconds must be finite and non-negative",
                provider=self.provider_name,
            )
        self._base_url = normalized
        self.model_version = model
        self._api_key = api_key
        self._timeout = validate_timeout(timeout)
        self._max_retries = max_retries
        self._backoff_seconds = backoff_seconds
        self._transport = transport
        self._sleep = sleep
        self._logger = logger
        self._secrets = tuple(secret for secret in (api_key,) if secret)

    def _url(self, path: str) -> str:
        return f"{self._base_url}/{path.lstrip('/')}"

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        return headers

    def _log(self, level: int, event: str, **fields: Any) -> None:
        if self._logger is None:
            return
        safe = {key: sanitize_text(str(value), self._secrets) for key, value in fields.items()}
        self._logger.log(
            level,
            "%s %s %s",
            self.provider_name,
            event,
            json.dumps(safe, sort_keys=True, default=str),
        )

    def _json_object(self, response: httpx.Response, *, operation: str) -> dict[str, Any]:
        try:
            payload = response.json()
        except ValueError:
            raise ProviderResponseError(
                f"{operation} returned a non-JSON response (HTTP {response.status_code})",
                provider=self.provider_name,
                status=response.status_code,
            ) from None
        if not isinstance(payload, dict):
            raise ProviderResponseError(
                f"{operation} returned a non-object JSON response (HTTP {response.status_code})",
                provider=self.provider_name,
                status=response.status_code,
            )
        return payload

    def _error_for(
        self,
        response: httpx.Response,
        *,
        operation: str,
        response_format_requested: bool,
    ) -> ProviderError:
        status = response.status_code
        try:
            payload = response.json()
        except ValueError:
            payload = None
        upstream = parse_upstream_code(payload)
        upstream = sanitize_text(upstream, self._secrets) if upstream else None
        retry_after = _retry_after_seconds(response.headers.get("retry-after"))
        common = {
            "provider": self.provider_name,
            "status": status,
            "retry_after": retry_after,
            "upstream_code": upstream,
        }
        if status in (401, 403):
            return ProviderAuthenticationError(
                f"{operation} was rejected by authentication (HTTP {status})", **common
            )
        if status == 429:
            return ProviderRateLimitError(f"{operation} was rate limited (HTTP {status})", **common)
        if 500 <= status <= 599:
            return ProviderServerError(
                f"{operation} failed with a server error (HTTP {status})", **common
            )
        if status == 404:
            return ProviderCapabilityError(
                f"{operation} endpoint or model is unavailable (HTTP {status})", **common
            )
        if status == 400 and response_format_requested:
            return ProviderCapabilityError(
                f"{operation} does not support the requested JSON schema (HTTP {status})",
                **common,
            )
        if 400 <= status <= 499:
            return ProviderRequestError(
                f"{operation} was rejected as invalid (HTTP {status})", **common
            )
        return ProviderResponseError(
            f"{operation} returned an unexpected HTTP status {status}", **common
        )

    def _request(
        self,
        operation: str,
        path: str,
        payload: Mapping[str, Any],
        *,
        timeout: float | None,
        response_format_requested: bool = False,
    ) -> tuple[httpx.Response, float]:
        request_timeout = self._timeout if timeout is None else validate_timeout(timeout)
        for attempt in range(self._max_retries + 1):
            started = time.perf_counter()
            try:
                with httpx.Client(
                    timeout=request_timeout,
                    transport=self._transport,
                    follow_redirects=False,
                ) as client:
                    response = client.post(
                        self._url(path), json=dict(payload), headers=self._headers()
                    )
            except httpx.TimeoutException:
                error: ProviderError = ProviderTimeoutError(
                    f"{operation} timed out after {request_timeout:.3f}s",
                    provider=self.provider_name,
                )
            except httpx.TransportError:
                error = ProviderTransportError(
                    f"{operation} failed in transport", provider=self.provider_name
                )
            else:
                elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
                if 200 <= response.status_code < 300:
                    self._log(
                        logging.INFO,
                        "request_succeeded",
                        operation=operation,
                        attempt=attempt,
                        status=response.status_code,
                        latency_ms=elapsed_ms,
                        model=self.model_version,
                    )
                    return response, elapsed_ms
                error = self._error_for(
                    response,
                    operation=operation,
                    response_format_requested=response_format_requested,
                )

            elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
            self._log(
                logging.WARNING,
                "request_failed",
                operation=operation,
                attempt=attempt,
                status=error.status,
                code=error.code,
                latency_ms=elapsed_ms,
                model=self.model_version,
            )
            if not error.retryable or attempt >= self._max_retries:
                raise error
            delay = (
                error.retry_after
                if error.retry_after is not None
                else self._backoff_seconds * (2**attempt)
            )
            self._sleep(min(delay, MAX_RETRY_AFTER_SECONDS))
        raise AssertionError("retry loop exited without a result")


class OpenAICompatibleChatProvider(_OpenAICompatibleProvider):
    """Chat completions over an OpenAI-compatible ``/chat/completions`` endpoint."""

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
        payload: dict[str, Any] = {
            "model": self.model_version,
            "messages": [message.model_dump() for message in messages],
            "temperature": temperature,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if response_model is not None:
            payload["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": response_model.__name__,
                    "schema": response_model.model_json_schema(),
                    "strict": True,
                },
            }

        response, latency_ms = self._request(
            "chat completion",
            "chat/completions",
            payload,
            timeout=timeout,
            response_format_requested=response_model is not None,
        )
        body = self._json_object(response, operation="chat completion")
        choices = body.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ProviderResponseError(
                "chat completion response has no choices",
                provider=self.provider_name,
                status=response.status_code,
            )
        first = choices[0]
        if not isinstance(first, Mapping):
            raise ProviderResponseError(
                "chat completion choice is not an object",
                provider=self.provider_name,
                status=response.status_code,
            )
        message = first.get("message")
        if not isinstance(message, Mapping):
            raise ProviderResponseError(
                "chat completion choice has no message object",
                provider=self.provider_name,
                status=response.status_code,
            )
        content = message.get("content")
        if not isinstance(content, str):
            raise ProviderResponseError(
                "chat completion message content is not text",
                provider=self.provider_name,
                status=response.status_code,
            )

        observed_model = body.get("model")
        model_observed = isinstance(observed_model, str) and bool(observed_model)
        model = observed_model if model_observed else self.model_version
        finish_reason = first.get("finish_reason")
        response_id = body.get("id")
        request_id = response.headers.get("x-request-id") or None
        parsed = (
            None
            if response_model is None
            else validate_response_model(content, response_model, provider=self.provider_name)
        )
        return ChatCompletion(
            text=content,
            model=model,
            model_observed=model_observed,
            provider=self.provider_name,
            usage=parse_usage(body.get("usage")),
            latency_ms=latency_ms,
            finish_reason=finish_reason if isinstance(finish_reason, str) else None,
            response_id=response_id if isinstance(response_id, str) else None,
            request_id=request_id,
            http_status=response.status_code,
            rate_limit_headers=parse_rate_limit_headers(response.headers),
            parsed=parsed,
        )


class OpenAICompatibleEmbeddingProvider(_OpenAICompatibleProvider):
    """Embeddings over an OpenAI-compatible ``/embeddings`` endpoint."""

    def __init__(
        self,
        base_url: str,
        model: str,
        *,
        api_key: str | None = None,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        max_retries: int = DEFAULT_MAX_RETRIES,
        backoff_seconds: float = DEFAULT_BACKOFF_SECONDS,
        transport: httpx.BaseTransport | None = None,
        sleep: Callable[[float], None] = time.sleep,
        logger: logging.Logger | None = None,
        dimensions: int | None = None,
    ) -> None:
        super().__init__(
            base_url,
            model,
            api_key=api_key,
            timeout=timeout,
            max_retries=max_retries,
            backoff_seconds=backoff_seconds,
            transport=transport,
            sleep=sleep,
            logger=logger,
        )
        if dimensions is not None and dimensions < 1:
            raise ProviderConfigurationError(
                "dimensions must be >= 1 when provided", provider=self.provider_name
            )
        self.dimensions = dimensions

    def embed(self, texts: Sequence[str], *, timeout: float | None = None) -> EmbeddingBatch:
        if not texts:
            raise ValueError("at least one text is required")
        payload = {"model": self.model_version, "input": list(texts)}
        response, latency_ms = self._request("embedding", "embeddings", payload, timeout=timeout)
        body = self._json_object(response, operation="embedding")
        data = body.get("data")
        if not isinstance(data, list) or len(data) != len(texts):
            raise ProviderResponseError(
                "embedding response does not contain one vector per input",
                provider=self.provider_name,
                status=response.status_code,
            )

        indexed: dict[int, tuple[float, ...]] = {}
        ordered: list[tuple[float, ...]] = []
        has_index_key = [isinstance(item, Mapping) and "index" in item for item in data]
        if any(has_index_key) and not all(has_index_key):
            raise ProviderResponseError(
                "embedding response mixes indexed and unindexed items",
                provider=self.provider_name,
                status=response.status_code,
            )
        indices_present = all(has_index_key)
        if indices_present:
            for item in data:
                index = item.get("index")
                if isinstance(index, bool) or not isinstance(index, int):
                    raise ProviderResponseError(
                        "embedding index must be an integer",
                        provider=self.provider_name,
                        status=response.status_code,
                    )
        for item in data:
            if not isinstance(item, Mapping):
                raise ProviderResponseError(
                    "embedding data item is not an object",
                    provider=self.provider_name,
                    status=response.status_code,
                )
            vector = item.get("embedding")
            if not isinstance(vector, list) or not vector:
                raise ProviderResponseError(
                    "embedding is missing or empty",
                    provider=self.provider_name,
                    status=response.status_code,
                )
            numbers: list[float] = []
            for value in vector:
                if isinstance(value, bool) or not isinstance(value, (int, float)):
                    raise ProviderResponseError(
                        "embedding contains a non-numeric value",
                        provider=self.provider_name,
                        status=response.status_code,
                    )
                try:
                    number = float(value)
                except (OverflowError, ValueError):
                    raise ProviderResponseError(
                        "embedding contains an unrepresentable numeric value",
                        provider=self.provider_name,
                        status=response.status_code,
                    ) from None
                if not math.isfinite(number):
                    raise ProviderResponseError(
                        "embedding contains a non-finite value",
                        provider=self.provider_name,
                        status=response.status_code,
                    )
                numbers.append(number)
            floats = tuple(numbers)
            if indices_present:
                index = item["index"]
                if index < 0 or index >= len(texts) or index in indexed:
                    raise ProviderResponseError(
                        "embedding indices are missing, duplicated, or out of range",
                        provider=self.provider_name,
                        status=response.status_code,
                    )
                indexed[index] = floats
            else:
                ordered.append(floats)

        vectors = (
            [indexed[position] for position in range(len(texts))] if indices_present else ordered
        )
        dimensions = len(vectors[0])
        if any(len(vector) != dimensions for vector in vectors):
            raise ProviderResponseError(
                "embedding vectors have inconsistent dimensions",
                provider=self.provider_name,
                status=response.status_code,
            )
        if self.dimensions is not None and dimensions != self.dimensions:
            raise ProviderResponseError(
                f"embedding dimension {dimensions} does not match configured {self.dimensions}",
                provider=self.provider_name,
                status=response.status_code,
            )
        self.dimensions = dimensions

        observed_model = body.get("model")
        model_observed = isinstance(observed_model, str) and bool(observed_model)
        model = observed_model if model_observed else self.model_version
        return EmbeddingBatch(
            vectors=tuple(vectors),
            model=model,
            model_observed=model_observed,
            provider=self.provider_name,
            dimensions=dimensions,
            usage=parse_usage(body.get("usage")),
            latency_ms=latency_ms,
            request_id=response.headers.get("x-request-id") or None,
            http_status=response.status_code,
            rate_limit_headers=parse_rate_limit_headers(response.headers),
        )
