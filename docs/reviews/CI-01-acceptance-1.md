## Verdict

**REQUEST_CHANGES**

Reviewed head `4df96be60bb3e05388c1886c6cd9bad3ffd368b9` against the specified base. All six hosted checks are green, but failure handling and publication violate the approved contract. No files were changed, fixtures regenerated, commits created, or work delegated.

## Criterion assessment

All six scenarios, including SCN-3405’s four examples, appear as passing in both local and hosted Cucumber reports. Acceptance assessments below also account for implementation defects.

| Criterion | Assessment | Evidence |
|---|---|---|
| SCN-3401 | **FAIL** | Hosted banking report pins baseline-b to `623b81adcb7fb9e0e5023d82bae206f44cac733e`; all six findings match the oracle’s declared fields, independently checked fingerprints, and revision fields. Report/manifest digests validate; outputs use `$RUNNER_TEMP`. However, the hosted evaluator identifier omits the contract-required package version: R7. |
| SCN-3402 | **PASS** | Read-only resolver checks selected PR head over a distinct merge SHA, push `after` over a different fallback SHA, and the fallback for zero `after`. Workflow checkout and self-assurance arguments use the selected revision; ingestion reads that commit’s Git objects. Hosted self-report pins the exact PR head. |
| SCN-3403 | **FAIL** | Hosted provenance checks pass: normalized execution digest matches, execution sources match all 31 imported feature hashes, and all 41 indexed feature hashes match HEAD. Coverage gaps create no findings or requirement verdict. Skipped executions are nevertheless misreported as unknown: R5. |
| SCN-3404 | **PASS** | Passing scenario exercises the CLI with failed input. Independently observed earlier hosted run `43695481792`: BDD failed while self-assurance succeeded and published a completed report containing six attributable `execution_failed` findings without requirement verdicts. |
| SCN-3405 | **FAIL** | Passing examples miss unsafe diagnostic destinations, retained stale completions, discarded input provenance, and incorrect failure classification: R1, R2, R4. |
| SCN-3406 | **FAIL** | Report/manifest uploads and preservation of a failing BDD gate are observed. Summary failure rewrites evaluator outcome, and banking omits stderr diagnostic capture: R3, R6. |

## Findings

1. **CI01-ACC-R1 — Major; blocking — rejected destinations still reach the writer.**  
   **Location:** `tools/assurance.py:152–158, 173–174, 258`.  
   **Expected:** Refusing a destination inside evaluated inputs must leave those inputs untouched.  
   **Actual:** `_outside()` raises, but the handler calls `_diagnostic()` with the same rejected paths. A read-only, mocked-I/O probe using `fixtures/banking-demo/expected/baselines.json` confirmed that this protected path reaches `write_report()`. The same pattern applies to self-assurance.  
   **Smallest correction/recheck:** Preserve destination validation through diagnostic handling; emit stderr when destinations are forbidden. Verify that rejected paths receive no write attempt.

2. **CI01-ACC-R2 — Major; blocking — an unwritable destination can retain a completed report.**  
   **Location:** `tools/assurance.py:152–163`; `backend/app/assurance/reporting.py:331–353`; `bdd/support/cta_bridge.py:544–545`.  
   **Expected:** A failed invocation must not leave an earlier completion available for publication.  
   **Actual:** Failed atomic replacement preserves the existing destination. The diagnostic path retries replacement and then prints stderr, without invalidating the old completion. The BDD bridge deletes prior outputs before invoking the CLI, hiding this case.  
   **Smallest correction/recheck:** Prevent publication of prior outputs after failure, including when cleanup fails. Recheck a reused destination containing a completed report; do not pre-delete it in the harness.

3. **CI01-ACC-R3 — Major; blocking — summary publication failure becomes evaluator failure.**  
   **Location:** `tools/assurance.py:228–275, 405–451`.  
   **Expected:** Contract §5 requires publication failure to fail the job while preserving the completed evaluator report.  
   **Actual:** An in-memory summary-permission failure produced a completed report with six findings, then overwrote it with `incomplete`, `failure_stage="input"`, `failure_code="input-unreadable"`, and zero findings.  
   **Smallest correction/recheck:** Separate summary publication handling from evaluation handling. Verify that summary failure preserves the completed report and has a distinguishable publisher failure.

