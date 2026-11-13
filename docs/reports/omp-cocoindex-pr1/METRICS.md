# Metrics — AI-06 PR 1

Measurements below are observed in this run. `unavailable` means the field was not exposed; it is
not zero. Times are UTC; durations come from the captured logs or the probe's measured fields.

## Timeline

| Event | Time | Source |
| --- | --- | --- |
| Issue #56 created | ~17:05:00Z (log mtime) | `/tmp/cta-cocoindex-pr1/issue-create.log` |
| Criteria advisory start/end | 17:12:07Z → 17:13:12Z | `reviews/advisory-criteria-start.txt` (external); verdict in `reviews/advisory-criteria.md` |
| Isolated snapshot index | 17:06:10Z daemon start; 2m31.9s build | `/tmp/cta-cocoindex-pr1/ccc-index-isolated.log` |
| Final live probe/test window | 17:50:11Z → 17:50:17Z | `evidence/live-window.txt` |
| Final default suite | 17:54:08Z (log mtime) | `evidence/final-pytest-full.log` |
| Network-denied suite | 17:54:34Z (log mtime) | `evidence/final-pytest-network-denied.log` |
| Acceptance review 1 | TBD | pending |

The session began before the first captured event; no start timestamp is asserted.

## Verification counts

| Measure | Value | Capture |
| --- | --- | --- |
| Backend tests passed (default) | 402 | `evidence/final-round5-pytest-full.log` |
| Opt-in skips (default) | 3 (2 hosted AI, 1 CocoIndex) | same |
| CocoIndex contract tests | 117 passed | `evidence/final-round5-cocoindex-tests.log` |
| Live CocoIndex test | 1 passed (opt-in) | `evidence/round5-live-test.log` |
| Network-denied backend suite | 402 passed / 3 skipped | `evidence/final-round5-pytest-network-denied.log` |
| New acceptance scenarios | 11 (`SCN-1001`…`SCN-1011`) | `docs/stories/AI-06.feature` |
| Acceptance review submissions | 5 of 7 (submissions 1–4 REQUEST_CHANGES, repaired; 5 pending) | `docs/reviews/AI-06-cocoindex-review*.md` |

## CocoIndex observations

| Measure | Value | Notes |
| --- | --- | --- |
| CocoIndex Code version | 0.2.43 | `ccc version`, probe step ok |
| MCP protocol | 2024-11-05 | observed initialize result |
| Embedding model | `ollama/embeddinggemma-2:270m-q8_0-text` | LiteLLM id; native tag without `ollama/` |
| Embedding dimensions | 768 | `/api/embed` |
| Model size | 303,957,438 bytes | `/api/tags` digest `c21dd30c…` |
| Indexed snapshot | 12 files / 16 chunks | python 7, json 6, markdown 3 |
| Index build (cold) | 2m31.9s | isolated daemon |
| Search, warm | 886.4 ms | round-5 probe, 3 hits |
| Search, cold | 26–53 s | earlier calls while the model loaded |
| `/api/embed` cold | 43.7 s | direct probe |
| MCP handshake latency | not separately measured | included in search wall time |
| `ccc doctor` | 357.0 ms | round-5 probe |
| `ccc status` | 241.1 ms | round-5 probe |
| Index file size | 9,535,488 bytes | SHA-256 recorded in `capabilities/live-summary.json` |
| Index identity (server) | unavailable | MCP contract exposes none; `index_identity=null` |
| Snapshot revision | `0f8607b29d1ccb423062d856835f5310c9f54aa3` | `baseline-a` worktree, clean |

These are latency observations on one workstation and one synthetic snapshot. They are not
throughput benchmarks, retrieval-quality metrics, or cost measurements.

## Artifact sizes

| Artifact | Lines | SHA-256 (prefix) |
| --- | --- | --- |
| `backend/app/discovery/cocoindex.py` | 573 | `7de622c6…` |
| `backend/app/discovery/cocoindex_mcp.py` | 1,008 | `0913d9e0…` |
| `backend/tests/test_cocoindex_client.py` | 1,484 | `13d5c536…` |
| `tools/probe_cocoindex.py` | 708 | `b994f7e3…` |
| `docs/adr/0008-cocoindex-code-adoption.md` | 188 | `98115f8a…` |
| `docs/cocoindex-integration.md` | 196 | `6e257f2b…` |
| Captured response fixture | 58 | `0b627f1f…` |

Full manifest hashes are in the review packet.

## Rework observed

| Item | Cost/effect |
| --- | --- |
| Criteria advisory `REVISE` (9 findings) | Revised the feature before implementation; no code rework |
| Ollama model prefix bug in the first live probe | Probe reported `ollama/embeddinggemma-…` as uninstalled; normalized the LiteLLM prefix, then all steps passed |
| Ruff format/import ordering | One formatter pass; one help-string length fix |
| Shared daemon contention on the first index attempt | Killed only the adapter's queued `ccc index`; re-ran with isolated `COCOINDEX_CODE_DIR`/`RUNTIME_DIR`; 2m31.9s pass |
| Test parameterization/formatter fixes | 12 initial failures, all test bugs; final 117/117 |
| Acceptance review 1 (`REQUEST_CHANGES`, 8 findings) | Repaired lifecycle/isolation, schema validation, write deadline, cleanup, content envelope, overall status, live manifest, commit refs; +22 tests |
| Acceptance review 2 (`REQUEST_CHANGES`, 3 open) | Absolute isolation paths, nullable/constraint schema checks, contradictory/envelope agreement; +12 tests |
| Acceptance review 3 (`REQUEST_CHANGES`, R2/R5 open) | Conservative keyword allowlists, offset/filter caps, strict JSON envelope equality; +10 tests |
| Acceptance review 4 (`REQUEST_CHANGES`, R2/R5 open) | Field-specific allowlists, outer filter combination rejection, independent normalization of every representation; +10 tests |
| Ollama port-forward loss during repair | The probe correctly reported `overall=failed` (ollama/search failed); restored a process-local port-forward to the approved Service, then all steps passed |

## Coordination experiment note

No OMP delegates were spawned. Delegate resource use, wall time, and rework are `unavailable`.
Codex usage is limited to one advisory (48,565 CLI-reported tokens) and the pending acceptance
review. No baseline comparison between OMP-led and Codex-led delivery is claimed from one slice.
