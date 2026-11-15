## Verdict

**REQUEST_CHANGES**

Reviewed `be0c3ab760cbc7d3965d7d281f6632116bb0fe59` against `827e487d84be990739e588e9080637c725ecc882`. **AS07-ACC-R1 remains blocking.** R2–R5 are repaired. No files were changed or work delegated.

## Criterion assessment

The committed specification contains **seven scenario IDs and 12 concrete cases**, including SCN-3107. Its approved unknown-provider code is `provider-not-registered`, rather than the submission prompt’s `discovery-provider-unknown`.

| Scenario ID | Assessment | Basis |
|---|---|---|
| SCN-3101 | PASS | Unknown-provider response includes the effective registry and failed provider; baseline data remains accessible. |
| SCN-3102 | FAIL | Recorded CocoIndex timeout passes, but typed availability failures still escape the required provider-problem mapping; R1 persists. |
| SCN-3103 | PASS | Empty fake success returns 200 with empty candidates and retained provenance. |
| SCN-3104 | PASS | Thread proposal rows now display fixture provenance; rejection history preserves it without adding accepted coverage. |
| SCN-3105 | PASS | Recorded transport exercises the real CocoIndex adapter, discovery route, and dashboard; presentation identifies model and CTA snapshot binding. |
| SCN-3106 | PASS | All six absent/null cases pass; proposal cards and thread rows explicitly display missing provenance. |
| SCN-3107 | PASS | Historical CocoIndex classification and recorded provenance survive disabling the provider, with availability presented separately. |

## Findings

1. **AS07-ACC-R1 — Major; blocking: yes — Typed availability failures still bypass the discovery boundary.**

   **Path/line:** `backend/app/api/routes.py:182` and `:202`; originating construction failure at `backend/app/discovery/registry.py:140`.

   **Expected:** A registered provider unable to construct or execute returns `503 provider-unavailable` with `failed_provider`, while preserving unknown-provider and request-validation semantics.

   **Actual:** Construction is now inside a `try`, repairing the original CocoIndex construction example. However, both `except DomainError: raise` clauses remain. The registered `local-embeddinggemma` provider raises `RetrievalUnavailable` when its model directory is unset, producing:

   ```json
   {"status":503,"code":"retrieval-unavailable"}
   ```

   `failed_provider` is absent. A typed execution failure produces the same result. Independent calls to the production route and exception handler reproduced both paths, using the actual local-provider builder for construction and a stubbed artifact lookup.

   Published contracts also conflict: `docs/api-contracts.md:244` promises the AS-07 mapping, while `:304` specifies `retrieval-unavailable` for local-provider failures.

   **Smallest correction/recheck:** Translate typed provider-availability failures at `/api/discovery` into `ProviderUnavailable`; preserve legitimate request errors. Align the local-provider documentation with that public boundary. Recheck actual missing-model construction and typed execution failures, asserting status, code, `failed_provider`, no fallback, and unchanged accepted data/findings. The construction test at `backend/tests/test_provider_availability.py:83` currently covers a CocoIndex exception outside the `DomainError` hierarchy.

Prior finding dispositions:

| ID | Disposition | Verified repair |
|---|---|---|
| R2 | Repaired | `frontend/src/App.tsx:575` renders proposal provenance in thread rows; browser assertions cover fixture and missing-value cases. |
| R3 | Repaired | `bdd/support/provider_ui_app.py:27` injects timeout beneath the real CocoIndex adapter; SCN-3102 records success followed by timeout. |
| R4 | Repaired | `frontend/src/App.tsx:982` consumes catalogue kinds while retaining historical classifications. |
| R5 | Repaired | `docs/development-lifecycle.md:86` documents fake-default offline operation; README provides invocation instructions. |

## Check verification

- Confirmed HEAD and inspected `git diff 827e487..be0c3ab`, the approved specification, prior findings, repair claims, implementation, and contracts.
- Verified **75/75 manifest hashes**.
- Parsed committed `final-cucumber.ndjson`: **177 executed cases, 1,704 passing step results**, successful completion, no retries. All **12 AS-07 cases** pass; embedded AS-07 source matches the committed feature.
- Independently executed the strict step-resolution gate from `bdd/`: **PASS**.
- Independently executed Ruff lint without cache, format checking, and commit-reference validation: **PASS**; two commits checked.
- Direct route/handler probes confirmed fake-default empty success, unknown-provider extensions, CocoIndex exception mapping, and R1. Instrumented provider lookups showed no fake fallback on the probed failures; **127 fixture files** retained identical hashes.
- Retained local reports show **544 backend tests passed, four skipped**, fixture verification passed, frontend build passed, and **14 component tests passed**. Full suites/browser flows were not rerun because their harnesses write files. An attempted TestClient probe stalled and was interrupted.
- `git diff --check` passes for the unchanged checkout. The requested base-to-head range check reports trailing whitespace in committed historical review documents.
- Saved, **untracked** `hosted-ci-run.json` identifies the exact head and reports run **43674743478 completed successfully**, with all four jobs successful: Commit references; Offline contract, fixture, and API tests; Cucumber acceptance suite and step-resolution gate; Frontend build and component tests. The saved watch log corroborates completion.
- **Live hosted conclusions were not independently retrieved:** `gh run view` failed to connect, and the web fallback could not fetch the run. Hosted success is therefore observed through retained captures only.
