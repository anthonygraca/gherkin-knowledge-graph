# AI-03 acceptance review — submission 4

## Scope

**Story:** AI-03 (#32), milestone M3 — revision-aware retrieval snapshot lifecycle.
**Canonical criteria:** `docs/stories/AI-03.feature` (6 scenarios, SCN-3301…SCN-3306).
**Companion/normative contract:** `docs/stories/AI-03.md`.
**Specification approval:** `docs/reviews/AI-03-spec-review-2.md`.
**Owner dispositions:** `docs/adr/0012-closeout-scope-decisions.md` §2; ADR 0008.
**Prior verdicts:** `docs/reviews/AI-03-acceptance-2.md` (R1/R2 partially repaired) and
`docs/reviews/AI-03-acceptance-3.md` (R2 pointer-read gap; R4 hosted-verification gap).
**Repair record:** `docs/reviews/AI-03-acceptance-1-repairs.md` (inspect, do not treat as proof).

This is an **independent acceptance review**. Inspect the actual repository; do not edit,
implement, regenerate fixtures, commit, or delegate. Read-only commands are allowed. Network access
is available for read-only `gh` verification in this review.

## Snapshot

* PR: `#75` (`feat/28-closeout-m3` → `main`)
* Head commit: `e3a729dadc1551c4bf0070b16143594ddc8b43f9`
* Base: `827e487d84be990739e588e9080637c725ecc882`
* Hosted CI: run `43681413192` on that head. Verify it directly with
  `gh run view 43681413192 --json databaseId,conclusion,status,headSha,jobs` and
  `gh pr checks 75`; the committed `docs/reports/omp-closeout/evidence/hosted-ci-final-run.json`
  is a hash-pinned fallback capture.

Use `git diff 827e487..e3a729d` and inspect the files at that commit.

## What changed since submission 3

* `previous_pointer = pointer.read_bytes()` now runs inside typed storage-error handling **before**
  staging. A `PermissionError`/`OSError` there returns `503 retrieval-unavailable`, leaves the
  previous publication intact, and leaves no staging file.
* A regression test (`test_pointer_read_failure_is_typed_and_leaves_previous_publication`) injects
  the read failure, checks the typed result, the original baseline-a binding, and empty staging.
* The final backend suite is **552 passed, 4 skipped**; the targeted AI-03 feature is 6 scenarios /
  67 steps passed. The final hosted run covers the same head.
* The AI-02 minor documentation finding (count/timing scope) is repaired in the same head.

## Evidence to inspect

* `docs/reports/omp-closeout/evidence/final-cucumber.ndjson` — AI-03 cases and full local run.
* `docs/reports/omp-closeout/evidence/final-backend.log` — final backend count.
* `backend/tests/test_retrieval_lifecycle.py` — change planning, cache keys, publication, rollback,
  compatibility, mixed-context rejection, evidence-only reuse, model changes, corrupt reads, timing,
  and the read/publication probes.
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
6. Every prior finding **R1–R4** is repaired: repository/commit/canonical-filename validation and
   exact-binding context; staged, reader-isolated publication with typed snapshot and pointer
   storage failures; elapsed time including key construction; and the hosted conclusions observed
   on this exact head.

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
