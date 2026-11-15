## Verdict

**REQUEST_CHANGES**

All 29 scenario IDs are present in the final Cucumber Messages report: **37 concrete cases passed**, including all outline examples and three browser scenarios. However, implementation defects violate the approved companion contract, and required frontend/hosted checks were not observed green for this snapshot.

## Criterion assessment

`M` denotes `docs/reports/omp-closeout/evidence/final-cucumber.ndjson`. PASS assesses the specified scenario examples using their execution records and inspected bindings/implementation; additional companion-contract defects appear below.

| Scenario ID | Assessment | Evidence selector or artifact inspected |
|---|---|---|
| SCN-3001 | PASS | M `@SCN-3001`; capture/provenance/fixture assertions; independent canonical-digest calculation matched. |
| SCN-3002 | PASS | M `@SCN-3002`; `test_accept_projects_workspace_and_preserves_baseline`; legacy snapshot construction. |
| SCN-3003 | PASS | M `@SCN-3003`; `test_rejection_retains_reason_and_excludes_proposal`. |
| SCN-3004 | PASS | M `@SCN-3004`; identity-mismatch assertion. Broader precedence defect: R1. |
| SCN-3005 | PASS | M `@SCN-3005`, both examples; absent/null reason assertions. |
| SCN-3006 | PASS | M `@SCN-3006`, both examples; empty/whitespace reason assertions. |
| SCN-3007 | PASS | M `@SCN-3007`; `test_unset_operator_disables_writes`. Broader precedence defect: R1. |
| SCN-3008 | PASS | M `@SCN-3008`; `test_second_terminal_decision_preserves_original_bytes`. |
| SCN-3009 | PASS | M `@SCN-3009`; `test_stale_acceptance_is_refused`; endpoint-hash comparison. |
| SCN-3010 | PASS | M `@SCN-3010`; `test_confirmed_rollback_does_not_publish`; restart assertions. |
| SCN-3011 | PASS | M `@SCN-3011`; missing-proposal assertion. Broader precedence defect: R1. |
| SCN-3012 | PASS | M `@SCN-3012`, all four examples; endpoint/direction/hash validation. |
| SCN-3013 | PASS | M `@SCN-3013`; duplicate-capture implementation returns the existing snapshot without appending. |
| SCN-3014 | PASS | M `@SCN-3014`; accepted-state recovery, unrelated pending proposal, history and byte assertions. |
| SCN-3015 | PASS | M `@SCN-3015`; append implementation inspected. Byte assertion weakness: R5. |
| SCN-3016 | PASS | M `@SCN-3016`; `test_concurrent_decisions_serialize`; workspace lock and terminal-event inspection. |
| SCN-3017 | PASS | M `@SCN-3017`, both examples; peer/origin refusals. Additional origin defects: R3. |
| SCN-3018 | PASS | M `@SCN-3018`; evidence-only revision binding and unchanged endpoint hashes. |
| SCN-3019 | PASS | M `@SCN-3019`; baseline-a/b acceptance projection assertions and `_applies`. |
| SCN-3020 | PASS | M `@SCN-3020`; browser provenance, rejection-reason control, acceptance and history assertions. |
| SCN-3021 | PASS | M `@SCN-3021`, both examples; pending/terminal capture conflicts. Baseline-scope defect: R2. |
| SCN-3022 | PASS | M `@SCN-3022`; successful loopback request without Origin. |
| SCN-3023 | PASS | M `@SCN-3023`; pending capture, provenance, history and restart-byte assertions. |
| SCN-3024 | PASS | M `@SCN-3024`; rejection/reason/operator recovery and exclusion assertions. |
| SCN-3025 | PASS | M `@SCN-3025`; browser rejection/history and baseline accepted-link exclusion. |
| SCN-3026 | PASS | M `@SCN-3026`; browser conflict, retained proposed state, refresh and single-decision assertions. |
| SCN-3027 | PASS | M `@SCN-3027`; tail replay exclusion, mutation refusal and append-count assertions. |
| SCN-3028 | PASS | M `@SCN-3028`; indeterminate durability, poisoning and bounded restart recovery. |
| SCN-3029 | PASS | M `@SCN-3029`, both examples; capture rollback/indeterminate live-state and restart assertions. |

## Findings

1. **AS06-ACC-R1 — major; blocking — Decision error precedence differs from the approved contract.**

   **Location:** `backend/app/api/review_routes.py:120`; `backend/app/persistence/review.py:392`; normative order at `docs/stories/AS-06.md:129`.

   **Expected:** Identity unavailable/mismatch precedes reason validation; missing proposal precedes reason validation.

   **Observed:** Direct route probes submitting a rejection with `reason: ""` returned `422 review-reason-required` for all three conditions: no configured operator, mismatched reviewer, and missing `LNK-999`. Expected responses are respectively `503 review-identity-unavailable`, `403 review-identity-mismatch`, and `404 proposal-not-found`. FastAPI body validation also precedes the configured identity checks.

   **Smallest correction/recheck:** Enforce the documented ordering across request validation and workspace checks. Add API assertions combining identity/proposal failures with invalid reasons and missing/invalid decision or baseline fields.

