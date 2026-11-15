# AS-07 acceptance review — submission 1

## Scope

**Story:** AS-07 (#29), milestone M3 — honest provider availability and proposal provenance.
**Canonical criteria:** `docs/stories/AS-07.feature` (7 scenarios, SCN-3101…SCN-3107).
**Companion/normative contract:** `docs/stories/AS-07.md`.
**Specification approval:** `docs/reviews/AS-07-spec-review-3.md` (round 3).
**Owner dispositions:** `docs/adr/0012-closeout-scope-decisions.md`.

This is an **independent acceptance review**, not a specification review. Inspect the actual
repository; do not edit, implement, regenerate fixtures, commit, or delegate. Read-only commands are
allowed.

## Snapshot

The cumulative close-out diff is the uncommitted working tree based on `827e487`. Use
`git diff 827e487` and inspect the files directly.

## Evidence to inspect

* `docs/reports/omp-closeout/evidence/final-cucumber.log` and `final-cucumber.ndjson`.
* `backend/tests/test_provider_availability.py` — registration, registered failure, empty success,
  catalogue, problem extensions, no finding, optional provider.
* `backend/app/discovery/registry.py`, `backend/app/api/routes.py`,
  `backend/app/domain/api.py`, `backend/app/domain/errors.py` — provider outcomes and extensions.
* `bdd/support/provider_ui_app.py` — deterministic recorded CocoIndex transport; the real adapter,
  discovery route, problem mapping, and dashboard are exercised.
* `bdd/step_definitions/providers.steps.js` — UI states and provenance.
* `frontend/src/App.tsx` — candidate panel, provenance labels, historical provider kind.

Verify, at minimum:

1. Unknown provider → `400 provider-not-registered` with the failed name and effective registered
   list; `fake` remains selectable and the accepted thread/evidence stay usable.
2. Registered provider failure → typed `503 provider-unavailable` with `failed_provider`; no
   baseline-a candidates shown as baseline-b results; no empty-success state; no silent fake switch;
   accepted links/evidence/findings unchanged.
3. Empty success → `200` with `candidates: []` and retained provider/model/index.
4. Fixture proposals display provider/model/index and a fixture-generated label; CocoIndex mapped
   proposals display model identity and a CTA snapshot binding; historical providers remain labelled
   when disabled; missing provenance renders “not recorded” without substitution.
5. Every SCN-3101…SCN-3107 scenario is present and passing in the final Cucumber report.
6. Provider failure never becomes a finding, accepted link, or empty success.

## Output format

Return exactly one Markdown document:

* `## Verdict` — `APPROVE`, `REQUEST_CHANGES`, or `NEEDS_INPUT`.
* `## Criterion assessment` — one row per scenario ID: PASS / FAIL / NOT VERIFIED.
* `## Findings` — numbered `AS07-ACC-R<n>` with severity, blocking, path/line, expected/actual,
  smallest correction/recheck.
* `## Check verification` — commands/reports observed and any unobserved hosted check.

APPROVE requires every criterion satisfied at this snapshot, invariants intact, no open major
finding, and observed green required checks.
