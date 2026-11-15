## Verdict

**APPROVE**

Reviewed `002e04b759c4fb5e0ce6ae972fadb6fc935711ac` against `b6e6931c90f527fa4009a9ba9e9b11f92f9f315e`. Every criterion passes; CI01-ACC-R1–R8 are closed. No open major finding remains.

No files were changed, fixtures regenerated, commits created, or work delegated.

## Criterion assessment

| Criterion | Result | Evidence |
|---|---|---|
| SCN-3401 | **PASS** | Banking report pins banking-demo/baseline-b to `623b81adcb7fb9e0e5023d82bae206f44cac733e`, records `cta@0.1.0+002e04b…` and 17 inputs. All six findings match the oracle, including explanations; fingerprints, revisions, content hashes and manifest bindings validate. Independent evaluation completed under confirmed OS-level network denial. Hosted outputs use `$RUNNER_TEMP`. |
| SCN-3402 | **PASS** | PR-head, push-after and zero-after fallback probes pass. Selected head/base commits drive real indexing and produce different source digests. Relabeling the current execution report to the base is rejected. Hosted self-assurance evaluates the exact requested head. |
| SCN-3403 | **PASS** | Scope is `gherkin_executability`. Tested commit, normalized execution-report digest and metadata digest validate. All 31 imported source hashes match their corresponding 41 indexed feature inputs. Coverage records 174 executed, 0 skipped and 32 unknown scenario definitions, without requirement verdicts. |
| SCN-3404 | **PASS** | Independent failed-report replay exits `0`, remains `completed`, and produces an attributable `execution_failed` finding without a requirement verdict. |
| SCN-3405 | **PASS** | Unknown revisions, malformed provenance, unreadable/missing inputs and unwritable outputs return exit `2`, incomplete diagnostics and no findings. Failure classifications and retained provenance validate. Unwritable-output stderr contains the diagnostic JSON. Current publication paths exclude stale outputs. |
| SCN-3406 | **PASS** | Exact-head artifacts contain reports, manifests and captured diagnostic files. Generated summaries identify evaluated/evaluator revisions and finding counts. Summary failure preserves evaluator completion and emits `publication-failed`. Workflow permissions and commands request no repository mutation, comment or deployment. Failed-gate publication is independently observed in historical hosted evidence and replayed against current code. |

## Findings

No new findings. All corrections below were independently rechecked; no further correction is required.

| Finding | Severity / blocking | Location | Expected and observed |
|---|---|---|---|
| **CI01-ACC-R1 — closed** | Former Major / **No** | `tools/assurance.py:200`, `:365` | Forbidden report and manifest destinations receive **no write attempt**, in both scopes. |
| **CI01-ACC-R2 — closed** | Former Major / **No** | `.github/workflows/ci.yml:179`, `:236` | Denying removal, truncation and replacement can preserve an immutable old CLI destination. Replayed this case; workflow publication uses distinct run/attempt paths and excludes that destination. |
| **CI01-ACC-R3 — closed** | Former Major / **No** | `tools/assurance.py:303`, `:546` | Summary failures exit `2` with `publication-failed`, preserving completed evaluator reports and findings in both scopes. |
| **CI01-ACC-R4 — closed** | Former Major / **No** | `tools/assurance.py:248`, `:462` | Malformed self-assurance provenance retains all **44 known inputs**, including 41 feature hashes, in report and manifest. Late banking-manifest failure retains all **17 inputs**, marking the unreadable manifest unavailable. Read-permission, missing-input, unknown-revision and output-failure probes also pass. |
| **CI01-ACC-R5 — closed** | Former Major / **No** | `tools/assurance.py:495` | Coverage buckets are disjoint. All-skipped replay yields **0 executed / 174 skipped / 32 unknown**; mixed-outline replay yields **174 / 0 / 32**, without failure findings. |
| **CI01-ACC-R6 — closed** | Former Major / **No** | `.github/workflows/ci.yml:187`, `:251` | Both jobs capture stderr and include diagnostic paths in always-run uploads. Both hosted artifacts contain their diagnostic files. |
| **CI01-ACC-R7 — closed** | Former Minor / **No** | `backend/app/assurance/reporting.py:94` | Both hosted reports include package version and exact CTA commit in `evaluator_revision`. |
| **CI01-ACC-R8 — closed** | Former Minor / **No** | `docs/reports/omp-closeout/evidence/final-run-hashes.txt:1` | All three recorded evidence hashes validate. |

## Check verification

- **Hosted snapshot:** Required `gh run view 43711430233 --json databaseId,conclusion,status,headSha,jobs` and `gh pr checks 78` observed **all six checks green** at the exact requested head. PR head/base match the supplied snapshot. [Hosted run](https://github.com/anthonygraca/gherkin-knowledge-graph/actions/runs/43711430233).
- **Artifacts inspected in memory:** `assurance-banking` **14160129677**, `assurance-self` **14161605443**, and `cucumber-messages` **14160712357**. Archive digests, report digests and manifest bindings validate.
- **Acceptance evidence:** Both retained and hosted reports contain **203 passing scenarios / 1,972 passing step results**, including all nine CI-01 instances. This supersedes the submission’s 202/1,963 count. Feature inventory agrees.
- **Backend and quality:** Hosted logs independently confirm **553 passed / 4 skipped**, fixture reproducibility, Ruff lint/format and strict step resolution. Retained local reports agree.
- **Fresh local checks:** Strict step resolution, Ruff lint/format, evidence hashes, commit references (**8 commits**) and Git whitespace checks pass.
- **Failure probes:** Production CLI handlers and real ingestion/import/evaluation ran with filesystem mutations intercepted in memory. Banking evaluation also passed with OS-level connection denial.
- **Failed hosted gate:** [Run 43695481792](https://github.com/anthonygraca/gherkin-knowledge-graph/actions/runs/43695481792) retains failed BDD while self-assurance successfully publishes a completed report with six attributable execution failures.
- **Unobserved:** Fresh full local suites/fixture verification, rendered hosted summaries, hosted publisher/tool-failure injection, and a hosted push-triggered run. Push behavior was checked deterministically through resolution and real indexing. No weakened offline default was found.
