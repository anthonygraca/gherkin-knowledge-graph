# PR 1 implementation review — submission 5 of 7 (post-approval live evidence)

## 1. Scope and prior verdict

**Slice:** PR 1 — hosted LLM capability and provider integration (RAG mission).
**Base / branch:** `60dcc1fc5d0383b6011e7a97a3bf2a110984ff07` (`main`) /
`feat/30-hosted-ai-provider`. **GitHub authority:** local-only; no issue creation, push, PR, or
merge. **Implementation commit:** `b722ef7` — `feat(ai): [issue #30] add optional hosted AI
provider boundary`. **Records commit:** `59d8644`. **Bookkeeping commit:** `c113ae9`.

**Prior verdict:** submission 4 — **APPROVE**
([`AI-01-hosted-provider-review-4.md`](AI-01-hosted-provider-review-4.md), sha256
`6ffd84693de8e9d6cee7285bfc1d609f19f5b68fe9cfb6883421bccc4306baf6`; packet 4 sha256
`760b974e4e4b5bf18153e26347026f7815a4c276396ed4593d6f5d59bf2bbf50`). That approval covers the
provider-boundary implementation and explicitly leaves hosted compatibility **NOT RUN**. It does
not cover the post-approval probe/test change or the live evidence in this packet.

The served issue and scope are unchanged: AI-01 #30 is closed; this is a follow-up on its
real-provider boundary, not a claim of its CandidateDiscovery scenarios or of AI-02/AI-03/AI-05.
M1's engineering gate is satisfied at `M1-review-2.md`; PR 1 does not consume M1 graph semantics.
PR 3 still needs PR 2 and a new story issue/feature; Test D waits for M2.

## 2. Post-approval change

After submission 4 approved the implementation, the endpoint variables were supplied. The first
live probe used the original `CANARY_TEXT` ("CTA capability canary; ignore this request.") with
`max_tokens=16`. The reasoning model spent the whole budget on `reasoning` and returned
`content: null` with `finish_reason: length`. The adapter correctly rejected the unusable completion
as `provider-response-error`; that was a probe-design issue, not a provider defect.

Change:

* `backend/app/discovery/capabilities.py`: use
  `CANARY_CHAT_PROMPT = "Reply with the single word: canary."` and `max_tokens=64` for the chat
  capability check. Add a comment explaining that a reasoning model can exhaust a small budget
  before producing content.
* `backend/tests/test_live_provider_integration.py`: same prompt and 64-token budget for the
  opt-in live chat test.
* No provider adapter, settings, registry, API, domain, assurance, schema, fixture, or production
  behavior changed.

## 3. Live observation (sanitized)

The user's process environment had `CTA_AI_MODE=fake`; the probe and live test were invoked with
process-only `CTA_AI_MODE=live`. No API key was configured. No key or endpoint URL is recorded in
this packet. Only synthetic canary text was sent.

**Configuration observation:** the configured chat model was `deepseek-ai/DeepSeek-V4.1-Flash`. The
endpoint catalogue exposed `deepseek-ai/DeepSeek-V4.1-Flash-1017` with `max_model_len=1048576`; the
configured value was not found and returned HTTP 404 (`provider-capability-error`). The final smoke
used the observed catalogue model as a process-only `CTA_LLM_MODEL` override; the user's environment
was not changed.

| Observation | Result |
| --- | --- |
| `/models` | HTTP 200; `deepseek-ai/DeepSeek-V4.1-Flash-1017`; context length 1,048,576; 67.3 ms |
| Chat completion | HTTP 200; model observed; `finish_reason=stop`; 553.3 ms; 39 prompt + 15 completion = 54 tokens; text `canary` |
| Schema-constrained JSON | supported; HTTP 200; parsed `{"ok": true, "label": "canary"}`; 92 total tokens |
| Embeddings | **unavailable**; configured local endpoint refused the connection (`provider-transport-error`); no chat substitution |
| Timeout | 5 ms probe deadline observed as timeout; configured timeout 10 s |
| Error format | empty `messages` request returned HTTP 200 with no error object; the endpoint accepted it |
| Live chat test | `test_live_chat_completion_returns_an_observed_response` — **1 passed** (0.55 s) |
| Live embeddings test | **NOT RUN** — local embedding endpoint unavailable |

Sanitized evidence:
`docs/reports/omp-rag-pr1/capabilities/live-observation.md`,
`docs/reports/omp-rag-pr1/capabilities/live-summary.json`,
`docs/reports/omp-rag-pr1/evidence/live-test-chat.log`, and
`docs/reports/omp-rag-pr1/evidence/live-test-chat-metadata.txt`. The raw live report (which may
contain local endpoint details) remains outside Git.

## 4. Snapshot manifest