4. **CI01-ACC-R4 — Major; blocking — incomplete diagnostics lose provenance and misidentify failures.**  
   **Location:** `tools/assurance.py:242–274, 418–450`.  
   **Expected:** Contract §1.4 retains known inputs and identifies unreadable inputs with `available=false` and `digest=null`; revision failure belongs to `resolution`.  
   **Actual:** Every handler supplies `inputs=[]`, including a write failure after 17 inputs were collected. A missing required execution report has no unavailable input entry. A read-only replay with an unknown self-assurance revision returned `report_parse/report-malformed`.  
   **Smallest correction/recheck:** Retain inputs as processing progresses and classify failures at their actual stage. Recheck missing inputs, unknown revisions in both scopes, and write failure after successful evaluation.

5. **CI01-ACC-R5 — Major; blocking — skipped coverage is hard-coded to zero.**  
   **Location:** `tools/assurance.py:340–349`.  
   **Expected:** Coverage distinguishes observed skips from unknown execution.  
   **Actual:** `scenarios_skipped=0` unconditionally. An in-memory replay of the hosted report with execution statuses changed to `SKIPPED` completed with zero skipped and all 206 indexed scenarios unknown. No files were written during this probe.  
   **Smallest correction/recheck:** Derive skipped and unknown counts from imported outcomes. Check partial coverage containing passed, skipped, and unreported scenarios.

6. **CI01-ACC-R6 — Major; blocking — banking cannot upload its stderr-only diagnostic.**  
   **Location:** `.github/workflows/ci.yml:177–192`.  
   **Expected:** Contract §5 uploads captured stderr diagnostics even when report output is unwritable.  
   **Actual:** Banking captures no stderr file and uploads only report/manifest paths. When those cannot be written, the JSON remains in the job log; artifact upload merely warns about missing files.  
   **Smallest correction/recheck:** Capture and upload banking stderr while preserving evaluator exit status. Verify the unwritable-output publication path.

7. **CI01-ACC-R7 — Minor; nonblocking — hosted evaluator identifiers omit package version.**  
   **Location:** `.github/workflows/ci.yml:179, 229`; both hosted reports.  
   **Expected:** `evaluator_revision` contains package version and CTA commit.  
   **Actual:** Both artifacts contain `cta@4df96be…`; the package is `0.1.0`.  
   **Smallest correction/recheck:** Use the existing version-aware identifier, yielding `cta@0.1.0+<sha>`, and inspect both artifacts.

8. **CI01-ACC-R8 — Minor; nonblocking — final evidence hashes are stale.**  
   **Location:** `docs/reports/omp-closeout/evidence/final-run-hashes.txt:1–3`.  
   **Expected:** Recorded hashes identify the submitted evidence.  
   **Actual:** All three entries mismatch. For example, the recorded Cucumber hash starts `506c40ea`; the actual tracked report is `78f03fb422e74a922d8e11bed59d2118068326488b5fa503df003c3c0623aea9`. Both inventory hashes also differ.  
   **Smallest correction/recheck:** Correct the hash record against the retained files and verify every entry.

## Check verification

- **Hosted:** [Run 43698670353](https://github.com/anthonygraca/gherkin-knowledge-graph/actions/runs/43698670353) succeeded at the exact requested head. `gh pr checks 78` reported all six checks passing. PR head/base match the supplied snapshot.
- **Artifacts:** Read `assurance-banking` (`14156000140`), `assurance-self` (`14155857204`), and `cucumber-messages` (`14154744966`) directly in memory. Both report digests and manifest bindings validate.
- **Execution:** Hosted and local Cucumber reports contain 202 executed cases and 1,963 passing step results; all nine CI-01 instances pass. Independently reran the read-only step-resolution command: **passed**.
- **Backend/quality:** Local retained log reports **553 passed, 4 skipped**. Hosted logs independently confirm that count, fixture verification, Ruff lint, and formatting passed.
- **Failed gate:** [Run 43695481792](https://github.com/anthonygraca/gherkin-knowledge-graph/actions/runs/43695481792) independently confirms failed BDD with successful completed execution-findings publication.
- **Limitations:** Full suites were not rerun locally. Failure probes replaced writes in memory. Rendered hosted summaries, hosted publisher failures, hosted tool-failure publication, and a hosted push-triggered assurance run were not observed. No new default dependency on inference or network access was found.
