# AS-06 acceptance review 1 — repair record

**Snapshot:** cumulative close-out working tree based on `827e487`; final local suite and report
paths are recorded in `docs/reports/omp-closeout/evidence/`. Hosted CI is recorded on the close-out
PR when it exists. This record is a disposition, not evidence of its own claims; the linked tests,
feature steps, and reports are the evidence.

| Finding | Disposition | Evidence |
|---|---|---|
| **AS06-ACC-R1** — decision error precedence | Repaired. The route dependency parses the raw body and evaluates identity availability/mismatch and malformed `reviewer_id` before Pydantic validation. `append_decision` resolves the proposal and baseline before reason validation. Tests assert the full precedence matrix across capture and decision routes. | `backend/app/api/review_routes.py`; `backend/app/persistence/review.py`; `test_identity_precedes_reason_validation`, `test_missing_proposal_precedes_reason_validation`, `test_baseline_validation_precedes_reason_validation`; SCN-3004/3007/3011. |
| **AS06-ACC-R2** — capture conflicts ignored the baseline | Repaired. `_proposal_for_triple` filters journal captures by canonical baseline. Distinct-baseline captures coexist; same-baseline duplicates and terminal conflicts retain their behavior. | `backend/app/persistence/review.py`; `test_same_triple_at_a_different_baseline_can_be_captured`; SCN-3021. |
| **AS06-ACC-R3** — origin allowlist and malformed origins | Repaired. Peer-loopback and socket-test exemptions are separate from the browser-origin allowlist; malformed origins are caught and refused as `403 review-origin-forbidden` with unchanged journal bytes. | `backend/app/api/review_routes.py`; `test_testclient_origin_is_refused`, `test_malformed_origin_is_refused`; SCN-3017. |
| **AS06-ACC-R4** — digest oracle used production helpers | Repaired. The acceptance test uses a reviewed fixed vector; the bridge computes the canonical digest independently from the published identity fields. The expected digest is hand-written, not derived from `compute_snapshot_digest`. | `backend/tests/test_review_workspace.py`; `bdd/support/cta_bridge.py`; SCN-3001. |
| **AS06-ACC-R5** — later decision did not compare committed bytes | Repaired. The bridge returns the journal byte length and `prefix_sha256`; SCN-3015 compares the first decision bytes with the prefix observed after the second append. | `bdd/support/cta_bridge.py`; `bdd/step_definitions/review.steps.js`; SCN-3015. |
| **AS06-ACC-R6** — capture failure guidance contradicted indeterminate recovery | Repaired. The published contract distinguishes confirmed rollback from an indeterminate append that may recover as a committed pending capture. | `docs/api-contracts.md`; `docs/stories/AS-06.md`; SCN-3029. |

**Residual risk:** the reviewer must re-observe the precedence probes and the post-decision prefix
assertion; the repair record does not substitute for execution evidence. The journal is a local
append-only file, not a replicated service; that limitation is accepted in ADR 0012.
