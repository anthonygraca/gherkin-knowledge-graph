# AS-07 acceptance review 1 — repair record

**Snapshot:** cumulative close-out working tree based on `827e487`; final local suite and report
paths are recorded in `docs/reports/omp-closeout/evidence/`. Hosted CI is recorded on the close-out
PR when it exists.

| Finding | Disposition | Evidence |
|---|---|---|
| **AS07-ACC-R1** — provider construction escaped the availability boundary | Repaired. `_registered_discovery` resolves the registered provider and enters `try`; `DomainError` availability and any provider exception map to `503 provider-unavailable` with `failed_provider`. Unknown providers stay `400 discovery-provider-unknown`; request validation stays `422`. | `backend/app/api/routes.py`; `test_registered_provider_failure_is_a_provider_problem`, `test_missing_executable_is_provider_unavailable`, `test_timeout_is_provider_unavailable`, `test_empty_valid_run_is_success`; SCN-3101/3102/3103. |
| **AS07-ACC-R2** — thread proposal presentation dropped provenance | Repaired. `LinksTable` uses the same `proposalProvenance` presentation as the proposal cards, including provider kind, model/index, fixture classification, and explicit missing-value labels. | `frontend/src/App.tsx`; `frontend/src/App.test.tsx`; SCN-3107/3108/3113. |
| **AS07-ACC-R3** — timeout replaced the CocoIndex adapter | Repaired. The provider fixture injects a failing transport beneath the real `CocoIndexCandidateDiscovery`; the timeout case executes the adapter and its contract before the transport raises. The recorded transport is documented as a deterministic test substitute, not a live bridge. | `bdd/support/provider_ui_app.py`; `bdd/step_definitions/providers.steps.js`; SCN-3102. |
| **AS07-ACC-R4** — catalogue kind metadata was not consumed | Repaired. The catalogue exposes provider kinds; `PROVIDER_KIND_LABELS` consumes them, with a separate historical fallback for disabled or absent providers. The registered local provider renders as `model`. | `backend/app/discovery/registry.py`; `frontend/src/App.tsx`; `frontend/src/App.test.tsx`; SCN-3113. |
| **AS07-ACC-R5** — fake-default lifecycle documentation missing | Repaired. `docs/development-lifecycle.md` identifies fake discovery as the default offline path and links the invocation; README remains consistent. | `docs/development-lifecycle.md`; SCN-3113. |

**Residual risk:** the CocoIndex smoke remains deterministic and optional; it is not live evidence
for the local provider. The fake provider remains the default and no fallback is hidden.
