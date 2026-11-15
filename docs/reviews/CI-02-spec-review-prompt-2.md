# CI-02 specification review — submission 2

## Scope

**Story:** CI-02 (#37), milestone M4. **Feature:** `docs/stories/CI-02.feature`.
**Companion:** `docs/stories/CI-02.md`. **Owner disposition:** ADR 0012 §3.
**Prior verdict:** `docs/reviews/CI-02-spec-review-1.md` (REQUEST_CHANGES; CI02-SPEC-R1…R5).
**Resolution:** `docs/assurance-report-contract.md` and the companion's “Specification review 1
disposition”; the feature now references the contract and defines comparable inputs, retained
payloads, invalid-input preconditions, and the source-locator refusal.

Specification review only. Do not implement, edit, commit, or delegate. Re-assess the six scenarios
and the comparison contract for implementation readiness. Approve only if implementation can begin
without a silent design choice.

## Output format

* `## Verdict` — `APPROVE` or `REQUEST_CHANGES`.
* `## Criterion assessment` — one row per SCN-3501…SCN-3506: CLEAR / AMBIGUOUS / MISSING.
* `## Findings` — `CI02-SPEC-R<n>`, severity, blocking, the exact remaining ambiguity/conflict, and
  the smallest correction. Re-use prior IDs where a finding persists.
* `## Implementation readiness` — what is frozen and what remains.
