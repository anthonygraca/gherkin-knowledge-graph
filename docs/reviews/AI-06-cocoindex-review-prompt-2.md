# AI-06 implementation review — submission 2 of 7 (repairs after REQUEST_CHANGES)

## 1. Snapshot and prior verdict

**Slice:** RAG mission PR 1 (CocoIndex variant). **Story:** AI-06
([#56](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/56)); parent F-08 #14.
**Base:** `a674fb910bb31b866dd7417e45842cfa26a0b265`. **Branch:** `feat/56-cocoindex-code`.
**Submission:** 2 of 7. **Reviewer:** `gpt-6.1-sol`, reasoning effort `high`, read-only.

**Prior verdict:** submission 1 — **REQUEST_CHANGES**, eight findings `AI06-R1`…`R8`
(`docs/reviews/AI-06-cocoindex-review.md`, sha256
`8a12b7d567beddc56edc097d8b9640340813de47dea5026d69dc2529dd8f9d15`; packet 1 sha256
`8d01f674d87e94372fba9127ccacbcfb45f23234b28efedef4060445a4138fe7`). All findings are dispositioned
below. Submission 1's independent checks (38 selected tests, hit/snapshot hashes) are not repeated
here; this packet focuses on the repairs and refreshed evidence.

**Criteria:** `docs/stories/AI-06.feature`, sha256
`02e256a655ef410e5c5086c9a9c2742ec5710e925ebcff932d7a4ca2380d02c3` (one line added to SCN-1006
requiring refusal of the shared default state; no scenario removed or weakened). M1 remains
satisfied; M2 is not implemented; the M3 ordering conflict remains recorded. PR 1 does not register
a discovery provider, change the API/schema/fixtures, or claim AI-02/AI-03/AI-05/M3 closure.

**Proposed commit:** `feat(discovery): [issue #56] add optional CocoIndex Code search contract`,
body `Refs #56` only. Parent #14 is in prose, not in the parsed `Refs` line; `commitlint
--message-file` exits 0.

## 2. Finding dispositions

### AI06-R1 — `ccc mcp` lifecycle effects (major) — repaired

Reproduced in the installed 0.2.43 `cli.py`: `ccc mcp` always schedules `_bg_index(project_root)`,
and `client.py` may start/restart a daemon. Repairs:

* `StdioMcpTransport` now **requires** `COCOINDEX_CODE_DIR` and `COCOINDEX_CODE_RUNTIME_DIR`,
  rejects the default `~/.cocoindex_code`, rejects the project-local `.cocoindex_code` state dir,
  and requires `global_settings.yml` in the isolated state (`validate_isolated_state`,
  `cocoindex_mcp.py` lines ~133–162, ~336–345).
* The probe validates isolation **before** running any `ccc version/status/doctor` command
  (`probe_cocoindex.py` `_probe_live`), records daemon PID and index-file SHA-256 before/after, and
  reports `daemon_started_by_session`, `daemon_restarted_by_session`, `index_changed_by_session`,
  and the background-index note.
* ADR 0008, the integration guide, AI-06 companion, STATUS, and the implementation report now state
  that `refresh_index=false` suppresses only the tool's explicit refresh; the startup background
  index cannot be disabled without forking `ccc`, so a session is treated as potentially
  index-mutating. The shared daemon is protected by refusing the default state, not by signalling
  it.
* SCN-1006 now states the refusal. Tests: `test_stdio_transport_requires_isolated_state`,
  `test_child_environment_drops_cta_and_unrelated_secrets`, `test_probe_live_refuses_shared_state_without_running_commands`.
* Live evidence: isolated daemon PID `1676339` before/after, index hash unchanged at the
  after-snapshot, `daemon_started/restarted=false`; manifest records the caveat that the background
  task may finish later. No shared daemon was touched.

### AI06-R2 — incompatible search schemas (major) — repaired

`_validate_search_tool` now rejects an object schema unless:

* `query` is `type: string`;
* `limit` is `type: integer` with `minimum <= 1` and `maximum >= 100`;
* `offset` is `type: integer` with `minimum <= 0`;
* `refresh_index` is `type: boolean`;
* `languages`/`paths` accept an array of strings or null (direct or `anyOf`);
* `required` is exactly `["query"]` (no unknown required argument).

Nine shape tests (`test_stdio_transport_rejects_incompatible_search_schema_shapes`) cover integer
query, `limit.maximum=2`, missing maximum, string offset, string refresh, integer paths/languages,
extra required, and empty required. The reviewed real schema passes
(`test_stdio_transport_accepts_the_reviewed_schema_shape`), and the live probe passed on 0.2.43.

### AI06-R3 — blocking writes escape the deadline (major) — repaired

`_send` now writes through `_write_all` with a non-blocking stdin fd, `selectors` writability, chunked
`os.write`, and the session deadline. A timeout raises `CocoIndexTimeoutError` and cleanup reaps the
process. Non-POSIX keeps a bounded writer thread. Test:
`test_stdio_transport_write_deadline_with_a_stalled_child` uses a 4 KiB stdin pipe, a child that
stops reading after `tools/list`, a 2,000-char query plus ten 190-char path filters, `timeout=0.5`,
and asserts the timeout within 5 s and process reaping.

### AI06-R4 — cleanup can exceed its interval (major) — repaired

`_stop` now:

* closes the reader, signals the **saved process group** even when the leader already exited, waits
  a bounded half-interval, SIGKILLs the group, waits the cleanup interval, stops/joins the stderr
  reader (select loop with a stop flag, max 0.5 s), then closes streams;
* closes session resources on handshake failure (`__enter__` calls `_stop`, which owns reader,
  stderr, streams);
* never signals the daemon (it starts in its own session).

Test: `test_stdio_transport_cleanup_kills_a_descendant_that_holds_stderr` spawns an
SIGTERM-ignoring child that inherits stderr, exits the leader, and asserts cleanup < 3 s and the
descendant disappears.

### AI06-R5 — malformed MCP content accepted partially (major) — repaired

`_payload` now:

* requires `content` to be a non-empty list when present;
* rejects any non-object or non-text block, requires exactly one text block, and parses that text;
* accepts `structuredContent` only when it is an object; a structured-only result is supported;
* rejects `isError=true` as `cocoindex-protocol-error` (aligning with SCN-1004), not a query error;
* still treats `success=false` as `cocoindex-query-error`.

Tests: `test_stdio_transport_rejects_partial_or_non_text_envelopes` (mixed, multiple, empty,
image-only), `test_stdio_transport_reports_a_tool_error_as_protocol_error`,
`test_stdio_transport_accepts_a_structured_only_result`.

### AI06-R6 — failed probe steps passing (major) — repaired

`_overall_status` requires every executed step — `ccc_version`, `ccc_status`, `ccc_doctor`,
`mcp_capabilities`, `ollama`, and `search` when requested — to be `ok`; any failed/timeout/unavailable
step fails the probe. A requested smoke with zero hits sets `search=failed`. Ordinary adapter
searches still accept an empty result. Tests:
`test_overall_status_requires_every_executed_step`, `test_probe_live_zero_hits_fails_the_smoke`,
plus the unavailable-prerequisite probe. A real pre-repair run with Ollama unreachable correctly
produced `overall=failed` with `ollama`/`search` failed.

### AI06-R7 — incomplete live metadata (medium) — repaired

`docs/reports/omp-cocoindex-pr1/capabilities/live-run-manifest.json` now records:

* exact argv with `<snapshot>`, `<ccc-state>`, `<ccc-runtime>`, `<external>`, `<cta-repository>`
  aliases; no ellipses;
* raw report alias + SHA-256 + bytes, sanitized report SHA-256 + bytes, captured payload SHA-256 +
  bytes, stdout SHA-256, live-test log SHA-256;
* index build argv/cwd/exit/timing/files/chunks/log hash;
* probe/test start/finish, exits, six step statuses, hit paths/scores, lifecycle before/after;
* adapter file hashes and the CTA revision.

`capabilities/live-smoke.md` links the manifest and uses the same aliases. Raw artifacts remain
outside Git. Evidence copies: `evidence/repair-live-test.log` and
`evidence/repair-probe-summary.txt` match the manifest hashes.

### AI06-R8 — commit body (low) — repaired

The proposed message is `feat(discovery): [issue #56] add optional CocoIndex Code search contract`
with body `Refs #56`; `#14` appears only in prose. `python tools/commitlint.py --message-file`
exits 0. No commit exists yet.

## 3. Changed-file manifest and pointers

Unchanged since submission 1 (hash-pinned; review as previously verified):
`backend/app/discovery/cocoindex.py` `7de622c6…`; `backend/app/discovery/registry.py`
`d045edcc…`; `backend/app/settings.py` `b4b1d331…`; `docs/setup.md` `f0567350…`;
`docs/traceability-issue-map.md` `f561f5d2…`;
`backend/tests/fixtures/cocoindex-search-response.json` `0b627f1f…`.

Changed in this submission:

```text
f912d01f0aa7a2c2c5d5b1539561b42cc47510f7d43622ce16731aaba2c9e75f   852  backend/app/discovery/cocoindex_mcp.py
d08a4481623b55a8ae658048078456a2f1baf54e97886c67e8efd246414fc964   689  tools/probe_cocoindex.py
abfae81fa9a0e2058a520cde8d3eaa6cc121614535cfac4caf4e002fe64e3db5  1240  backend/tests/test_cocoindex_client.py
61c1f47a43c8eb65beaf8ec2fa16743f292182e25fabb57775bf23b81ab96c0b    75  backend/tests/test_live_cocoindex_integration.py
02e256a655ef410e5c5086c9a9c2742ec5710e925ebcff932d7a4ca2380d02c3   130  docs/stories/AI-06.feature
4cf8df05311b8326be87a1b139579ddc2ca7a67c853d0db628e46a5fffa62d85   184  docs/stories/AI-06.md
98115f8a8f112a7eaa1a2f306167eb53492c11ecff834735fcaadf04a8ad6788   188  docs/adr/0008-cocoindex-code-adoption.md
6e257f2bc7247ce06897063ca39b2f5d9319baa49ccf4eb3e6a96de0525bd06a   196  docs/cocoindex-integration.md
567d84442be626af42154fca8ecfec2b69c7339bf198fbcd38396d50a516853c   335  docs/STATUS.md
6b11efd16a9a89f568b344f7dda15afca6999aba66a2a13a884586b462d6f6af   199  docs/reports/omp-cocoindex-pr1/IMPLEMENTATION.md
f63358898192544cb2a503330698ebb09a34532813a80a0135ea6f627fa6b702    86  docs/reports/omp-cocoindex-pr1/METRICS.md
d2c94ccba8409063770a32d22923bc1907e09d804427ed421fd1d2f9e0709498    71  docs/reports/omp-cocoindex-pr1/PROMPT_LOG.md
ce017f5165b10d17fc0ba330d71a8793987ffb9258c99e35e0637fe066bab24e   124  docs/reports/omp-cocoindex-pr1/capabilities/live-smoke.md
ebf4f4a7395bc661a3647c9b80717df5890dff0619cf81896f9254d0d18be072   151  docs/reports/omp-cocoindex-pr1/capabilities/live-summary.json
46acb51362b2d489da41988a92be04f6c2a6ca9c86b2fee726a955afd1ebdb75   113  docs/reports/omp-cocoindex-pr1/capabilities/live-run-manifest.json
```

New review/evidence files: `docs/reviews/AI-06-cocoindex-review.md` (prior verdict),
`docs/reports/omp-cocoindex-pr1/evidence/final-repair-*`,
`evidence/repair-live-test.log`, `evidence/repair-probe-summary.txt`.

Unrelated working-tree changes (`.gitignore`, `prompts/`, `.agents/`, `.omp/`, `skills-lock.json`)
remain excluded.

## 4. Key implementation excerpts (R3/R4)

Read the exact file for full context; these are the repaired control points:

```python
# cocoindex_mcp.py — saved group survives leader exit; bounded joins
def _stop(self, process):
    if self._reader is not None: self._reader.close(); self._reader = None
    if process is not None:
        if os.name == "posix" and self._pgid is not None:
            self._signal_group(signal.SIGTERM)
        elif process.poll() is None: process.terminate()
        term_wait = min(1.0, self._cleanup_timeout / 2.0)
        ...
        if os.name == "posix" and self._pgid is not None:
            self._signal_group(signal.SIGKILL)
        ...
        process.wait(timeout=self._cleanup_timeout)
    self._stop_stderr()   # select loop, stop flag, join <= 0.5s
    for stream in (...): ...close()

# cocoindex_mcp.py — deadline-aware write
os.set_blocking(self._stdin_fd, False)
selector.register(self._stdin_fd, selectors.EVENT_WRITE)
while view:
    if not selector.select(remaining): raise CocoIndexTimeoutError(...)
    try: written = os.write(self._stdin_fd, view[:4096])
    except BlockingIOError: continue
```

## 5. Evidence (repaired snapshot)

| Check | Result | Capture |
| --- | --- | --- |
| Backend suite | **370 passed, 3 skipped**, exit 0 | `evidence/final-repair-pytest-full.log` |
| CocoIndex contracts | **85 passed**, exit 0 | `evidence/final-repair-cocoindex-tests.log` |
| Live pytest (opt-in) | **1 passed**, exit 0 | `evidence/repair-live-test.log` |
| Fixture drift | exit 0 | `evidence/final-repair-fixturectl.log` |
| ruff / format / diff | exit 0 / 0 / 0 | `evidence/final-repair-ruff-*.log`, `evidence/final-repair-git-diff-check.log` |
| Network denial proof | probe exit 1 (`Network is unreachable`) | `evidence/final-repair-network-probe.log` |
| Network-denied suite | **370 passed, 3 skipped**, exit 0 | `evidence/final-repair-pytest-network-denied.log` |
| Live probe | all six steps ok; 3 hits; search 914.4 ms; exit 0 | `evidence/repair-probe-summary.txt`, `capabilities/live-summary.json`, `capabilities/live-run-manifest.json` |

Live configuration: isolated `fixtures/banking-demo` worktree at `baseline-a`
`0f8607b29d1ccb423062d856835f5310c9f54aa3`; CocoIndex 0.2.43; MCP `2024-11-05`;
`embeddinggemma-2:270m-q8_0-text` (768 dims); 12 files/16 chunks; hits `src/__init__.py` 1–1,
`src/transfers.py` 1–29, `src/accounts.py` 1–10, verified against the snapshot; `index_identity=null`.
The local Ollama endpoint was restored with a process-local `kubectl port-forward` to the approved
Service after the pre-repair run; no deployment changed.

**NOT RUN:** baseline-b isolation/refresh (PR 2), `.feature` semantic retrieval, retrieval-quality
metrics (AI-05), chat/GraphRAG, M2 explanations, production data handling; default-suite live test
skips.

## 6. Reviewer instructions

Decide whether this exact snapshot satisfies the AI-06 PR 1 slice, the 11 scenarios, and repository
invariants, including whether each round-1 finding is closed. Treat summaries/hashes/logs as claims
to check. Inspect the changed files and evidence; run read-only targeted checks if useful. Do not
edit, install, regenerate, commit, or delegate. Do not demand PR 2, API changes, `.feature` indexing,
GraphRAG, M2, or M3 closure. Check the lifecycle isolation, structural schema validation, deadline
and cleanup behavior, whole-envelope rejection, probe outcome propagation, live manifest, offline
default, proposal/accepted/evidence separation, untrusted text, and commit references. Return
**APPROVE**, **REQUEST_CHANGES**, or **NEEDS_INPUT** with stable finding IDs (`AI06-Rn`), severity,
affected criterion/invariant, and the smallest acceptable evidence/repair.
