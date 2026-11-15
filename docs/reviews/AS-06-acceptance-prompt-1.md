# AS-06 acceptance review — submission 1

## Scope

**Story:** AS-06 (#28), milestone M3 — human decisions on version-bound proposals.
**Canonical criteria:** `docs/stories/AS-06.feature` (29 scenarios, SCN-3001…SCN-3029).
**Companion/normative contract:** `docs/stories/AS-06.md`.
**Specification approval:** `docs/reviews/AS-06-spec-review-5.md` (round 5).
**Owner dispositions:** `docs/adr/0012-closeout-scope-decisions.md` §1.

This is an **independent acceptance review**, not a specification review. Inspect the actual
repository; do not edit, implement, regenerate fixtures, commit, or delegate. Read-only commands are
allowed.

## Snapshot

The cumulative close-out diff is the uncommitted working tree based on `827e487`. Use
`git diff 827e487` and inspect the files directly. Do not treat a summary as evidence.

## Evidence to inspect

* `docs/reports/omp-closeout/evidence/final-cucumber.log` and
  `docs/reports/omp-closeout/evidence/final-cucumber.ndjson` — the full Cucumber run and its
  Messages report.
* `backend/tests/test_review_workspace.py` — review journal, capture, decisions, restart,
  concurrency, stale/conflict, durability, loopback/origin, fixture immutability.
* `backend/tests/test_api_contract.py`, `backend/tests/api` behavior — real API problem shapes.
* `frontend/src/App.tsx`, `frontend/src/App.test.tsx`, `bdd/step_definitions/review.steps.js` —
  review workspace UI/history and browser acceptance.
* `backend/app/domain/review.py`, `backend/app/persistence/review.py`,
  `backend/app/api/review_routes.py` — implementation.
* `docs/domain-contracts.md`, `docs/api-contracts.md` — published contracts.

Verify, at minimum:

1. Capture produces only a `proposed` link, with the submitted provider/model/index provenance,
   baseline/commit, endpoint hashes, and canonical snapshot digest; no accepted link, evidence, or
   finding, and no fixture byte changes.
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

## Output format

Return exactly one Markdown document:

* `## Verdict` — `APPROVE`, `REQUEST_CHANGES`, or `NEEDS_INPUT`.
* `## Criterion assessment` — one row per scenario ID: PASS / FAIL / NOT VERIFIED, with the
  evidence selector or artifact inspected.
* `## Findings` — numbered `AS06-ACC-R<n>` with severity (`critical`/`major`/`minor`), blocking
  status, path/line, expected/actual behavior, and the smallest correction/recheck. Distinguish
  observed defects from hypotheses.
* `## Check verification` — what commands/reports you observed, and any hosted check you could not
  observe.

APPROVE requires every criterion satisfied at this snapshot, the repository invariants intact, no
open major finding, and observed green required checks. Do not re-review the specification.
