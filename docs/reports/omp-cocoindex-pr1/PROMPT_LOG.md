# Prompt and call log — AI-06 PR 1

All timestamps are UTC. A statement about a command cites the file captured at call time; raw
reports, daemon logs, and the local index stay outside Git. No prompt or log contains an API key,
token, endpoint credential, or private source.

## Run inputs

| Input | Value |
| --- | --- |
| Mode / slice | `mission` — PR 1 CocoIndex Code compatibility, integration contract, live smoke |
| Milestone ceiling | M3 for PR 1/PR 2; GraphRAG/M1 gate for PR 3; PR 4 does not close M4 |
| Repository | `anthonygraca/gherkin-knowledge-graph`, base `a674fb9` (`main`) |
| OMP model/thinking | installed DeepSeek V4.1 Flash provider; `max` thinking |
| Codex advice/review | `gpt-6.1-sol`, reasoning effort `high` |
| Review limit | 7 submissions; 1 used (acceptance), advisory separate |
| GitHub authority | issue creation, push, PR, merge granted by the run inputs; issue closure not implied |
| Branch | `feat/56-cocoindex-code` (created from `a674fb9`) |

The repository copy of `prompts/omp-codex-rag-graphrag-loop.md` still describes the earlier
hosted-provider slice and was **not** edited; the mission prompt supplied for this run is the
authority. `prompts/omp-codex-agentic-loop.md` changed in the working tree during the session
(owner edit); it is excluded from this slice's commits. `prompts/` is ignored by a pre-existing
`.gitignore` edit; both changes are unrelated.

## Calls

