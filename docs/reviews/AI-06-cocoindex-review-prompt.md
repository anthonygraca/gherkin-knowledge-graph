# AI-06 implementation review — submission 1 of 7

## 1. Scope, traceability, and gates

**Slice:** RAG mission PR 1 (CocoIndex variant) — "CocoIndex Code compatibility, integration
contract, and live smoke." **Story:** AI-06
([#56](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/56), open, label
`user-story`, sub-issue of F-08 [#14](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/14)).
**Owner:** A. **Implementer:** OMP. **Base:** `a674fb910bb31b866dd7417e45842cfa26a0b265`
(`main`). **Branch:** `feat/56-cocoindex-code`. **Review limit:** 7 submissions; this is 1.

**Mission premise correction.** The mission brief treated "M1 completed and independently reviewed"
as a premise to verify. The current records show the M1 engineering gate **SATISFIED**:
`docs/reviews/M1-review-2.md` is APPROVE at `e1497cf` (submission 2 of 7, `gpt-6.1-sol` xhigh), no
open major finding. The earlier `M1-review-attempt-1.md` credit-exhaustion record is historical.
M1 is not reopened. M2 is **not** implemented. `AGENTS.md` forbids starting later milestone work
while an earlier gate is unmet; roadmap §7 explicitly permits M3 work in parallel after M0, and the
mission selected this M3 slice. The conflict is recorded in `docs/stories/AI-06.md` and
`docs/STATUS.md`; this slice consumes no M2 semantics and does not claim M3 completion. Treat the
ordering disposition as a reviewed constraint; do not demand M2 implementation.

**Served issue:** #56 only. AI-01 (#30) is closed and is not reopened; AI-02 (#31), AI-03 (#32),
AI-04 (#34), AI-05 (#35) remain open. The slice does **not** deliver a real
`CandidateDiscovery`, a hit→`TraceCandidate` mapping, an API/schema change, scenario/requirement
semantic indexing, chat/GraphRAG, M2 findings, deployment, or a milestone closure.

**Proposed commit:** `feat(discovery): [issue #56] add optional CocoIndex Code search contract`
(body `Refs #56, #14`). No commit exists yet; this is the proposed reference for the reviewer to
check against the work served.

**Acceptance criteria:** `docs/stories/AI-06.feature`, sha256
`31d0044e8de0c254177fe345b2ce98f2d59c96839dd77a753f54493b0368292b`, 11 scenarios
(`SCN-1001`…`SCN-1011`). Full text below. The criteria advisory (REVISE) ran **before**
implementation; its nine findings are dispositioned in `docs/stories/AI-06.md`. No Gherkin runner
exists; scenarios map to pytest checks.

**User outcome:** an optional, bounded adapter returns attributable source-code hits from one
configured snapshot, with explicit version/contract checks, no link/evidence/assurance authority,
and no offline regression. A synthetic live smoke demonstrates the real MCP contract.

## 2. Canonical acceptance snapshot (normative; copied from the working tree at the hash above)

```gherkin
@AI-06 @issue-56 @M3
Feature: AI-06: CocoIndex Code semantic code-search capability and integration contract
  As a developer, I want an optional, bounded CocoIndex Code adapter that returns attributable
  source-code hits from one configured project snapshot, so that semantic code retrieval can be
  integrated later without weakening CTA's offline default or its separation of proposals,
  accepted relationships, and verification evidence.

  Rule: CocoIndex is optional and never required by default paths.

    @SCN-1001
    Scenario: Offline default is unchanged
      Given no CocoIndex executable, project root, daemon, or embedding endpoint is configured
      When the default configuration is loaded and a discovery request runs
      Then discovery uses the deterministic "fake" provider
      And no CocoIndex process is started
      And no CocoIndex index is accessed and no network request is made
      And "cocoindex" is not a registered discovery provider in this slice

  Rule: Requests and results are bounded observations.

    @SCN-1002
    Scenario: Search requests are bounded before execution
      Given a CocoIndex client with configured request bounds
      When a search requests a limit of 1 or 100, a non-negative offset, and a non-empty query
      Then the request is accepted
      And a limit of 0 or 101, a negative offset, an empty or over-2000-character query, or more than 10 path or language filters is rejected with "cocoindex-request-error" before any process starts
      And a path filter that is absolute, carries a drive or UNC prefix, contains a parent-directory component, or does not use relative POSIX path syntax is rejected with "cocoindex-request-error"
      And response bytes, per-hit content, and captured stderr have configurable limits

    @SCN-1003
    Scenario: A structured search returns normalized hits
      Given a captured structured result and a configured project root
      When the client normalizes the result
      Then it preserves the reported order and any duplicate chunks
      And every hit reports its project-relative path, language, 1-based line range, content, and score as reported
      And the configured project root is recorded as caller-supplied context, not as observed index identity
      And the server name and version are recorded when the server reports them
      And the index identity is reported as unavailable because the MCP contract does not expose it
      And a valid empty result is a success with no hits
      And no hit exposes a link id, review state, evidence id, verification claim, or assurance conclusion

    @SCN-1004
    Scenario: Malformed results are rejected whole, never repaired
      Given a result with an absolute path, a parent-directory escape, an empty path, an invalid line range, a non-finite score, a wrong field type, missing or non-text content, a mismatched response id, an MCP error flag, inconsistent counts, or a response beyond the configured bound
      When the client normalizes the result
      Then it raises "cocoindex-protocol-error"
      And the entire response is rejected, including any otherwise-valid hits, instead of returning a partial list
      And no invalid hit is dropped, clamped, or rewritten
      And no artifact identity is invented

    @SCN-1005
    Scenario Outline: Failures are typed and owned processes are reaped
      Given <condition>
      When a search is attempted
      Then it raises "<error>"
      And a process the adapter started is terminated and reaped within the configured cleanup interval, without stopping an unrelated shared daemon
      And the caller receives no hit list

      Examples:
        | condition                                            | error                         |
        | the executable is missing                            | cocoindex-configuration-error |
        | the project root has no CocoIndex settings marker    | cocoindex-configuration-error |
        | the server name, version, or search schema is incompatible | cocoindex-capability-error |
        | the server exits before initialize                   | cocoindex-unavailable         |
        | the server closes its output pipe                    | cocoindex-unavailable         |
        | the server exits non-zero                            | cocoindex-unavailable         |
        | the server does not answer before the deadline       | cocoindex-timeout             |
        | the server ignores termination after the deadline    | cocoindex-timeout             |
        | the search reports success false, even with partial results | cocoindex-query-error   |

  Rule: The adapter selects one configured project and validates what it returns.

    @SCN-1006
    Scenario: Only the configured project is selected and returned paths are validated
      Given a configured project root containing CocoIndex settings
      When the client searches
      Then the server runs with that project root as its working directory
      And the adapter never falls back to an ancestor CocoIndex project
      And only allow-listed subprocess environment variables are passed
      And when hits are verified against the snapshot, a missing file, a symlink resolving outside the root, a line range beyond end of file, or content that differs from the declared comparison rule is rejected

  Rule: Indexed repository text is untrusted data, not instruction.

    @SCN-1007
    Scenario: Instruction-like text stays data
      Given an indexed source file whose comments contain instruction-like text
      When the search returns a hit for that file
      Then the text is carried as data in the hit
      And it creates no link, review decision, evidence record, policy change, verification claim, or coverage claim

  Rule: Live integration evidence is explicit, attributable, and optional.

    @SCN-1008
    Scenario: Without live opt-in the probe reports NOT RUN
      Given live opt-in is not enabled
      When the capability probe runs
      Then it reports "NOT RUN" with the reason
      And it starts no CocoIndex process, accesses no CocoIndex index, and contacts no embedding endpoint
      And an offline suite that skips the live test does not satisfy a live acceptance criterion

    @SCN-1009
    Scenario: Opted-in prerequisites are unavailable
      Given live opt-in is enabled but the executable, project marker, daemon, or embedding runtime is unavailable
      When the capability probe runs
      Then it reports an explicit unavailable or failed outcome with the reason
      And it does not report a pass or substitute fake hits

    @SCN-1010
    Scenario: Opted-in execution fails
      Given live opt-in is enabled and a probe step fails
      When the capability probe runs
      Then the failure is reported with its typed error and step
      And the outcome is not reported as a pass, a skip, or a successful offline result

    @SCN-1011
    Scenario: An opted-in synthetic smoke is attributable
      Given explicit live opt-in, an installed CocoIndex release, a reachable embedding runtime, and a pinned synthetic fixture snapshot
      When that snapshot is indexed and the capability probe searches it for a hand-selected source-code target
      Then at least one returned path and line range exists at the recorded snapshot revision
      And the returned content equals that snapshot's lines for the range after removing a single trailing newline
      And the report records the CocoIndex version, embedding model, adapter revision, snapshot revision and content hashes, index isolation configuration, indexing outcome, server-reported index identity or explicit unavailability, latency, observed result fields, invocation, and raw report digest
      And the report claims a bounded integration observation only, not retrieval quality or requirement verification
```

## 3. Snapshot manifest and task diff

Base `a674fb9`. Working tree includes the new files below; unrelated working-tree changes
(`.gitignore`, `prompts/`, `.agents/`, `.omp/`, `skills-lock.json`) are **excluded** from this
slice and must not be reviewed as task content. `prompts/omp-codex-agentic-loop.md` was edited by
the owner during the session and is also excluded.

```text
7de622c65af9ce676f40805644ecf7d0a0276d3d13d15fdb4aff7f38dc958bc2    573  backend/app/discovery/cocoindex.py
0838847216a2dd848009feca5425c1dfa674a31ee981506baa932e2be544a4aa    620  backend/app/discovery/cocoindex_mcp.py
d045edcc07340c56f0a8f7919cba70a1ef7a31a1811304250a4af24867afcaee     89  backend/app/discovery/registry.py
b4b1d33193d284a10ecec824d59f17463fdd4925896b9942e657f5f9cf439cee    255  backend/app/settings.py
a90fa7560f88cfbc0abd768d1d319041847f031a006eff551f98d146a1d48fbd    925  backend/tests/test_cocoindex_client.py
8d406c018406511c88bc29ea3c4c31baa3c2945f4c994a2e1168f311ae73ca04     67  backend/tests/test_live_cocoindex_integration.py
0b627f1f3d47392ed51c4b45432546013fb5df8ab91437ac023bdae93835b343     58  backend/tests/fixtures/cocoindex-search-response.json
8e36d802983bf13c1c22d923b5e24a17ebffe4075b5c35f80a07f40832a79062    611  tools/probe_cocoindex.py
143b7e31d1b38108a423409a8b4b9059fba05199803d2832be5814fefa35f112    162  docs/adr/0008-cocoindex-code-adoption.md
d9a11e1472cd8bca6963d8297b2e1b3ec1a63bc0014b719c40949e27c1b1fc7f    184  docs/cocoindex-integration.md
f0567350e84a79f7cb75f71363e2a83108f9b9619adca89981d0b67e6a9e2572    162  docs/setup.md
f561f5d2816f236a32789e98ffd850db42269ea1e4b40474e529d020f20db355    106  docs/traceability-issue-map.md
31d0044e8de0c254177fe345b2ce98f2d59c96839dd77a753f54493b0368292b    129  docs/stories/AI-06.feature
ee09f92c79a7dac9c548ca2c4a44f3931a7679a5ec3376d37fdc310defcb77a3    165  docs/stories/AI-06.md
25f1f1846396a48471794a4897d95b98ee10860d06f1957c4c2ed6d1aa602016    321  docs/STATUS.md
```

Report/evidence files are under `docs/reports/omp-cocoindex-pr1/`; read
`IMPLEMENTATION.md`, `PROMPT_LOG.md`, `METRICS.md`, `capabilities/live-smoke.md`,
`capabilities/live-summary.json`, and `evidence/`. Hashes for those files are in the run log;
inspect the tree for the frozen values.

**Modified tracked files (task diff):**

```diff
diff --git a/backend/app/discovery/registry.py b/backend/app/discovery/registry.py
@@ -38,8 +38,8 @@
-                f"{', '.join(REGISTERED_PROVIDERS)}. Local model providers arrive with AI-02 (M3); "
-                f"they are optional plugins and never required for tests."
+                f"{', '.join(REGISTERED_PROVIDERS)}. Code-search candidates arrive with AI-06 "
+                f"PR 2; they are optional plugins and never required for tests."
diff --git a/backend/app/settings.py b/backend/app/settings.py
@@ new CTA_CCC_* names, fields, marker/home validation, cocoindex_enabled, load_settings wiring @@
+ENV_CCC_EXECUTABLE / ENV_CCC_PROJECT_ROOT / ENV_CCC_LIVE_OPT_IN / ENV_CCC_LIVE_TESTS
+ccc_executable, ccc_project_root, cocoindex_live_opt_in, ccc_live_tests
+live opt-in requires a root; a configured root must be a directory, not $HOME, with
+.cocoindex_code/settings.yml
diff --git a/docs/setup.md, docs/traceability-issue-map.md, docs/STATUS.md @@
+optional integration guide link; AI-06 map row/provenance note; slice state/evidence
```

`backend/app/domain/**`, `backend/app/api/**`, `backend/app/assurance/**`, fixtures, generated API
responses, frontend, and `SCHEMA_VERSION` are unchanged.

## 4. Implementation context and key boundaries

* **Agent plugin ≠ CTA runtime.** The OMP-mounted `cocoindex_code` MCP tool and the project
  `.cocoindex_code/` index are agent ergonomics. The CTA adapter invokes `ccc mcp` through
  `StdioMcpTransport`, validates the observed schema, and is tested separately. Do not treat the
  agent search as application evidence.
* **Not a `CandidateDiscovery`.** `app/discovery/cocoindex.py` has no `discover()` method, no
  repository, no link/review/evidence operation. `cocoindex` is not in `REGISTERED_PROVIDERS`.
  PR 2 owns path/line→artifact mapping and the additive API behavior.
* **Observed MCP contract.** 0.2.43: `initialize` → `serverInfo {name, version}`, protocol
  `2024-11-05`; tool `search(query, limit 1..100, offset, refresh_index, languages, paths)`;
  `tools/call` → `content[0].text` JSON `{success, results:[...], total_returned, offset, message}`.
  No index revision/hash/project identity. The adapter rejects a different version/schema.
* **Bounds/cleanup.** One process per call; total deadline (default 90 s, cap 600 s); process group
  SIGTERM→SIGKILL→reap; stderr drained concurrently and bounded; response line/payload 512 KiB;
  hit content 256 KiB; request path/query/filter bounds. `refresh_index=false` by default.
* **Environment.** Child sees only allow-listed keys (PATH, HOME, locale, TMPDIR,
  XDG_RUNTIME_DIR, COCOINDEX_CODE_DIR/RUNTIME_DIR, OLLAMA_API_BASE, CA bundles). CTA keys and
  `GITHUB_TOKEN` are dropped. The shared daemon is not started/stopped/signalled.
* **Provenance.** Configured root is caller-supplied context; `index_identity=None` is explicit.
  The probe records an external index-file SHA-256 with the method, plus snapshot revision,
  settings/adapter hashes, latency, hits. The live check resolves paths inside the root and
  compares content after removing one trailing newline.
* **Untrusted text.** Instruction-like content is only `content`. No acceptance, review, evidence,
  policy, verification, or coverage operation exists in the result/client.
* **No API/schema change.** `POST /api/discovery` and `GET /health` unchanged; no fixture
  regeneration. The captured `backend/tests/fixtures/cocoindex-search-response.json` is harness
  data from a real response, not an oracle or generated API response.

## 5. Evidence

Full reports: `docs/reports/omp-cocoindex-pr1/IMPLEMENTATION.md` (AC table, commands), `METRICS.md`,
`capabilities/live-smoke.md`, `capabilities/live-summary.json`, and `evidence/final-*` captures.

| Check | Actual result | Capture |
| --- | --- | --- |
| `uv run --project backend pytest backend/tests -q` | **348 passed, 3 skipped**, exit 0 | `evidence/final-pytest-full.log` |
| `pytest backend/tests/test_cocoindex_client.py -q` | **63 passed**, exit 0 | `evidence/final-cocoindex-tests.log` |
| `CTA_CCC_LIVE_TESTS=1 … test_live_cocoindex_integration.py -q` | **1 passed**, exit 0 | `evidence/live-test.log` |
| `fixturectl.py verify` | exit 0 | `evidence/final-fixturectl-verify.log` |
| `ruff check .` | exit 0 | `evidence/final-ruff-check.log` |
| `ruff format --check .` | exit 0 | `evidence/final-ruff-format.log` |
| `git diff --check` | exit 0 (empty) | `evidence/final-git-diff-check.log` |
| network denial proof + suite | probe exit 1 (`Network is unreachable`); suite **348 passed / 3 skipped**, exit 0 | `evidence/network-denial-probe.log`, `evidence/final-pytest-network-denied.log` |
| offline probe | `NOT RUN`, exit 0, no process/contact | `evidence/final-probe-offline.log` |
| live probe | all six steps ok, exit 0; 3 hits verified; 984.6 ms warm | `evidence/probe-summary.txt`, `capabilities/live-summary.json` |

**Live observation:** isolated `fixtures/banking-demo` worktree at `baseline-a`
`0f8607b29d1ccb423062d856835f5310c9f54aa3`, clean; CocoIndex 0.2.43; MCP `2024-11-05`; LiteLLM
`ollama/embeddinggemma-2:270m-q8_0-text` (768 dims); 12 files/16 chunks; hits
`src/__init__.py` 1–1 (0.7128), `src/transfers.py` 1–29 (0.7049), `src/accounts.py` 1–10 (0.6955);
index SHA-256 `59a34c…` external; `index_identity=null`. Only synthetic content was sent.
Cold search was 26–53 s, index build 2m31.9 s; warm search 984.6 ms. This is a capability
observation, not retrieval quality.

**Explicitly NOT RUN:** baseline-b worktree/index isolation and incremental refresh (PR 2);
`.feature`/requirement semantic retrieval (outside the code corpus; future story); retrieval-quality
metrics (AI-05); chat/GraphRAG; M2 finding explanations; production data-handling/license review;
the default suite's live test (skipped, not a pass).

**Negative/injection cases:** malformed envelope/ids/types/counts, non-text content, bad paths/lines/
scores, oversized payloads/content, `success=false` with partial results, tool error, missing
executable/marker, incompatible version/schema, early exit, pipe close, timeouts with SIGTERM-ignored
child, stderr noise, secret-env canaries, symlink escape, snapshot content mismatch, instruction-
like text. All are covered by the 63 offline tests.

**Confidentiality/redaction:** the sanitized report contains no absolute paths, endpoint URLs, keys,
or raw content; `grep` for `/tmp`, `localhost`, `/home` returned no matches. The raw report, daemon
logs, and index remain outside Git. The live evidence uses only the synthetic banking fixture.

## 6. Reviewer instructions

Decide whether this exact working-tree snapshot satisfies the selected AI-06 PR 1 slice, every
applicable scenario above, and repository invariants. Treat the coordinator's summaries, hashes,
and test logs as claims to check against the tree and captures. Inspect the exact files and
evidence paths; run read-only targeted checks if useful (do not install dependencies, regenerate
fixtures, edit files, commit, or delegate). Do not demand PR 2's candidate mapping, API changes,
`.feature` indexing, GraphRAG, M2 implementation, or M3 closure. Check specifically:

* CocoIndex 0.2.43's actual MCP contract and that the adapter validates it, not an invented schema;
* agent-side plugin/MCP usage is not being mistaken for the CTA runtime adapter;
* configured project selection, no ancestor fallback, allow-listed env, bounded process lifetime,
  and honest index-identity unavailability;
* path/line/content verification against the snapshot and the trailing-newline rule;
* offline default: no `ccc`, index, daemon, network, model, or vector store in default tests/CI;
* proposal/accepted/evidence separation: the adapter cannot create links, review state, evidence,
  findings, verification, or coverage claims;
* response bounds, whole-response rejection, typed errors, and cleanup after timeouts;
* untrusted retrieved text and prompt-injection resistance;
* independent labels/oracles unchanged, generated vs captured test data, no fixture/API drift;
* the M1 premise correction and the recorded M3/AGENTS ordering conflict;
* sanitized evidence, no secrets/paths/endpoints, and the exact command/exits.

Request missing runtime proof rather than inferring a pass. Distinguish confirmed defects from
hypotheses. Return **APPROVE**, **REQUEST_CHANGES**, or **NEEDS_INPUT** with stable finding IDs
(`AI06-Rn`), severity, the criterion/invariant affected, and the smallest acceptable evidence or
repair. Do not edit, repair, regenerate, commit, or delegate.
