# CI-01 acceptance review — submission 1

## Scope

**Prior verdicts:** `docs/reviews/CI-01-acceptance-1.md`, `CI-01-acceptance-2.md`, and `CI-01-acceptance-3.md` (REQUEST_CHANGES).
**Repairs:** `docs/reviews/CI-01-acceptance-1-repairs.md` (second-pass section).

**Story:** CI-01 (#36), milestone M4 — revision-triggered assurance and typed reports.
**Canonical criteria:** `docs/stories/CI-01.feature` (6 scenarios, SCN-3401…SCN-3406).
**Companion:** `docs/stories/CI-01.md`. **Spec approval:** `docs/reviews/CI-01-spec-review-4.md`.
**Owner disposition:** ADR 0012 §3. **Normative contract:** `docs/assurance-report-contract.md`.

This is an **independent acceptance review**. Inspect the actual repository; do not edit, implement,
regenerate fixtures, commit, or delegate. Read-only commands are allowed. Network access is available
for read-only `gh` verification.

## Snapshot

* PR: `#78` (`feat/36-37-m4-assurance` → `main`)
* Head commit: `2ad9205302d5ce97b38645acc7d61749c6a04f07`
* Base: `b6e6931c90f527fa4009a9ba9e9b11f92f9f315e`
* Hosted CI: run `43709476207`. Inspect the exact job/artifact conclusions with
  `gh run view 43709476207 --json databaseId,conclusion,status,headSha,jobs` and `gh pr checks 78`.

## Evidence to inspect

* `docs/reports/omp-closeout/evidence/final-cucumber.ndjson` / `final-cucumber.log`, the full
  acceptance report (202 scenarios / 1963 steps) and CI-01 cases.
* `docs/reports/omp-closeout/evidence/final-backend.log` (553 passed, 4 skipped),
  `final-step-resolution.log`, `final-fixture.log`, `final-run-hashes.txt`, the feature inventory.
* `tools/assurance.py`, `backend/app/assurance/reporting.py`,
  `backend/app/domain/assurance_report.py`.
* `.github/workflows/ci.yml` (`banking-assurance` and `self-assurance` jobs) and the hosted run
  artifacts (`assurance-banking`, `assurance-self`).
* `bdd/step_definitions/ci.steps.js`, `bdd/support/cta_bridge.py`; the CI-01 scenarios' execution.
* `docs/assurance-report-contract.md`, `docs/stories/CI-01.feature/.md`,
  `docs/reviews/CI-01-spec-review-4.md`.
* The hand-labeled oracle at `fixtures/banking-demo/expected/baseline-b.json`; the CLI report.

Verify, at minimum:

1. The completed banking report pins banking-demo/baseline-b, the exact resolved evaluated commit,
   the CTA evaluator revision, and input content hashes; findings match the hand-labeled oracle;
   the report/manifest live outside the evaluated repository.
2. The event resolver selects the PR head (never the test-merge SHA) and the push after SHA; the
   selected commit drives ingestion/evaluation, not just a field. Verify push/PR examples.
3. Portable self-assurance uses an attributable Cucumber report: `gherkin_executability` scope,
   tested commit, execution-report digest, source hashes equal to the indexed features, coverage gaps
   counted rather than findings, and no requirement-to-production-code claim.
4. A valid failed Cucumber report yields a completed report, `execution_failed` finding, exit 0, and
   no requirement verdict.
5. Each listed tool failure exits 2 with an incomplete diagnostic (stage/code, no findings); an
   unwritable destination emits the same JSON on stderr and cannot publish a stale completed report.
6. Hosted publication contains the report and input manifest, names the evaluated revision and
   finding count in the summary, requests no branch/commit/comment/deploy, and a failing test gate
   still allows completed execution findings publication without masking the gate. Publisher
   failure is distinguishable from evaluator outcome.
7. Every SCN-3401…SCN-3406 scenario is present and passing with real command/workflow evidence; the
   implementation matches the approved contract and does not weaken the offline default.

## Output format

* `## Verdict` — `APPROVE`, `REQUEST_CHANGES`, or `NEEDS_INPUT`.
* `## Criterion assessment` — one row per SCN: PASS / FAIL / NOT VERIFIED with the evidence.
* `## Findings` — numbered `CI01-ACC-R<n>` with severity, blocking, path/line/artifact,
  expected/actual, and the smallest correction/recheck.
* `## Check verification` — observed commands/reports/artifacts/hosted checks; name anything
  unobserved.

Verify every prior finding is repaired by re-running the failing probes. APPROVE requires every criterion satisfied at this snapshot, the contract and invariants intact, no
open major finding, and the required local/hosted checks observed green. Do not re-review the
specification.
