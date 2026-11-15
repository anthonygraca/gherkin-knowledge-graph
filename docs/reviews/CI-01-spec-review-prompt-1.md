# CI-01 specification review — submission 1

## Scope

**Story:** CI-01 (#36), milestone M4 — revision-triggered assurance and typed reports.
**Canonical feature:** `docs/stories/CI-01.feature` (draft, 6 scenarios, SCN-3401…SCN-3406).
**Companion:** `docs/stories/CI-01.md`.
**Owner disposition:** `docs/adr/0012-closeout-scope-decisions.md` §3.
**Issue body:** GitHub #36.
**Current code:** `backend/app/assurance/`, `tools/`, `.github/workflows/ci.yml`, the portable
execution importer and fixtures.

This is a **specification review only**. Do not implement, edit, commit, or delegate. Read-only
commands are allowed. The question is whether implementation can begin without guessing about scope,
observable behaviour, report shape, evidence, or the boundary with existing tests.

Assess:

1. Are the six scenarios precise, observable, and consistent with the issue and ADR 0012?
2. Is the typed report contract sufficiently specified for implementation and CI-02 comparison
   (scope, evaluated revision, evaluator revision, input content hashes/manifest, findings,
   completeness, policy/rule identity, digests, self-assurance provenance)?
3. Are revision selection (PR head vs test-merge SHA), exit codes (`0` completed, `2` tool failure),
   incomplete diagnostics, and the “failure is not a finding” rule unambiguous?
4. Is the self-assurance scope (`gherkin_executability`) clearly separated from banking
   requirement assurance, with no production-code verification claim?
5. Are the workflow publication requirements (artifact, summary, no branch writes) testable, and
   is hosted execution required rather than inferred from YAML?
6. Are any scenarios missing failure/boundary cases or conflicting with the existing M0–M3
   contracts? Distinguish blocking ambiguities from nonblocking improvements.

## Output format

Return exactly one Markdown document:

* `## Verdict` — `APPROVE` or `REQUEST_CHANGES`.
* `## Criterion assessment` — one row per SCN-3401…SCN-3406: CLEAR / AMBIGUOUS / MISSING, with the
  exact text or contract needing change.
* `## Findings` — numbered `CI01-SPEC-R<n>`, severity (`major`/`minor`), blocking status, the
  ambiguity/conflict, and the smallest correction.
* `## Implementation readiness` — what can be implemented without guessing, and what must be frozen
  first.

APPROVE only if implementation can begin without a silent design choice.
