# AS-06 specification review — round 4

Specification freeze re-review for AS-06 (#28). Round 3
(`docs/reviews/AS-06-spec-review-3.md`) returned **REVISE** with AS06-SPEC2-R2 and AS06-SPEC-R9 open
and new finding AS06-SPEC3-R1. The feature and companion were revised.

Read-only inspection only. Do not edit, run tests, implement, commit, or delegate.

## Inputs

- `docs/stories/AS-06.feature` (SCN-3001…SCN-3028).
- `docs/stories/AS-06.md` (normative contract notes).
- Round-3 review.

## Required assessment

For `AS06-SPEC2-R2`, `AS06-SPEC-R9`, and `AS06-SPEC3-R1`, state whether each is repaired with the
exact revised location. Then assess the full revised specification for new blocking ambiguity,
contradiction, or coverage gaps. Do not re-raise a resolved point; do not demand implementation
detail beyond the observable contract.

Return one Markdown document:

- `## Verdict` — `APPROVE` or `REVISE`.
- `## Round-3 dispositions` — one row per finding: repaired/open, location, one-sentence basis.
- `## New findings` — numbered `AS06-SPEC4-R<n>` with severity and smallest repair (empty if none).
- `## Scenario assessment` — one row per scenario ID: PASS/FAIL/NOT VERIFIED for specification
  readiness.
- `## Freeze conditions` — empty if APPROVE.

APPROVE only when no blocking specification ambiguity remains and every prior blocking finding is
repaired.
