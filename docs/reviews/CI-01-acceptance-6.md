## Verdict

**APPROVE**

Reviewed `0aa9c6ad37585fc5a3906030536d59e38b5ccd08` against `b6e6931c90f527fa4009a9ba9e9b11f92f9f315e`. Input-revision binding does not regress CI-01. All criteria pass, CI01-ACC-R1–R8 remain closed, and no open major finding remains.

No files were changed, fixtures regenerated, commits created, or work delegated.

## Criterion assessment

| Criterion | Result | Evidence |
|---|---|---|
| SCN-3401 | **PASS** | Banking report pins banking-demo/baseline-b to `623b81adcb7fb9e0e5023d82bae206f44cac733e`, records `cta@0.1.0+0aa9c6ad…`, and carries 17 inputs. All six findings match every oracle-declared field, including explanations. Input hashes and manifest binding validate. Fresh evaluation completed under confirmed OS-level network denial. Hosted outputs reside under `$RUNNER_TEMP`. |
| SCN-3402 | **PASS** | PR-head, push-after and zero-after fallback probes pass. Selected head/base commits drive real indexing and evaluation, producing different input hashes. Relabeling the current full execution report as the base is rejected. Hosted self-assurance evaluates the exact submitted head. |
| SCN-3403 | **PASS** | Scope is `gherkin_executability`. Tested commit, normalized execution-report digest and metadata digest validate. All 31 execution sources match corresponding indexed feature hashes; all 41 indexed hashes match Git content. Coverage is 174 executed / 0 skipped / 32 unknown. No requirement verdict is produced. |
| SCN-3404 | **PASS** | Failed-execution replay exits `0`, produces a completed report with an attributable `execution_failed` finding, and creates no requirement verdict. |
| SCN-3405 | **PASS** | Unknown revisions, malformed provenance, unreadable/missing inputs and unwritable destinations return exit `2`, incomplete diagnostics and no findings. Provenance retention and stage/code classifications pass. Unwritable-output stderr carries the diagnostic JSON; publication excludes earlier-run outputs. |
| SCN-3406 | **PASS** | Hosted artifacts contain reports, manifests and diagnostic files. Generated summaries identify revisions and finding counts. Publisher failures preserve completed evaluator results. Workflow permissions and commands request no repository mutation, comment or deployment. Failed-gate publication is independently observed historically and replayed through current handlers. |

All six scenarios, including SCN-3405’s four examples, appear as **nine passing executions** in both retained and hosted reports.

## Findings

No new findings. Prior findings were independently rechecked:

| Finding | Severity / blocking | Location | Expected and observed; correction/recheck |
|---|---|---|---|
| **CI01-ACC-R1 — closed** | Former Major / No | `tools/assurance.py:202` | Forbidden report/manifest destinations receive no write attempt in either scope. Replayed; no correction needed. |
| **CI01-ACC-R2 — closed** | Former Major / No | `.github/workflows/ci.yml:179`, `:236` | Denied cleanup can preserve an immutable old file, but publication uses distinct run/attempt paths. Replayed and inspected upload paths; no correction needed. |
| **CI01-ACC-R3 — closed** | Former Major / No | `tools/assurance.py:303`, `:546` | Summary failure returns `publication-failed` while retaining completed reports and findings. Replayed in both scopes. |
| **CI01-ACC-R4 — closed** | Former Major / No | `tools/assurance.py:248`, `:462` | Malformed provenance retains 44 known inputs; late banking-manifest failure retains 17, including the unavailable manifest. Read, missing-input, revision and output-failure probes pass. |
| **CI01-ACC-R5 — closed** | Former Major / No | `tools/assurance.py:495` | Coverage buckets remain disjoint: all-skipped yields 0/174/32; mixed-outline yields 174/0/32. Replayed without failure findings. |
| **CI01-ACC-R6 — closed** | Former Major / No | `.github/workflows/ci.yml:187`, `:251` | Both jobs capture stderr and always upload diagnostic paths. Both hosted archives contain diagnostic files. |
| **CI01-ACC-R7 — closed** | Former Minor / No | `backend/app/assurance/reporting.py:94` | Both hosted evaluator identifiers include package version and exact CTA commit. |
| **CI01-ACC-R8 — closed** | Former Minor / No | `docs/reports/omp-closeout/evidence/final-run-hashes.txt` | All three recorded hashes validate. |

## Check verification

- **Hosted:** Required `gh run view 43713557672 --json databaseId,conclusion,status,headSha,jobs` and `gh pr checks 78` show all six checks green at the exact requested head. PR head/base also match. [Hosted run](https://github.com/anthonygraca/gherkin-knowledge-graph/actions/runs/43713557672).
- **Artifacts inspected in memory:** `assurance-banking` **14161288643**, `assurance-self` **14161419427**, and `cucumber-messages` **14161663642**. Archive digests, report digests, input hashes and manifest bindings validate.
- **Acceptance evidence:** Retained and hosted reports show **203 passing scenarios / 1,972 passing steps**, superseding the submission’s 202/1,963 count. Feature inventory agrees.
- **Backend/quality:** Hosted logs confirm **553 passed / 4 skipped**, fixture verification, Ruff lint/format and strict step resolution. Fresh local strict step resolution, Ruff lint/format, commit references (**9 commits**) and Git checks pass.
- **Revision-binding regression:** Current models reject **118** null or contradictory input-revision mutations across both scopes. Full-SHA and symbolic-`HEAD` self-assurance evaluations complete successfully.
- **Failed hosted gate:** [Run 43695481792](https://github.com/anthonygraca/gherkin-knowledge-graph/actions/runs/43695481792) retains failed BDD while self-assurance successfully publishes six completed execution-failure findings.
- **Limits:** Full local suites and fixture verification were not freshly rerun. Failure probes intercepted filesystem mutations in memory. Rendered hosted summaries, hosted publisher/tool-failure injection and a hosted push-triggered run were unobserved; push behavior was verified deterministically through real indexing/evaluation.

No weakened offline default or regression of the stated invariants was found.
