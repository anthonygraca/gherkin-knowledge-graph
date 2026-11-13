# PR 1 — hosted LLM capability and provider integration

| Field | Value |
| --- | --- |
| Mode / slice | mission; **PR 1** (hosted LLM capability and provider integration) |
| Workstream | A (semantic discovery / provider behavior), with the shared integration owner for settings and docs |
| Repository | `anthonygraca/gherkin-knowledge-graph`; intended remote `origin` verified 2026-11-13T07:24:33Z |
| Starting revision | `60dcc1fc5d0383b6011e7a97a3bf2a110984ff07` (`main`, 2026-11-13T07:24:33Z) |
| Task branch | `feat/30-hosted-ai-provider` (base `60dcc1f`) |
| Served issue | [AI-01 #30](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/30) — **closed**; this is a follow-up on its real-provider boundary, not a reopening or closure claim |
| Implementation commit | `b722ef7076d13ad51f0e1f12596c3adf6c81d8ff` — `feat(ai): [issue #30] add optional hosted AI provider boundary` (local; not pushed) |
| Submission-4 records commit | `59d8644` — `docs(review): [issue #30] record PR 1 provider acceptance` (local; not pushed) |
| Post-approval fix | `d7f9203` — `fix(ai): [issue #30] use a final-answer canary budget` (local; not pushed) |
| Submission-5 records commit | the commit containing this report (record-only; see branch history) |
| GitHub authority | **Broadened by the user on 2026-11-13T16:39:52Z:** “stop after the first PR has been merged.” Branch push, PR creation, and merge are authorized after required checks. No issue creation, issue closure, force push, or deployment is authorized. This is the pre-publication snapshot. |
| Milestone ceiling | M3 for PR 1–PR 3; PR 1 implements no M2 deterministic assurance and does not close M4 |
| OMP model / thinking | installed `vllm/deepseek-ai/DeepSeek-V4.1-Flash-1017`; `max` (usage/cost telemetry not exposed; not claimed) |
| Reviewer | Codex `gpt-6.1-sol`, reasoning effort `high` — **APPROVE** at submission 4 (implementation; [record](../../reviews/AI-01-hosted-provider-review-4.md)) and submission 5 (post-approval live probe/test change and evidence; [record](../../reviews/AI-01-hosted-provider-review-5.md)) |

## Premise check (corrected before claiming)

The mission brief's premise was that M1 "has been completed and independently reviewed." At the
prompt's creation that was **not** true: `docs/reviews/M1-review-attempt-1.md` records an
infrastructure failure with no verdict (workspace out of credits), and the milestone gate was
`NOT SATISFIED`. Current records at invocation are different:

* [`docs/reviews/M1-review-2.md`](../../reviews/M1-review-2.md) (sha256
  `14a2442c1ce17279e951301034a50f0aef5cda162e357fa9e262abd8837bc6d2`) records **APPROVE** at
  review tree `e1497cf`, submission 2 of 7: all 40 M1 criteria and the engineering exit PASS, no
  open major finding.
* [`docs/STATUS.md`](../../STATUS.md) records the M1 gate **SATISFIED** and the approval record merged
  through `c8390a6`; the current `main` at invocation is `60dcc1f`.
* The approval covers the M1 **engineering** gate only. It is not stakeholder validation, a human
  link decision, or release authorization.

PR 1 therefore proceeds under the roadmap's explicit post-M0 parallel allowance for M3 work. It
does not consume M1 graph semantics. PR 3/GraphRAG consumes M1's accepted-link and thread
contracts; the M1 gate is now satisfied, but PR 3 still depends on PR 2 and on a new story issue
with human-reviewed criteria. Test D and M2 integration remain deferred.

## What existed before this slice

The repository already had ingestion of requirements, Gherkin scenarios, source, tests, links, and
evidence; typed accepted/proposed link separation; `GET /api/threads/{artifact_id}`; deterministic
`missing_verification_link`; a fixture-backed `FakeCandidateDiscovery`; a provider registry; and
`POST /api/discovery`. It had **no chat provider, embedding provider, vector index, GraphRAG, live
provider configuration, or model call**. `httpx` was a dev-only dependency. The base-revision
search is retained in [evidence/ai-surface.txt](evidence/ai-surface.txt); the task touches no
`backend/app/assurance/`, `backend/app/api/`, `backend/app/domain/`, or `backend/app/version.py`
files.

The extension points used were the existing provider convention (`app.discovery.registry`) and
`app.settings.Settings`. `CandidateDiscovery` and `ArtifactRepository` were left unchanged: this
slice is a provider layer beneath future retrieval, not a second artifact store and not a real
candidate provider.

## Traceability and scope disposition

AI-01 was closed with the fake-provider slice; its closure record in `docs/STATUS.md` says the real
`CandidateDiscovery` adapter is a later story. This slice serves the **provider-boundary intent** of
AI-01: one typed interface with fake and real adapters, explicit configuration, and no model
requirement in the default path. It does not deliver a real `CandidateDiscovery`, does not claim
AI-01's two CandidateDiscovery scenarios, and does not close AI-02 (#31), AI-03 (#32), or AI-05
(#35). The canonical extraction of AI-01's closed criteria is
[`docs/stories/AI-01.feature`](../../stories/AI-01.feature); the companion records the non-applicable
scope and the existing-check mapping. No new GitHub issue was created because the run holds
local-only authority. If the owner wants a dedicated child task, the prepared title is
`AI-01 follow-up — optional hosted chat and embedding provider boundary`; it would be a child of
#30 and would not close any open AI story.

The acceptance slice for this report is the mission's PR 1 deliverable and exit criterion, expanded
into the `PR1-AC` table below. The AI-01 scenarios are context, not claimed execution evidence.

## Implementation

### Typed boundary (`backend/app/discovery/ai.py`)

* `ChatGenerationProvider` and `EmbeddingProvider` protocols, deliberately separate from
  `CandidateDiscovery`; neither has a link, review, evidence, or assurance operation.
* Pydantic request/result shapes: `ChatMessage`, `ChatCompletion`, `EmbeddingBatch`,
  `TokenUsage`. Results carry configured/observed model identity (`model_observed`), usage when
  reported (missing fields are `None`), latency, HTTP status, request id, and only allow-listed
  rate-limit headers.
* Error taxonomy: configuration, authentication, rate limit, server, timeout, transport, response,
  capability, and request errors, with stable codes, status, retryability, and a sanitized upstream
  code. Details never include headers, payloads, or credentials.
* Schema-constrained output: a caller-provided Pydantic `response_model` becomes an OpenAI
  `response_format` JSON schema request and is re-validated with `model_validate_json`; a rejection
  is a capability error and a violation is a response error without echoing model text.

### Fake providers (`backend/app/discovery/ai_fake.py`)

Deterministic `FakeChatGenerationProvider` (fixed or scripted text, no reported usage) and
`FakeEmbeddingProvider` (hash-derived, dimension-stable vectors). They exist for offline contract
tests and are never retrieval-quality evidence. Neither exposes a write/accept/review method.

### HTTP adapters (`backend/app/discovery/ai_http.py`)

OpenAI-compatible `POST {base}/chat/completions` and `POST {base}/embeddings`. Compatibility is an
observation, not an assumption. The adapter uses an explicit per-request timeout (default 10 s), a
bounded retry budget (default 1, hard cap 5), retries only 429/5xx/timeouts/transport failures,
honors `Retry-After` (seconds or HTTP-date, capped at 5 s), and never retries authentication,
other 4xx, malformed responses, or a rejected schema. `httpx` is a runtime dependency but is
imported only by the live adapter module; fake mode imports no transport (proved by a subprocess
test). The adapter does not follow redirects, validates embedding shape/dimensions/index
consistency, rejects chat-shaped embedding responses, and distinguishes configured from observed
model identifiers.

### Settings and registry (`backend/app/settings.py`, `backend/app/discovery/registry.py`)

Environment names are the mission's starting names: `CTA_AI_MODE` (default `fake`),
`CTA_LLM_BASE_URL`, `CTA_LLM_MODEL`, `CTA_LLM_API_KEY`, `CTA_EMBED_BASE_URL`, `CTA_EMBED_MODEL`,
`CTA_EMBED_API_KEY`, `CTA_VECTOR_BACKEND` (default `memory`), and `CTA_AI_LIVE_TESTS` (default
off). Construction validates combinations without contacting the network: live mode requires the
chat URL/model; embedding URL/model must be set together; unknown modes/backends are rejected. API
keys are excluded from `repr`; only presence is reported. `ProviderRegistry.chat()` and
`.embeddings()` build fake providers in fake mode, real adapters lazily in live mode, and return
`None` for live embeddings when no embedding endpoint is configured. There is no silent fallback.

### Capability probe (`backend/app/discovery/capabilities.py`, `tools/probe_ai_capabilities.py`)

Without `--live`, the CLI reads the process environment, prints a redacted summary, and makes no
request. With `--live` it sends synthetic canary text only and reports model catalogue/model IDs,
deployment metadata, context-window facts or `unknown`, one chat observation (status, latency,
usage availability, finish reason, request id, rate-limit headers), schema-constrained JSON support,
embedding availability/model/dimension/count/shape or an explicit unavailability reason, timeout
behavior from a deliberately tiny deadline, one invalid request's sanitized error shape, and the
unknown concurrency limit without stress-testing. A live report may contain local endpoint details;
the CLI refuses a repository path unless `--allow-repo-report` is explicit. The report is sanitized
for credentials and URL userinfo/query.

### Documentation

[ADR 0007](../../adr/0007-ai-provider-boundary.md) records the provider interface, configuration,
timeout/retry policy, data-handling decision, credential redaction, and why the hosted provider is
optional. [`docs/setup.md`](../../setup.md) has the operator commands; `docs/architecture.md` lists the
new modules and their status; ADR 0006 cross-references the provider decision. No API shape,
schema version, fixture, or assurance rule changed.

## Acceptance evidence (`PR1-AC`)

| ID | Observable requirement | Check / probe | Result |
| --- | --- | --- | --- |
| PR1-AC-1 | Existing application and offline suite run with no AI configuration; fake providers are the default; fake mode does not import the HTTP transport. | `test_default_settings_are_fake_and_offline`, `test_fake_registry_returns_offline_providers`, `test_fake_mode_import_does_not_import_the_http_transport`; full suite and network-denied suite | PASS |
| PR1-AC-2 | Settings read the mission environment names, default offline, validate required combinations at construction, and never render keys. | `test_live_mode_requires_llm_configuration`, `test_embedding_configuration_must_be_complete`, `test_unknown_mode_and_vector_backend_are_rejected`, `test_api_keys_are_excluded_from_repr` | PASS |
| PR1-AC-3 | Real chat adapter has explicit timeout, bounded retry, Retry-After handling, schema validation, error taxonomy, and safe logging. | `test_chat_request_uses_configured_model_key_and_observes_response`, `test_chat_retries_a_rate_limit_and_honors_retry_after`, `test_retry_after_is_capped`, `test_bounded_retry_stops_after_the_budget`, `test_authentication_failure_is_not_retried_and_does_not_echo_the_key`, `test_timeout_is_retryable_and_bounded`, `test_malformed_success_is_not_retried`, `test_schema_constrained_completion_sends_and_validates_json_schema`, `test_schema_violation_is_a_response_error`, `test_schema_rejection_is_a_capability_error`, `test_logs_sanitize_url_credentials` (success and 401) | PASS |
| PR1-AC-4 | Separate real embedding adapter validates vector shape/dimension, rejects chat-shaped output, and is unavailable when not configured. | `test_embeddings_use_the_embeddings_endpoint_and_report_dimensions`, `test_embedding_rejects_invalid_index_types`, `test_embedding_rejects_unrepresentable_numbers`, `test_embedding_rejects_mixed_index_shapes`, `test_embedding_rejects_a_chat_shaped_response`, `test_embedding_404_is_a_capability_error_and_is_not_retried`, `test_embedding_dimension_mismatch_is_a_response_error`, `test_live_registry_without_embeddings_reports_unavailable`, `test_probe_reports_embeddings_unavailable_without_substituting_chat` | PASS |
| PR1-AC-5 | Probe CLI reports configuration without contact; `--live` is explicit; it reports the required capability fields with synthetic canary text and sanitizes/refuses in-repo reports. | `test_probe_offline_fake_mode_never_contacts_the_endpoint`, `test_probe_records_observed_capabilities`, `test_probe_reports_an_absent_embedding_endpoint`, `test_probe_reports_json_schema_unsupported`, `test_probe_sanitizes_urls_in_model_metadata`, `test_probe_sanitizes_dynamic_model_id_keys`, `test_fake_mode_probe_report_is_sanitized`, `test_offline_summary_is_sanitized`, `test_probe_does_not_claim_identity_from_an_unrelated_catalogue`, `test_probe_cli_offline_makes_no_probe`, `test_probe_cli_offline_sanitizes_model_credentials`, `test_probe_cli_offline_import_does_not_import_the_transport`, `test_probe_cli_refuses_a_repository_report`, `test_sanitizer_redacts_dynamic_dictionary_keys`, `test_sanitizer_redacts_credentials_and_url_query`; manual CLI runs below | PASS (offline/mocked); live **NOT RUN** |
| PR1-AC-6 | Offline contract tests cover fake/real adapters and provider failure classes; live integration is opt-in and skips by default; the default suite needs no network. | 52 provider tests passed, 2 live tests skipped; full suite 285 passed, 2 skipped; network-denied suite 285 passed with a denied socket probe | PASS |
| PR1-AC-7 | ADR and docs cover interface, configuration, timeout/retry, data handling, redaction, optionality; no API/schema/assurance change. | ADR 0007, setup, architecture; `git status` shows no changes under `backend/app/assurance/`, `backend/app/api/`, `backend/app/domain/`, or `version.py`; `SCHEMA_VERSION` unchanged | PASS |
| PR1-AC-8 | Traceability and publication state are recorded; the slice does not claim a later story, milestone closure, or hosted inference. | Issue #30 verified; branch/base recorded; no push/PR/merge; post-approval live chat/schema observed, embeddings `NOT RUN`; M1 premise corrected above | PASS (local-only) |

## Checks at the final snapshot

All commands were run from the repository root at the base/branch above. Logs are retained under
[`evidence/`](evidence/); earlier checkpoint logs (`check-1-*`, `check-final-*`) are retained but
are not the post-repair evidence. The approved implementation snapshot is `check-repair-3-*`; the
post-approval probe/test change is `check-live-repair-*`.

```text
uv sync --project backend --frozen                       exit 0  (25 packages checked)
uv run --project backend pytest backend/tests -q         exit 0  285 passed, 2 skipped
unshare -rn backend/.venv/bin/python -m pytest -q        exit 0  285 passed, 2 skipped
  socket probe under the same namespace                  DENIED  OSError: [Errno 101] Network is unreachable
uv run --project backend python tools/fixturectl.py verify  exit 0  reproducible and current
uv run --project backend ruff check .                    exit 0
uv run --project backend ruff format --check .           exit 0  (57 files)
git diff --check                                         exit 0
uv run --project backend python tools/probe_ai_capabilities.py
                                                         exit 0  probed=false, mode=fake
uv run --project backend python tools/probe_ai_capabilities.py --live
                                                         exit 2  expected: fake mode refuses live
```

Post-approval live evidence (process-only `CTA_AI_MODE=live`; observed catalogue model override):

```text
CTA_AI_MODE=live CTA_LLM_MODEL=deepseek-ai/DeepSeek-V4.1-Flash-1017 \
  probe_ai_capabilities.py --live --report /tmp/...     exit 0  11 s
  chat: HTTP 200, finish=stop, 54 tokens, 553.3 ms, text=canary
  json_schema: HTTP 200, parsed, 92 tokens
  models: HTTP 200, context=1048576
  embeddings: unavailable (provider-transport-error; connection refused)
CTA_AI_LIVE_TESTS=1 ... pytest ...::test_live_chat_completion_returns_an_observed_response
                                                         exit 0  1 passed (0.55 s)
```

The 2 skipped tests are the opt-in live integration tests. The network-denied suite used the venv
interpreter under `unshare -rn`; the denied socket probe is retained in
[`evidence/network-probe.log`](evidence/network-probe.log). This proves the default suite does not
need network, not that a hosted endpoint is reachable.

## Live provider smoke — RUN (post-approval observation)

The endpoint variables were supplied after the submission-4 approval. The process environment had
`CTA_AI_MODE=fake`; the probe and live test were invoked with process-only `CTA_AI_MODE=live`.
No API key was configured; no key or endpoint URL is recorded in the committed evidence. Only
synthetic canary text was sent.

**Configuration observation.** The configured chat model was `deepseek-ai/DeepSeek-V4.1-Flash`.
The endpoint's `/models` catalogue exposed `deepseek-ai/DeepSeek-V4.1-Flash-1017` with
`max_model_len=1048576`; the configured value was **not found**, and a chat request using it
returned HTTP 404 (`provider-capability-error`). The final smoke used the observed catalogue model as
a process-only `CTA_LLM_MODEL` override; the user's environment was not changed.

| Observation | Result |
| --- | --- |
| `/models` | HTTP 200; model `deepseek-ai/DeepSeek-V4.1-Flash-1017`; context length 1,048,576; 67.3 ms |
| Chat completion | HTTP 200; model observed; `finish_reason=stop`; 553.3 ms; 39 prompt + 15 completion = 54 tokens; text `canary` |
| Schema-constrained JSON | supported; HTTP 200; parsed `{"ok": true, "label": "canary"}`; 92 total tokens |
| Embeddings | **unavailable**; configured local endpoint refused the connection (`provider-transport-error`); no chat substitution |
| Timeout | 5 ms probe deadline observed as timeout; configured timeout 10 s |
| Error format | empty `messages` request returned HTTP 200 with no error object; the endpoint accepted it |
| Live chat test | `test_live_chat_completion_returns_an_observed_response` — **1 passed** (0.55 s) |
| Live embeddings test | **NOT RUN** — local embedding endpoint unavailable |

**Probe-design repair.** The first live probe used the original "ignore this request" canary with
`max_tokens=16`. The reasoning model spent the budget on `reasoning` and returned `content: null`
with `finish_reason=length`; the adapter correctly rejected the unusable completion as
`provider-response-error`. The probe now asks for a final answer explicitly ("Reply with the single
word: canary.") and allows 64 tokens; the live test uses the same prompt and budget. This was a
post-approval probe/test change, reviewed and approved at submission 5; the submission-4 approval
did not cover it or the live evidence.

Sanitized evidence: [capabilities/live-observation.md](capabilities/live-observation.md) and
[capabilities/live-summary.json](capabilities/live-summary.json). The raw live report (which may
contain local endpoint details) remains outside Git. Exact commands:

```bash
CTA_AI_MODE=live CTA_LLM_MODEL='deepseek-ai/DeepSeek-V4.1-Flash-1017' \
  uv run --project backend python tools/probe_ai_capabilities.py --live \
  --report /tmp/cta-ai-capabilities.json
CTA_AI_LIVE_TESTS=1 CTA_AI_MODE=live CTA_LLM_MODEL='deepseek-ai/DeepSeek-V4.1-Flash-1017' \
  uv run --project backend pytest \
  backend/tests/test_live_provider_integration.py::test_live_chat_completion_returns_an_observed_response -q
```

The probe sends synthetic canary text only. Repository artifacts must not be sent until a documented
owner-approved data-handling configuration exists (ADR 0007).

## Independent review

**Final verdict: APPROVE, submission 4 of 7** — all PR1-AC criteria supported within the documented
offline/mocked scope; PR1-R1/R5 closed; PR1-R2/R3/R4 remain closed; no new findings. The approval
does not establish live endpoint compatibility or close a later story or milestone.

### Submission 1 of 7 — REQUEST_CHANGES

Reviewer: Codex `gpt-6.1-sol`, reasoning `high`, read-only, session
`01a1d3d2-52f6-78b3-861b-5c22926f382c`; 2026-11-13T07:32:17Z → 07:35:26Z (189 s), exit 0, 91,486
CLI-reported tokens. Packet: [`AI-01-hosted-provider-review-prompt.md`](../../reviews/AI-01-hosted-provider-review-prompt.md),
sha256 `26733dbd222c71ce55ac250bb93449cca29650f367c373e135467734b89f047b`. Verdict record:
[`AI-01-hosted-provider-review.md`](../../reviews/AI-01-hosted-provider-review.md).

| Finding | Severity | Observed defect | Repair | Recheck |
| --- | --- | --- | --- | --- |
| PR1-R1 | Major | The probe sanitizer only handled keys ending in `_url`; a URL in `models.deployment_metadata.root` retained userinfo/query, and the `_url` branch bypassed configured-secret replacement. | All report strings now pass through URL sanitization and secret replacement together; `sanitize_url` is robust to malformed input. | `test_probe_sanitizes_urls_in_model_metadata`; full probe text contains no password, query token, or configured key. |
| PR1-R2 | Major | Invalid index types (for example `"1"`/`"0"` or booleans) were treated as absent indices, so vectors were returned in response order and could associate with the wrong input. | The adapter now distinguishes an absent index key from an invalid one and rejects any supplied non-integer or boolean index. | `test_embedding_rejects_invalid_index_types` (string and boolean cases). |
| PR1-R3 | Major | `deployment_identifiable` was true for any non-empty catalogue, and the schema probe reported the configured fallback as an observed model. | Identification now requires the configured model to be found with metadata; chat, schema, and embedding observed-model fields honor `model_observed` and stay unknown otherwise. | `test_probe_does_not_claim_identity_from_an_unrelated_catalogue`. |
| PR1-R4 | Minor | A huge integer embedding value raised raw `OverflowError`, escaping the provider error taxonomy. | Numeric conversion now rejects non-numeric, unrepresentable, and non-finite values as `ProviderResponseError`. | `test_embedding_rejects_unrepresentable_numbers`. |

The reviewer independently ran 27 existing tests, Ruff lint, formatting checks, and
`git diff --check`; all passed. Hosted compatibility remained **NOT RUN**. Proposal/accepted/
evidence separation and deterministic-assurance isolation were confirmed; SCN-901/902 remained
contextual and unclaimed.

### Submission 2 of 7 — REQUEST_CHANGES

Reviewer: same model/effort, read-only, session `01a1d3de-2e54-7b01-8a65-4d70e5ec6ef0`;
2026-11-13T07:45:15Z → 07:47:08Z (113 s), exit 0, 92,552 CLI-reported tokens. Packet:
[`AI-01-hosted-provider-review-prompt-2.md`](../../reviews/AI-01-hosted-provider-review-prompt-2.md),
sha256 `02f3c22076216cc8d0dcff74d9daa03936fb07a18ec44edf8980c4db61135dee`. Record:
[`AI-01-hosted-provider-review-2.md`](../../reviews/AI-01-hosted-provider-review-2.md).

PR1-R2, PR1-R3, and PR1-R4 were **closed**. PR1-R1 remained open because credential redaction had
two bypasses: dynamic dictionary keys (a model URL used as a `models.context_lengths` key) and the
offline CLI summary path. Repair:

* Moved the report sanitizer to `app/discovery/ai.py` (no `httpx` import) so the offline CLI can use
  it without acquiring the transport.
* Sanitizes dynamic dictionary keys as well as values, with collision suffixes; every CLI output
  path (offline and live, stdout and `--report`) applies it.
* Added `test_probe_sanitizes_dynamic_model_id_keys`,
  `test_probe_cli_offline_sanitizes_model_credentials`,
  `test_sanitizer_redacts_dynamic_dictionary_keys`, and
  `test_probe_cli_offline_import_does_not_import_the_transport`.

### Submission 3 of 7 — REQUEST_CHANGES

Reviewer: same model/effort, read-only, session `01a1d3e6-7dca-78c3-a371-a17262f82609`;
2026-11-13T07:54:20Z → 07:57:09Z (169 s), exit 0, 79,113 CLI-reported tokens. Packet:
[`AI-01-hosted-provider-review-prompt-3.md`](../../reviews/AI-01-hosted-provider-review-prompt-3.md),
sha256 `b8233550b3807dc61505a7f73ec69dd053c76477782336184775c75b112ffd97`. Record:
[`AI-01-hosted-provider-review-3.md`](../../reviews/AI-01-hosted-provider-review-3.md).

PR1-R2/R3/R4 remained closed. PR1-R1 remained open for two report-return paths: the fake-mode return
from `probe_capabilities` and the public `offline_summary` helper were not sanitized. PR1-R5 was a
new major finding: provider logging replaced configured secrets but did not remove URL credentials/
query, so the configured model URL could appear in success and 401 logs. Repair:

* `_base_summary`, the fake-mode `probe_capabilities` return, `offline_summary`, and the CLI's
  `_offline_summary` now sanitize at construction; every output path is covered.
* `ai_http._log` uses `sanitize_text` (URL credentials/query plus configured secrets) for every
  logged field; upstream error codes use the same sanitizer.
* Added `test_fake_mode_probe_report_is_sanitized`, `test_offline_summary_is_sanitized`, and
  `test_logs_sanitize_url_credentials` (success and 401).

### Submission 4 of 7 — APPROVE

Reviewer: same model/effort, read-only, session `01a1d3ef-6d7f-7a70-8f16-25d95fb41265`;
2026-11-13T08:04:05Z → 08:06:16Z (131 s), exit 0, 88,098 CLI-reported tokens. Packet:
[`AI-01-hosted-provider-review-prompt-4.md`](../../reviews/AI-01-hosted-provider-review-prompt-4.md),
sha256 `760b974e4e4b5bf18153e26347026f7815a4c276396ed4593d6f5d59bf2bbf50`. Record:
[`AI-01-hosted-provider-review-4.md`](../../reviews/AI-01-hosted-provider-review-4.md).

PR1-R1 and PR1-R5 were **closed**; PR1-R2/R3/R4 remained closed; no new findings. The reviewer
independently ran 34 pytest checks plus 18 direct read-only invocations, and inspected the retained
285 passed / 2 skipped, network-denial, and fixture-verification evidence. Hosted compatibility
remains **NOT RUN**. This approval covers the provider-boundary slice only; it does not close AI-01
(already closed), AI-02/AI-03/AI-05, M1, or any later milestone.

The submission-4 approval covers the implementation snapshot `b722ef7`. After that approval, the
live endpoint was supplied; the probe's canary prompt/budget and the live test's prompt/budget were
changed so a reasoning model can return a final answer. That post-approval probe/test change and
the live evidence were reviewed and approved at submission 5. Record updates after review 5 are
limited to the report, review records, prompt/metrics/retrospective records, and `docs/STATUS.md`.

### Submission 5 of 7 — APPROVE

Reviewer: same model/effort, read-only, session `01a1d5bd-f1bc-7c71-bf92-84bc65844181`;
2026-11-13T16:29:16Z → 16:31:51Z (155 s), exit 0, 85,412 CLI-reported tokens. Packet:
[`AI-01-hosted-provider-review-prompt-5.md`](../../reviews/AI-01-hosted-provider-review-prompt-5.md),
sha256 `e549b736b036f6594f5cef552c3021577d301b074ed8f8837e5211667a5e743a`. Record:
[`AI-01-hosted-provider-review-5.md`](../../reviews/AI-01-hosted-provider-review-5.md).

The reviewer accepted the explicit canary prompt/64-token budget and the sanitized live evidence:
no new findings; PR1-R1…R5 remain closed. The configured model still returned 404; chat and
schema-constrained JSON succeeded only with the process-only observed catalogue model; embeddings
remained unavailable, so the live embeddings test is **NOT RUN**. This approval does not establish
general live compatibility or a tested capacity guarantee.

## Changed files

Modified:

* `backend/app/settings.py` — AI configuration/validation, secret-safe repr.
* `backend/app/discovery/registry.py` — lazy chat/embedding provider construction.
* `backend/app/discovery/__init__.py` — export protocols/fakes without importing the transport.
* `backend/pyproject.toml`, `backend/uv.lock` — `httpx` becomes a runtime dependency.
* `docs/adr/0006-deferred-decisions.md`, `docs/architecture.md`, `docs/setup.md` — cross-reference
  and operator documentation.

New:

* `backend/app/discovery/ai.py`, `ai_fake.py`, `ai_http.py`, `capabilities.py`.
* `backend/tests/test_ai_providers.py`, `test_live_provider_integration.py`.
* `tools/probe_ai_capabilities.py`.
* `docs/adr/0007-ai-provider-boundary.md`.
* `docs/stories/AI-01.feature`, `docs/stories/AI-01.md`.
* `docs/reports/omp-rag-pr1/` (this record and evidence).

Unrelated pre-existing change preserved and **not staged**: `.gitignore` (adds `prompts/`).

## Local commit traceability

| Commit | Subject | Served issue | Scope / evidence |
| --- | --- | --- | --- |
| `b722ef7` | `feat(ai): [issue #30] add optional hosted AI provider boundary` | [#30](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/30) | Provider boundary, adapters, settings, probe, tests, ADR/docs, AI-01 feature/companion. This is the implementation snapshot approved at review submission 4 of 7. |
| `59d8644` | `docs(review): [issue #30] record PR 1 provider acceptance` | [#30](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/30) | Submission-4 report, prompt/call log, metrics, retrospective, sanitized capability evidence, four review records/packets, and `docs/STATUS.md`. Record-only after approval. |
| `d7f9203` | `fix(ai): [issue #30] use a final-answer canary budget` | [#30](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/30) | Post-approval probe canary prompt/64-token budget and live test prompt/budget, reviewed and approved at submission 5. |
| submission-5 records | `docs(review): [issue #30] record PR 1 live evidence` | [#30](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/30) | This report update, review 5 record/packet, live capability evidence, prompt/metrics/retrospective updates, and `docs/STATUS.md`. The commit containing this report is identified by branch history. |

These commits were prepared locally. The user authorized publication on 2026-11-13T16:39:52Z
(“stop after the first PR has been merged”). The PR number, checks, merge commit, and merge outcome
are recorded in GitHub and the final run summary; this report is the pre-publication snapshot and is
not rewritten to claim a future merge. The unrelated `.gitignore` working-tree change was preserved
and not staged.

## Remaining risks and limitations

* **Live compatibility is partial.** The observed catalogue model
  (`deepseek-ai/DeepSeek-V4.1-Flash-1017`) returned a chat completion and schema-constrained JSON;
  the configured model value was not the catalogue identifier and returned 404. Embeddings are
  unavailable (connection refused). No general endpoint, model, context-window, or concurrency
  compatibility claim is made.
* **No semantic retrieval or GraphRAG yet.** PR 1 provides providers only; there is no index,
  vector store, retrieval pipeline, answer endpoint, UI, or graph expansion. Retrieval quality is
  unmeasured.
* **No real `CandidateDiscovery`.** `POST /api/discovery` remains fixture-backed. AI-02/AI-03/
  AI-05 remain open and are not satisfied by a hosted embedding adapter.
* **Data handling.** Only synthetic canary text is allowed to the hosted endpoint in PR 1. Sending
  repository artifacts requires a separate owner-approved decision.
* **No concurrency claim.** The probe records `concurrency_limit: unknown` and does not stress-test
  a shared endpoint. Free calls are not treated as unlimited capacity.
* **Live test is opt-in.** The default suite proves the offline contract and mocked transport
  behavior. The chat live test was run manually and passed; the embeddings live test was not run
  because the endpoint was unavailable.
* **`httpx` runtime dependency.** It is imported only by the live adapter module; fake mode import
  isolation is tested, but the dependency is still installed by default.
* **Approval scope.** The independent approval covers the offline/mocked provider-boundary slice;
  live compatibility, retrieval quality, GraphRAG, and later stories remain outside it.

## PR 2 brief — artifact-aware RAG (independently assignable, not started)

**Slice ID:** PR 2. **Workstream:** A, with the shared integration owner for `app/domain/`,
`app/api/`, settings, docs, and fixtures. **Milestone ceiling:** M3; no M2 assurance.

**Issue mapping and prerequisites.** Use AI-02 [#31](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/31)
(local EmbeddingGemma inference), AI-03 [#32](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/32)
(revision-aware incremental refresh), and AI-05 [#35](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/35)
(labeled retrieval evaluation) only for the criteria actually delivered. AI-04 #34 is closed; the
additive discovery extension serves its proposal behavior without reopening it. Refine canonical
`docs/stories/AI-02.feature`, `AI-03.feature`, and `AI-05.feature` from the issues before
implementation, with stable scenario IDs and a human-review disposition. Do not call a hosted
embedding adapter "AI-02 local inference." If artifact-aware RAG needs scope not covered by those
stories, create a real story issue (or prepare exact text and wait for issue-write authority); do
not make an unlinked commit.

**Scope.** Build a baseline-aware index over existing ingested artifacts, not a second parser:
requirement text, Gherkin feature/rule/scenario units with tags and steps, and source/test symbols
or files as coherent units. Each unit carries artifact ID/type, source URI/locator, revision,
content hash, requirement/scenario/test identifiers, embedding model, index version, and baseline.
Use an in-memory vector store. Resolve the baseline to a commit before retrieval; never mix models
or index versions. Update on content-hash change and remove units absent from the selected
snapshot. Retrieval: normalize the query from authoritative artifact content, produce a
deterministic lexical baseline, produce embedding retrieval when a real/fake provider is
configured, optionally rerank with the LLM with recorded provenance, and return ranked candidates
with scores/method/sources/uncertainty. Extend `POST /api/discovery` only additively; preserve
fields and provider semantics; bump `SCHEMA_VERSION` and docs if the shape changes.

**Evidence and gates.** Offline deterministic fixtures for baseline filtering, cross-baseline
reporting, incremental refresh, model/index isolation, candidate schema, and no accepted-link/
assurance mutation. REQ-002 produces useful provenance-rich candidates without changing accepted
links or assurance status. Produce an initial lexical-vs-embedding evaluation on the labeled
fixtures as a measurement, not an acceptance claim. PR 1 must be approved; M1's gate is satisfied;
no M2 implementation; hosted embeddings require the owner-approved data-handling decision unless
only synthetic/fixture inputs are used.

## PR 3 brief — GraphRAG evidence retrieval (blocked on a real story issue, not started)

**Slice ID:** PR 3. **Workstream:** A, with shared integration. **Milestone ceiling:** M3; no M2
implementation.

**Gate.** GraphRAG is new scope beyond AI-01…AI-05. The repository has no story issue or canonical
`.feature` for it, and this run has local-only GitHub authority. Before implementation, create or
identify a real story issue (suggested title: `AI-06 — GraphRAG evidence-grounded explanations over
accepted traceability links`) with a reviewed `.feature` and human-reviewed acceptance criteria.
Until that exists, prepare the issue text and stop dependent implementation; do not invent an issue
number or commit unlinked work. M1's milestone gate is now satisfied, so the M1 dependency is met;
PR 2 remains a dependency.

**Scope.** Reuse M1's accepted-link and thread contracts; do not add a graph database. Resolve the
selected baseline to its commit; identify the requirement by stable identity, then lexical/vector
fallback with the method reported; expand only accepted links; keep proposed links in a separate
labeled result set; retrieve scenarios, implementation, tests, and execution evidence with
revisions/hashes; record every graph path (artifact sequence, link IDs, review state, baseline);
exclude non-matching evidence unless a cross-baseline comparison is explicit; build a bounded
context and label repository text as untrusted data. The LLM explains only what the supplied
evidence establishes; validate every cited artifact/link/evidence ID against the retrieved set and
reject or downgrade unsupported citations. Deterministic assurance rules decide findings; the LLM
never re-derives or overrides policy. Return a typed response with authoritative graph context and
semantic candidates separated, plus question, baseline, answer, referenced IDs, source URIs,
revisions, retrieval method, model/index provenance, and explicit uncertainty/abstention. A new
endpoint must be additive and versioned and name its owning story; do not hide GraphRAG in the
discovery endpoint.

**Evidence and gates.** REQ-001's authoritative answer path matches the M1 thread with accepted
link IDs, revisions, and EV-001; REQ-002 abstains from a verification claim and lists proposals
separately; prompt-injection probes cannot create links, evidence, or unsupported citations;
finding conclusions remain deterministic. Tests cover accepted-only expansion, proposed-link
exclusion, baseline filtering, citation validation, abstention, and no link/evidence writes.
PR 1 and PR 2 approved; new issue/feature reviewed; hosted LLM use over repository artifacts needs
the owner-approved data-handling decision (otherwise fake/offline only). Test D waits for M2.
