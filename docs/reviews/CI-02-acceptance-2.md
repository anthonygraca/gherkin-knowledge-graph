## Verdict

**REQUEST_CHANGES**

Reviewed `28ad8033bb0e66053dc0106f54a6fbae96806b1d`, matching PR #78 and hosted run `43703346736`, against base `b6e6931c90f527fa4009a9ba9e9b11f92f9f315e`.

The original payload and version defects are repaired. A blocking completeness bypass remains, and dual-input attribution is only partially repaired.

## Criterion assessment

| Scenario | Assessment | Evidence |
|---|---|---|
| SCN-3501 | **PASS** | Independent CLI comparison returns **2 new / 4 unchanged / 0 resolved**. New types are exactly `reverification_required` and `verification_failed`; revisions and digests match inputs. Findings checked against hand-labeled banking oracles. |
| SCN-3502 | **PASS** | Reverse comparison returns **0/4/2**. Resolved identities are absent from the current set. Comparison creates no evidence, accepted links, or requirement verdicts. |
| SCN-3503 | **PASS** | Baseline-a self-comparison returns **0/4/0**. |
| SCN-3504 | **PASS** | Reordered/repeated artifact IDs retain identity and exact payload values. Status, severity, explanation, evidence, execution keys, and artifact revisions remain intact in before/after payloads. Stale digests are rejected. |
| SCN-3505 | **FAIL** | All twelve canonical invalid examples pass. Additional probes expose incomplete-input acceptance and incomplete dual-failure attribution; see R5 and R3. |
| SCN-3506 | **PASS** | Source-locator comparisons are refused without classifications, including supplied mapping claims. |

All six identifiers appear in retained and exact-run hosted Cucumber evidence: **17 expanded CI-02 cases, all passing**. Those cases do not cover the defects below.

## Findings

1. **CI02-ACC-R5 — Major; blocking: yes — Missing mandatory inputs bypass completeness validation.**

   **Location:** `backend/app/domain/assurance_report.py:125,158`; `backend/app/assurance/reporting.py:418`.

   **Expected:** Contract §§1.1–1.3 require the evidence set and other mandatory ingestion inputs to be present, required, available, and digested before comparison.

   **Actual:** Validation checks only supplied entries marked `required=true`. Using the exact downloaded `banking-report.json` from artifact **14157535738**, each following mutation—followed by clearing findings and correctly recomputing the report digest—exits **0**, classifying **0 new / 0 unchanged / 6 resolved**:

   - Remove the `evidence_set` input entry.
   - Replace `inputs` with `[]`.
   - Mark the evidence-set entry `required=false, available=false, digest=null`.

   An explicitly unavailable entry still marked required correctly exits 2; the original R2 probe is repaired, but completeness remains bypassable.

   **Smallest correction/recheck:** Validate mandatory input presence and requiredness for the report’s scope, alongside availability and digest checks. Repeat these three probes on both sides; require attributable `findings-not-comparable`, exit 2, and no classification.

2. **CI02-ACC-R3 — Minor; blocking: no individually — Dual-failure attribution remains partial.**

   **Location:** `backend/app/assurance/reporting.py:399`; `tools/assurance.py:539`.

   **Expected:** Contract §3 requires `invalid_input="both"` when both reports fail.

   **Actual:** Loading failures return before semantic validation examines the successfully loaded side. Independently reproduced:

   | Invalid previous | Invalid current | Actual attribution |
   |---|---|---|
   | Missing revision | Inconsistent finding identity | `previous` |
   | Digest mismatch | Source-locator identity | `previous` |
   | Contradictory finding baseline | Unsupported report version | `current` |

   Each comparison safely exits 2 without classifications, but omits an invalid input and its reason. Same-stage dual failures now correctly identify `both`.

   **Smallest correction/recheck:** Collect loading failures and semantic failures from every loadable report before returning the diagnostic. Rerun these mixed-stage pairs and require `both` with both reasons.

Prior-finding disposition: **R1 closed**, **R2’s original probe repaired** with broader completeness tracked under R5, **R3 partially repaired/open**, **R4 closed**. Unsupported versions are rejected on either or both sides.

## Check verification

[Hosted run 43703346736](https://github.com/anthonygraca/gherkin-knowledge-graph/actions/runs/43703346736) completed successfully at the submitted head. Observed every job:

| Job | Job ID | Conclusion |
|---|---:|---|
| Banking requirement assurance | 132779048108 | Success |
| Commit references | 132779048258 | Success |
| Cucumber acceptance and resolution gate | 132779048292 | Success |
| Frontend build and component tests | 132779048314 | Success |
| Offline contract, fixture, and API tests | 132779048402 | Success |
| Portable CTA self-assurance | 132781845563 | Success |

Observed hosted logs show **553 backend tests passed / 4 skipped**, fixture verification passing, Ruff lint/format passing, **14 frontend tests passed**, and **203 Cucumber scenarios / 1,972 steps passed**.

Downloaded and inspected these artifacts entirely in memory; all archive hashes match GitHub’s published digests:

- `cucumber-messages` — **14158220245**: all 17 CI-02 cases pass; embedded CI-02 feature matches the checkout.
- `assurance-banking` — **14157535738**: completed, six oracle-matching findings, valid digest and expected revisions.
- `assurance-self` — **14157965604**: completed, valid digest, evaluated at the submitted head, zero findings.

Retained `final-cucumber.ndjson`, its log, and the feature inventory agree on 17 passing CI-02 cases. `gt02-m4-recheck.ndjson` records three passing GT-02 cases; it supplies no CI-02 execution evidence.

Fresh local checks included independent CLI comparison and boundary probes, strict resolution (**203 cases / 1,972 results**), Ruff lint/format, and commit-reference validation (**five commits**). Cumulative `git diff --check` reports trailing whitespace in review Markdown.

**Not freshly executed locally:** full pytest/Cucumber suites, frontend build/tests, or fixture verification; their exact-run hosted results were inspected.

No files were edited, fixtures regenerated, commits created, or work delegated.
