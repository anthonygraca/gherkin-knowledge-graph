# PR 1 prompt and call log

All timestamps are UTC, captured at call time. Raw logs remain outside Git under
`/tmp/omp-rag-pr1-run/`; sanitized evidence is copied to `docs/reports/omp-rag-pr1/evidence/`.
The mission prompt is the user's invocation; it was not launched by saving a file.

## Run inputs

| Field | Value |
| --- | --- |
| Mode / slice | mission; PR 1 — hosted LLM capability and provider integration |
| Milestone ceiling | M3 for PR 1–PR 3; no M2 implementation |
| Workstream | A, with shared integration for settings/docs |
| Repository | `anthonygraca/gherkin-knowledge-graph` (remote verified 2026-11-13T07:24:33Z) |
| Starting revision | `60dcc1fc5d0383b6011e7a97a3bf2a110984ff07` |
| Branch | `feat/30-hosted-ai-provider` |
| OMP model / thinking | installed `vllm/deepseek-ai/DeepSeek-V4.1-Flash-1017`; `max` |
| Codex advice/review | `gpt-6.1-sol`, reasoning `high`, explicit on every call |
| Review limit | 7 submissions for PR 1; **APPROVE at submission 4 of 7** (implementation) and **submission 5 of 7** (post-approval live probe/test change and evidence) |
| GitHub policy | local-only; no issue creation, push, PR, or merge |

## Prompt sources

| Prompt | Path | sha256 |
| --- | --- | --- |
| Inherited loop rules | `prompts/omp-codex-agentic-loop.md` (untracked; ignored) | `3cb76165e75466141c7e7f5f8e939b23d269f3a34f23057d99dfc9f83dfdad1e` |
| Mission loop rules | `prompts/omp-codex-rag-graphrag-loop.md` (untracked; ignored) | `67ff85acbed2503df06bd3878ae2de08d2404ebb93c828808e37477eb04d8cbe` |
| Kickoff | user message / copy-paste kickoff in the mission prompt | parameters recorded above; no repository file |

`prompts/` is ignored by the repository; these files are not part of the committed task snapshot.

## OMP calls

The coordinator inspected the repository, implemented the slice, and ran the checks directly. No OMP
delegates, pools, or advisory calls were used: the slice was one cohesive provider boundary with no
independent parallel slices, and no concrete design ambiguity required advice. OMP usage/cost
telemetry was not exposed; unavailable fields are not recorded as zero. Review repairs were handled
by the coordinator and rechecked before resubmission.

## Capability probe calls

| Call | Command | UTC | Exit | Observation |
| --- | --- | --- | --- | --- |
| Offline summary | `uv run --project backend python tools/probe_ai_capabilities.py` | 2026-11-13T07:26Z | 0 | `probed=false`, `mode=fake`; no endpoint contacted |
| Final offline summary | same, after repairs | 2026-11-13T08:01:16Z | 0 | `probed=false`, `mode=fake`; sanitized output |
| Live refused in fake mode | `... --live` | 2026-11-13T08:01:16Z | 2 | `--live requires CTA_AI_MODE=live`; no endpoint contacted |
| Hosted live probe, configured model | `CTA_AI_MODE=live` probe with configured `CTA_LLM_MODEL=deepseek-ai/DeepSeek-V4.1-Flash` | 2026-11-13T16:18Z | 0 | HTTP 404 for chat; configured model not in catalogue; `/models` exposed `deepseek-ai/DeepSeek-V4.1-Flash-1017` |
| Hosted live probe, observed model | `CTA_AI_MODE=live CTA_LLM_MODEL=deepseek-ai/DeepSeek-V4.1-Flash-1017` | 2026-11-13T16:22:11Z → 16:22:22Z | 0 | Chat 200, 54 tokens, 553.3 ms; JSON schema 200, 92 tokens; embeddings unavailable (connection refused) |
| Live chat test | `CTA_AI_LIVE_TESTS=1 CTA_AI_MODE=live CTA_LLM_MODEL=...` | 2026-11-13T16:23:00Z → 16:23:01Z | 0 | 1 passed; embeddings test NOT RUN |