```text
e4c4246eedd363f76299bedec9e49ecaf6b1ecaa47a028293a1829796547d0d8  backend/app/discovery/ai.py
abf4170c82603cd819df12f8fc7786aefaac9b7f551ddbc9b9ccca2098d09191  backend/app/discovery/ai_fake.py
3ad0e0c62085de0ae084074f2e291f41f9d85b61bde902d015d820dbac8a818b  backend/app/discovery/ai_http.py
01cf3f22cdd8fe7e47cb8c6b4c7d453cb8cf2ed7d172d503798baba82f076464  backend/app/discovery/capabilities.py
bc2d1cf6d75f74e52651b9679e1c41bb68d9a76843bb52135cf0a61a4802a997  backend/app/discovery/__init__.py
7b4fa24de134806590a8cd8626df1a91c6a6b9b381fa85eee6138fefcfb9c57b  backend/app/discovery/registry.py
93a293342a93be9974b91ae40b1b02bf2b9c6f3a55fd871151961ff9aaf880f1  backend/app/settings.py
805b2fa79111e2b62c7f72b9eb1bd022dc0891f10ca4e9c4419d45b49af0b63d  backend/pyproject.toml
d2acd9c9398df945cde02915fc4bd284e21f76ca5d5a51d0ebb1b6922c19994d  backend/tests/test_ai_providers.py
672062738b68ddfb812145830ca8c6b6eb8d7cd84f74573635b01e74ea9f7ffd  backend/tests/test_live_provider_integration.py
02106d33af5d3c4de0549f9fc20ef8466ef19fd256a7cd7b7439b9c03c9d8e0e  backend/uv.lock
5e29bbc004de6110f13339b87e8dfc7b94ab31a5a42ccc4f2093b294b0039e58  tools/probe_ai_capabilities.py
```

Compared with the submission-4 snapshot, only `capabilities.py` and
`test_live_provider_integration.py` changed. The provider adapters, settings, registry, CLI, and
offline tests retain their approved hashes. The cumulative diff remains
`git diff b722ef7 -- . ':(exclude).gitignore'` for the post-approval change; the earlier cumulative
diff remains `git diff 60dcc1f -- . ':(exclude).gitignore'`. `.gitignore` is unrelated and
unmodified by this task.

## 5. Evidence at the post-approval change

```text
uv sync --project backend --frozen                       exit 0  (25 packages checked)
uv run --project backend pytest backend/tests -q         exit 0  285 passed, 2 skipped
unshare -rn backend/.venv/bin/python -m pytest -q        exit 0  285 passed, 2 skipped
  socket probe under the same namespace                  DENIED  OSError: [Errno 101] Network is unreachable
uv run --project backend python tools/fixturectl.py verify  exit 0  reproducible and current
uv run --project backend ruff check .                    exit 0
uv run --project backend ruff format --check .           exit 0  (57 files)
git diff --check                                         exit 0
probe_ai_capabilities.py (offline)                       exit 0  probed=false, mode=fake
probe_ai_capabilities.py --live (observed model)         exit 0  11 s; chat/schema/model observations above
  live chat test                                         exit 0  1 passed (0.55 s)
  live embeddings test                                   NOT RUN (endpoint unavailable)
```

The two skipped tests in the default suite are the opt-in live integration tests. Logs:
`docs/reports/omp-rag-pr1/evidence/check-live-repair-*`, `live-test-chat.log`, and
`live-test-chat-metadata.txt`. No endpoint was contacted by the default suite; the live probe was an
explicit process-only override with synthetic canary text.

## 6. Reviewer instructions

You are the independent CTA implementation reviewer using GPT-6.1 Sol high. Decide whether this
exact post-approval snapshot satisfies the supplied mission slice, every applicable Gherkin
criterion, and the repository invariants. Treat OMP summaries and test results as claims to check
against the packet and targeted source inspection. Check proposal/accepted/evidence separation, no
LLM authority in deterministic assurance, revision and content-hash provenance, baseline and model
isolation, offline defaults, bounded retry/timeout and redaction behavior, untrusted-retrieved-text
handling, citation validation, honest 501/error behavior, independent oracle expectations, and
generated-file discipline. Do not demand implementation of a later milestone. Do not edit files,
implement repairs, regenerate fixtures, commit, or delegate. Ask OMP for missing runtime evidence;
distinguish observed defects from hypotheses. Return APPROVE, REQUEST_CHANGES, or NEEDS_INPUT with
findings stable by ID. The submission-4 implementation approval remains; this review covers the
probe/test prompt-and-budget change and the sanitized live chat/schema evidence. PR1-R1/R5 remain
closed; PR1-R2/R3/R4 remain closed. Live embeddings are `NOT RUN`; do not treat that as a pass.
