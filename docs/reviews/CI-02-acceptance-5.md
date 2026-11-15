## Verdict

**REQUEST_CHANGES**

Reviewed HEAD `002e04b759c4fb5e0ce6ae972fadb6fc935711ac`, matching PR #78 and hosted run `43711430233`, against base `b6e6931c90f527fa4009a9ba9e9b11f92f9f315e`.

All previously reported failing probes now pass. One new major finding blocks acceptance: comparison accepts missing or contradictory artifact-input revisions.

## Criterion assessment

| Scenario | Assessment | Evidence |
|---|---|---|
| SCN-3501 | **PASS** | Independent CLI comparison returns **2 new / 4 unchanged / 0 resolved**. New types are exactly `reverification_required` and `verification_failed`. Findings match the hand-labeled banking expectations; both revisions and digests match their inputs. |
| SCN-3502 | **PASS** | Reverse returns **0/4/2**. Resolved identities are absent from the current set. Inspection confirms comparison creates no evidence, accepted link, or requirement verdict. |
| SCN-3503 | **PASS** | Baseline-a self-comparison returns **0/4/0**. Complete empty reports return **0/0/0**. |
| SCN-3504 | **PASS** | Independent probes preserve complete before/after payloads through changes to status, severity, explanation, evidence, execution keys, artifact revisions, and reordered/repeated artifact IDs. Stale digests are refused. |
| SCN-3505 | **FAIL** | All twelve canonical invalid examples pass. Prior completeness and attribution probes also pass. Additional probes show that inputs lacking valid revision provenance remain comparable; see R6. |
| SCN-3506 | **PASS** | Source-locator reports are refused on either or both sides, including different revisions, displaced locators, and claimed mappings, without classifications. |

Retained and exact-run hosted Cucumber evidence contain **all six scenario IDs and 17 passing expanded CI-02 cases**.

## Findings

1. **CI02-ACC-R6 — Major; blocking: yes — Comparison accepts contradictory input revisions.**

   **Location:** [assurance_report.py:74](</home/anthonygraca/CSU Fullerton Dropbox/Anthony Graca/cpsc-583-knowledge-representation/project/gherkin-knowledge-graph/backend/app/domain/assurance_report.py:74>), with completeness checks at lines 198–225.  
   **Input artifact:** hosted `assurance-banking`, ID **14160129677**, `banking-report.json`.

   **Expected:** [Contract §1.1](</home/anthonygraca/CSU Fullerton Dropbox/Anthony Graca/cpsc-583-knowledge-representation/project/gherkin-knowledge-graph/docs/assurance-report-contract.md:51>) binds evaluated artifacts to `evaluated_revision` and historical content to its historical revision. Invalid provenance must prevent comparison.

   **Actual:** Membership validation checks IDs, availability, requiredness, and digests but never validates the input revisions. Starting with the exact hosted report, I independently reproduced:

   - Set the `CODE-001` input revision to `null` or the actual **baseline-a** commit while retaining its baseline-b digest.
   - Set historical input `9efce693…`’s revision to `null` or the **evaluated baseline-b** commit.
   - Recompute the report digest correctly.

   Every mutation succeeds on either side:

   | Mutated side | Findings retained | Findings cleared |
   |---|---|---|
   | Previous | Exit **0**, **0/6/0** | Exit **0**, **6/0/0** |
   | Current | Exit **0**, **0/6/0** | Exit **0**, **0/0/6** |

   Counts are **new/unchanged/resolved**. The current-side case therefore permits six resolved classifications from a report with invalid revision provenance. Independent fixture reads confirm `CODE-001` has different content hashes at baseline-a and baseline-b.

   **Smallest correction/recheck:** Validate revision relationships for completed reports: evaluated artifact inputs must identify the evaluated revision; historical inputs must identify their declared historical revision. Repeat these mutations on both sides, with findings retained and cleared; require exit **2**, the correct invalid side, `findings-not-comparable`, and no classifications.

**Prior-finding disposition:** R1–R5’s reported failing probes are repaired. Rechecks covered payload normalization and stale digests; unavailable required inputs; missing/downgraded mandatory sets; individual artifact and historical-input removal/downgrade; unsupported versions; and same-stage/mixed-stage dual failures. Historical removal/downgrade now refuses comparison in all eight retained/cleared, previous/current combinations.

## Check verification

[Hosted run 43711430233](https://github.com/anthonygraca/gherkin-knowledge-graph/actions/runs/43711430233) completed successfully at the submitted head. Observed every job and its logs:

| Job | Job ID | Conclusion |
|---|---:|---|
| Cucumber acceptance and resolution gate | 132803624311 | Success |
| Offline contract, fixture, and API tests | 132803624498 | Success |
| Frontend build and component tests | 132803624509 | Success |
| Banking requirement assurance | 132803624512 | Success |
| Commit references | 132803624617 | Success |
| Portable CTA self-assurance | 132806501173 | Success |

Hosted results: **553 backend tests passed / 4 skipped**, successful fixture verification and Ruff checks, **14 frontend tests passed**, **203 Cucumber scenarios / 1,972 step results passed**, and eight commits passing reference validation.

Downloaded and inspected entirely in memory; archive hashes match GitHub’s published digests:

- **14160712357 — cucumber-messages:** all 17 CI-02 cases pass; embedded feature matches the checkout.
- **14160129677 — assurance-banking:** completed, six oracle-matching findings, valid digest and matching manifest.
- **14161605443 — assurance-self:** completed at the submitted head, zero findings, valid digest and matching manifest.

Retained `final-cucumber.ndjson`, `final-cucumber.log`, and feature inventory agree. `gt02-m4-recheck.ndjson` records three passing GT-02 cases and **no executed CI-02 cases**.

Fresh local checks: real CLI comparisons using memory-backed inputs, prior-finding and provenance probes, strict resolution gate, Ruff lint/format, and eight-commit reference validation. Cumulative `git diff --check` reports trailing whitespace in review Markdown.

**Not freshly executed locally:** full pytest/Cucumber suites, frontend build/tests, or fixture verification; their exact-run hosted results were observed.

No repository files were edited, fixtures regenerated, commits created, or work delegated.
