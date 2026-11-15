# AS-07 acceptance review — submission 3

## Scope

**Story:** AS-07 (#29), milestone M3 — honest provider availability and proposal provenance.
**Canonical criteria:** `docs/stories/AS-07.feature` (7 scenario IDs, SCN-3101…SCN-3107; 12 concrete
cases).
**Companion/normative contract:** `docs/stories/AS-07.md`.
**Specification approval:** `docs/reviews/AS-07-spec-review-3.md`.
**Owner dispositions:** `docs/adr/0012-closeout-scope-decisions.md` §1.
**Prior verdicts:** `docs/reviews/AS-07-acceptance-1.md` (R1–R5) and
`docs/reviews/AS-07-acceptance-2.md` (R1 persisted).
**Repair record:** `docs/reviews/AS-07-acceptance-1-repairs.md` (inspect, do not treat as proof).

This is an **independent acceptance review**. Inspect the actual repository; do not edit,
implement, regenerate fixtures, commit, or delegate. Read-only commands are allowed.

## Snapshot

* PR: `#75` (`feat/28-closeout-m3` → `main`)
* Head commit: `e463e9e3b496a6f60644d90c52e04da6f50f7dff`
* Base: `827e487d84be990739e588e9080637c725ecc882`
* Hosted CI: run `43679892961` on that head. Inspect the actual check conclusions.

Use `git diff 827e487..e463e9e3b496a6f60644d90c52e04da6f50f7dff` and inspect the files at that commit. Later review-artifact commits
must not be treated as implementation changes.

## What changed since submission 2

The AS-07 companion now records the **specific-over-general provider precedence** required by the
two canonical stories:

* `/api/discovery` maps registered-provider construction/execution failures to
  `503 provider-unavailable` with `failed_provider` for non-local providers (including typed
  `RetrievalUnavailable`). SCN-3102's CocoIndex timeout is this path.
* `local-embeddinggemma` is a retrieval capability governed by AI-02. Its own missing/mismatched
  weights, missing runtime, and malformed embeddings keep `503 retrieval-unavailable` per AI-02
  SCN-3203/SCN-3206. This is the documented exception, not a fallback or a finding.
* Unknown providers remain `400 provider-not-registered` with `registered_providers`; request
  validation remains `422`.
* New tests cover typed non-local construction and execution failures and the local-provider
  exception; the AS-07 and API contracts state the same distinction.

Verify that this resolution is consistent with both canonical features and does not hide a failure.
If you conclude the AS-07 contract requires the local-provider exception to map to
`provider-unavailable` instead, identify the exact AI-02 criterion it would break and the owner
decision needed; do not silently accept a contradiction.

## Evidence to inspect

* `docs/reports/omp-closeout/evidence/final-cucumber.ndjson` — AS-07 cases and full run.
* `backend/tests/test_provider_availability.py` — availability, typed mapping, local exception,
  empty success, catalogue, provenance, no-fallback, and fixture immutability.
* `backend/app/api/routes.py`, `backend/app/discovery/registry.py`,
  `backend/app/domain/errors.py`, `backend/app/domain/api.py` — provider boundary and problems.
* `frontend/src/App.tsx`, `frontend/src/App.test.tsx` — thread proposal and discovery provenance.
* `bdd/step_definitions/providers.steps.js`, `bdd/support/provider_ui_app.py` — real adapter and
  recorded transport.
* `docs/domain-contracts.md`, `docs/api-contracts.md`, `docs/stories/AI-02.md`,
  `docs/development-lifecycle.md`.

## Output format

Return exactly one Markdown document:

* `## Verdict` — `APPROVE`, `REQUEST_CHANGES`, or `NEEDS_INPUT`.
* `## Criterion assessment` — one row per canonical scenario ID: PASS / FAIL / NOT VERIFIED.
* `## Findings` — numbered `AS07-ACC-R<n>` with severity, blocking status, path/line,
  expected/actual, and the smallest correction/recheck. Re-use prior IDs where the finding persists.
* `## Check verification` — observed commands/reports and hosted checks; name anything unobserved.

APPROVE requires every canonical criterion satisfied at this snapshot, the repository invariants
intact, no open major finding, all prior findings repaired or explicitly resolved by the documented
contract precedence, and required local and hosted checks observed green.
