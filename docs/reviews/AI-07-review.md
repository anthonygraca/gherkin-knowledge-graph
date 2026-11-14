**REQUEST_CHANGES — AI-07 submission 1.**

Reviewed base `e4bbd82c4bb70c6dc13d7d59554b5525177234c8` plus the uncommitted working tree. The canonical feature and submitted evidence digests match the packet. Review was read-only; no installation, regeneration, commits, or delegation occurred.

| Canonical criterion | Assessment |
|---|---|
| SCN-2301 — canonical artifact mapping | **FAIL.** Expected IDs and unresolved paths work, but returned chunk content is never validated against the authoritative snapshot. R1. |
| SCN-2302 — baseline-b binding | **FAIL.** Baseline-b metadata is attached even when the returned chunk contains baseline-a code. R1. |
| SCN-2303 — reject another checkout commit | **PASS at service level.** An actual baseline-b checkout requesting baseline-a raises `CrossBaselineError`. Public error handling and the submitted scenario setup have defects. R3/R5. |
| SCN-2304 — unconfigured capability | **PASS.** Explicit CocoIndex requests return `not_available`, no candidates, and an honestly named CTA snapshot binding. |
| SCN-2305 — lexical determinism | **PASS.** Repeated hits, scores, and bindings match; CODE-001 ranks first. |
| SCN-2306 — no graph mutation | **PASS by inspection and independent probe.** Accepted/proposed links, review states, artifacts, evidence, and deterministic findings remained unchanged. Submitted Cucumber assertions need repair. R5. |
| SCN-2307 — reject requirements | **PASS.** Non-scenario input raises `InvalidRequest`; no relationship is created. |
| SCN-2308 — instruction-like text | **PASS for policy isolation.** Retrieved instructions have no execution or mutation path. Their content still encounters the provenance defect in R1. |

The blocking findings are:

