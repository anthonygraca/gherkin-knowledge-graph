# AI-03 specification review request

You are the independent specification reviewer for CTA story AI-03 (#32), milestone M3. This is a
**specification freeze review**, not an implementation or acceptance review. Read-only inspection
only. Do not edit files, run tests, implement, commit, or delegate.

## Inputs

- Canonical criteria: `docs/stories/AI-03.feature` (6 scenarios, SCN-3301…SCN-3306).
- Companion with normative contract notes: `docs/stories/AI-03.md`.
- Owner re-scope: `docs/adr/0012-closeout-scope-decisions.md` §2; ADR 0008 amendment.
- Existing contracts: `backend/app/domain/retrieval_lifecycle.py`,
  `backend/app/retrieval/lifecycle.py`, `backend/app/domain/models.py` (`TraceCandidate`),
  `docs/domain-contracts.md`, `docs/api-contracts.md`.
- GitHub issue #32 intake (verbatim):

```text
As a developer, I want revision-aware incremental embedding refresh, so that re-indexing only what changed stays cheap and honest.

Scenario: Only changed artifacts are re-embedded
  Given an index built for "baseline-a"
  When the repository moves to "baseline-b"
  Then only artifacts whose content_hash changed are re-embedded
  And unchanged artifacts keep their existing vectors
  And the new index revision differs from the previous one

Scenario: Index revisions are never mixed
  Given candidates produced from two different index revisions
  When results are combined
  Then they are rejected or reported separately, never merged into one ranked list

Definition of done:
- Refresh keyed on content_hash; cost measured and reported (items embedded, wall time)
- Index revision reported in every response that carries candidates
- Incremental path tested without a model, using the fixture index
```

## What to decide

Assess only whether the canonical specification is ready to freeze for implementation/acceptance:

1. Does the re-scope honestly avoid claiming CocoIndex internal embedding work while still
   satisfying the observable intent of revision-aware refresh and never mixing index revisions?
2. Are content-hash planning, cache keys, config manifests, evidence-only reuse, model-change
   invalidation, isolated publication, failed-refresh recovery, and honest cost reporting covered
   without contradiction?
3. Are mixed-context rejection and no-partial-list outcomes observable through the real
   combination boundary?
4. Are scenario IDs stable, unique, and correctly ranged?
5. Does the companion define the cache-key/snapshot-binding distinction and the API surface
   precisely enough for independent tests?

## Output format

Return exactly one Markdown document:

- `## Verdict` — `APPROVE` or `REVISE`.
- `## Findings` — numbered `AI03-SPEC-R<n>` with severity (`blocking`/`nonblocking`), scenario or
  section, ambiguity/contradiction, and smallest precise repair.
- `## Scenario assessment` — one row per scenario ID with PASS/FAIL/NOT VERIFIED for specification
  readiness.
- `## Freeze conditions` — empty if APPROVE.
