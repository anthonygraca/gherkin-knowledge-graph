# Live provider observation (post-approval)

**Observed at 2026-11-13T16:22:11Z–16:22:22Z**, using the sourced endpoint variables with
synthetic canary text only. No repository artifact was sent. No API key was configured, and no key
or endpoint URL is recorded here.

## Configuration

* The process environment had `CTA_AI_MODE=fake`; the probe and live test were invoked with a
  process-only `CTA_AI_MODE=live`.
* The configured chat model was `deepseek-ai/DeepSeek-V4.1-Flash`.
* The endpoint's `/models` catalogue exposed `deepseek-ai/DeepSeek-V4.1-Flash-1017` with
  `max_model_len=1048576`; the configured value was **not** found, and a chat request using it
  returned HTTP 404 (`provider-capability-error`).
* The observed catalogue model was used as a process-only `CTA_LLM_MODEL` override for the final
  smoke. The user's environment was not changed.
* The embedding endpoint was configured but refused the connection (`ConnectionRefusedError`);
  embeddings are unavailable. No chat output was substituted.

## Observed chat and JSON schema

| Field | Observation |
| --- | --- |
| Chat HTTP status | 200 |
| Observed model | `deepseek-ai/DeepSeek-V4.1-Flash-1017` |
| Finish reason | `stop` |
| Latency | 553.3 ms |
| Usage | 39 prompt + 15 completion = 54 total tokens |
| Text | `canary` (6 chars) |
| Schema-constrained JSON | supported; HTTP 200; parsed `{"ok": true, "label": "canary"}`; 92 total tokens |
| Timeout probe | 5 ms deadline observed as timeout; configured timeout is 10 s |
| Error-format probe | empty `messages` request returned HTTP 200 with no error object; the endpoint accepted it |

The live chat test
`backend/tests/test_live_provider_integration.py::test_live_chat_completion_returns_an_observed_response`
passed (1 passed, 0.55 s) with the observed model. The live embeddings test was **NOT RUN** because
the configured local embedding endpoint was unavailable.

## Probe-design repair

The first probe run used the original `CANARY_TEXT` ("CTA capability canary; ignore this request.")
with `max_tokens=16`. The reasoning model spent the entire budget on `reasoning` and returned
`content: null` with `finish_reason: length`; the adapter correctly rejected the unusable completion
as `provider-response-error`. The probe now asks for a final answer explicitly ("Reply with the
single word: canary.") and allows 64 tokens; the live test uses the same prompt and budget. The
second probe run produced the observations above.

This observation is **post-approval** evidence. It is not covered by the submission-4 approval; the
probe/test change and this evidence were submitted for review 5.

## Reproduce

The raw live report was written outside Git. The sanitized summary is
[`live-summary.json`](live-summary.json). To reproduce, source the endpoint variables and run:

```bash
CTA_AI_MODE=live CTA_LLM_MODEL='deepseek-ai/DeepSeek-V4.1-Flash-1017' \
  uv run --project backend python tools/probe_ai_capabilities.py --live \
  --report /tmp/cta-ai-capabilities.json

CTA_AI_LIVE_TESTS=1 CTA_AI_MODE=live CTA_LLM_MODEL='deepseek-ai/DeepSeek-V4.1-Flash-1017' \
  uv run --project backend pytest \
  backend/tests/test_live_provider_integration.py::test_live_chat_completion_returns_an_observed_response -q
```

The embedding live test remains `NOT RUN` until a local embedding service is listening.
