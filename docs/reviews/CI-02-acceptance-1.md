## Verdict

**REQUEST_CHANGES**

Reviewed HEAD `4df96be60bb3e05388c1886c6cd9bad3ffd368b9`, matching PR #78 and hosted run `43698670353`. Hosted checks are green, but two major implementation defects violate payload integrity and comparison completeness.

## Criterion assessment

| Scenario | Assessment | Evidence |
|---|---|---|
| SCN-3501 | **PASS** | Independent CLI comparison: **2 new / 4 unchanged / 0 resolved**; new types are `reverification_required` and `verification_failed`. Both revisions and report digests match the inputs. |
| SCN-3502 | **PASS** | Reverse CLI comparison: **0/4/2**. Resolved identities are absent from the current set. Implementation creates no evidence, accepted link, or requirement verdict. |
| SCN-3503 | **PASS** | Self-comparison returns **0/4/0**. |
| SCN-3504 | **FAIL** | Ordinary status, revision, severity, evidence, and explanation changes retain complete payloads. However, finding-list normalization violates exact payload retention; see R1. |
| SCN-3505 | **FAIL** | All eleven canonical examples pass. Additional contract probes expose acceptance of a mismatching report digest and an internally incomplete report; see R1–R3. |
| SCN-3506 | **PASS** | Source-locator reports are refused without classification, including different evaluated revisions and a supplied mapping claim. Dual-invalid-input attribution remains defective under R3. |

All six scenario identifiers are present and passing in retained and hosted Cucumber evidence: **16 expanded CI-02 cases**, including eleven SCN-3505 examples. Those green results do not cover the failures below.

## Findings

1. **CI02-ACC-R1 — Major; blocking: yes — Loading rewrites payloads before digest verification.**

   **Location:** `backend/app/domain/assurance_report.py:96`; `backend/app/assurance/reporting.py:364`.

   **Expected:** Validate the digest over the supplied report and retain exact serialized finding field values. Sorting/deduplication determines fingerprint identity without rewriting payloads.

   **Actual:** `ReportFinding` sorts and deduplicates artifact, evidence, and execution lists before digest verification. Independent CLI probes demonstrated both directions:
   
   - Reordering artifact IDs and correctly recomputing the input digest causes an erroneous exit **2**, reporting a digest mismatch.
   - Appending a duplicate artifact ID while retaining the now-stale digest causes exit **0**, **0/4/0** classification, and an `after` payload different from the supplied finding.

   **Smallest correction/recheck:** Preserve supplied finding values and verify the digest against the parsed input object before model normalization/default insertion. Normalize only fingerprint inputs. Recheck reordered/deduplicated artifact identities, stale-digest refusal, and complete before/after equality. Strengthen `bdd/step_definitions/ci.steps.js:594` to compare entire payloads; its current assertions do not establish retention.

2. **CI02-ACC-R2 — Major; blocking: yes — An explicitly unavailable required input can produce resolved findings.**

   **Location:** `backend/app/domain/assurance_report.py:157`; `backend/app/assurance/reporting.py:387`.

   **Expected:** Contract §1.3 requires every required input to be readable and digested before a report is completed and comparable.

   **Actual:** The model accepts `tool_outcome="completed"` alongside a required input with `available=false` and `digest=null`. Using the downloaded banking report, marking one required input unavailable, clearing findings, and recomputing the digest produced exit **0** with **0 new / 0 unchanged / 6 resolved**.

   **Smallest correction/recheck:** Reject completed reports containing unavailable or undigested required inputs. Exercise each side independently and require exit **2**, attributable `findings-not-comparable`, and no classifications.

3. **CI02-ACC-R3 — Minor; blocking: no — Validation stops before identifying both invalid inputs.**

   **Location:** `tools/assurance.py:456`; `backend/app/assurance/reporting.py:415`.

   **Expected:** Contract §3 requires `invalid_input="both"` when both reports fail.

   **Actual:** Removing both evaluated revisions returns `invalid_input="previous"`. Comparing two source-locator reports likewise reports only `previous`. Sequential loading/validation prevents examination of the second failure.

   **Smallest correction/recheck:** Collect validation failures from both sides before constructing the refusal. Recheck dual missing revisions, dual digest failures, and dual source-locator inputs.

4. **CI02-ACC-R4 — Minor; blocking: no — Unsupported report versions are accepted.**

   **Location:** `backend/app/domain/assurance_report.py:116`.

   **Expected:** The report contract fixes `report_version` to `"1.0"`.

   **Actual:** Changing the current report to `"999.0"` and recomputing its digest still produces a successful **2/4/0** comparison.

   **Smallest correction/recheck:** Constrain the accepted version to `"1.0"` and verify that unsupported versions receive an attributable refusal without classification.

## Check verification

- **Snapshot:** Read-only `gh pr view 78` confirmed the supplied head, base, and branch names.
- **Exact hosted run:** [43698670353](https://github.com/anthonygraca/gherkin-knowledge-graph/actions/runs/43698670353) completed successfully at the submitted HEAD. All six jobs succeeded:
  - Offline contract, fixture, and API tests — `132764723674`
  - Frontend build and component tests — `132764723832`
  - Cucumber acceptance suite and step-resolution gate — `132764723841`
  - Banking requirement assurance report — `132764723851`
  - Commit references — `132764723853`
  - Portable CTA self-assurance report — `132767546532`
- **Hosted logs:** Observed **553 backend tests passed / 4 skipped**, fixture verification passing, Ruff lint/format passing, **14 frontend tests passed**, and **202 Cucumber scenarios / 1,963 steps passed**.
- **Artifacts downloaded and inspected in memory:** `assurance-banking` (`14156000140`), `assurance-self` (`14155857204`), and `cucumber-messages` (`14154744966`). Archive hashes match GitHub’s published digests. Both assurance reports are completed with valid report digests and the expected evaluated/evaluator revisions.
- **Retained evidence:** Parsed `final-cucumber.ndjson`, inspected `final-cucumber.log`, and checked the feature inventory. `gt02-m4-recheck.ndjson` contains three passing GT-02 cases; it is inventory evidence, not another CI-02 execution.
- **Fresh local checks:** Independent oracle-backed CLI comparisons and boundary probes; strict resolution gate; Ruff lint/format; four-commit reference validation; submitted-range whitespace check — all completed. The boundary probes exposed the findings above.
- **Not freshly executed locally:** Full pytest/Cucumber suites, frontend build/tests, or fixture verification. Their retained evidence and exact-run hosted results were inspected.

No repository files were edited, fixtures regenerated, commits created, or work delegated.
