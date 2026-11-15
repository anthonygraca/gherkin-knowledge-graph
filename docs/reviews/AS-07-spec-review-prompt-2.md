# AS-07 specification review — round 2

Specification freeze re-review for AS-07 (#29). Round 1
(`docs/reviews/AS-07-spec-review.md`) returned **REVISE** with AS07-SPEC-R1…R5. The feature and
companion were revised.

Read-only inspection only. Do not edit, run tests, implement, commit, or delegate.

## Inputs

- `docs/stories/AS-07.feature` (SCN-3101…SCN-3106).
- `docs/stories/AS-07.md` (normative contract notes: problem extensions, provider outcomes,
  provider catalogue, provenance presentation, UI states, verification boundary, fake-mode docs).
- `docs/stories/AS-06.md` and `docs/adr/0012-closeout-scope-decisions.md` for the proposal surfaces.
- Round-1 review.

## Required assessment

For each round-1 finding AS07-SPEC-R1…R5, state whether it is repaired with the exact revised
location. Then assess the full revised specification for new blocking ambiguity, contradiction, or
coverage gaps. Do not re-raise a resolved point; do not demand implementation detail beyond the
observable contract.

Return one Markdown document:

- `## Verdict` — `APPROVE` or `REVISE`.
- `## Round-1 dispositions` — one row per finding: repaired/open, location, one-sentence basis.
- `## New findings` — numbered `AS07-SPEC2-R<n>` with severity and smallest repair (empty if none).
- `## Scenario assessment` — one row per scenario ID: PASS/FAIL/NOT VERIFIED for specification
  readiness.
- `## Freeze conditions` — empty if APPROVE.

APPROVE only when no blocking specification ambiguity remains and every round-1 finding is repaired.
