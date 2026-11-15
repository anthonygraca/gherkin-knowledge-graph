## Verdict

**REQUEST_CHANGES**

Reviewed `2ad9205302d5ce97b38645acc7d61749c6a04f07`. The banking repair passes, but **CI01-ACC-R4 remains partially open and blocking** in self-assurance.

No repository files were changed, fixtures regenerated, commits created, or work delegated.

## Criterion assessment

Both retained and hosted reports contain **203 passing scenarios / 1,972 passing steps**, including all nine CI-01 instances. This supersedes the submission’s count.

| Criterion | Assessment | Evidence |
|---|---|---|
| SCN-3401 | **PASS** | Banking report pins baseline-b to `623b81adcb7fb9e0e5023d82bae206f44cac733e`, records the versioned evaluator and 17 inputs. Six findings match every oracle-declared field. Artifact hashes, fingerprints and manifest bindings validate. Independent evaluation completes under confirmed OS-level network denial. |
| SCN-3402 | **PASS** | PR-head, push-after and zero-after fallback probes pass. Selected commits drive real indexing with different source digests; relabeling the current execution report to the base is rejected. Hosted self-assurance evaluates the exact submitted head. |
| SCN-3403 | **PASS** | Execution and metadata digests validate; 31 imported source hashes match 41 indexed feature inputs. Mixed-outline and all-skipped coverage probes pass. Coverage gaps produce no requirement verdict. |
| SCN-3404 | **PASS** | Independent failed-report replay exits `0`, remains completed and produces an attributable `execution_failed` finding without a requirement verdict. |
| SCN-3405 | **FAIL** | Listed failure outcomes and the original late banking-manifest probe now pass. However, malformed self-assurance provenance still discards already-known indexed inputs: R4 below. |
| SCN-3406 | **PASS** | Exact-head report/manifest/diagnostic uploads succeed. Run-unique paths exclude stale outputs. Summary failure preserves evaluator completion. Earlier hosted failed-gate evidence confirms publication while BDD remains failed. |

## Findings

1. **CI01-ACC-R4 — Major; blocking; partially repaired — self-assurance diagnostics omit known feature provenance.**

   **Location:** `tools/assurance.py:459–478`; normative contract `docs/assurance-report-contract.md:118–124`.

   **Expected:** An incomplete diagnostic retains inputs known at failure, including available content hashes already collected through indexing.

   **Actual:** I supplied readable Cucumber Messages with metadata naming the wrong repository. Production indexing successfully resolved the submitted head and indexed **41 features with content hashes**. The subsequent provenance rejection returned exit `2`, `report_parse/report-malformed`, and no findings, but both diagnostic and manifest retained **only the execution-report and sidecar entries**. All 41 known feature inputs were omitted because they are appended only after `registry.import_report()` succeeds.

   The previous banking-manifest failure is repaired: its diagnostic now retains all 17 inputs.

   **Smallest correction/recheck:** Append indexed feature inputs immediately after obtaining the snapshot, before importing the execution report. Repeat the malformed-metadata probe and verify that both diagnostic and manifest retain all 41 available feature hashes alongside the report and sidecar inputs.

**Other prior findings rechecked and closed:** R1 forbidden destinations; R2 stale-output publication safeguards; R3 publisher/evaluator separation; R5 coverage aggregation; R6 captured diagnostics; R7 versioned evaluator identity; R8 retained evidence hashes.

## Check verification

- **Hosted:** Requested `gh run view … --json …` and `gh pr checks 78` show all six checks green at the exact submitted head. PR head/base match the snapshot. [Run 43709476207](https://github.com/anthonygraca/gherkin-knowledge-graph/actions/runs/43709476207).
- **Artifacts inspected in memory:** `assurance-banking` **14159712480**, `assurance-self` **14160267201**, and `cucumber-messages` **14160501229**.
- **Hosted logs:** **553 backend passed / 4 skipped**, fixture verification, Ruff lint/format, **203 Cucumber scenarios / 1,972 steps passed**, and strict step resolution.
- **Fresh local checks:** Strict step resolution, Ruff lint/format, all three recorded evidence hashes and `git diff --check` pass.
- **Failure probes:** Ran production handlers and real ingestion/import/evaluation; filesystem mutations were intercepted in memory.
- **Failed gate:** Independently inspected [run 43695481792](https://github.com/anthonygraca/gherkin-knowledge-graph/actions/runs/43695481792): BDD failed while self-assurance published a completed report containing six attributable execution failures.
- **Unobserved:** Fresh full local suites/fixture verification, rendered hosted summaries, hosted publisher/tool-failure injection, and a hosted push-triggered run. Push selection was verified deterministically. No weakened offline default was found.
