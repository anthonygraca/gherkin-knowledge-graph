# CI-02 acceptance review — submission 1

## Scope

**Story:** CI-02 (#37), milestone M4 — comparable finding-set diff.
**Canonical criteria:** `docs/stories/CI-02.feature` (6 scenarios, SCN-3501…SCN-3506).
**Companion:** `docs/stories/CI-02.md`. **Spec approval:** `docs/reviews/CI-02-spec-review-4.md`.
**Owner disposition:** ADR 0012 §3. **Normative contract:** `docs/assurance-report-contract.md`.

This is an **independent acceptance review**. Inspect the actual repository; do not edit, implement,
regenerate fixtures, commit, or delegate. Read-only commands are allowed. Network access is available
for read-only `gh` verification.

## Snapshot

* PR: `#78` (`feat/36-37-m4-assurance` → `main`)
* Head commit: `7ed56c28ffc33552eab2575e501dd5292e522180`
* Base: `b6e6931c90f527fa4009a9ba9e9b11f92f9f315e`
* Hosted CI: run `43695481792`; inspect the exact job/artifact conclusions.

## Evidence to inspect

* `docs/reports/omp-closeout/evidence/final-cucumber.ndjson`, `final-cucumber.log`,
  `gt02-m4-recheck.ndjson`; CI-02 cases and the feature inventory.
* `backend/app/assurance/reporting.py`, `backend/app/domain/assurance_report.py`,
  `tools/assurance.py`; the CLI diff.
* `bdd/step_definitions/ci.steps.js`, `bdd/support/cta_bridge.py`; the executed CI-02 scenarios.
* `docs/assurance-report-contract.md`, `docs/stories/CI-02.feature/.md`,
  `docs/reviews/CI-02-spec-review-4.md`.
* The hand-labeled banking expected findings; run the CLI diff independently if useful.

Verify, at minimum:

1. Stable identity is the existing fingerprint over rule id, finding type, sorted artifact ids/keys;
   supplied identities are verified and duplicates rejected without rewriting payloads.
2. Forward banking comparison reports exactly 2 new / 4 unchanged / 0 resolved, with new types
   `reverification_required` and `verification_failed`; reverse reports 0/4/2; self reports 0/4/0.
3. The diff includes both evaluated revisions and both report digests; resolved means absent from the
   current comparable set; no verification evidence, accepted link, or requirement verdict is
   created.
4. Payload-only changes stay unchanged and retain complete before/after payloads, including status
   and artifact revisions; neither payload is rewritten.
5. Every invalid-comparison example (missing previous/current revision, current incomplete,
   repository/rule-scope/policy/evaluator mismatch, contradictory baseline, duplicate/inconsistent
   identity, report-digest mismatch) exits 2 with `findings-not-comparable`, identifies the invalid
   input and reason, and returns no classification.
6. Source-locator reports are refused, including claimed mappings; no displaced finding is classified
   as resolved/new.
7. Every SCN-3501…SCN-3506 scenario is present and passing with real CLI/BDD evidence; the
   implementation matches the approved contract.

## Output format

* `## Verdict` — `APPROVE`, `REQUEST_CHANGES`, or `NEEDS_INPUT`.
* `## Criterion assessment` — one row per SCN: PASS / FAIL / NOT VERIFIED with the evidence.
* `## Findings` — numbered `CI02-ACC-R<n>` with severity, blocking, path/line/artifact,
  expected/actual, and the smallest correction/recheck.
* `## Check verification` — observed commands/reports/hosted checks; name anything unobserved.

APPROVE requires every criterion satisfied at this snapshot, the contract and invariants intact, no
open major finding, and the required local/hosted checks observed green. Do not re-review the
specification.
