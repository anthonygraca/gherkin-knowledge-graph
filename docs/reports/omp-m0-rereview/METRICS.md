# M0 re-review — resource and outcome metrics

Per the loop's measurement table. Values not exposed by a tool are marked *unavailable* (never
reconstructed from memory or mtimes).

## Task and quality

| Measure | Record |
|---|---|
| Story / findings | M0 re-review of R1–R7 (FT-01 #18, FT-02 #19; platform tasks M0-P1…P3); new finding R8 raised by the reviewer, owner-attested |
| Milestone / owner | M0 ceiling; shared platform / B lead; coordinator OMP |
| Acceptance | AC-1.1…AC-1.8, AC-2.1…AC-2.5: all PASS (rounds 1 and 2); M0 exit-criteria table: all PASS within scope |
| Final snapshot | Approved: commit `bca69cf14a7c94e9ff29ec860fd28fbef83a0798`, tree `e55ff9f9b2d669d1417ee1e4df0c858817a1eb82` |
| Verdict / rounds | Round 1: NEEDS_INPUT (submission 1/7). Round 2: **APPROVE** (submission 2/7). No APPROVE-by-exhaustion; limit not reached |
| Confirmed defects this run | R8 (evidence gap, blocking — repaired by human attestation, closed in round 2). OMP self-review defect: one stale doc reference (`FixtureStore.resolve`), fixed in `5f5d843` |
| Rework | 1 doc-only fix + a bookkeeping commit set (reports, verdict records, one lint-scope line in `ruff.toml`); no code rework; review counter used: 2 of 7 |
| Unresolved items | NOT VERIFIED list in `docs/STATUS.md` (hosted CI, macOS re-run, `uv --offline` under denial, UI, M2 classification, M3 provider side effects) — none blocks M0 |
| Escapes observed later | none observed in-session |

## Evidence

| Item | Record |
|---|---|
| Gate exits | pytest 107 passed (two snapshots); `fixturectl verify` exit 0; `ruff check`/`format --check` clean; `git diff --check` exit 0 — raw outputs in `evidence/` and `evidence2/` |
| Probes | `probe_r1`…`probe_r7` executed on the frozen snapshot; identical probe scripts committed under `probes/` (excluded from lint scope so a formatter cannot rewrite them); outputs under `evidence/` |
| Network-denied run | `unshare -rn`: socket `[Errno 101] Network is unreachable` (**denial effective**) + 107 passed |
| Live HTTP | uvicorn 8031 (pristine) / 8032 (tampered copy): statuses and codes as recorded in `probes/p_http_live.py` output (`evidence/probe_http_live.txt`) |
| Independent expectations | Fixture baselines from the committed manifest (`67109fac…`, `c02064fe…`); independent fingerprint vectors; oracle labels hand-written; human attestation recorded separately |
| NOT RUN | Hosted GitHub Actions; macOS/Git 2.54 re-run; `uv run --offline` under OS denial (venv interpreter used instead); browser/UI |

## Context per Codex call

| Call | Purpose | Packet | Content supplied | Extra context requested | Broad discovery |
|---|---|---|---|---|---|
| 1 | Acceptance review (submission 1/7) | 192,804 bytes, sha256 `077eaf64d893d392f6baeea736e6ab28a8716e26bd2e6343df3d59827cb5ca3e` | ACs, R1–R7 originals + repair map, full cumulative diff, tracked-file manifest, all probe/gate outputs, limits | none | reviewer inspected the repo read-only and ran its own probes (reported independently recomputing fingerprints and content hashes); its own TestClient probe stalled under the read-only sandbox and was terminated |
| 2 | Acceptance review (submission 2/7) | 89,237 bytes, sha256 `03225153e885f12213c013268b749df43013f07e17f1b33f9cfe9d0bc5d26d39` | Round-1 verdict verbatim, attestation record, docs-only incremental diff, product-tree blob-hash identity proof, round-2 gates, manifest, limits | none | read-only Git inspection to re-verify blob hashes; no broad re-discovery |

## Codex resources

| Measure | Call 1 | Call 2 |
|---|---|---|
| Model / effort | `gpt-6.1-sol` / `xhigh` | `gpt-6.1-sol` / `xhigh` |
| Kind | acceptance review | acceptance review (also R8 disposition check) |
| Session id | `01a1c912-1adf-7c21-bd6c-3744561b0a76` | `01a1c926-5f47-7751-b38c-8dc16bdf4c03` |
| Start → end (UTC) | 05:26:06 → 05:30:49 | 05:48:17 → 05:51:06 |
| Elapsed | 284 s | 169 s |
| Exit | 0 | 0 |
| Tokens | "tokens used 149,880" (CLI-reported single total; input/cached/output split **unavailable**) | "tokens used 79,482" (same limitation) |
| Cost | **unavailable** (CLI does not report cost) | **unavailable** |
| Failures / retries | none | none |
| Advice calls | 0 (no advisory call was warranted: no ambiguity emerged that the reviewer's own contract could not settle; the R8 question went to the human, per the rules) | — |

## OMP resources

| Measure | Record |
|---|---|
| Coordinator model / thinking | Configured role `default` = `vllm/deepseek-ai/DeepSeek-V4.1-Flash` (`~/.omp/agent/config.yml`); session thinking level `max` (host default). The loop requested `xhigh`; the `--thinking` flag exists and was verified, but a running session's level is host-configured — recorded as a deviation, not a substitution of a lesser level |
| Delegates / pools | 0 subagents, 0 workflowz pools (`workflowz` not installed). Rationale: the selected task was a single coherent verification chain (probe → gate → packet) where every step depends on the prior result and the coordinator is the designated verification worker; no genuine independent slices existed to parallelize (the loop's instruction: do not manufacture parallel tasks) |
| Usage / cost | **unavailable** to the agent (no exposed meter for this session's spend) |
| Implementation/verification effort | 23 tool-era actions before submission 1 (recon 8, environment 2, probes/gates 2 batches, packet 1, review 1); 12 actions between submissions (attestation, 2 commits, packet 2, review 2); bookkeeping after |

## Total effort

| Measure | Record |
|---|---|
| First recorded / last recorded (UTC) | `2026-11-11T05:10:29Z` / `2026-11-11T05:52:48Z` (session start slightly earlier; not instrumented) |
| Elapsed wall time | ≈ 43 min for the recorded window; all work sequential; user wait for the attestation inside that window (duration not instrumented) |
| Agent/call inventory | 1 coordinator (OMP, this session), 2 Codex acceptance reviews; 0 advisory calls; 0 delegates |
| Commit state | 4 commits unpushed on `feat/8-m0-foundation` (`5f5d843`, `bca69cf`, `c0b70fa`, final `chore(lint)` commit); branch remains ahead of `origin` |
| Batch / continuation | Not applicable — single selected task; no continuation list was authorized; nothing skipped |

## Quota

Not exposed by any participating tool in this session → **unavailable**; no percentage-point
attribution attempted (requires a confirmed common window without other-session contamination).

## Comparator

No comparator report was supplied, so the loop's experiment question (Sol reserved for advice +
acceptance vs. Codex-led coordination) cannot be answered from this run alone. This run's
recorded resources (2 review calls, 2/7 submissions, 229,362 reviewer tokens total as reported,
453 s of reviewer wall time, 0 advisory calls) are the inputs a matching baseline run would need to
compare against for scope, acceptance, model/effort and verification parity.
