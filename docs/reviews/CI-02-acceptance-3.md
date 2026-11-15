## Verdict

**REQUEST_CHANGES**

Reviewed HEAD `9fb390b2c821a3a4fc5618e10424727a89e756d5`, matching PR #78 and hosted run `43707421956`, against base `b6e6931c90f527fa4009a9ba9e9b11f92f9f315e`.

The payload, version, and dual-input attribution repairs pass independent rechecks. **CI02-ACC-R5 remains blocking:** comparison still accepts reports with unavailable mandatory artifact inputs.

## Criterion assessment

| Scenario | Assessment | Evidence |
|---|---|---|
| SCN-3501 | **PASS** | Independent CLI comparison returns **2 new / 4 unchanged / 0 resolved**. New types are exactly `reverification_required` and `verification_failed`; both revisions and digests match inputs. Findings match the hand-labeled banking oracles. |
| SCN-3502 | **PASS** | Reverse returns **0/4/2**. Resolved identities are absent from the current comparable set. Inspection confirms comparison creates no evidence, accepted link, or requirement verdict. |
| SCN-3503 | **PASS** | Baseline-a self-comparison returns **0/4/0**. Complete empty reports return **0/0/0**. |
| SCN-3504 | **PASS** | Independent probes retain complete, equal before/after payloads through status, severity, explanation, evidence, execution-key, artifact-revision, and reordered/repeated artifact-ID changes. Stale digests are rejected. |
| SCN-3505 | **FAIL** | All twelve canonical invalid examples pass. Prior completeness examples now fail safely, and mixed-stage failures identify both inputs. Mandatory individual artifact inputs can still bypass completeness checks; see R5. |
| SCN-3506 | **PASS** | Source-locator reports are refused on either or both sides, including claimed mappings, without classifications. |

Retained and exact-run hosted Cucumber evidence contain **all six identifiers and 17 passing expanded CI-02 cases**. These cases do not cover the remaining bypass.

## Findings

1. **CI02-ACC-R5 — Major; blocking: yes — Mandatory input-kind checks do not establish artifact completeness.**

   **Location:** `backend/app/domain/assurance_report.py:177–188`; `backend/app/assurance/reporting.py:418–424`. Input artifact: hosted `assurance-banking`, ID **14159520470**, `banking-report.json`.

   **Expected:** Contract §1.1 requires every evaluated artifact and every consulted historical artifact to be required, available, and digested. An incomplete input must produce exit **2**, attributable `findings-not-comparable`, and no classification.

   **Actual:** Validation checks availability only for entries already marked required, then checks whether each mandatory **kind** has at least one required entry.

   Independently reproduced using the downloaded report:

   - Change the `CODE-001` artifact entry to `required=false, available=false, digest=null`.
   - Recompute the report digest.
   - Comparison still exits **0**, returning **0 new / 6 unchanged / 0 resolved**.
   - Additionally clear the mutated report’s findings and recompute its digest: comparison exits **0**, returning **0 new / 0 unchanged / 6 resolved**.

   Removing that artifact entry also succeeds. Downgrading or removing a consulted `historical_artifact` likewise succeeds. Both previous-side and current-side probes were exercised.

   **Smallest correction/recheck:** Enforce mandatory artifact membership and requiredness per input, beyond kind presence. Recheck individual artifact/historical-input removal and optional-unavailable downgrades on both sides; require exit 2, the correct invalid side, and no classifications.

   **Prior-finding disposition:** R1, R3, and R4 are closed by rerun. R2’s original unavailable-required-input probe passes. R5’s three earlier probes—missing evidence set, empty inputs, and downgraded evidence set—now pass, but the broader completeness defect remains open.

## Check verification

[Hosted run 43707421956](https://github.com/anthonygraca/gherkin-knowledge-graph/actions/runs/43707421956) completed successfully at the submitted head. Observed every job and its logs:

| Job | Job ID | Conclusion |
|---|---:|---|
| Cucumber acceptance and resolution gate | 132791408979 | Success |
| Offline contract, fixture, and API tests | 132791409240 | Success |
| Banking requirement assurance | 132791409254 | Success |
| Commit references | 132791409277 | Success |
| Frontend build and component tests | 132791409359 | Success |
| Portable CTA self-assurance | 132794252181 | Success |

Hosted logs show **553 backend tests passed / 4 skipped**, fixture verification passing, Ruff lint/format passing, **14 frontend tests passed**, and **203 Cucumber scenarios / 1,972 steps passed**.

Downloaded and inspected entirely in memory; archive hashes match GitHub’s published digests:

- **14159078299 — cucumber-messages:** all 17 CI-02 cases pass; embedded feature matches the checkout.
- **14159520470 — assurance-banking:** completed, six oracle-matching findings, valid digest, matching manifest, expected revisions.
- **14158814297 — assurance-self:** completed at the submitted head, zero findings, valid digest and matching manifest.

Retained `final-cucumber.ndjson`, `final-cucumber.log`, and feature inventory agree. `gt02-m4-recheck.ndjson` records three passing GT-02 cases; it provides no CI-02 execution evidence.

Fresh local checks: independent CLI comparisons and boundary probes, strict resolution gate, Ruff lint/format, and six-commit reference validation. Cumulative `git diff --check` reports trailing whitespace in review Markdown.

**Not freshly executed locally:** full pytest/Cucumber suites, frontend build/tests, or fixture verification; their exact-run hosted results were observed.

No repository files were changed, fixtures regenerated, commits created, or work delegated.
