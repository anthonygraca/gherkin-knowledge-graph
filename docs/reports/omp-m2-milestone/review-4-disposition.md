# Disposition of independent review 4 (submission 4 of 7)

Verdict: **REQUEST_CHANGES** (`review-4.md`, `gpt-6.1-sol`, high, finished 2026-11-14T00:01:22Z).
Budget used: 4 of 7.

| Finding | Disposition | Repair |
| --- | --- | --- |
| M2-R07 unjoinable results / inconsistent run summary | **repaired** | Gate builds the set of `(attempt, testStep)` identities from started cases and rejects any result that does not join; it also rejects `testRunFinished.success=true` when any result is `FAILED`. Reproduced: unknown `testStepId`, unknown `testCaseStartedId`, and a failed hook with success=true all exit 1; the real report still passes. |
| M2-R09 orphan results ignored | **repaired** | The inventory generator refuses a report containing results for unknown attempts; GT-02 reconciliation asserts an empty orphan list. Reproduced: the orphan variant is rejected before a status can be claimed. |
| M2-R01 manifest stale / logs included | **repaired for this submission** | Log exclusion matches the basename (`review-<n>-stdout.log`) at any depth; the manifest is generated after the final documentation edits. |
| M2-R16 | closed by review 4 | — |
| M2-R08 / M2-R12 | **not repaired — blockers** | Migration and owner oracle attestation remain outstanding. |
