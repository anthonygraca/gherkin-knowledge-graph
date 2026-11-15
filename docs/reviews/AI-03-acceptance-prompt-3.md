# AI-03 acceptance review — submission 3

## Scope

**Story:** AI-03 (#32), milestone M3 — revision-aware retrieval snapshot lifecycle.
**Canonical criteria:** `docs/stories/AI-03.feature` (6 scenarios, SCN-3301…SCN-3306).
**Companion/normative contract:** `docs/stories/AI-03.md`.
**Specification approval:** `docs/reviews/AI-03-spec-review-2.md`.
**Owner dispositions:** `docs/adr/0012-closeout-scope-decisions.md` §2; ADR 0008.
**Prior verdict:** `docs/reviews/AI-03-acceptance-2.md` (R1/R2 partially repaired, blocking).
**Repair record:** `docs/reviews/AI-03-acceptance-1-repairs.md` (inspect, do not treat as proof).

This is an **independent acceptance review**. Inspect the actual repository; do not edit,
implement, regenerate fixtures, commit, or delegate. Read-only commands are allowed.

## Snapshot

* PR: `#75` (`feat/28-closeout-m3` → `main`)
* Head commit: `e463e9e3b496a6f60644d90c52e04da6f50f7dff`
* Base: `827e487d84be990739e588e9080637c725ecc882`
* Hosted CI: run `43679892961` on that head. Inspect the actual check conclusions.

Use `git diff 827e487..e463e9e3b496a6f60644d90c52e04da6f50f7dff` and inspect the files at that commit.

## What changed since submission 2

* Reads now require a canonical snapshot filename/binding, validate the stored repository identity,
  resolve the manifest baseline to a canonical baseline and commit, and reject a mislabeled or
  cross-baseline snapshot. Exact-binding refresh passes the requested baseline. `manifests()` omits
  non-canonical/corrupt files instead of serving them.
* Publication is staged outside `snapshots/`; readers take the lifecycle lock and cannot observe a
  pending snapshot until the pointer is committed and the snapshot is atomically moved into
  `snapshots/`. Pointer failure removes staging and restores the previous pointer; an initial
  snapshot storage failure is typed `RetrievalUnavailable`; retry works.
* New tests cover repository mutation, a mislabeled baseline, an arbitrary snapshot filename, a
  paused pointer publication with a concurrent reader, and a typed initial snapshot write failure.

## Evidence to inspect

* `docs/reports/omp-closeout/evidence/final-cucumber.ndjson` — AI-03 cases and full run.
* `backend/tests/test_retrieval_lifecycle.py` — change planning, cache keys, publication, rollback,
  compatibility, mixed-context rejection, evidence-only reuse, model changes, corrupt reads, timing,
  and the new read/publication probes.
* `backend/app/retrieval/lifecycle.py`, `backend/app/domain/retrieval_lifecycle.py` — implementation.
* `backend/app/api/retrieval_lifecycle_routes.py` — API surfaces.
* `docs/domain-contracts.md`, `docs/api-contracts.md`, ADR 0008.
* `bdd/step_definitions/retrieval_lifecycle.steps.js`.

Verify, at minimum:

1. Content-hash change planning is CTA-owned; added/changed/removed artifacts are reported by
   `artifact_id`/locator; no CocoIndex internal embedding count is claimed. `items_embedded` is
   `null` when the transport cannot observe it; refresh reports `not_available` honestly.
2. Cache keys and manifests bind settings, artifact content hashes, model config, formatting
   version, and repository identity; artifacts outside the candidate batch remain in the corpus.
3. Snapshot publication is isolated; a pointer failure publishes neither pointer nor usable
   snapshot; concurrent readers cannot observe the pending snapshot; retry/recovery works;
   baseline-a remains intact.
4. Reads validate the canonical filename/binding, stored repository, resolved baseline commit, derived
   identity, stored corpus key, and requested baseline/context; corrupt, renamed, or cross-baseline
   snapshots are refused or omitted, not served.
5. Mixed contexts are rejected; evidence-only reuse does not change retrieval identity; refresh
   metrics are honest.
6. Every prior finding **R1–R3** is repaired: repository/commit/canonical-filename validation and
   exact-binding context; staged, reader-isolated publication with typed storage failure; and elapsed
   time including key construction.

## Output format

Return exactly one Markdown document:

* `## Verdict` — `APPROVE`, `REQUEST_CHANGES`, or `NEEDS_INPUT`.
* `## Criterion assessment` — one row per canonical scenario ID: PASS / FAIL / NOT VERIFIED.
* `## Findings` — numbered `AI03-ACC-R<n>` with severity, blocking status, path/line,
  expected/actual, and the smallest correction/recheck. Re-use prior IDs where the finding persists.
* `## Check verification` — observed commands/reports and hosted checks; name anything unobserved.

APPROVE requires every canonical criterion satisfied at this snapshot, the repository invariants
intact, no open major finding, all prior findings repaired, and required local and hosted checks
observed green.