## Independent review calls

| Submission | Packet / sha256 | Session | Window (UTC) | Duration | Exit | Tokens | Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 of 7 | `AI-01-hosted-provider-review-prompt.md` / `26733dbd222c71ce55ac250bb93449cca29650f367c373e135467734b89f047b` | `01a1d3d2-52f6-78b3-861b-5c22926f382c` | 07:32:17 → 07:35:26 | 189 s | 0 | 91,486 | REQUEST_CHANGES |
| 2 of 7 | `AI-01-hosted-provider-review-prompt-2.md` / `02f3c22076216cc8d0dcff74d9daa03936fb07a18ec44edf8980c4db61135dee` | `01a1d3de-2e54-7b01-8a65-4d70e5ec6ef0` | 07:45:15 → 07:47:08 | 113 s | 0 | 92,552 | REQUEST_CHANGES |
| 3 of 7 | `AI-01-hosted-provider-review-prompt-3.md` / `b8233550b3807dc61505a7f73ec69dd053c76477782336184775c75b112ffd97` | `01a1d3e6-7dca-78c3-a371-a17262f82609` | 07:54:20 → 07:57:09 | 169 s | 0 | 79,113 | REQUEST_CHANGES |
| 4 of 7 | `AI-01-hosted-provider-review-prompt-4.md` / `760b974e4e4b5bf18153e26347026f7815a4c276396ed4593d6f5d59bf2bbf50` | `01a1d3ef-6d7f-7a70-8f16-25d95fb41265` | 08:04:05 → 08:06:16 | 131 s | 0 | 88,098 | **APPROVE** |
| 5 of 7 | `AI-01-hosted-provider-review-prompt-5.md` / `e549b736b036f6594f5cef552c3021577d301b074ed8f8837e5211667a5e743a` | `01a1d5bd-f1bc-7c71-bf92-84bc65844181` | 16:29:16 → 16:31:51 | 155 s | 0 | 85,412 | **APPROVE** |

Each review used a fresh Codex session, `--sandbox read-only`, and passed the packet on stdin. The
output-last-message file and stdout/stderr are retained outside Git. `git status` before/after each
call is in `/tmp/omp-rag-pr1-run/review-N/review-N-metadata.txt`; the reviewer was instructed not
to edit, commit, regenerate fixtures, or delegate.

## Review repair provenance

* Submission 1 findings PR1-R1…R4 were reproduced with failing tests before repair.
* Submission 2 closed PR1-R2/R3/R4 and left PR1-R1 open for dynamic keys and the offline CLI path.
* The second repair moved the sanitizer to `app/discovery/ai.py`, sanitized dynamic keys and all
  CLI output paths, added four regressions, and re-ran the full gates (281 passed, 2 skipped; also
  network-denied).
* Submission 3 found two remaining report-return paths and a new logging-URL bypass (PR1-R5).
* The third repair sanitized `_base_summary`, the fake-mode probe return, `offline_summary`, the CLI
  `_offline_summary`, and every log field/upstream error code; added four regressions; re-ran the
  full gates (285 passed, 2 skipped; also network-denied).
* Submission 4 approved the implementation snapshot with no new findings; the approval covered the
  offline/mocked provider-boundary slice only.
* The endpoint variables were then supplied. The first live probe exposed a reasoning-model budget
  issue: the "ignore this request" canary with 16 tokens returned `content: null` and
  `finish_reason=length`; the adapter rejected it as designed. The probe/test now asks for a final
  answer with a 64-token budget.
* The live smoke with the observed catalogue model passed chat and schema-constrained JSON;
  embeddings were unavailable (connection refused). Submission 5 approved the probe/test change and
  the sanitized live evidence. This does not establish general live compatibility.
