# Disposition of independent review 3 (submission 3 of 7)

Verdict: **REQUEST_CHANGES** (`review-3.md`, `gpt-6.1-sol`, high, finished 2026-11-13T23:46:53Z).
Budget used: 3 of 7.

| Finding | Disposition | Repair |
| --- | --- | --- |
| M2-R07 gate accepts omitted cases / bad hooks | **repaired** | The gate derives eligible pickles from the tag exclusion policy, requires a test case and completed attempts for each, validates result identity (missing/duplicate/unknown), and requires hook results to be `PASSED`/`FAILED`. Counterexamples reproduced and now rejected: omitted case → exit 1; one hook `SKIPPED` → exit 1; duplicated result → exit 1. The real report still passes. |
| M2-R09 inventory depends on surviving cases/results | **repaired** | Generator counts eligible pickles from tags, requires a case for each, matches results by expected test-step id, and records `duplicate_results`/`unknown_results`; complete/passing requires all of them zero. Counterexamples: removed case → `incomplete=1`; duplicate result → `duplicate_results=1`, not passing. GT-02 reconciliation mirrors the same rules. |
| M2-R08 GT-02 | **not repaired — blocker** | AS-04 (5), AS-05 (2), SETUP-01 (8) still unexecuted. |
| M2-R12 human oracle review | **not repaired — owner action** | No owner attestation for the two external inventories. |
| M2-R16 evidence cache ignores baseline | **repaired** | Cache and pending keys are `baseline:requirement`; failed lookups retry. New test opens REQ-003's lifecycle finding at baseline-a, switches to baseline-b, opens the failure, and sees EV-003 with its tested commit. |
| M2-R01 manifest stale | **repaired for this submission** | The final manifest is generated after all documentation edits and excludes mutable review logs. |

**Not claimed.** R08 and R12 remain blockers; expanded M2 is incomplete.
