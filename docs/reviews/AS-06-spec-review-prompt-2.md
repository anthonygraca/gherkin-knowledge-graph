# AS-06 specification review — round 2

This is the specification freeze re-review for AS-06 (#28). Round 1
(`docs/reviews/AS-06-spec-review.md`) returned **REVISE** with blocking findings AS06-SPEC-R1…R9.
The canonical feature and companion were revised; the owner dispositions are accepted in
`docs/adr/0012-closeout-scope-decisions.md` §1.

Read-only inspection only. Do not edit files, run tests, implement, commit, or delegate.

## Inputs

- Revised canonical criteria: `docs/stories/AS-06.feature`.
- Revised normative contract notes: `docs/stories/AS-06.md` (baseline selection, snapshot identity
  and digest, legacy binding, capture/decision surfaces, error precedence, journal, workspace
  reads, local write boundary, UI).
- Accepted ADR 0012 §1.
- Round 1 findings: `docs/reviews/AS-06-spec-review.md`.

## Required assessment

For each round-1 finding AS06-SPEC-R1…R9, state whether it is repaired, with the exact revised
text/contract location. Then assess the full revised specification for new blocking ambiguity,
contradiction, or coverage gaps. Do not demand implementation detail beyond the observable
contract; do not re-raise a finding that the revised text resolves.

Return exactly one Markdown document:

- `## Verdict` — `APPROVE` or `REVISE`.
- `## Round-1 dispositions` — one row per finding: `repaired` / `open`, location, one-sentence
  justification.
- `## New findings` — numbered `AS06-SPEC2-R<n>` with severity and smallest repair (empty if none).
- `## Scenario assessment` — one row per scenario ID: PASS/FAIL/NOT VERIFIED for specification
  readiness.
- `## Freeze conditions` — empty if APPROVE, otherwise what must change.

APPROVE only when no blocking specification ambiguity remains and every round-1 finding is repaired.
