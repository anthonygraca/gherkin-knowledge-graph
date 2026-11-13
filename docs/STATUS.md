# Status

```text
Date:                2026-11-13
Current branch:      main at a674fb9 (RAG PR 1 hosted-provider slice merged); local task
                     branch feat/56-cocoindex-code based on a674fb9
Milestone:           M0 — exit gate SATISFIED by re-review round 2 (historical record below)
                     M1 — exit gate SATISFIED by independent review round 2 at e1497cf;
                     no open major finding
                     M2 — not implemented
                     M3 — AI-06 PR 1 (CocoIndex capability/contract/live smoke) implemented
                     locally; review 1 REQUEST_CHANGES (8), review 2 REQUEST_CHANGES (3),
                     review 3 REQUEST_CHANGES (R2/R5), review 4 REQUEST_CHANGES (R2/R5), all repaired;
                     review 5 APPROVE (submission 5 of 7); AI06-R9 minor metadata repaired;
                     AI-02/AI-03/AI-05 open
Active task:         AI-06 (#56) CocoIndex Code capability and integration contract (M3)
Independent review:  docs/reviews/M0-review.md — first review: "M0 not verified"
                     docs/reviews/M0-rereview-1.md — re-review round 1 (GPT-6.1 Sol, xhigh):
                     NEEDS_INPUT; R1–R7 all repaired; AC-1.1…AC-1.8 and AC-2.1…AC-2.5 all PASS;
                     sole blocker R8 (no recorded human review of the hand-labeled oracle)
                     docs/reviews/M0-oracle-human-review.md — the owner's attestation (R8
                     evidence, sha256-tied to the three oracle files at revision 191c829)
                     docs/reviews/M0-rereview-2.md — re-review round 2 (GPT-6.1 Sol, xhigh):
                     APPROVE at snapshot bca69cf (tree e55ff9f); R8 repaired/closed; no open
                     major finding; M0 exit criteria verified within scope
                     docs/reviews/M1-review.md — M1 round 1 NEEDS_INPUT (all 40 criteria and the
                     engineering exit PASS; E1 hosted evidence, N1/N2); repairs landed
                     docs/reviews/M1-review-2.md — M1 round 2 APPROVE at e1497cf, submission
                     2 of 7; E1/N1/N2 closed; no open major finding
                     docs/reviews/AI-01-hosted-provider-review-4.md — PR 1 provider slice
                     APPROVE at submission 4 of 7; R1/R5 closed; implementation snapshot
                     docs/reviews/AI-01-hosted-provider-review-5.md — post-approval probe/test
                     change and sanitized live chat/schema evidence APPROVE at submission 5 of 7;
                     embeddings NOT RUN
                     AI-06 criteria advisory: docs/reports/omp-cocoindex-pr1/reviews/
                     advisory-criteria.md (REVISE before implementation; not an acceptance review)
                     docs/reviews/AI-06-cocoindex-review.md — AI-06 submission 1 of 7
                     REQUEST_CHANGES (8 findings AI06-R1…R8); repairs completed
                     docs/reviews/AI-06-cocoindex-review-2.md — AI-06 submission 2 of 7
                     REQUEST_CHANGES (R1/R2/R5 open; R3/R4/R6/R7/R8 closed); repairs completed
                     docs/reviews/AI-06-cocoindex-review-3.md — AI-06 submission 3 of 7
                     REQUEST_CHANGES (R1 closed; R2/R5 open); repairs completed
                     docs/reviews/AI-06-cocoindex-review-4.md — AI-06 submission 4 of 7
                     REQUEST_CHANGES (R2/R5 open); repairs completed
                     docs/reviews/AI-06-cocoindex-review-5.md — AI-06 submission 5 of 7
                     APPROVE; R2/R5 closed, R1/R3/R4/R6/R7/R8 remain closed; AI06-R9 minor
                     metadata repaired; approval covers this PR 1 slice only
Historical (SETUP-01, 2026-11-12): the commit-reference slice landed via PR #42; commitlint
                     green on the landed history (9 commits); the M0 approved snapshot bca69cf
                     had 107 passed; the SETUP-01 tree then had 135 passed (also under an
                     OS-level network denial). Outstanding owner actions: #18/#19 closure, the
                     FT-03/project-definition reviews, the required-check ruleset, README work item.
Tests executed:      AI-06 repaired snapshot (local branch): 402 backend passed, 3 opt-in skips
                     (default suite); CocoIndex contract module 117 passed; opt-in live test
                     1 passed; fixturectl verify exit 0; ruff, format, and `git diff --check`
                     clean; network-denied suite 402 passed. Live probe: all six steps ok; search
                     886.4 ms warm; 3 hits verified against snapshot 0f8607b; index identity
                     unavailable by contract; isolated daemon/index hash recorded before/after.
                     PR 1 hosted-provider snapshot: 285 backend passed, 2 opt-in skips
                     (also under an OS-level network denial, probe DENIED); live chat HTTP 200 /
                     54 tokens / 553.3 ms, schema JSON 200 / 92 tokens; live chat test 1 passed;
                     embeddings unavailable (connection refused), live embeddings test NOT RUN.
                     M1 integrated snapshot 29df105: 233 backend passed (also under an OS-level
                     network denial, probe DENIED); frontend 10 passed; fixturectl verify exit 0;
                     ruff and `git diff --check` clean; commitlint 25 commits; hosted run
                     43370472013 (all three jobs) success.
                     AS-04 approved snapshot: 233 passed / 10 frontend; PR #49 merged as 29df105;
                     issue #26 closed.
                     AS-01 approved snapshot: 233 passed; PR #48 merged as d238776; issue #2 closed.
                     DT-04 approved snapshot: 227 passed; PR #47 merged as c43541b; issue #23 closed.
                     DT-03 approved snapshot: 219 passed; PR #46 merged as 0970f7a with both
                     hosted checks passing; issue #22 closed.
                     DT-02 approved snapshot: 208 passed; PR #45 merged as 590e776 with both
                     hosted checks passing; issue #21 closed.
                     DT-01 approved snapshot: 183 passed; PR #44 merged as 26a25d0 with both
                     hosted checks passing; issue #20 closed.
Current API/schema version: 0.2.0 (unchanged by AI-06: no API/domain/fixture shape change)
Tracker:             docs/traceability-issue-map.md (features → user stories → tasks)
Run records:         docs/reports/omp-m0-rereview/, docs/reports/omp-setup-01-commitlint/,
                     docs/reports/omp-m1-milestone/, docs/reports/omp-rag-pr1/, and the six
                     omp-<task> report folders
                     (reports, prompt logs, metrics, evidence, packets; excluded from ruff scope
                     — records, not sources)
Environment:         Python ≥3.11, uv, git ≥2.28; no GPU, LLM, vector store, Docker, or network
                     during tests
```

