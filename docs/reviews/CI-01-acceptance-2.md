## Verdict

**REQUEST_CHANGES**

Reviewed `28ad8033bb0e66053dc0106f54a6fbae96806b1d` against the supplied base. All six hosted checks pass, but **CI01-ACC-R2, R4, and R5 remain blocking**.

No repository files were changed, fixtures regenerated, commits created, or work delegated.

## Criterion assessment

The retained and hosted Cucumber reports contain **203 passing scenarios / 1,972 passing steps**, including all nine CI-01 instances. This supersedes the submission’s 202/1,963 count.

| Criterion | Assessment | Evidence |
|---|---|---|
| SCN-3401 | **PASS** | Hosted banking report identifies banking-demo/baseline-b at `623b81adcb7fb9e0e5023d82bae206f44cac733e`, with `cta@0.1.0+28ad8033…` and 17 inputs. All six findings match every oracle-declared field; fingerprints and revision fields independently validate. Outputs use `$RUNNER_TEMP`. |
| SCN-3402 | **PASS** | Resolver probes select PR head over a distinct merge SHA, push `after` over fallback, and fallback for zero `after`. Selected revisions drive real Git indexing and produce different source digests. Hosted self-assurance evaluates the exact submitted head. |
| SCN-3403 | **FAIL** | Hosted execution digest, all 31 imported source hashes, and all 41 indexed feature hashes validate. Scope and requirement-claim boundaries hold. Mixed outline outcomes still produce incorrect coverage counts: R5. |
| SCN-3404 | **PASS** | A valid failed-report replay at the submitted revision exits `0`, produces a completed report and attributable `execution_failed` finding, and creates no requirement verdict. |
| SCN-3405 | **FAIL** | Unknown revisions now classify correctly; write failures retain collected inputs and emit matching stderr JSON. Stale completions can survive, and unreadable-input diagnostics remain incorrect: R2/R4. |
| SCN-3406 | **PASS** | Exact-head report/manifest uploads succeed. Banking now captures stderr. Summary failure preserves evaluator completion and emits `publication-failed`. Earlier hosted failed-gate evidence confirms completed execution-findings publication while BDD remains failed. Hosted fault-injection limitations are listed below. |

## Findings

1. **CI01-ACC-R2 — Major; blocking; partially repaired — stale completion survives denied cleanup.**

   **Location:** `tools/assurance.py:121–136, 178–189`.

   **Expected:** A failed invocation must prevent an earlier completed report from remaining eligible for publication.

   **Actual:** With a completed destination already present, independently denying unlink, truncation, and subsequent writing returns exit `2` and an incomplete stderr diagnostic, but leaves the old destination containing `tool_outcome="completed"`. `_clear_outputs()` suppresses the truncation failure; diagnostic handling cannot invalidate the destination.

   **Smallest correction/recheck:** Make publication conditional on outputs belonging to the current invocation, using fresh output paths or an equivalent publication safeguard. Repeat the reused-destination probe with removal, truncation, and replacement denied; verify the earlier completion cannot be published.

2. **CI01-ACC-R4 — Major; blocking; partially repaired — unreadable inputs still lose provenance and receive the wrong classification.**

   **Location:** `tools/assurance.py:326–348, 360–411, 518–534`; banking input collection at `232–241`.

   **Expected:** Required-input read failures use stage `input`, retain known inputs, and identify the unreadable entry with `available=false` and `digest=null`.

   **Actual:** Independent permission-failure probes against an existing Cucumber report and existing metadata both return `report_parse/report-malformed` with `inputs=[]`. Malformed provenance also discards already readable report provenance. A banking manifest read failure after evaluation retains no collected inputs.

   Unknown-revision classification and retention of 17 inputs after a banking output failure **are repaired**.

   **Smallest correction/recheck:** Collect provenance progressively, register inputs before reading them, and distinguish filesystem read errors from parsing/provenance errors. Recheck unreadable existing report, metadata, and fixture-manifest inputs.

3. **CI01-ACC-R5 — Major; blocking; partially repaired — outline examples overlap coverage buckets.**

   **Location:** `tools/assurance.py:438–456`; scenario aggregation in `backend/app/persistence/portable.py:307–329`.

   **Expected:** Unknown coverage reflects scenarios without observed execution; mixed example outcomes must not reduce that count through double counting.

   **Actual:** All-skipped coverage is repaired. However, changing one SCN-3405 outline example to skipped while its other examples pass produces this completed CLI report:

   ```
   total=206, executed=174, skipped=1, unknown=31
   ```

   The same scenario key appears in both executed and skipped sets. The report still leaves **32 scenario definitions unobserved**, so `unknown=31` is incorrect.

   **Smallest correction/recheck:** Use consistent scenario granularity and disjoint buckets, calculating unknown coverage from the union of observed scenario keys. Recheck an outline containing both passed and skipped examples alongside unreported scenarios.

**Prior findings closed:**

- **R1:** Forbidden report/manifest destinations produce stderr diagnostics with no write attempt, in both scopes.
- **R3:** Summary permission failure exits `2` with `publication-failed`, preserving the completed report and six findings.
- **R6:** Banking captures stderr and includes the diagnostic file in the always-run upload; the hosted artifact contains it.
- **R7:** Both hosted evaluator identifiers include package version and CTA commit.
- **R8:** Every entry in `final-run-hashes.txt` validates.

## Check verification

- **Hosted:** Required `gh run view` and `gh pr checks 78` commands observed all six checks green at the exact submitted head. PR head/base match the snapshot. [Run 43703346736](https://github.com/anthonygraca/gherkin-knowledge-graph/actions/runs/43703346736).
- **Artifacts inspected in memory:** `assurance-banking` **14157535738**, `assurance-self` **14157965604**, and `cucumber-messages` **14158220245**. Report digests, manifest bindings, normalized execution digest, and feature hashes validate.
- **Execution evidence:** Local and hosted reports show **203/1,972 passing**. Hosted backend logs independently confirm **553 passed / 4 skipped**, fixture verification, Ruff lint, and formatting.
- **Fresh local checks:** Strict step-resolution gate, Ruff lint, formatting, evidence hashes, and `git diff --check` pass.
- **Failure probes:** Production evaluation/import paths ran with filesystem writes replaced by memory. Replayed forbidden destinations, stale outputs, summary failure, unknown revisions, unreadable/missing inputs, malformed provenance, failed execution, and skipped/mixed coverage.
- **Failed hosted gate:** [Run 43695481792](https://github.com/anthonygraca/gherkin-knowledge-graph/actions/runs/43695481792) has failed BDD and successful self-assurance publication containing six attributable execution failures.
- **Unobserved:** Fresh full local suites, rendered hosted summaries, hosted publisher/tool-failure injection, and a hosted push-triggered assurance run. Push selection was checked deterministically. No new default inference or network dependency was found.
