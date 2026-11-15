# AI-02 acceptance review 1 — repair record

**Snapshot:** cumulative close-out working tree based on `827e487`; final local suite and report
paths are recorded in `docs/reports/omp-closeout/evidence/`. Hosted CI is recorded on the close-out
PR when it exists.

| Finding | Disposition | Evidence |
|---|---|---|
| **AI02-ACC-R1** — live checks used the wrong baseline | Repaired. Both live paths explicitly pass `baseline="baseline-a"` and derive `git` from `store.commit_of("baseline-a")`. The observed binding is `sha256:814eb991…`, matching baseline-a. | `bdd/support/cta_bridge.py`; `backend/tests/test_local_embedding_live.py`; SCN-3205; `AI-02-live-observations.json`. |
| **AI02-ACC-R2** — live observations were discarded | Repaired. The bridge writes a structured, separately hashed observation record containing weights, runtime, formatting, egress probe, network namespace, manifest/binding comparisons, candidate provenance, empty-result provenance, and shared-case results. The pytest measurement records the observed egress result. | `AI-02-live-observations.json`; `AI-02-live-measurement.jsonl`; `AI-02-EVIDENCE.md`; SCN-3205. |
| **AI02-ACC-R3** — live checks skipped shared contract cases | Repaired. Both live paths now execute `top_k=0` rejection (`ValueError` in the provider contract), assert the reviewed baseline-a fixed vector `sha256:814eb991…`, exercise the incompatible relation filter, empty-result provenance, and compare `/api/threads/REQ-001?baseline=baseline-a` before and after discovery so `accepted_links` (3) and `proposed_links` (0) remain separate and unchanged. The retained record carries `top_k_rejected`, `binding_matches_fixture`, `thread_accepted_links`, `thread_proposed_links`, and `thread_equal`. | `backend/tests/test_local_embedding_live.py` `bdd/support/cta_bridge.py` `bdd/step_definitions/local_embedding.steps.js`; `AI-02-live-measurement.jsonl`; `AI-02-live-observations.json`; SCN-3205. |
| **AI02-ACC-R4** — reported model version disagreed with the manifest | Repaired. The 12-hex digest body excludes the `sha256:` prefix; the reported version is `embeddinggemma-2-text-270m-q8_0@sha256:b396bde0f7a8`, matching the accepted manifest. | `backend/app/discovery/local_embedding.py`; `AI-02-MODEL-MANIFEST.md`; SCN-3205. |

**Acceptance-3 minor R5 repaired:** the final backend count is now 552 passed / 4 skipped, and the model manifest distinguishes the pytest and live-bridge timing ranges instead of collapsing them.

**Residual risk:** the live checks are opt-in and were executed only on this CPU host; the fake
provider remains the deterministic default. The model is not a retrieval-quality claim.
