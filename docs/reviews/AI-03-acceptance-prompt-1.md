# AI-03 acceptance review — submission 1

## Scope

**Story:** AI-03 (#32), milestone M3 — revision-aware retrieval snapshot and cache lifecycle.
**Canonical criteria:** `docs/stories/AI-03.feature` (6 scenarios, SCN-3301…SCN-3306).
**Companion/normative contract:** `docs/stories/AI-03.md`.
**Specification approval:** `docs/reviews/AI-03-spec-review-2.md` (round 2).
**Owner re-scope:** `docs/adr/0012-closeout-scope-decisions.md` §2; ADR 0008 amendment.

This is an **independent acceptance review**, not a specification review. Inspect the actual
repository; do not edit, implement, regenerate fixtures, commit, or delegate. Read-only commands are
allowed.

## Snapshot

The cumulative close-out diff is the uncommitted working tree based on `827e487`. Use
`git diff 827e487` and inspect the files directly.

## Evidence to inspect

* `docs/reports/omp-closeout/evidence/final-cucumber.log` and `final-cucumber.ndjson`.
* `backend/tests/test_retrieval_lifecycle.py` — hand-labeled change set, evidence-only reuse,
  model-change invalidation, failed refresh, mixed context, compatible combination, API, settings.
* `backend/app/domain/retrieval_lifecycle.py`, `backend/app/retrieval/lifecycle.py`,
  `backend/app/api/retrieval_lifecycle_routes.py`.
* `bdd/step_definitions/retrieval_lifecycle.steps.js` and the bridge op.
* `docs/domain-contracts.md`, `docs/api-contracts.md`.

Verify, at minimum:

1. The plan compares eligible source/test artifacts by content hash; baseline-a→b yields
   CODE-001/TEST-002 changed, CODE-002/TEST-001 unchanged; both resolved commits and the referenced
   previous immutable manifest's artifact hashes are observable.
2. `corpus_cache_key` excludes commits; `snapshot_binding` includes the commit; evidence-only
   content with identical config shares the cache key but not the binding, with an empty plan, no
   source/failure inference, and no adapter call.
3. A model/weights change changes the config digest/cache key, the old snapshot remains readable and
   unchanged, and compatibility is not claimed.
4. A failing adapter reports a typed failure, publishes no baseline-b pointer/snapshot, keeps the
   baseline-a manifest usable, and never substitutes baseline-a results for baseline-b.
5. Mixed-binding batches fail `409 mixed-index-context` with no combined list; a compatible bound
   batch returns a contiguous ranked list carrying the CTA binding while retaining the provider's
   own index revision in batch provenance; `TraceCandidate` is unchanged.
6. The refresh report has measured non-negative elapsed time, added/changed/removed/unchanged
   counts, `items_embedded: null` with `not_available` when unobserved, and the snapshot/config
   identity. No CocoIndex internal embedding count is inferred.
7. Every SCN-3301…SCN-3306 scenario is present and passing in the final Cucumber report.

## Output format

Return exactly one Markdown document:

* `## Verdict` — `APPROVE`, `REQUEST_CHANGES`, or `NEEDS_INPUT`.
* `## Criterion assessment` — one row per scenario ID: PASS / FAIL / NOT VERIFIED.
* `## Findings` — numbered `AI03-ACC-R<n>` with severity, blocking, path/line, expected/actual,
  smallest correction/recheck.
* `## Check verification` — commands/reports observed and any unobserved hosted check.

APPROVE requires every criterion satisfied at this snapshot, invariants intact, no open major
finding, and observed green required checks.