1. **AI07-R1 — Major: stale or fabricated chunks receive authoritative provenance.**  
   [code_index.py:198](backend/app/discovery/code_index.py#L198) hashes the snapshot’s own blob; it never compares `hit.content` with the committed line range. Root validation checks only `HEAD`.

   **Observed:** I supplied the whole baseline-a `accounts.py` chunk while the configured project was actually at baseline-b. Retrieval returned `ok`, CODE-001, baseline-b’s revision and hash, and no unresolved result. Fabricated text also mapped successfully.

   Validate chunk bytes against the requested committed range, reject or report mismatches, and enforce checkout-content isolation. Recheck stale-index and dirty-checkout cases.

2. **AI07-R2 — Major: empty discovery responses carry the wrong baseline binding.**  
   [code_index.py:465](backend/app/discovery/code_index.py#L465) initializes provider provenance from the default baseline. [routes.py:193](backend/app/api/routes.py#L193) uses that value whenever no candidates remain.

   **Observed:** an empty baseline-a `/api/discovery` result carried baseline-b’s `snapshot:sha256:2552a742…`, rather than baseline-a’s `3a8ea30c…`.

   Preserve request-specific provenance independently of candidate presence. Recheck empty results and filters that remove every candidate.

3. **AI07-R3 — Major: cross-baseline errors escape the public API contract.**  
   `SnapshotError` and `CrossBaselineError` are ordinary exceptions. [retrieval_routes.py:51](backend/app/api/retrieval_routes.py#L51) catches only `CocoIndexError`; neither snapshot exception has an API handler.

   Direct route invocation reproduced the uncaught `CrossBaselineError`. Through the normal middleware this becomes a generic server error, losing the explicit cross-baseline explanation.

   Add a typed problem response identifying the requested and actual revisions, and verify both public discovery surfaces.

4. **AI07-R4 — Major: model identity is asserted without verification.**  
   [code_index.py:514](backend/app/discovery/code_index.py#L514) always reports `embeddinggemma-2:270m-q8_0-text`. It neither reads nor validates the configured CocoIndex embedding model.

   Another valid project configuration would therefore be silently mislabeled. Obtain attributable model/configuration identity, enforce the expected configuration or report identity unavailable, and test a model mismatch.

5. **AI07-R5 — Major: several Cucumber bindings do not verify their stated outcomes.**  
   [retrieval.steps.js:66](bdd/step_definitions/retrieval.steps.js#L66) checks that accepted/proposed links exist, without comparing prior state or evidence. At [line 160](bdd/step_definitions/retrieval.steps.js#L160), “equal their prior values” checks only nonempty collections; “no finding” checks only an array’s type. Separate bridge calls construct fresh stores.

   SCN-2303 also uses the nonexistent `/snapshot` root supplied at [cta_bridge.py:614](bdd/support/cta_bridge.py#L614), rather than establishing a baseline-b checkout.

   Perform before/after comparisons around retrieval on the same store, include findings and evidence, and establish the declared checkout precondition.

6. **AI07-R6 — Major, NOT VERIFIED: live execution is not attributable to the submitted implementation.**  
   [live-run-manifest.json:11](docs/reports/omp-cocoindex-pr2/capabilities/live-run-manifest.json#L11) names the base commit, which excludes the uncommitted AI-07 implementation. It lacks hashes identifying the executed implementation and evaluator, and the exact sanitized invocation/configuration.

   Report and index hashes identify those retained artifacts, but do not establish which working-tree code produced the observations. Retain execution-time input hashes and invocation/configuration alongside the results; rerun where the original identity cannot be established.

7. **AI07-R7 — Major, NOT VERIFIED: human review of the new oracle is unrecorded.**  
   [code-retrieval.json:4](fixtures/banking-demo/expected/code-retrieval.json#L4) declares `hand_labeled: true`, but supplies no identifiable human review. The existing M0 attestation covers other files.

   Record the human reviewer’s disposition against `sha256:c92515d6ae3897a0e7e850326469a23fc14e3c491735a90a5226e73553dc3f34`. Agent inspection cannot supply that attestation.

8. **AI07-R8 — Major: the comparator does not use the claimed identical eligible file set.**  
   Lexical search uses four authoritative artifact files. [code_index.py:404](backend/app/discovery/code_index.py#L404) requests all Python hits without path restrictions; CocoIndex also searches `src/__init__.py` and `conftest.py`. Those chunks consume result slots before artifact mapping.

   Restrict or otherwise equalize eligibility before truncation, then reassess the comparison and corpus description.

Two additional defects should be repaired:

- **AI07-N1 — Medium:** [code_index.py:269](backend/app/discovery/code_index.py#L269) applies lexical `top_k` before relation filtering. For SCN-001, `top_k=1` with `exercised_by` returns nothing, although TEST-001 appears with a larger limit. Filter before truncating.
- **AI07-N2 — Medium:** [retrieval_routes.py:37](backend/app/api/retrieval_routes.py#L37) constructs the live client even for explicit lexical requests. Invalid live-provider setup can therefore disable lexical retrieval. Select the method before initializing its provider.

Other mandate checks:

| Check | Assessment |
|---|---|
| Reuse of actual CocoIndex 0.2.43 contract | **PASS.** Existing client and transport are unchanged; the installed 0.2.43 server source matches the reused request/result contract. |
| Proposal/acceptance/evidence separation | **PASS.** No retrieval writer or policy execution path found. |
| Raw-score semantics | **PASS.** Rich responses preserve raw values and separately clamp candidate scores. |
| Offline defaults | **PASS.** Default retrieval needs no daemon, model, network, or vector service. |
| Negative-result arithmetic and reporting | **PASS**, subject to R6–R8. Reported metrics recompute correctly and the negative result is stated plainly. |

Independent verification passed 11 submitted non-HTTP retrieval checks using the existing fixture, additional adversarial probes, Ruff checks, formatting checks, and `git diff --check`. The retained Cucumber report contains 101 cases and 834 passed results, with the exact AI-07 feature hash. The full backend suite, fixture verification, strict gate, and live services were not rerun.