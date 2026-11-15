## Verdict

**REQUEST_CHANGES**

Reviewed HEAD `2ad9205302d5ce97b38645acc7d61749c6a04f07`, matching PR #78 and hosted run `43709476207`, against the supplied base.

**CI02-ACC-R5 remains blocking:** evaluated-artifact completeness is repaired, but historical-input completeness still permits invalid comparisons and false resolution classifications.

## Criterion assessment

| Scenario | Assessment | Evidence |
|---|---|---|
| SCN-3501 | **PASS** | Independent CLI comparison returns **2 new / 4 unchanged / 0 resolved**. New types are exactly `reverification_required` and `verification_failed`. Both revisions and report digests match their inputs; banking findings match hand-labeled expectations. |
| SCN-3502 | **PASS** | Reverse comparison returns **0/4/2**. Resolved identities are absent from the current comparable set. Inspection confirms comparison creates no evidence, accepted links, or requirement verdicts. |
| SCN-3503 | **PASS** | Baseline-a self-comparison returns **0/4/0**; complete empty reports return **0/0/0**. |
| SCN-3504 | **PASS** | Independent probes preserve complete before/after payloads through status, severity, explanation, evidence, execution-key, artifact-revision, and reordered/repeated artifact-ID changes. Stale digests are rejected. |
| SCN-3505 | **FAIL** | All twelve canonical invalid examples pass. Historical-input removal and downgrade probes still permit comparison; see R5. Other prior refusal probes now pass, including mixed-stage dual failures. |
| SCN-3506 | **PASS** | Source-locator reports are refused without classifications, including different revisions, displaced locators, and claimed mappings. |

Retained and exact-run hosted evidence contain **all six scenario IDs and 17 passing expanded CI-02 cases**. Those cases do not cover the remaining historical-input defect.

## Findings

1. **CI02-ACC-R5 — Major; blocking: yes — Historical-input completeness remains unenforced.**

   **Location:** `backend/app/domain/assurance_report.py:184–211`; `backend/app/assurance/reporting.py:424–454`.  
   **Input artifact:** hosted `assurance-banking`, ID **14159712480**, `banking-report.json`.

   **Expected:** Contract §1.1 requires every historical input consulted for freshness to remain required, available, digested, and revision-qualified. An incomplete report must produce exit **2**, attributable `findings-not-comparable`, and no classification.

   **Actual:** Validation enforces evaluated-artifact membership but has no equivalent historical-input membership check. Using the exact hosted report, I independently reproduced both mutations:

   - Remove a `historical_artifact` entry.
   - Set that entry to `required=false, available=false, digest=null`.

   After recomputing the report digest:

   | Mutated input | Findings retained | Findings cleared |
   |---|---|---|
   | Previous | Exit **0**, **0/6/0** | Exit **0**, **6/0/0** |
   | Current | Exit **0**, **0/6/0** | Exit **0**, **0/0/6** |

   Counts are **new/unchanged/resolved**. The current-side probe therefore classifies six findings as resolved despite unavailable mandatory historical input.

   **Smallest correction/recheck:** Enforce revision-qualified historical-input membership and requiredness. Repeat removal and optional/unavailable downgrade probes on both sides, with findings retained and cleared; require exit **2**, the correct invalid side, and no classifications.

   **Prior-finding disposition:** R1, R3, and R4 remain closed after rerunning their probes. R2’s unavailable-required-input probe passes. R5’s missing evidence-set, empty-input, downgraded evidence-set, and individual evaluated-artifact probes now pass. Its historical-input probes still fail.

## Check verification

[Hosted run 43709476207](https://github.com/anthonygraca/gherkin-knowledge-graph/actions/runs/43709476207) completed successfully at the submitted head. Observed all six jobs:

| Job | Job ID | Conclusion |
|---|---:|---|
| Frontend build and component tests | 132797692929 | Success |
| Banking requirement assurance | 132797693056 | Success |
| Commit references | 132797693090 | Success |
| Offline contract, fixture, and API tests | 132797693100 | Success |
| Cucumber acceptance and resolution gate | 132797693123 | Success |
| Portable CTA self-assurance | 132800476417 | Success |

Hosted evidence shows **553 backend tests passed / 4 skipped**, successful fixture verification and Ruff checks, **14 frontend tests passed**, and **203 Cucumber scenarios / 1,972 steps passed**.

Downloaded and inspected entirely in memory; archive hashes match GitHub’s published digests:

- **14160501229 — cucumber-messages:** all 17 CI-02 cases pass; embedded CI-02 feature matches the checkout.
- **14159712480 — assurance-banking:** completed, six oracle-matching findings, valid digest, matching manifest, expected revisions.
- **14160267201 — assurance-self:** completed at the submitted head, zero findings, valid digest and matching manifest.

Retained `final-cucumber.ndjson`, its log, and the feature inventory agree. `gt02-m4-recheck.ndjson` contains three executed GT-02 cases and **no executed CI-02 cases**.

Fresh local checks included independent CLI comparisons and boundary probes, strict resolution (**203 cases / 1,972 results**), Ruff lint/format, and commit-reference validation (**seven commits**). Cumulative `git diff --check` reports trailing whitespace in review Markdown.

**Not freshly executed locally:** full pytest/Cucumber suites, frontend build/tests, or fixture verification; their exact-run hosted results were inspected.

No repository files were edited, fixtures regenerated, commits created, or work delegated.
