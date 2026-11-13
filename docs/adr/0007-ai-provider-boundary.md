# ADR 0007 — Optional AI provider boundary and hosted adapter

**Status:** Accepted for the PR 1 slice; independent review pending at the time of writing.
**Date:** 2026-11-13
**Owner:** A (semantic discovery), with the shared integration owner for settings and docs.

## Context

The RAG mission needs chat generation and embeddings for later retrieval and explanation work, but
the repository must remain offline by default: no test, CI job, or default path may require a
model, network, GPU, vector database, or Docker. At this revision the only retrieval provider is the
fixture-backed `fake` `CandidateDiscovery`; no chat provider, embedding provider, vector index, or
GraphRAG path exists.

The hosted endpoint is optional and may expose an OpenAI-compatible API, only some of its
capabilities, or no embeddings API at all. A key being present does not prove capability, and a
successful process exit does not prove it either. The provider boundary therefore has to report
what was actually observed and fail honestly when something is unavailable.

## Decision

### One typed boundary, two separate capabilities

`app.discovery.ai` defines `ChatGenerationProvider` and `EmbeddingProvider` protocols plus the
result, usage, and error types. They are deliberately separate from
`app.domain.ports.CandidateDiscovery`:

* A chat provider generates text. It has no link, review, evidence, or assurance operation.
* An embedding provider returns vectors. It never substitutes chat output for an embedding.
* A future `CandidateDiscovery` may use either internally, but it still returns `TraceCandidate`
  values with no link id and no review state.

Fake implementations live in `app.discovery.ai_fake`; the OpenAI-compatible HTTP adapters live in
`app.discovery.ai_http`. The registry builds them lazily. Fake mode never imports `httpx`.

### Configuration and offline default

| Variable | Default | Meaning |
| --- | --- | --- |
| `CTA_AI_MODE` | `fake` | `fake` keeps every normal path offline. `live` enables the HTTP adapters. |
| `CTA_LLM_BASE_URL` | unset | OpenAI-compatible API root, including its path prefix (for example `/v1`). Required in live mode. |
| `CTA_LLM_MODEL` | unset | Requested chat model identifier. Required in live mode. |
| `CTA_LLM_API_KEY` | unset | Optional bearer token. Presence is reported; the value is never logged or serialized. |
| `CTA_EMBED_BASE_URL` | unset | OpenAI-compatible API root for embeddings. Both embedding variables must be set together. |
| `CTA_EMBED_MODEL` | unset | Requested embedding model identifier. |
| `CTA_EMBED_API_KEY` | unset | Optional embedding bearer token; same handling as the chat key. |
| `CTA_VECTOR_BACKEND` | `memory` | Validated selector. PR 1 implements no index; PR 2 owns the in-memory index. |
| `CTA_AI_LIVE_TESTS` | `0` | Explicit opt-in for the live integration test. |

`Settings.__post_init__` validates the combinations without contacting the network. A live mode
missing the chat URL/model, an incomplete embedding pair, an unknown mode, or an unsupported vector
backend raises `SettingsError` at construction. It never silently falls back to fake and never
prints a credential. The live mode without embedding configuration is valid: embeddings are simply
unavailable.

### HTTP behavior

The adapter uses the OpenAI-compatible `POST {base}/chat/completions` and `POST {base}/embeddings`
shapes. Compatibility is treated as an observation, not an assumption: the capability probe reports
what the endpoint returned.

* **Timeout:** explicit, default 10 seconds, per request. Callers may pass a shorter positive
  timeout.
* **Retry:** default one retry, hard-capped at five. Retry only 429, 5xx, timeouts, and transport
  failures. Honor `Retry-After` (seconds or HTTP-date), capped at 5 seconds. Never retry
  authentication failures, other 4xx responses, malformed responses, or a rejected JSON schema.
* **Schema validation:** when the caller supplies a Pydantic `response_model`, the adapter requests
  `response_format={"type": "json_schema", ...}` and validates the returned content with
  `model_validate_json`. A 400 rejection becomes `ProviderCapabilityError`; a schema violation
  becomes `ProviderResponseError` without echoing the model text.
