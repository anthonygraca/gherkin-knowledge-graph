# AI-06 PR 1 — CocoIndex Code capability, integration contract, and live smoke

**Slice:** RAG mission PR 1 (CocoIndex variant) · **Story:** AI-06
([#56](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/56), sub-issue of F-08 #14) ·
**Owner:** A · **Implementer:** OMP · **Base:** `a674fb910bb31b866dd7417e45842cfa26a0b265`
(`main`) · **Branch:** `feat/56-cocoindex-code` · **Review:** **APPROVE** at submission 5 of 7
(`docs/reviews/AI-06-cocoindex-review-5.md`, `gpt-6.1-sol` high); one non-blocking metadata
finding (AI06-R9) repaired after approval.

## 1. Premise correction and gates

The mission brief said M1 "has been completed and independently reviewed" but treated that as a
premise to verify. The current records **do** show the M1 engineering gate satisfied:
`docs/reviews/M1-review-2.md` is an **APPROVE** at `e1497cf` (submission 2 of 7) with no open major
finding, and `docs/STATUS.md` records it. The mission's warning was written when
`M1-review-attempt-1.md` had no verdict; that is historical. This slice is therefore **not**
blocked by M1.

M2 is **not** implemented. `AGENTS.md` says not to start a later milestone while an earlier
milestone's exit criteria are unmet; roadmap §7 explicitly says "Start M3 work in parallel after
M0, but merge through contracts only", and the mission selected this M3 slice. The conflict is
recorded in `docs/stories/AI-06.md` and `docs/STATUS.md`. This slice consumes no M2 semantics,
writes no accepted links/evidence/findings, and does not claim M3 completion. If the owner applies
the stricter `AGENTS.md` reading, stop publication and treat the work as an unmerged proposal.

The prior RAG PR 1 (hosted provider boundary) is merged as `a674fb9`; its evidence is not reused as
this slice's evidence.

## 2. Traceability

| Record | Value |
| --- | --- |
| Story issue | [#56](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/56) — created 2026-11-13, open, label `user-story`, parent #14 |
| Canonical criteria | `docs/stories/AI-06.feature`, sha256 `02e256a655ef410e5c5086c9a9c2742ec5710e925ebcff932d7a4ca2380d02c3` |
| Companion / map | `docs/stories/AI-06.md`, `docs/traceability-issue-map.md` (AI-06 row and provenance note) |
| ADR | `docs/adr/0008-cocoindex-code-adoption.md` |
| Scope | CocoIndex capability/contract/live smoke only |
| Non-goals | real `CandidateDiscovery`, hit→`TraceCandidate`, API/schema/fixture change, `.feature` semantic indexing, chat/GraphRAG, M2 findings, deployment, closing AI-02/AI-03/AI-05 |
| Proposed commit | `feat(discovery): [issue #56] add optional CocoIndex Code search contract` (body `Refs #56`; parent #14 stays in prose because commitlint excludes feature-only references) |

The issue body contains the draft intent; the `.feature` file is normative. The issue was created
before implementation with the run's explicit issue-creation authority. The criteria advisory
(REVISE) was obtained **before** implementation and its findings were incorporated. No issue
closure is warranted: PR 1 is a slice of AI-06, not its full acceptance (no `TraceCandidate`
mapping).

## 3. What existed at the base

* `FakeCandidateDiscovery` is the only registered provider; `POST /api/discovery` returns
  `TraceCandidate` values with no link id/review state; `accepted_links`/`proposed_links` are
  separate.
* `app.domain.ports.CandidateDiscovery` / `ArtifactRepository` are the extension points.
  `app.discovery.registry.ProviderRegistry` and `app.settings.Settings` are the provider/config
  conventions.
* No CocoIndex adapter, no `ccc` dependency, no chat/GraphRAG path. The OMP project plugin and
  `.cocoindex_code/` index are **agent-side** tooling, not application integration.
* 285 backend tests passed at the base (2 opt-in skips).

## 4. Implementation

### Added

| Path | Purpose |
| --- | --- |
| `backend/app/discovery/cocoindex.py` | Typed request/hit/result models, error taxonomy, deterministic fake transport, normalization, snapshot verification. `index_identity` is `None` because the MCP contract does not expose one. |
| `backend/app/discovery/cocoindex_mcp.py` | Bounded `ccc mcp` stdio transport: one process per call, initialize/tools handshake, server/version/schema validation, allow-listed environment, deadline, SIGTERM→SIGKILL→reap cleanup, concurrent bounded stderr drain, whole-response rejection. |
| `backend/app/settings.py` | `CTA_CCC_EXECUTABLE`, `CTA_CCC_PROJECT_ROOT`, `CTA_CCC_LIVE_OPT_IN`, `CTA_CCC_LIVE_TESTS`; offline defaults; marker/home/root validation; `cocoindex_enabled`. |
| `backend/app/discovery/registry.py` | Guidance text only; `cocoindex` is still **not** registered. |
| `tools/probe_cocoindex.py` | Offline summary by default; opt-in live probe of `ccc version/status/doctor`, MCP capabilities, one search, Ollama tags/embed, snapshot revision/index hash/adapter hashes; raw report outside repo; sanitized report; external hit verification. |
| `backend/tests/test_cocoindex_client.py` | 63 offline contract tests (normalization, malformed data, bounds, snapshot checks, settings/offline default, stub MCP server framing/cleanup/env, probe). |
| `backend/tests/test_live_cocoindex_integration.py` | Opt-in live test; skips by default (NOT RUN). |
| `backend/tests/fixtures/cocoindex-search-response.json` | Sanitized structural capture from CocoIndex 0.2.43 on the synthetic snapshot (harness metadata separate from the server payload). |
| `docs/adr/0008-cocoindex-code-adoption.md` | Adoption decision, version pin 0.2.43, MCP-vs-CLI, isolation, security, rollback. |
| `docs/cocoindex-integration.md` | Install/init/index/status/doctor/MCP, settings, isolation, probe, limitations. |
| `docs/stories/AI-06.feature` / `.md` | Canonical criteria and companion mapping. |

### Changed

* `docs/setup.md` — optional CocoIndex section linking the guide.
* `docs/traceability-issue-map.md` — AI-06 row and provenance note.
* `docs/STATUS.md` — AI-06 slice state and evidence; no milestone closure.
* `docs/reports/omp-cocoindex-pr1/**` — this report, evidence, capabilities, advisory/retrospective.

### Not changed

`backend/app/domain/**`, `backend/app/api/**`, `backend/app/assurance/**`,
`fixtures/banking-demo/**`, generated API responses, frontend, `SCHEMA_VERSION` (0.2.0), and the
hand-labeled oracle. `POST /api/discovery` and `GET /health` are byte-for-byte unchanged.

### Key semantics

* **Proposals ≠ accepted ≠ evidence.** The adapter returns raw observations; it has no repository,
  link, review, evidence, or assurance operation. PR 2 owns candidate mapping.
* **Offline default.** `FakeCandidateDiscovery` remains registered; CocoIndex requires an explicit
  project root and live opt-in. The default test suite starts no `ccc`, reads no CocoIndex index,
  and contacts no endpoint.
* **Provenance.** Hits carry path, language, 1-based lines, content, score as reported, server
  identity, and configured project root as caller-supplied context. `index_identity=None`; the
  probe computes an external index-file SHA-256 with the method stated. The live test verifies
  content against the snapshot (trailing-newline rule).
* **Bounds.** Response line/payload 512 KiB, hit content 256 KiB (client-configurable within the
  cap), stderr 64 KiB retained tail, default deadline 90 s, hard cap 600 s, one process per call.
* **Untrusted text.** Instruction-like content is carried only as `content`; no consumer acts on
  it in this slice.
* **Version pin.** Server name/version/schema validated every session; only `0.2.43` is accepted.
* **Lifecycle.** `ccc mcp` starts its own asynchronous index update and may start/restart a daemon.
  CTA requires an isolated `COCOINDEX_CODE_DIR`/`COCOINDEX_CODE_RUNTIME_DIR` pair, refuses the
  default shared state, and treats every session as potentially index-mutating;
  `refresh_index=false` suppresses only the tool's explicit refresh.

## 5. Acceptance evidence

Mapping detail is in `docs/stories/AI-06.md`. Summary:

| Scenario | Result | Evidence |
| --- | --- | --- |
| SCN-1001 offline default | PASS | `test_default_settings_keep_cocoindex_off`, `test_offline_default_registers_only_fake_and_spawns_nothing`, `test_probe_offline_is_not_run_and_contacts_nothing` |
| SCN-1002 request bounds | PASS | `test_request_bounds_are_accepted_at_the_edges`, `test_invalid_requests_are_rejected_before_the_transport`, `test_more_hits_than_the_requested_limit_is_rejected`, `test_invalid_results_are_rejected_whole`, `test_client_content_bound_is_configurable_within_the_hard_cap` |
| SCN-1003 normalized hits | PASS | `test_captured_response_normalizes_to_ordered_hits`, `test_valid_empty_result_is_a_success_with_no_hits`, `test_result_has_no_link_review_evidence_or_assurance_surface` |
| SCN-1004 malformed rejected whole | PASS | `test_invalid_results_are_rejected_whole`, `test_malformed_envelope_is_rejected`, `::test_stdio_transport_reports_non_text_and_bad_payload_as_protocol_errors`, `::test_stdio_transport_rejects_partial_or_non_text_envelopes`, `::test_stdio_transport_reports_a_tool_error_as_protocol_error`, `::test_stdio_transport_accepts_a_structured_only_result` |
| SCN-1005 typed failures/cleanup | PASS | `::test_stdio_transport_rejects_a_missing_executable_and_project_marker`, `::test_stdio_transport_rejects_a_bad_server_version`, `::test_stdio_transport_rejects_an_incompatible_tool_schema`, `::test_stdio_transport_rejects_incompatible_search_schema_shapes`, `::test_stdio_transport_accepts_the_reviewed_schema_shape`, `::test_stdio_transport_reports_early_exit_as_unavailable`, `::test_stdio_transport_reports_malformed_output_as_protocol_error`, `::test_stdio_transport_write_deadline_with_a_stalled_child`, `::test_stdio_transport_cleanup_kills_a_descendant_that_holds_stderr`, `::test_stdio_transport_timeout_reaps_the_process_it_started`, `::test_stdio_transport_reports_a_tool_error_as_protocol_error`, `::test_stdio_transport_reports_success_false_as_a_query_error` |
| SCN-1006 configured project/paths/env | PASS | `::test_stdio_transport_handshakes_and_searches`, `::test_stdio_transport_requires_isolated_state`, `::test_stdio_transport_uses_the_allowlisted_environment`, `::test_child_environment_drops_cta_and_unrelated_secrets`, `::test_snapshot_verification_accepts_the_declared_comparison_rule`, `::test_snapshot_verification_rejects_missing_escaping_and_mismatched_hits` |
| SCN-1007 instruction-like text | PASS | `::test_instruction_like_text_is_returned_as_data_only` |
| SCN-1008 no live opt-in | PASS | `::test_probe_live_without_opt_in_is_not_run`, `::test_probe_offline_is_not_run_and_contacts_nothing` |
| SCN-1009 prerequisites unavailable | PASS | `::test_probe_live_with_unavailable_prerequisites_fails_without_fake_success`, `::test_probe_live_refuses_shared_state_without_running_commands`, `::test_stdio_transport_rejects_a_missing_executable_and_project_marker`, `::test_stdio_transport_requires_isolated_state` |
| SCN-1010 opted-in failure not a pass | PASS | `::test_overall_status_requires_every_executed_step`, `::test_probe_live_zero_hits_fails_the_smoke`, `::test_probe_live_with_unavailable_prerequisites_fails_without_fake_success`, `::test_stdio_transport_reports_early_exit_as_unavailable`, `::test_stdio_transport_reports_a_tool_error_as_protocol_error` |
| SCN-1011 live synthetic smoke | **RUN — PASS** | [capabilities/live-smoke.md](capabilities/live-smoke.md); `test_live_cocoindex_integration.py` 1 passed; probe all six steps ok |

### Commands (exact captures under `evidence/`)

| Check | Command | Exit | Capture |
| --- | --- | --- | --- |
| Full offline suite | `uv run --project backend pytest backend/tests -q` | 0 | `final-round5-pytest-full.log` (402 passed, 3 skipped) |
| CocoIndex contracts | `uv run --project backend pytest backend/tests/test_cocoindex_client.py -q` | 0 | `final-round5-cocoindex-tests.log` (117 passed) |
| Live integration | `CTA_CCC_LIVE_TESTS=1 … pytest backend/tests/test_live_cocoindex_integration.py -q` | 0 | `round5-live-test.log` (1 passed) |
| Fixture drift | `uv run --project backend python tools/fixturectl.py verify` | 0 | `final-round5-fixturectl.log` |
| Lint | `uv run --project backend ruff check .` | 0 | `final-round5-ruff-check.log` |
| Format | `uv run --project backend ruff format --check .` | 0 | `final-round5-ruff-format.log` |
| Whitespace | `git diff --check` | 0 | `final-round5-git-diff-check.log` (empty) |
| Network denial proof | `unshare -rn python -c 'socket.create_connection(("1.1.1.1",80))'` | 1 | `final-round5-network-probe.log` (`Network is unreachable`) |
| Network-denied suite | `unshare -rn backend/.venv/bin/python -m pytest backend/tests -q` | 0 | `final-round5-pytest-network-denied.log` (402 passed, 3 skipped) |
| Live probe | `… tools/probe_cocoindex.py --live --query …` | 0 | `round5-probe-summary.txt`; [capabilities/live-summary.json](capabilities/live-summary.json); [live-run-manifest.json](capabilities/live-run-manifest.json) |

### Live observation (synthetic only)

Isolated `fixtures/banking-demo` worktree at `baseline-a`
`0f8607b29d1ccb423062d856835f5310c9f54aa3`; CocoIndex 0.2.43; MCP protocol `2024-11-05`;
`embeddinggemma-2:270m-q8_0-text` (768 dims); 12 files/16 chunks; warm search 886.4 ms; 3 hits
(`src/__init__.py` 1–1, `src/transfers.py` 1–29, `src/accounts.py` 1–10) verified against the
snapshot; `index_identity=null`. Index build 2m31.9 s cold; earlier cold searches 26–53 s. The
probe records daemon PID/index hash before/after and the raw-report digest in
[capabilities/live-run-manifest.json](capabilities/live-run-manifest.json). No endpoint URL, API
key, or non-synthetic source is committed.

## 6. NOT RUN / limitations

* Default-suite live CocoIndex test is **skipped** (NOT RUN), not a pass.
* `baseline-b` worktree/index isolation, incremental refresh, and cross-baseline detection: PR 2.
* `.feature`/requirement semantic retrieval: outside the CocoIndex Code corpus; separate future
  story.
* Retrieval quality (recall/precision/MRR/false-candidate rate): AI-05, not this slice.
* Chat generation, GraphRAG, M2 findings explanations: not implemented.
* Production data-handling/license review for non-synthetic repositories: not performed.
* The default shared user daemon is never used; live use requires isolated state/runtime. The
  isolated daemon may inherit its launching environment, and `ccc mcp` always schedules a
  background index; a session is not claimed to be read-only.

## 7. Risks

| Risk | Mitigation |
| --- | --- |
| MCP contract drift in a newer `ccc` | Exact version pin; name/version/schema validation; captured fixture; capability error otherwise. |
| Index provenance is weaker than the artifact store | `index_identity=None`; external index hash with method; snapshot revision + content verification; no accepted links from hits. |
| Arbitrary subprocess behavior | Configured root only, no ancestor fallback, home rejected, allow-listed env, deadlines, process-group cleanup, bounded output. |
| `ccc mcp` may start/restart a daemon and always schedules a background index | Mandatory isolated state/runtime, default shared state refused, disposable snapshot, probe records PID/index hash before/after; no read-only-index claim. |
| Offline regression | Default provider unchanged; settings require opt-in; network-denied suite passes; live tests skip. |
| Review overclaim | No `TraceCandidate`/API change; feature explicitly limits claims; live evidence is one synthetic snapshot. |
| M3 ordering conflict | Recorded in AI-06.md/STATUS; no M2 or milestone closure claim; owner can stop publication. |

## 8. Review status and repair rounds

Submission **1 of 7** (`gpt-6.1-sol`, effort `high`, read-only) returned **REQUEST_CHANGES** with
eight findings; the verdict is `docs/reviews/AI-06-cocoindex-review.md`. All were reproduced and
repaired:

| Finding | Repair |
| --- | --- |
| AI06-R1 lifecycle/index/daemon | Mandatory isolated `COCOINDEX_CODE_DIR`/`RUNTIME_DIR`; default shared state and project-local state dir rejected; startup background index documented; probe records daemon PID/index hash before/after; SCN-1006 extended |
| AI06-R2 schema | Structural validation of types, exact required args, `limit` 1..100, non-negative `offset`, nullable string arrays; nine schema-shape tests |
| AI06-R3 blocking write | Deadline-aware non-blocking chunked writes; 4 KiB pipe + stalled-child test |
| AI06-R4 cleanup | Saved process-group SIGTERM→SIGKILL even after leader exit; stop-aware stderr select loop; bounded joins; handshake-failure resources closed; descendant-holding-stderr test |
| AI06-R5 content envelope | Exactly one text block; mixed/multiple/empty/non-text rejected; `isError` is `cocoindex-protocol-error` |
| AI06-R6 overall status | Every executed step (including `ccc_status`/`ccc_doctor`) propagates; zero-hit smoke fails; helper tests |
| AI06-R7 live metadata | `capabilities/live-run-manifest.json` with raw-report digest, aliases, exits, index build, adapter hashes |
| AI06-R8 commit body | `Refs #56` only; `#14` in prose; commitlint message check exit 0 |

Repair-round checks: 117 CocoIndex tests, 402 backend passed / 3 skipped, live probe all six steps
ok, opt-in live test 1 passed. Submission **5 of 7** was approved; the verdict is recorded in
`docs/reviews/AI-06-cocoindex-review-5.md`. The criteria advisory (REVISE, 48,565 CLI-reported tokens,
65 s) was not an acceptance review and does not consume a submission.

### Review round 2 (submission 2) and round 3 repairs

Submission 2 (`docs/reviews/AI-06-cocoindex-review-2.md`) returned **REQUEST_CHANGES**: R3/R4/R6/R7/
R8 were closed; three majors remained. Repairs:

| Finding | Repair |
| --- | --- |
| AI06-R1 path resolution | `COCOINDEX_CODE_DIR`/`RUNTIME_DIR` must be absolute; the transport resolves them once and passes the resolved absolute values to every child. Regression covers different caller/snapshot dirs and a relative path that would resolve to the shared state. |
| AI06-R2 schema constraints | Filters must be nullable (search sends null); `offset.maximum` is rejected; `query.maxLength`/`minLength` and filter `maxItems` must admit the adapter's supported range. Regressions for each. |
| AI06-R5 contradictory envelopes | Distinguishes absent from explicit-null `content`/`structuredContent`; validates every supplied representation; rejects disagreement. Regressions for null/conflict/metadata-only; matching text+structured is accepted. |

Round 3 checks: 97 contract tests, 382 backend passed / 3 skipped, live probe all six steps ok,
opt-in live test 1 passed. Review 3 returned REQUEST_CHANGES with R1 closed and R2/R5 open.

### Review round 3 (submission 3) and round 4 repairs

Submission 3 (`docs/reviews/AI-06-cocoindex-review-3.md`) closed R1 and kept R2/R5 open.
Round 4 repairs:

| Finding | Repair |
| --- | --- |
| AI06-R2 unhandled schema assertions | Added conservative keyword allowlists: unknown assertion keywords (`exclusiveMaximum`, `enum`, `const`, `pattern`, etc.) are rejected; offset caps are rejected; filter `maxItems` is checked on both the outer nullable schema and the array branch; query length constraints must admit the supported range. Regressions include `offset.exclusiveMaximum=1`, `query.enum`, `query.const`, `query.pattern`, `limit.exclusiveMaximum`, and outer `paths.maxItems=0`. |
| AI06-R5 bool/int equality masking | Envelope agreement uses strict JSON comparison (`True` is not `1`, `False` is not `0`); differing text/structured representations are rejected, while matching text+structured and structured-only remain accepted. Regressions cover `success: 1`, `start_line: true`, and matching invalid representations. |

Round 4 checks: 107 contract tests, 392 backend passed / 3 skipped, live probe all six steps ok,
opt-in live test 1 passed. Review 4 kept R2/R5 open with field-specific and numeric variants.

### Review round 4 (submission 4) and round 5 repairs

Submission 4 (`docs/reviews/AI-06-cocoindex-review-4.md`) kept R2/R5 open. Round 5 repairs:

| Finding | Repair |
| --- | --- |
| AI06-R2 hidden field combinations | Field-specific keyword allowlists: `query` no longer permits `anyOf`/`items`; `offset` no longer permits `anyOf`/caps; an `anyOf` filter schema rejects an outer `type`/`items`; the direct nullable-array form remains supported. Regressions cover `query.anyOf`, `offset.anyOf`, outer `paths.type`, outer `paths.items`, `limit.anyOf`, and `refresh_index.anyOf`. |
| AI06-R5 numeric masking | Every supplied representation is normalized independently with the exact integer rules before one is selected; a float line/count in text cannot hide behind an exact integer in structured content. Regressions cover `start_line: 1.0`, `total_returned: 1.0`, `offset: 0.0`, and matching float fields. |

Round 5 checks: 117 contract tests, 402 backend passed / 3 skipped, live probe all six steps ok,
opt-in live test 1 passed, same gate set.

### Submission 5 — APPROVE and AI06-R9

`docs/reviews/AI-06-cocoindex-review-5.md` returns **APPROVE** at submission 5 of 7: R2/R5 closed;
R1/R3/R4/R6/R7/R8 remain closed; all 11 scenarios supported within the slice; no major finding.
One non-blocking finding:

| Finding | Severity | Disposition |
| --- | --- | --- |
| AI06-R9 stale report metadata | Minor | Repaired in this record: the summary now names the canonical criteria hash `02e256a6…` and the submission-5 approval. Historical round records are preserved. |

Approval covers this PR 1 slice only. It does not close AI-06, AI-02/AI-03/AI-05, M3, or authorize
a later slice. Publication remains subject to the commit/CI gate.
