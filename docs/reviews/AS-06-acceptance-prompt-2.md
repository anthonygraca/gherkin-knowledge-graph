# AS-06 acceptance review — submission 2

## Scope

**Story:** AS-06 (#28), milestone M3 — human decisions on version-bound proposals.
**Canonical criteria:** `docs/stories/AS-06.feature` (29 scenarios, SCN-3001…SCN-3029).
**Companion/normative contract:** `docs/stories/AS-06.md`.
**Specification approval:** `docs/reviews/AS-06-spec-review-5.md` (round 5).
**Owner dispositions:** `docs/adr/0012-closeout-scope-decisions.md` §1.
**Prior verdict:** `docs/reviews/AS-06-acceptance-1.md` (REQUEST_CHANGES; R1–R6).
**Author repair disposition:** `docs/reviews/AS-06-acceptance-1-repairs.md` (inspect, do not treat as proof).

This is an **independent acceptance review**, not a specification review. Inspect the actual
repository; do not edit, implement, regenerate fixtures, commit, or delegate. Read-only commands are
allowed.

## Snapshot

Review the committed cumulative close-out snapshot:

* PR: `#75` (`feat/28-closeout-m3` → `main`)
* Head commit: `be0c3ab760cbc7d3965d7d281f6632116bb0fe59`
* Base: `827e487d84be990739e588e9080637c725ecc882`
* Hosted CI: run `43674743478` on that head. Inspect the actual check conclusions; this prompt is
  not evidence that they passed.

Use `git diff 827e487..be0c3ab` and inspect the files at that commit. Later review-artifact commits
must not be treated as implementation changes.

## Evidence to inspect

* `docs/reports/omp-closeout/evidence/final-cucumber.log` and
  `docs/reports/omp-closeout/evidence/final-cucumber.ndjson` — full Cucumber run and Messages report.
* `docs/reports/omp-closeout/evidence/final-step-resolution.log` — strict gate.
* `backend/tests/test_review_workspace.py` — review journal, capture, decisions, restart,
  concurrency, stale/conflict, durability, loopback/origin, fixture immutability, and the repaired
  precedence/baseline/digest checks.
* `backend/tests/test_api_contract.py` — real API problem shapes and precedence.
* `frontend/src/App.tsx`, `frontend/src/App.test.tsx`, `bdd/step_definitions/review.steps.js` —
  review workspace UI/history and browser acceptance.
* `backend/app/domain/review.py`, `backend/app/persistence/review.py`,
  `backend/app/api/review_routes.py` — implementation.
* `docs/domain-contracts.md`, `docs/api-contracts.md` — published contracts.

Verify, at minimum:

1. Capture produces only a `proposed` link, with submitted provider/model/index provenance,
   baseline/commit, endpoint hashes, and canonical snapshot digest; no accepted link, evidence, or
   finding; no fixture byte changes.
2. Accept/reject append durable audit events; the journal is outside the fixture/evaluated repo;
   legacy LNK-007 acquires a snapshot at first decision; stale/conflicting/missing proposals are
   typed; a second terminal decision preserves the original bytes.
3. Workspace thread/pending/history project decisions over immutable baseline reads; baseline
   threads, findings, evidence, and fixture hashes are unchanged.
4. Identity unavailable/mismatch, loopback/origin restrictions, reason precedence, concurrency, and
   confirmed-rollback vs indeterminate persistence are observable and honest.
5. Restart recovery preserves accepted, pending, rejected, and history state; an uncommitted tail is
   not replayed and blocks mutations.
6. Every SCN-3001…SCN-3029 scenario is present and passing in the final Cucumber report; the
   implementation matches the companion's normative contract.
7. The UI shows proposal provenance, accept/reject controls with a required rejection reason, the
   decision history, and a refused write without a success-looking state.
8. Every prior finding **R1–R6** is repaired: precedence across identity/proposal/reason; baseline-
   scoped capture conflicts; separate browser-origin allowlist and malformed-origin refusal; an
   independent hand-written canonical digest oracle; a post-write byte-preservation assertion; and
   published failure guidance consistent with indeterminate recovery.

## Output format

Return exactly one Markdown document:

* `## Verdict` — `APPROVE`, `REQUEST_CHANGES`, or `NEEDS_INPUT`.
* `## Criterion assessment` — one row per scenario ID: PASS / FAIL / NOT VERIFIED, with the
  evidence selector or artifact inspected.
* `## Findings` — numbered `AS06-ACC-R<n>` with severity (`critical`/`major`/`minor`), blocking
  status, path/line, expected/actual behavior, and the smallest correction/recheck. Distinguish
  observed defects from hypotheses. Re-use the prior finding IDs where the finding persists.
* `## Check verification` — what commands/reports and hosted checks you observed, and any required
  check you could not observe.

APPROVE requires every criterion satisfied at this snapshot, the repository invariants intact, no
open major finding, all prior findings repaired, and the required local and hosted checks observed
green. Do not re-review the specification.