| # | Call | Exact input | Start → end | Exit | Usage/result |
| --- | --- | --- | --- | --- | --- |
| 1 | Criteria advisory (not acceptance) | `docs/reports/omp-cocoindex-pr1/reviews/advisory-criteria-prompt.md` | 2026-11-13T17:12:07Z → 17:13:12Z | 0 | `REVISE`; 9 findings; CLI-reported 48,565 tokens; verdict `reviews/advisory-criteria.md` |
| 2 | Issue creation | `gh issue create --repo anthonygraca/gherkin-knowledge-graph --title "AI-06 — CocoIndex Code semantic code-search capability and integration contract" --body-file /tmp/…/issue-ai-06-body.md --label user-story` | log mtime 17:05:00Z | 0 | [#56](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/56); sub-issue of #14 verified by `gh issue view 56` |
| 3 | Live CocoIndex smoke (pre-repair) | `tools/probe_cocoindex.py --live --query "withdraw whole dollar amounts" --limit 3 --language python --path 'src/*' --timeout 180 --ollama-timeout 90` with isolated state | 2026-11-13T17:50:11Z → 17:50:17Z | 0 | six steps ok; 3 hits verified; `evidence/probe-summary.txt` |
| 4 | Live pytest (pre-repair) | `pytest backend/tests/test_live_cocoindex_integration.py -q` with `CTA_CCC_LIVE_TESTS=1` | 17:50:11Z → 17:50:17Z | 0 | 1 passed; `evidence/live-test.log` |
| 5 | Acceptance review 1 | `docs/reviews/AI-06-cocoindex-review-prompt.md` | 2026-11-13T18:04:16Z; reviewer-reported wall 602.93 s | 0 | **REQUEST_CHANGES**, 8 findings (`AI06-R1`…`R8`); verdict `docs/reviews/AI-06-cocoindex-review.md` |
| 6 | Live smoke after review 1 repairs | same probe command with isolated state | 2026-11-13T18:40:25Z → 18:40:31Z | 0 | six steps ok; 3 hits; `evidence/repair-probe-summary.txt` |
| 7 | Live pytest after review 1 repairs | same live pytest command | 18:40:25Z → 18:40:31Z | 0 | 1 passed; `evidence/repair-live-test.log` |
| 8 | Acceptance review 2 | `docs/reviews/AI-06-cocoindex-review-prompt-2.md` | 2026-11-13T18:52:57Z; reviewer-reported wall 228.91 s | 0 | **REQUEST_CHANGES**, R1/R2/R5 open (R3/R4/R6/R7/R8 closed); verdict `docs/reviews/AI-06-cocoindex-review-2.md` |
| 9 | Live smoke round 3 | same probe command with isolated state | 2026-11-13T19:03:55Z → 19:04:00Z | 0 | six steps ok; 3 hits; `evidence/round3-probe-summary.txt`; manifest `capabilities/live-run-manifest.json` |
| 10 | Live pytest round 3 | same live pytest command | 19:03:55Z → 19:04:00Z | 0 | 1 passed; `evidence/round3-live-test.log` |
| 11 | Acceptance review 3 | `docs/reviews/AI-06-cocoindex-review-prompt-3.md` | 2026-11-13T19:12:04Z; reviewer-reported wall 185.69 s | 0 | **REQUEST_CHANGES**, R1 closed; R2/R5 open; verdict `docs/reviews/AI-06-cocoindex-review-3.md` |
| 12 | Live smoke round 4 | same probe command with isolated state | 2026-11-13T19:21:35Z → 19:21:41Z | 0 | six steps ok; 3 hits; `evidence/round4-probe-summary.txt`; manifest `capabilities/live-run-manifest.json` |
| 13 | Live pytest round 4 | same live pytest command | 19:21:35Z → 19:21:41Z | 0 | 1 passed; `evidence/round4-live-test.log` |
| 14 | Acceptance review 4 | `docs/reviews/AI-06-cocoindex-review-prompt-4.md` | 2026-11-13T19:29:30Z; reviewer-reported wall 171.26 s | 0 | **REQUEST_CHANGES**, R1/R3/R4/R6/R7/R8 closed; R2/R5 open; verdict `docs/reviews/AI-06-cocoindex-review-4.md` |
| 15 | Live smoke round 5 | same probe command with isolated state | 2026-11-13T19:39:46Z → 19:39:52Z | 0 | six steps ok; 3 hits; `evidence/round5-probe-summary.txt` |
| 16 | Live pytest round 5 | same live pytest command | 19:39:46Z → 19:39:52Z | 0 | 1 passed; `evidence/round5-live-test.log` |
| 17 | Acceptance review 5 | next packet | TBD | TBD | TBD |

The advisory is not an acceptance verdict and did not consume one of the seven submissions. Reviews 1–4 are submissions 1–4; review 5 will be submission 5. No OMP delegates were spawned; the
coordination/model-comparison experiment therefore has no delegate resource data for this slice
(`unavailable`, not zero).

## User interjection

At ~2026-11-13T17:2xZ the user said "indexing is done. try out ccc". The agent-side CocoIndex MCP
tool was invoked with
`{"query":"CocoIndex code search adapter settings and MCP transport","limit":5,"refresh_index":false,"languages":["python"],"paths":["backend/app/discovery/*"]}`
and returned five hits from `backend/app/discovery/cocoindex.py` and `cocoindex_mcp.py`. This is
**agent ergonomics**, not CTA runtime evidence: it used the OMP-mounted MCP server and the user's
index, not the `StdioMcpTransport` subject of this slice. The CTA-specific live evidence is call 3/4.

## Verification calls

| Command | Exit | Capture |
| --- | --- | --- |
| `uv run --project backend pytest backend/tests -q` | 0 | `evidence/final-round5-pytest-full.log` |
| `uv run --project backend pytest backend/tests/test_cocoindex_client.py -q` | 0 | `evidence/final-round5-cocoindex-tests.log` |
| `uv run --project backend python tools/fixturectl.py verify` | 0 | `evidence/final-round5-fixturectl.log` |
| `uv run --project backend ruff check .` | 0 | `evidence/final-round5-ruff-check.log` |
| `uv run --project backend ruff format --check .` | 0 | `evidence/final-round5-ruff-format.log` |
| `git diff --check` | 0 | `evidence/final-round5-git-diff-check.log` (empty) |
| `unshare -rn … socket.create_connection(("1.1.1.1",80))` | 1 | `evidence/final-round5-network-probe.log` |
| `unshare -rn backend/.venv/bin/python -m pytest backend/tests -q` | 0 | `evidence/final-round5-pytest-network-denied.log` |
| `tools/probe_cocoindex.py` (no `--live`) | 0 | `evidence/final-probe-offline.log` (`NOT RUN`) |

Earlier attempts are retained (`evidence/pytest-full.log`, `evidence/ruff-format.log`,
`evidence/final-pytest-full.log`, `evidence/final-cocoindex-tests.log`, etc.), not overwritten.
The final repaired attempts are the `final-round5-*` captures; earlier `final-round4-*`, `final-round3-*`, `final-repair-*`, and `final-*` captures remain as prior attempts. The Ollama endpoint was restored by
a process-local `kubectl port-forward` to the approved in-cluster Service after the pre-repair run;
no deployment was changed.
