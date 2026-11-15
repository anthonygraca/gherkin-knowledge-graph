# M4 milestone review — submission 2

## Scope

**Milestone:** M4 — Continuous integration and research comparison (roadmap §7).
**Prior verdict:** `docs/reviews/M4-review-1.md` (REQUEST_CHANGES; M4-R1…R6).
**Repair record:** `docs/reviews/M4-review-1-repairs.md` (inspect; it is a disposition, not proof).
**Merged snapshot:** `main` at `db8e3096a5b4fc1fea2a190f3113de98f706a6f8` (PR #79 merge).
**Hosted CI on the merge commit:** run `43725911468`; verify with
`gh run view 43725911468 --json databaseId,conclusion,status,headSha,jobs`.

This is a **focused independent M4 re-review**. Inspect the actual repository; do not edit,
implement, commit, regenerate fixtures, or delegate. Read-only commands are allowed. Network access
is available for read-only `gh` verification.

## Required rechecks

Re-run the failing probes from M4-R1…R3 and verify R4–R6:

1. **M4-R1:** a `gherkin_executability`/portable report with `identity_kind` forged to
   `stable_fingerprint` must be refused with exit 2 / `findings-not-comparable` / no classification.
2. **M4-R2:** an unreadable historical commit must produce an incomplete `input`/`input-unreadable`
   diagnostic with the unavailable historical entry and known inputs retained; no completed report.
3. **M4-R3:** a non-UTF-8 report must be refused with `findings-not-comparable`, not a traceback.
4. **M4-R4:** the diff revision assertion now compares the saved reports' `evaluated_revision`.
5. **M4-R5:** an unwritable diff `--output`/`--summary` returns exit 2 with the publication diagnostic.
6. **M4-R6:** the merge-run JSON is committed/pinned in the final manifest and STATUS names the
   merged snapshot/run.

Then recheck the full M4 exit criteria. Prior review PASS evidence for benchmark/reproducibility,
optional-scope honesty, story approvals, invariants, and hosted checks may be referenced, but
re-observe the code/evidence for the repaired criteria. The final evidence to inspect:

* `docs/reports/omp-closeout/evidence/final-cucumber.ndjson` / `final-cucumber.log`,
  `final-backend.log`, `final-step-resolution.log`, `final-run-hashes.txt`, `final-manifest.sha256`,
  `hosted-ci-m4-main-run.json`, `hosted-ci-m4-review-fix-run.json`.
* `backend/tests/test_assurance_cli.py`; `bdd/step_definitions/ci.steps.js`;
  `docs/stories/CI-02.feature`.
* `backend/app/assurance/reporting.py`; `tools/assurance.py`; `docs/assurance-report-contract.md`.
* The M4 benchmark/research records and story acceptance records named in
  `docs/reviews/M4-review-prompt-1.md`.

## Output format

* `## Verdict` — `APPROVE`, `REQUEST_CHANGES`, or `NEEDS_INPUT`.
* `## M4 exit criteria` — one row per criterion: PASS / FAIL / NOT VERIFIED.
* `## Findings` — `M4-R<n>`, severity, blocking, path/artifact, expected/actual, smallest correction.
  Re-use prior IDs where a finding persists.
* `## Check verification` — observed commands/reports/hosted checks; name anything unobserved.

APPROVE requires all M4 exit criteria satisfied at the merged snapshot, the prior findings repaired,
the story approvals/invariants intact, no open major finding, and hosted checks observed green.