2. **AS06-ACC-R2 — major; blocking — Capture conflict detection ignores the capture baseline.**

   **Location:** `backend/app/persistence/review.py:704`; contract at `docs/stories/AS-06.md:108`.

   **Expected:** Capture conflicts use `(source_id, target_id, relation_type, baseline)`.

   **Observed:** Capturing SCN-002 → CODE-001 at baseline-a then submitting authoritative baseline-b hashes returned `409 proposal-conflict`. After accepting the baseline-a proposal, the baseline-b submission returned `409 review-conflict`. `_proposal_for_triple` considers journal captures without filtering their baseline. This prevents capturing a fresh version after endpoint content changes.

   **Smallest correction/recheck:** Include the canonical baseline in captured-proposal matching. Verify distinct-baseline captures coexist while same-baseline duplicate, provenance-conflict and terminal-conflict behavior remains correct.

3. **AS06-ACC-R3 — major; blocking — Browser-origin enforcement admits a test hostname and mishandles malformed origins.**

   **Location:** `backend/app/api/review_routes.py:36` and `backend/app/api/review_routes.py:63`.

   **Expected:** Present browser origins are restricted to the documented loopback hosts; disallowed origins produce `403 review-origin-forbidden`.

   **Observed:** The guard accepted `Origin: http://testclient` because socket-test exemptions also populate the browser-origin allowlist. `Origin: http://[` raised an uncaught `ValueError`; application exception handling maps that to an internal error instead of the typed origin refusal.

   **Smallest correction/recheck:** Separate transport-test exemptions from allowed browser hosts, catch origin parsing failures, and assert typed refusal with unchanged journal bytes for both inputs on capture and decision routes.

4. **AS06-ACC-R4 — major; blocking — Canonical-digest tests use the implementation as their expected-result oracle.**

   **Location:** `backend/tests/test_review_workspace.py:121`; `bdd/support/cta_bridge.py:977`.

   **Expected:** Repository invariant 6 requires expectations independent of the code under test.

   **Observed:** Both checks recompute the expected digest using the production `compute_snapshot_digest` and `snapshot_identity_payload` helpers. An incorrect field set or canonicalization shared by those helpers can pass both checks. Independent calculation during this review matched the current implementation, so this is an observed verification defect, not an observed incorrect digest.

   **Smallest correction/recheck:** Use a reviewed fixed vector or independent canonical JSON/hash calculation with explicitly specified identity fields. Verify presentation metadata does not affect identity.

5. **AS06-ACC-R5 — minor; nonblocking — The later-decision byte-preservation assertion compares two pre-write observations.**

   **Location:** `bdd/step_definitions/review.steps.js:680`.

   **Expected:** SCN-3015 checks that the later append preserves the earlier committed bytes.

   **Observed:** The assertion compares `journal_hashes_before` with `firstDecision.bytes_sha256`; neither observes the journal after the second decision. The append implementation supports preservation, but this assertion would miss rewriting during that operation.

   **Smallest correction/recheck:** Compare the post-operation journal prefix against the saved earlier bytes and rerun SCN-3015.

6. **AS06-ACC-R6 — minor; nonblocking — Published capture failure guidance contradicts indeterminate recovery.**

   **Location:** `docs/api-contracts.md:321`.

   **Expected:** The published API contract distinguishes confirmed rollback from an indeterminate append that may recover as a committed pending capture.

   **Observed:** “No failure appends an event” contradicts SCN-3029 and the companion’s approved durability contract.

   **Smallest correction/recheck:** Restrict that guarantee to validation/conflict refusals and confirmed rollback; describe indeterminate recovery consistently with the companion.

## Check verification

- Inspected `git diff 827e487`, relevant tracked and untracked implementation files, approved criteria/companion, owner dispositions, tests, bindings and published contracts.
- Parsed the full final Messages report: **177 executed cases, 1704 passing step results, successful run completion**. AS-06 contributes **29 IDs / 37 cases**, all passing without retries. Embedded AS-06 feature text equals the current file.
- Executed the strict report gate: **passed**, reporting 177 cases and 1704 resolved/started results.
- Observed retained backend execution: **535 passed, 4 skipped**. Observed fixture verification and retained lint/format logs as green.
- Independently executed read-only checks: `git diff --check 827e487`, Ruff lint and format with caching disabled, and frontend TypeScript checking with `--noEmit --incremental false`: **passed**.
- Direct route/workspace probes used an in-memory journal append substitute and wrote no files. They support R1–R3; they are not durability execution evidence. An attempted TestClient probe was interrupted after failing to complete and is not counted as passing.
- Manifest validation initially matched **54/54 entries**. At final recheck, `docs/STATUS.md` had changed externally and was the sole mismatch; listed implementation and execution artifacts still matched.
- Current-snapshot frontend `npm run build` and component-test results were **not observed**. Browser execution alone does not establish those checks.
- Hosted CI and commit-reference checks for this uncommitted snapshot were **not observed**. No files were edited, fixtures regenerated, commits created, or work delegated.