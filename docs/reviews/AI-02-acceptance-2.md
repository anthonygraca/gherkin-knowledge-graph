## Verdict

**REQUEST_CHANGES**

At `be0c3ab760cbc7d3965d7d281f6632116bb0fe59`, R1, R2, and R4 are repaired. **R3 remains partially open:** the live paths still omit required shared contract cases.

## Criterion assessment

| Scenario ID | Assessment | Basis |
|---|---|---|
| SCN-3201 | PASS | Unqualified discovery selects `fake`; independent read-only probe observed no ONNX import or network attempt. |
| SCN-3202 | PASS | Remote endpoint rejection precedes runtime construction and returns typed `invalid-request`; retained offline execution passes. |
| SCN-3203 | PASS | All three outline cases pass in the retained report. Inspected paths reject absent weights, digest mismatch, and unavailable runtime without download or fallback. |
| SCN-3204 | PASS | Deterministic adapter checks cover ranking, filters, invalid top-k, bindings, empty-result provenance, unavailable identity, and no mutation. Independent probes corroborated these behaviors. |
| SCN-3205 | FAIL | Real baseline-a inference and retained provenance are substantiated, but the live shared-case execution remains incomplete. |
| SCN-3206 | PASS | Non-finite vectors produce typed retrieval failure without partial candidates. Independent probe confirmed unchanged links, evidence, and findings. |

## Findings

1. **AI02-ACC-R3 — Major; blocking: yes — Live shared-contract coverage remains incomplete.**

   **Path/line:** `backend/tests/test_local_embedding_live.py:98`, `bdd/support/cta_bridge.py:1795`, `bdd/step_definitions/local_embedding.steps.js:216`; normative expectations at `docs/stories/AI-02.md:62–64`. The repair claim is at `docs/reviews/AI-02-acceptance-1-repairs.md:11`.

   **Expected:** Real-runtime execution includes top-k trimming **and rejection**, baseline-binding verification, and accepted/proposed response separation.

   **Actual:** Both live paths now exercise trimming, incompatible filters, and empty-result provenance. Neither calls `discover(..., top_k=0)` or checks a thread response’s separate `accepted_links` and `proposed_links` arrays. Binding assertions compare candidates with the provider’s own binding; the companion’s binding comparison case is absent. The repair record’s claim that malformed top-k rejection executes live is unsupported.

   **Smallest correction/recheck:** Execute and retain the missing cases with the real runtime. Verify the selected baseline-a binding against independently computed fixture metadata; any contrasting baseline fingerprint can be computed without baseline-b inference. Recapture the live reports under egress denial and correct the repair disposition.

Prior-finding dispositions:

- **R1 repaired:** Every live discovery explicitly selects baseline-a. Independent recomputation matches retained binding `sha256:814eb991…` and fixture commit `28c70cb4…`; baseline-b produces a different binding.
- **R2 repaired:** The separately hashed observation record retains the probe result, namespace, weights/runtime/formatting, candidate provenance, empty-response provenance, and executed case results.
- **R4 repaired:** Candidate and response model versions now match the manifest’s `…@sha256:b396bde0f7a8`.

## Check verification

- Inspected the requested base-to-head diff, approved specification, normative companion, implementation, tests, manifest, and retained evidence. **75/75** recorded manifest hashes match files at the requested commit.
- Independently hashed installed weights, tokenizer, and configuration: all match the manifest. Provisioning metadata names distribution revision `daa72c5…`; installed runtime versions agree. The installed model card and [upstream model card](https://huggingface.co/google/embeddinggemma-2) identify Apache-2.0.
- CPU inference loads local ONNX files with `CPUExecutionProvider`; inspected execution contains no remote transport or download path. Fake remains the default, and live tests are opt-in. AI-02 records invent no `items_embedded` count.
- Retained offline evidence: **544 passed, 4 skipped**; Cucumber **177 scenarios / 1704 results passed**, including all seven offline AI-02 cases. Fixture verification, lint, formatting, frontend build, and **14 component tests** report success.
- Retained live evidence: pytest **1 passed**; SCN-3205 **1 scenario / 14 results passed**. Both reports embed the current feature text. Measurement and observation records agree; these green results retain the R3 coverage limitation.
- Independently reran read-only Ruff checks, formatting, commitlint (**2 commits**), and the full offline report-resolution gate successfully. The default gate is unsuitable for the live-only report; separate inspection confirmed its complete execution and unambiguous step bindings.
- `git diff --check 827e487..be0c3ab` exits **2** for trailing whitespace in two historical review documents.
- Available raw hosted metadata for [run 43674743478](https://github.com/anthonygraca/gherkin-knowledge-graph/actions/runs/43674743478) identifies the requested head and reports **success** for all four jobs: commit references, offline tests, Cucumber/step resolution, and frontend checks. **Fresh hosted verification was unavailable:** GitHub CLI connectivity failed and web retrieval failed.
- Full suites, fixture generation, and live inference were not rerun during this read-only review. No repository files were changed and no work was delegated.
