**REQUEST_CHANGES — submission 2 of 7.** AI07-R2 and AI07-R5 remain major blockers. AI07-R1 and AI07-N2 have residual defects.

| Criterion / finding | Verdict | Assessment |
|---|---|---|
| AI07-R1: authoritative bytes, range, hash | **FAIL** | Substantive fabricated content is rejected, but newline stripping permits byte/range mismatches. |
| AI07-R2: empty-result provenance | **FAIL** | The route still returns the construction-time binding. |
| AI07-R3: public error contracts | **PASS** | Both API surfaces produced 409 `cross-baseline` and 422 `snapshot-invalid`. |
| AI07-R4: configured model identity | **PASS** | Different configured model and missing configuration reported correctly. Parsing robustness remains under N2. |
| AI07-R5: substantive Cucumber assertions | **FAIL** | Same-store audits improved; findings and injection assertions remain incomplete. |
| AI07-R6: live attribution | **PASS** | Implementation, evaluator, labels, and evidence hashes match; snapshot bindings recompute correctly. |
| AI07-R7: human oracle review | **PASS** | Recorded owner disposition covers the current label hash. |
| AI07-R8: equal eligible corpus | **PASS** | Requests restrict retrieval to the four authoritative paths before server truncation. |
| AI07-N1: lexical filtering before truncation | **PASS** | `top_k=1`, `exercised_by` returns TEST-001. |
| AI07-N2: lexical independence from live configuration | **FAIL** | Malformed model settings still cause explicit lexical requests to fail. |
| Proposal/acceptance/evidence separation | **PASS** | Inspection found no retrieval writer or assurance execution path. |
| Offline default and score semantics | **PASS** | Defaults remain offline; raw scores are preserved separately from clamped scores. |
| Honest negative-result reporting | **PASS** | Retained metric arithmetic supports the stated negative outcome. |

The remaining findings are:

1. **AI07-R2 — Major: empty responses still carry the wrong baseline binding.**  
   [routes.py:193](</home/anthonygraca/CSU Fullerton Dropbox/Anthony Graca/cpsc-583-knowledge-representation/project/gherkin-knowledge-graph/backend/app/api/routes.py:193>) never calls `binding_for`. With the captured client, requesting baseline-a and `relation_types=["verified_by"]` returned no candidates but baseline-b’s binding, `2552a742…`, instead of baseline-a’s `3a8ea30c…`. Use the request-specific binding for empty responses and verify the public endpoint. The added test checks only the helper.

2. **AI07-R5 — Major: acceptance assertions still miss the stated mutations.**  
   [retrieval.steps.js:171](</home/anthonygraca/CSU Fullerton Dropbox/Anthony Graca/cpsc-583-knowledge-representation/project/gherkin-knowledge-graph/bdd/step_definitions/retrieval.steps.js:171>) still checks only that a fresh findings response contains an array. The injection step discards the bridge audit; its final assertion reads fresh links and checks one existing review state. The bridge audit also excludes findings. Complete same-store comparisons for SCN-2306/2308, retain and assert the injection audit, and capture the rejection path’s state for SCN-2307. The wrong-checkout precondition and fabricated-content rejection are repaired.

3. **AI07-R1 — Medium residual: chunk comparison erases meaningful newline differences.**  
   [code_index.py:243](</home/anthonygraca/CSU Fullerton Dropbox/Anthony Graca/cpsc-583-knowledge-representation/project/gherkin-knowledge-graph/backend/app/discovery/code_index.py:243>) applies `.strip("\n")` to both strings. Independent probes accepted CODE-001 after adding two fabricated leading newlines, and accepted content covering lines 1–10 while declaring lines 1–12. Preserve line content and permit only the adapter’s documented trailing-newline normalization.

4. **AI07-N2 — Medium residual: explicit lexical retrieval still parses live settings.**  
   [retrieval_routes.py:51](</home/anthonygraca/CSU Fullerton Dropbox/Anthony Graca/cpsc-583-knowledge-representation/project/gherkin-knowledge-graph/backend/app/api/retrieval_routes.py:51>) calls `configured_model_version` unconditionally. An isolated global settings document containing `embedding: []` caused an explicit lexical request to return 500 `internal-error`. Skip CocoIndex configuration reads for lexical requests and handle invalid configuration shapes explicitly.

Independent verification passed 14 existing non-HTTP retrieval checks against the already-built fixture, targeted API probes, model-identity checks, metric recomputation, Ruff, formatting, and `git diff --check`. The retained Cucumber report matches the canonical feature and its declared digest; the strict gate passed for 101 cases and 834 results.

API probes used inline synchronous dispatch because threaded dispatch stalled in this environment. The full backend suite, fixture verification, Cucumber execution, and live services were **not rerun**. No files were edited, installed, regenerated, or committed; no work was delegated.