## Verdict

REQUEST_CHANGES

The five offline criteria pass. SCN-3205 remains unsatisfied: live discovery used baseline-b, retained isolation observations are missing, and the live checks omit required shared contract cases.

## Criterion assessment

| Scenario ID | Assessment | Basis |
|---|---|---|
| SCN-3201 | PASS | Unqualified discovery selects `fake`; independent read-only probe observed no connection attempt or ONNX import. Default construction has no model execution/download path. |
| SCN-3202 | PASS | Remote endpoint validation precedes runtime construction; recorded API result is `400 invalid-request`, without candidates or connection attempts. |
| SCN-3203 | PASS | All three outline examples pass: absent weights, digest mismatch, and missing runtime return `503 retrieval-unavailable`. Inspected paths contain no download, fallback, or domain-state writes. |
| SCN-3204 | PASS | Real adapter boundary with deterministic embeddings covers ranking, filters, top_k, contiguous ranks, provenance, empty API results, unavailable identity, and no mutation. |
| SCN-3205 | FAIL | Separate report passes, but discovery executes against baseline-b; isolation observations are not retained, and shared contract coverage is incomplete. |
| SCN-3206 | PASS | Non-finite embeddings produce typed `503 retrieval-unavailable` without partial candidates. Provider inspection and recorded checks support no writes. |

## Findings

1. **AI02-ACC-R1 — Major; blocking: yes — Live execution uses the wrong baseline.**

   **Path/line:** `bdd/support/cta_bridge.py:1775`; `backend/tests/test_local_embedding_live.py:72`; `backend/tests/test_local_embedding_live.py:126`.

   **Expected:** SCN-3205 indexes and discovers against baseline-a, with truthful revision attribution.

   **Actual:** Both live paths omit `baseline`, which resolves to baseline-b. Independent recomputation confirms the recorded binding `sha256:e341e772…` belongs to baseline-b; baseline-a produces `sha256:dc25a7ff…`. The pytest measurement nevertheless labels its `git` field with baseline-a’s commit.

   **Smallest correction/recheck:** Explicitly select baseline-a for every live discovery and binding lookup; derive the recorded commit from that selected baseline. Rerun both live checks under `unshare -rn` and replace their evidence.

2. **AI02-ACC-R2 — Major; blocking: yes — Required live observations are discarded.**

   **Path/line:** `bdd/support/world.js:21`; `bdd/step_definitions/local_embedding.steps.js:183`; `docs/reports/omp-closeout/AI-02-EVIDENCE.md:59`.

   **Expected:** Retained execution evidence identifies observed weights/runtime/formatting, egress denial, namespace, and candidate model/snapshot bindings.

   **Actual:** The bridge returns those values into transient World state, but no attachment or structured record preserves them. The live NDJSON has **zero attachments** and contains none of `external_egress`, `egress_denied_env`, or `network_namespace`. The pytest measurement records weights/runtime but lacks formatting and an observed egress result; its network field is a fixed string. The evidence document’s claim that these observations are retained is unsupported.

   **Smallest correction/recheck:** Attach the structured live bridge result to Cucumber Messages or retain a separately hashed execution record. Include namespace/interface or route observations, the probe result, exact manifest comparisons, and candidate provenance. Recapture under the documented isolation command.

3. **AI02-ACC-R3 — Major; blocking: yes — Live checks do not execute the specified shared contract cases.**

   **Path/line:** `bdd/step_definitions/local_embedding.steps.js:202`; `bdd/support/cta_bridge.py:1771`; `backend/tests/test_local_embedding_live.py:67`.

   **Expected:** The real runtime executes the shared discovery contract cases identified in `docs/stories/AI-02.md:52`.

   **Actual:** The Cucumber “shared contract” step checks only that SCN-001 has results. The bridge makes filtered requests without asserting their contract. Live pytest covers several behaviors, but omits top_k trimming/rejection, the incompatible relation filter, empty-result API provenance, and baseline binding comparison.

   **Smallest correction/recheck:** Reuse substantive contract assertions with deterministic and real runtime fixtures, keeping runtime substitution as the variable. Execute and retain the complete live case results.

4. **AI02-ACC-R4 — Minor; blocking: no — Reported model version disagrees with the manifest.**

   **Path/line:** `backend/app/discovery/local_embedding.py:190`; `docs/reports/omp-closeout/AI-02-MODEL-MANIFEST.md:35`.

   **Expected:** Reported model identity agrees with the accepted manifest.

   **Actual:** Slicing `weights_digest[:12]` includes `sha256:`, producing `…@sha256:b396b`; the manifest specifies `…@sha256:b396bde0f7a8`. The full recorded weights digest agrees.

   **Smallest correction/recheck:** Align the version construction and manifest, then regenerate affected bindings and live evidence.

## Check verification

- Inspected the working-tree diff against `827e487`, relevant implementation/tests, canonical criteria, specification approval, manifest, and evidence.
- Verified **54/54** entries in `final-manifest.sha256`; both Cucumber reports embed the current AI-02 feature text.
- Final offline report: **177 scenarios passed / 1704 step results**; all five offline AI-02 scenario IDs are present, including all three SCN-3203 examples.
- Separate live report: **1 scenario passed / 14 step results** for SCN-3205. Recorded live pytest: **1 passed**. These green results have the limitations above.
- Observed captured checks: backend **535 passed, 4 skipped**; fixture verification, Ruff, formatting, and whitespace checks green.
- Independently reran read-only Ruff, format, whitespace, and strict report-resolution checks successfully. Read-only adapter probes also passed; no live inference was run.
- Full pytest/fixture generation were not rerun because they write temporary artifacts. Hosted checks and current frontend build/component results were **not observed** for this uncommitted snapshot.