# CI-02 specification review — submission 1

## Scope

**Story:** CI-02 (#37), milestone M4 — comparable finding-set diff.
**Canonical feature:** `docs/stories/CI-02.feature` (draft, 6 scenarios, SCN-3501…SCN-3506).
**Companion:** `docs/stories/CI-02.md`.
**Owner disposition:** `docs/adr/0012-closeout-scope-decisions.md` §3.
**Issue body:** GitHub #37.
**Current code:** `backend/app/domain/models.py` (`finding_fingerprint`),
`backend/app/assurance/`, the banking expected finding sets, and CI-01’s report contract.

This is a **specification review only**. Do not implement, edit, commit, or delegate. Read-only
commands are allowed. The question is whether implementation can begin without guessing about
finding identity, report comparability, classification, payload retention, refusal semantics, or
the report format.

Assess:

1. Are the six scenarios precise, observable, and consistent with the issue and ADR 0012?
2. Is finding identity fixed to the existing `(rule_id, finding_type, sorted artifact ids)` stable
   fingerprint, with prose/evidence excluded? Are the expected 2 new / 4 unchanged forward and
   0 new / 4 unchanged / 2 resolved reverse counts derivable from the hand-labeled fixtures?
3. Are the seven invalid-comparison conditions and the portable source-locator refusal precisely
   specified, including the `findings-not-comparable` exit code and the “no classification”
   requirement?
4. Does the spec define the comparison report shape and the retained before/after payloads well
   enough to implement and document?
5. Are new/unchanged/resolved semantics compatible with “change is not failure” and “absence does
   not imply remediation”?
6. Are any scenarios missing boundary cases or conflicting with CI-01’s report contract? Distinguish
   blocking ambiguities from nonblocking improvements.

## Output format

Return exactly one Markdown document:

* `## Verdict` — `APPROVE` or `REQUEST_CHANGES`.
* `## Criterion assessment` — one row per SCN-3501…SCN-3506: CLEAR / AMBIGUOUS / MISSING, with the
  exact text or contract needing change.
* `## Findings` — numbered `CI02-SPEC-R<n>`, severity (`major`/`minor`), blocking status, the
  ambiguity/conflict, and the smallest correction.
* `## Implementation readiness` — what can be implemented without guessing, and what must be frozen
  first.

APPROVE only if implementation can begin without a silent design choice.
