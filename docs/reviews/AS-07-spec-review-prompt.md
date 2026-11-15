# AS-07 specification review request

You are the independent specification reviewer for CTA story AS-07 (#29), milestone M3. This is a
**specification freeze review**, not an implementation or acceptance review. Read-only inspection
only. Do not edit files, run tests, implement, commit, or delegate.

## Inputs

- Canonical draft: `docs/stories/AS-07.feature` (6 scenarios, SCN-3101…SCN-3106).
- Companion: `docs/stories/AS-07.md`.
- Owner decisions: `docs/adr/0012-closeout-scope-decisions.md` (AS-06 provenance/workspace contract
  is adopted; AS-07 depends on it).
- Repository invariants: `AGENTS.md`; roadmap AS-07/F-07; the GitHub issue body reproduced below.
- Existing provider/error/UI contracts: `backend/app/discovery/registry.py`,
  `backend/app/domain/errors.py`, `backend/app/domain/api.py`, `backend/app/api/routes.py`,
  `backend/app/api/errors.py`, `backend/app/domain/retrieval.py`, `docs/domain-contracts.md`.

GitHub issue #29 intake (verbatim):

```text
As a reviewer, I want useful behaviour when the AI is offline and clear fake/real provenance, so that the tool stays usable without the model.

Scenario: Discovery provider unavailable
  Given the configured discovery provider is not registered
  When the reviewer requests candidates
  Then the response is a 400 problem naming the failed provider
  And the response lists the providers that are registered
  And the candidate panel states that no provider is available
  And accepted links and evidence remain fully usable

Scenario: Provenance is visible for every proposal
  Given a candidate produced by the "fake" provider
  When the proposal is displayed
  Then the provider name, model version, and index revision are shown
  And a proposal produced by a real model is distinguishable from a fixture proposal

Definition of done:
- Provider failure surfaces as a problem document and a UI state, never as a finding or an empty success
- Provenance (provider, model_version, index_revision) displayed wherever a proposal appears
- Offline fake mode documented as the default development path
```

## What to decide

Assess only whether the canonical specification is ready to freeze for implementation:

1. Are unregistered provider, registered-but-failing provider, empty success, and proposal
   provenance separated by observable outcomes with no fallback or finding?
2. Is the deterministic failure transport / recorded CocoIndex response honestly described as a test
   double at the provider boundary, with the real API route, problem mapping, and UI exercised?
3. Are the UI states and provenance labels specific enough to test (failed provider, registered
   list, empty result, fixture label, CTA snapshot binding label, "not recorded" historical value)?
4. Does it preserve invariants: failure never becomes a finding or accepted link, fake remains the
   default, no silent provider switch, accepted thread/evidence unaffected?
5. Are scenario IDs stable, unique, and correctly ranged?
6. Are success, failure, boundary, and missing-provenance paths covered without contradiction?

## Output format

Return exactly one Markdown document:

- `## Verdict` — `APPROVE` or `REVISE`.
- `## Findings` — numbered `AS07-SPEC-R<n>` entries; each with severity (`blocking`/`nonblocking`),
  the scenario or section, the ambiguity/contradiction, and the smallest precise wording or
  contract change that repairs it. Do not raise implementation-style findings.
- `## Scenario assessment` — one row per scenario ID with PASS/FAIL/NOT VERIFIED for
  specification readiness.
- `## Freeze conditions` — empty if APPROVE.

APPROVE only when no blocking ambiguity or contradiction remains.