* **Error taxonomy:** configuration, authentication, rate limit, server, timeout, transport,
  response, capability, and request errors. Each carries a stable code, HTTP status where
  applicable, retryability, and a sanitized upstream code. Details exclude headers, payloads, and
  credentials.
* **Provenance:** results carry configured and observed model identity (an `observed` flag prevents
  a configured fallback from masquerading as an observation), token usage when reported (missing
  fields stay `None`), latency, HTTP status, request id, and only allow-listed rate-limit headers.
* **Logging:** provider name, operation, attempt, status, error code, latency, and model only. No
  headers, payloads, prompts, completions, or keys.

### Capability probe and data handling

`tools/probe_ai_capabilities.py` reads the process environment. Without `--live` it prints a
redacted summary and makes no request. With `--live` it sends synthetic canary text only and
reports:

* model catalogue, model identifiers, deployment metadata, and context-window facts when the
  endpoint exposes them (`unknown` otherwise; oversized prompts are never used to infer it);
* one chat completion's observed status, latency, usage, finish reason, request id, and rate-limit
  headers;
* schema-constrained JSON support, or the capability error that rejected it;
* embedding availability, model, vector dimension, count, usage, and shape evidence — or an
  explicit unavailability reason;
* timeout behavior from a deliberately tiny deadline, and one invalid request's sanitized error
  shape;
* whether the deployment/model version is identifiable reproducibly.

A live report may contain local endpoint details. It must be written outside the committed tree;
the CLI refuses a repository path unless `--allow-repo-report` is explicit. Sanitized capability
summaries may be committed only with owner approval. PR 1 sends no repository artifacts,
proprietary source, user data, or fixture content to the endpoint. Sending such data requires a
separate owner-approved data-handling configuration; a key's presence is not approval.

## Consequences

* The default application, tests, and CI still acquire no model or network dependency. `httpx` is a
  runtime dependency for the optional live adapter, but importing the registry in fake mode does not
  import it.
* A live configuration is either usable or fails with a concrete error; there is no silent fake
  fallback that would make a missing model look like a passing retrieval result.
* Embeddings are unavailable when the endpoint or configuration lacks them. Chat completions are
  never treated as vectors, and no index is mixed across models or versions.
* The provider layer cannot accept links, mutate review state, or change assurance policy. It is
  retrieval and reasoning support, not assurance authority.
* PR 2 can build an index and a retrieval pipeline on these protocols; PR 3 can use the chat
  provider to explain supplied evidence while deterministic rules remain authoritative.

## Alternatives considered

* **Keep `httpx` dev-only.** Rejected: the live adapter would not run from a normal install. It is
  now a runtime dependency, with a lazy import for the offline path.
* **Use chat completions to synthesize embeddings when no embedding API exists.** Rejected: it
  would fabricate vectors, mix incompatible representations, and make "semantic retrieval" a false
  claim.
* **Fall back to the fake provider when live configuration is incomplete.** Rejected: the caller
  could mistake a fake result for a live observation.
* **Retry all failures, or retry unboundedly because calls are free.** Rejected: auth and malformed
  requests cannot succeed by repetition, and free calls do not imply unlimited capacity.
* **Commit the raw live probe report.** Rejected: it can expose local endpoint details and is not
  needed for reproducibility.

## Revisit when

* PR 2 adopts a vector index: the index must key collections by embedding model and index version,
  and the retrieval evaluation must compare lexical and semantic methods on the same inputs.
* The endpoint's compatibility differs from the OpenAI shapes (for example a different JSON-schema
  field): record the difference in a probe observation and this ADR before changing the adapter.
* Repository artifacts are to be sent to a hosted endpoint: record the owner-approved data-handling
  decision, scope, and retention rules first.
* A real `CandidateDiscovery` provider lands (AI-02): it must satisfy the existing contract tests
  and report its model/index provenance through the existing candidate fields.
