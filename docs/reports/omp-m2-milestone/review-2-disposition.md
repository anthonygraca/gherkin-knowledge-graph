# Disposition of independent review 2 (submission 2 of 7)

Verdict: **REQUEST_CHANGES** (`review-2.md`, `gpt-6.1-sol`, high, finished 2026-11-13T23:31:04Z).
Review budget used: 2 of 7; this disposition prepares submission 3.

| Finding | Disposition | Repair |
| --- | --- | --- |
| M2-R07 incomplete reports pass the gate | **repaired** | `step-resolution.mjs` now requires at least one pickle and test case, a `testCaseFinished` for every started attempt, and a result for every expected test step; `SKIPPED`/`UNKNOWN` remain failures. A report with removed results or attempts now fails (probe suites still pass/fail as intended). |
| M2-R08 GT-02 incomplete | **not repaired — blocker** | AS-04, AS-05, SETUP-01 still unbound; inventory says so. |
| M2-R09 inventory infers passing from insufficient outcomes | **repaired** | Generator distinguishes starts, invoked steps, complete attempts, and outcomes; adds `incomplete_scenarios`, `skipped_results`, `missing_results`; `passing`/`complete` only when every case started, every attempt finished, and every result passed. GT-02 reconciliation compares every field. |
| M2-R12 human oracle review | **not repaired — owner action** | Needs the owner's hash-tied review of the two external inventories. |
| M2-R13 added accepted artifacts evade reverification | **repaired** | A relevant artifact absent at the tested revision is now a change. New test adds an accepted `SCN-001 implemented_by CODE-999` link plus the artifact and expects reverification naming `CODE-999`, with no failure. |
| M2-R14 provenance leaks across revisions | **repaired** | `provenance(repository_id, revision)` filters by the selected commit; execution responses pass the snapshot revision. New API test imports v1 and v2 and asserts each response lists only its own report. |
| M2-R15 FT-01 builds reuse one directory | **repaired** | The bridge builds each fixture into a distinct UUID directory and the step asserts the paths differ; FT-01 still passes. |

Full suite after these repairs: 78 scenarios passed (331 Gherkin steps + 156 hooks, 487 results),
strict gate ok. Submission 3 is recorded in `review-prompt-3.md` / `review-3.md`.

**Not claimed.** R08 and R12 remain blockers; expanded M2 is incomplete and unapproved. No commit,
push, PR, issue closure, human attestation, or stakeholder validation was produced.