## Roadmap execution — M1 (active)

Run started 2026-11-13T00:44Z from `e18cdcf` in roadmap mode with the milestone ceiling at M1.
GitHub authority for this run: scoped issue updates, branch pushes, PR creation, and merges after
required CI and independent/owner reviews. M0's gate is satisfied; **M1's gate is not yet
satisfied**. Lifecycle note: the draft `project-definition.md` intent/obligations and the M0
feature-extraction reviews remain owner dispositions; M1 stories derive from the roadmap and do
not claim that draft as an approved baseline.

| Story | GitHub | Owner | Canonical feature | State |
| --- | --- | --- | --- | --- |
| DT-01 requirements + scenarios parsed | [#20](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/20) | B | [DT-01.feature](stories/DT-01.feature) | **merged** PR [#44](https://github.com/anthonygraca/gherkin-knowledge-graph/pull/44) → `26a25d0`; APPROVE at submission 5; issue closed |
| DT-02 source/test artifacts | [#21](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/21) | B | [DT-02.feature](stories/DT-02.feature) | **merged** PR [#45](https://github.com/anthonygraca/gherkin-knowledge-graph/pull/45) → `590e776`; APPROVE at submission 4; issue closed |
| DT-03 typed links + review state | [#22](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/22) | B | [DT-03.feature](stories/DT-03.feature) | **merged** PR [#46](https://github.com/anthonygraca/gherkin-knowledge-graph/pull/46) → `0970f7a`; APPROVE at submission 2; issue closed |
| DT-04 requirement thread | [#23](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/23) | B | [DT-04.feature](stories/DT-04.feature) | **merged** PR [#47](https://github.com/anthonygraca/gherkin-knowledge-graph/pull/47) → `c43541b`; APPROVE at submission 2; issue closed |
| AS-01 missing-link finding | [#2](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/2) | C | [AS-01.feature](stories/AS-01.feature) | **merged** PR [#48](https://github.com/anthonygraca/gherkin-knowledge-graph/pull/48) → `d238776`; APPROVE at submission 1; issue closed |
| AS-04 findings/coverage summary | [#26](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/26) | C | [AS-04.feature](stories/AS-04.feature) | **merged** PR [#49](https://github.com/anthonygraca/gherkin-knowledge-graph/pull/49) → `29df105`; APPROVE at submission 3; issue closed |

Per-task reports live under `docs/reports/omp-<task-slug>/`; each carries the AC-to-check table,
actual commands/exits, the snapshot identity, and the independent verdict. Issue closure is
recorded separately from implementation, approval, and merge.

### M1 milestone — exit gate satisfied (2026-11-13)

All six M1 stories are independently approved and merged (`26a25d0`, `590e776`, `0970f7a`,
`c43541b`, `d238776`, `29df105`); issues #20/#21/#22/#23/#2/#26 are closed. The exit demo and
checks are recorded in [omp-m1-milestone/IMPLEMENTATION.md](reports/omp-m1-milestone/IMPLEMENTATION.md):

* REQ-001 thread with SCN-001/CODE-001/TEST-001, LNK-001..003, EV-001 (tag/SHA identical).
* REQ-002 `missing_verification_link` from the deterministic evaluator and in the UI.
* 233 backend tests (normal and network-denied), 10 frontend tests, fixture verify, ruff,
  commitlint, and hosted CI run `43370472013` all pass.

**M1 gate: SATISFIED.** Independent milestone review round 2 **APPROVE** at review tree `e1497cf`
(submission 2 of 7, `gpt-6.1-sol` at `xhigh`): all 40 story criteria and the engineering exit PASS,
no open major finding. Round 1 NEEDS_INPUT (M1-E1 retained hosted evidence, M1-N1 OpenAPI text,
M1-N2 packet digest) was repaired; the credit-exhaustion attempts did not consume submissions.
Approval covers the M1 **engineering** gate only — stakeholder validation, human labels/link
decisions, and release authorization remain owner gates.

## RAG mission — PR 1 hosted provider slice (local, approved; publication authorized)

As of 2026-11-13T16:36Z, the M1 milestone gate remains **SATISFIED** at the independent
engineering review (`docs/reviews/M1-review-2.md`); M1 is not reopened. The RAG mission's PR 1 slice
is implemented locally on `feat/30-hosted-ai-provider` (base `60dcc1f`) and independently
**APPROVE** at submission 4 of 7 (`docs/reviews/AI-01-hosted-provider-review-4.md`); the
post-approval probe/test change and live evidence were independently **APPROVE** at submission 5 of
7 (`docs/reviews/AI-01-hosted-provider-review-5.md`).

* **Served issue:** AI-01 [#30](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/30)
  (closed) — follow-up on its real-provider boundary; PR 1 does not reopen/close AI-01 or claim
  AI-02/AI-03/AI-05. It does not deliver a real `CandidateDiscovery`.
* **Delivered:** typed chat/embedding protocols, deterministic fake providers, OpenAI-compatible
  HTTP adapters with bounded retry/timeout/redaction, construction-time settings validation, a
  synthetic-canary capability probe, 52 provider tests (50 offline + 2 opt-in skips), ADR 0007, and
  operator docs. No API/schema/fixture/assurance change.
* **Checks:** 285 backend passed / 2 skipped (also under an OS-level network denial), fixture verify,
  ruff, format, and `git diff --check` clean. Evidence:
  [omp-rag-pr1/IMPLEMENTATION.md](reports/omp-rag-pr1/IMPLEMENTATION.md).
* **Live path:** **RUN (partial, post-approval)** — with process-only `CTA_AI_MODE=live` and the
  observed catalogue model `deepseek-ai/DeepSeek-V4.1-Flash-1017`, chat returned HTTP 200
  (`finish_reason=stop`, 54 tokens, 553.3 ms) and schema-constrained JSON parsed (92 tokens). The
  configured model `deepseek-ai/DeepSeek-V4.1-Flash` was not in the catalogue and returned 404.
  Embeddings are **NOT RUN** — the configured local endpoint refused the connection.
* **Publication:** user-authorized on 2026-11-13T16:39:52Z (“stop after the first PR has been
  merged”); branch push, PR creation, and merge are authorized after required checks. No issue
  creation, issue closure, force push, or deployment is authorized. Local commits: `b722ef7`
  (implementation), `59d8644` (submission-4 records), `c113ae9` (traceability), `d7f9203`
  (post-approval probe/test fix), `01f8f16` (submission-5 records); this record is pre-PR. The PR
  and merge outcome are recorded in GitHub and the final run summary. PR 2/PR 3 are not started;
  PR 3 still needs a real story issue with human-reviewed criteria.

## RAG mission — AI-06 CocoIndex Code slice (approved at submission 5; publication pending)

**As of 2026-11-13T17:50Z**, the M1 engineering gate remains **SATISFIED**
(`docs/reviews/M1-review-2.md`); M1 is not reopened. The RAG mission's second slice is **AI-06**
([#56](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/56)), an
implementation-approach story under F-08 (#14) created with the run's issue-creation authority. It
adopts CocoIndex Code 0.2.43 for semantic *code* search and does **not** amend or close AI-01 (#30),
AI-02 (#31), AI-03 (#32), AI-04 (#34), or AI-05 (#35). AI-02's "no request leaves the machine"
criterion is not satisfied by the external Ollama runtime used for the smoke.

* **Delivered locally (uncommitted at this record):** `app/discovery/cocoindex.py` (typed models,
  errors, fake transport, normalization), `app/discovery/cocoindex_mcp.py` (bounded `ccc mcp` stdio
  transport with mandatory isolated state/runtime), `CTA_CCC_*` settings with offline defaults,
  `tools/probe_cocoindex.py`, 117 offline contract tests, an opt-in live test, the captured MCP
  response fixture, ADR 0008, the integration guide, and the AI-06 canonical feature/companion.
* **No API/domain/fixture change:** `POST /api/discovery`, `GET /health`, `SCHEMA_VERSION` 0.2.0,
  the fixture oracle, and `FakeCandidateDiscovery` are unchanged. `cocoindex` is not a registered
  discovery provider; PR 2 owns hit-to-`TraceCandidate` mapping.
* **Verification:** 402 backend passed / 3 opt-in skips in the default suite; CocoIndex contract
  module 117 passed; `fixturectl verify`, ruff, format, and `git diff --check` clean (final repaired
  captures under `docs/reports/omp-cocoindex-pr1/evidence/`).
* **Live path:** **RUN (pass)** with explicit opt-in on an isolated `fixtures/banking-demo`
  worktree at `baseline-a` (`0f8607b`), CocoIndex 0.2.43, MCP protocol `2024-11-05`, local
  `embeddinggemma-2:270m-q8_0-text`; 3 hits verified against the snapshot, warm search 886.4 ms,
  `index_identity=null` by contract. The probe records the isolated daemon PID and index SHA-256
  before/after. Evidence: [capabilities/live-smoke.md](reports/omp-cocoindex-pr1/capabilities/live-smoke.md)
  and [live-run-manifest.json](reports/omp-cocoindex-pr1/capabilities/live-run-manifest.json).
* **Lifecycle:** `ccc mcp` starts/restarts a daemon and always schedules a background index. CTA
  requires isolated `COCOINDEX_CODE_DIR`/`COCOINDEX_CODE_RUNTIME_DIR`, refuses the default shared
  state and the project-local state directory, and does not claim a session leaves an index
  unchanged.
* **NOT RUN:** baseline-b isolation/indexing, `.feature` semantic retrieval, retrieval-quality
  metrics, chat/GraphRAG, production data-handling review, and the default suite's live test
  (skipped; not a pass).
* **Gates:** M1 satisfied; M2 not implemented. Roadmap §7 permits M3 work in parallel after M0;
  `AGENTS.md`'s stricter "no later milestone while an earlier gate is unmet" reading is recorded as
  a conflict in `docs/stories/AI-06.md`. This slice consumes no M2 semantics and does not claim M3
  completion.
* **Review:** independent review 1
  ([AI-06-cocoindex-review.md](reviews/AI-06-cocoindex-review.md), submission 1 of 7) returned
  **REQUEST_CHANGES** with eight findings. Review 2
  ([AI-06-cocoindex-review-2.md](reviews/AI-06-cocoindex-review-2.md), submission 2 of 7) closed
  R3/R4/R6/R7/R8 and left R1/R2/R5 open. Review 3
  ([AI-06-cocoindex-review-3.md](reviews/AI-06-cocoindex-review-3.md), submission 3 of 7) closed
  R1 and kept R2/R5 open. Review 4
  ([AI-06-cocoindex-review-4.md](reviews/AI-06-cocoindex-review-4.md), submission 4 of 7) kept
  R2/R5 open. Round 5 repairs: field-specific schema allowlists, rejection of conflicting outer
  filter keywords, and independent normalization of every supplied payload. Submission 5
  **APPROVE**; the only finding (AI06-R9, minor stale report metadata) was repaired after
  approval. Publication is pending. The pre-implementation
  criteria advisory (REVISE, incorporated) is under
  `docs/reports/omp-cocoindex-pr1/reviews/`. No approval is claimed.

## M0 tracker closure (2026-11-13T06:49:39Z)

The M0 engineering gate was already independently approved at `bca69cf`
(`docs/reviews/M0-rereview-2.md`); the remaining open items were tracker hygiene. All six were
closed with evidence comments and milestone 3 was closed with **7 closed, 0 open**:

| Issue | Closure basis |
| --- | --- |
| [#8](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/8) SETUP-01 | `CONTRIBUTING.md` (`d4dc0ca`, Refs #8), recorded retro-attribution, and the CI commit-reference job (`37135cf`, PR #42 → `d4af73a`, hosted runs green) |
| [#18](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/18) FT-01 | M0 APPROVE; fixture generator/oracle tests and drift guard; owner oracle attestation |
| [#19](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/19) FT-02 | M0 APPROVE; contract/API tests. Its M0 501 for `POST /api/assurance/evaluate` was intentionally superseded by AS-01 in M1 |
| [#30](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/30) AI-01 | M0 fake-provider slice and port contract; real adapter is AI-02 (#31, M3) |
| [#34](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/34) AI-04 | Discovery API and ranked-proposal tests; no accepted/evidence writes |
| [#7](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/7) F-01 | Feature parent; its stories are closed and the M0 gate is approved |

## SETUP-01 commit-reference enforcement — landed (2026-11-12)

The previously uncommitted SETUP-01 follow-up slice (#8) was resumed, re-verified on base `f34ae07`
(focused 28 passed; full suite 135 passed — also under an OS-level network denial; `fixturectl
verify` exit 0; ruff and `git diff --check` clean), repaired per review round 1, and **approved** in
round 2 at snapshot v2 (`2026-11-12`):

* **Round 1 (submission 1 of 7) — REQUEST_CHANGES.** R1 (blocking): the bare `pull_request` trigger
  omitted `edited`, so a PR retargeted to a new base was never re-checked — repaired in
  `.github/workflows/ci.yml` (`types: [opened, synchronize, reopened, edited]`), rechecked in
  `reports/omp-setup-01-commitlint/probes/`. R2 (records): repaired.
* **Round 2 (submission 2 of 7) — APPROVE.** R1/R2 closed, all eight scenarios PASS, no new
  blocking finding; the reviewer confirmed all seven slice hashes and the 34-file manifest.

**Local commits** on `ci/8-commit-reference-enforcement` (base `f34ae07`; checkpoint `a82e466`):
`37135cf` — the slice (`ci(traceability): [issue #8] enforce commit references in CI`); the
review-record pair (`docs(review)`); and this commit (`docs(reports)` — records plus this file).
Audits after the local commits: range `--base f34ae07 --head HEAD` → 5 commits, exit 0; full
history → 8 commits, exit 0; the landed `main` reports 9 commits, exit 0.

**Landed (owner-merged 2026-11-12T05:23:12Z):** PR **#42** merged as
`d4af73a514d90a9784329303c03c49e996113c19` with a conforming subject
(`docs: [issue #8] Merge pull request #42 …`). Hosted runs: PR run `43158573099` (both checks pass)
and main push run `43161043845` — **Commit references pass** and **Offline contract, fixture, and
API tests pass**. Issue #8 remains open by design (`Refs`, not `Closes`). The task retrospective is
[reports/omp-setup-01-commitlint/RETROSPECTIVE.md](reports/omp-setup-01-commitlint/RETROSPECTIVE.md);
its run rules are folded into `prompts/omp-codex-agentic-loop.md`, which now also records the M1
handoff for the next session. Still outstanding / owner actions: the required-status-check ruleset
(`Administration: write` needed), tracker closure of #18/#19, the FT-03/project-definition reviews,
and the uncommitted README rewrite (its own work item). The `edited` retargeting trigger path has
not been exercised hosted. Full records:
[reports/omp-setup-01-commitlint/IMPLEMENTATION.md](reports/omp-setup-01-commitlint/IMPLEMENTATION.md),
[reviews/SETUP-01-review.md](reviews/SETUP-01-review.md),
[reviews/SETUP-01-review-2.md](reviews/SETUP-01-review-2.md).

## What exists

* Reproducible fixture history for `banking-demo`: four commits, fixed SHAs, tags `baseline-a`
  and `baseline-b`, verified identical across builds in the same environment.
* Hand-labeled oracle covering coverage gaps, a pending proposal, a superseded requirement, a
  reverification case, and a confirmed failure — with explicit negative expectations.
* Domain contracts: artifacts, links, evidence, candidates, findings, envelopes, ports, error
  codes, severity policy, stable finding fingerprints.
* Mock services: fixture-backed `FixtureStore`, `SampleFindingsSource` (findings replay), and the
  fixture `CandidateDiscovery` provider. All offline.
* API: reads and discovery implemented; three endpoints frozen as contracts and returning 501
  with the owning story.
* 107 offline tests (92 at the first review; the repair commits added 15), including proof that
  committed generated fixtures are what the generator produces and proof that the fixture's own
  suite passes at `baseline-a` and fails exactly twice at `baseline-b`.

## Findings and their dispositions (M0)

The independent review is ground truth. Reproduce before repairing; do not declare the milestone
complete while a major finding is open. No major finding is open at the approved snapshot.

All findings below have repair commits and regression tests on branch `feat/8-m0-foundation`
(PR #38). Round 1 dispositioned R1–R7 as repaired, passed every M0 acceptance criterion, and
raised one blocking evidence gap — R8, no recorded human review of the hand-labeled oracle. The
repository owner's attestation is recorded at `docs/reviews/M0-oracle-human-review.md`, and
round 2 (`docs/reviews/M0-rereview-2.md`) **approved** the snapshot `bca69cf` with **no open
major finding**, satisfying the independent-review gate in `AGENTS.md`'s milestone definition
of done. Milestone closure itself (undraft/merge PR #38, closing #18/#19) is a team action;
this session made no push.

| Finding | Severity | What it meant | Repair | Regression test |
| --- | --- | --- | --- | --- |
| R1 | major | `FixtureStore` did not satisfy the declared `ArtifactRepository` port and routes depended on the concrete class | Store implements the port (`baselines`, `resolve_baseline`, `get_artifact`, `list_artifacts`, `list_links`, `list_evidence`, `changed_artifacts`); routes depend on `RepositoryDep`; the two fixture-only surfaces are named in code | `test_contract_boundaries.py::test_consumer_can_read_everything_through_the_port_alone`, `::test_store_satisfies_the_artifact_repository_port` |
| R2 | major | `ThreadResponse` accepted a non-accepted link inside `accepted_links` | `validate_link_partition` is applied to `ThreadResponse` and `BaselineSnapshot`; the loader rejects a mispartitioned file | `::test_thread_response_rejects_a_proposal_inside_accepted_links`, `::test_thread_response_rejects_an_accepted_link_inside_proposals`, `::test_loader_rejects_a_mispartitioned_thread_file` |
| R3 | major | `verify` reported success for a tampered or deleted `expected/baselines.json` | `compare_file` replaces the directory walker for the manifest, with explicit absence handling; CLI gains `--baselines` | `test_fixture_drift.py::test_drift_detection_fails_when_the_baseline_manifest_is_tampered`, `::test_drift_detection_fails_when_the_baseline_manifest_is_missing` |
| R4 | minor | Thread and sample-findings loaders served files declaring an unsupported `schema_version` | Shared `require_supported_schema_version` used by the snapshot, thread, findings, and candidate-index loaders | `::test_served_responses_reject_an_unsupported_schema_version`, `::test_snapshot_and_index_versions_are_enforced` |
| R5 | minor | The generator inherited `GIT_DEFAULT_HASH`, so baselines differed under another object format | `GIT_DEFAULT_HASH=sha1` pinned in the generator environment and documented | `test_fixture_repo.py::test_generator_pins_the_object_format` |
| R6 | minor | The fingerprint test took its expected value from the production helper | Three independently computed fingerprint vectors with duplicate and out-of-order ids | `test_domain_contracts.py::test_fingerprint_matches_an_independently_computed_vector` |
| R7 | minor | The review prompt's fixture-test command failed collection | Prompt now runs pytest from each worktree root and explains why | — (documentation; exercised manually) |
| R8 | major (evidence gap) | Round 1 raised: no recorded human review of the hand-labeled oracle (`AGENTS.md` invariant 6) | Repository-owner attestation recorded (`docs/reviews/M0-oracle-human-review.md`), tied to the three files' sha256 values at `191c829`; final disposition in round 2 | — (human record, not an automated test) |

**NOT VERIFIED** in the M0 re-review run (state honestly in any report; none of these establishes
an unmet M0 criterion):

* hosted GitHub Actions execution — verified since: push runs `43062001235` (`efa824b`),
  `43122387139` (`2481087`), and `43124897661` (`f34ae07`) completed successfully on 2026-11-11/12;
  the new **Commit references** job has not run yet (workflow unlanded);
* the first review's macOS / Git 2.54 environment — accepted limitation; the generator pins the
  object format and every identity/date/TZ input (R5);
* `uv run --offline` under an OS-level network denial — the network-denied suite ran the venv
  interpreter directly under `unshare -rn`, with the denial proven effective;
* browser/UI behavior — no frontend exists in M0 (arrives with C-PR1, AS-04/AS-05);
* general staleness/failure classification beyond the labeled fixture cases — M2 (C: AS-02/AS-03);
* side-effect freedom for future provider plugins — M3 (A: AI-02/AI-04).

## Next tasks (in order)

**Development lifecycle alignment:** The owner's requested process is documented in
[development-lifecycle.md](development-lifecycle.md), starting with the draft
[project definition](project-definition.md). FT-01/FT-02 criteria have been extracted without
wording changes into `.feature` files and mapped to the existing pytest checks in
[the M0 index](stories/M0-foundation.md#acceptance-verification-map). This is a specification
organization change, not new requirement approval, direct Gherkin execution, or another M0
independent re-review. Review the draft intent and extracted criteria/mappings before claiming
a new accepted lifecycle baseline. The implementation/landing prerequisites below still apply.
The adoption slice is story **FT-03**
([#39](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/39)) — see its
[criteria](stories/FT-03.feature) and [record/verification map](stories/FT-03.md). Its author
checks are recorded; the review of the draft intent and of the extracted criteria/mappings
remains outstanding, so nothing here changes the M0 approval recorded above.

| # | Task | Issue | Acceptance condition |
| --- | --- | --- | --- |
| 1 | **Re-review M0** — done: round 1 NEEDS_INPUT (R1–R7 repaired; ACs PASS; R8), owner attestation recorded, round 2 **APPROVE** at `bca69cf` (`docs/reviews/M0-rereview-1.md`, `M0-rereview-2.md`) | #18, #19 | Every R1–R7 finding reported `repaired` with command output; no open major finding — met |
| 2 | **Land the work** — PR #38 is merged as `efa824b` (2026-11-11) with a successful hosted CI push run (`43062001235`); the remaining tracker action is closing #18/#19 | #18, #19 | PR #38 merged — met; hosted CI confirmed; tracker closure of #18/#19 outstanding |
| 3 | **Then start B-PR1 / C-PR1 / A-PR1 in parallel** — eligible now; not started in the 2026-11-12 session | #20, #21, #23 / #2, #26 / #30 | See `docs/stories/M0-foundation.md` for the per-stream acceptance conditions |

Task 1 has passed; the branch landed (PR #38 → `efa824b`; PR #41 → `f34ae07` after the owner's
conforming merge-message rewrite). M1/M2 (B-PR1/C-PR1) and M3 (A) are eligible and **not started**.
The 2026-11-12 resume session made no push; its one task — the SETUP-01 commit-reference slice — is
blocked on the mandatory review above, with the slice deliberately left uncommitted.

## Verification commands (copy/paste)

```bash
uv sync --project backend
uv run --project backend python tools/fixturectl.py verify
uv run --project backend pytest backend/tests -q
uv run --project backend uvicorn app.main:app --reload   # then GET /api/threads/REQ-001?baseline=baseline-b
```
