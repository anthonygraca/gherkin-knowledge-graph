## Verdict

**REQUEST_CHANGES**

Reviewed merged snapshot `6b80def6a1e9de6c1583e5206563410d1b84b726`. Hosted checks are green and the story approvals are recorded, but one reproduced integration defect blocks M3: lifecycle binding rejects valid historical-baseline candidates and misattributes empty-result provenance.

## M3 exit criteria

| Criterion | Result | Evidence |
|---|---|---|
| 1. One provider contract | PASS | Fake, local, and CocoIndex adapters implement `CandidateDiscovery`. Shared read-only probes passed ranking, top-k, relation filtering, provenance, and candidate-state separation. Domain assurance requires no model. |
| 2. Offline fake mode | PASS | `fake` remains the default. Runtime imports and live tests are opt-in; CI installs no model extra. Hosted default suites pass without model services. |
| 3. Measured real retrieval | PASS | AI-07 live captures use independently labeled cases; recalculated per-case and aggregate metrics match. Reports explicitly state the negative observation: no Recall@1 improvement, lower precision, approximately one second per query on the small corpus. Limitations and methodology are documented. AI-02 smoke results remain distinct from quality benchmarking. |
| 4. M3 deliverables | FAIL | Adapters, formatting, local indexing, discovery API, review workflow, and evaluation reports are present with story approvals. Their lifecycle integration fails for both real adapters at a valid earlier baseline; see M3-R1. |
| 5. M3 story approvals | PASS | Inspected approvals covering AI-01/AI-04 through the foundation review, AI-05 submission 3, AI-06 submission 5, AI-07 submission 5, AI-08/AI-09 submission 4, and the four specified close-out acceptance records. Prior major findings are closed. M3-R1 is a new milestone integration finding. |
| 6. Invariants | FAIL | Proposal/accepted/evidence separation, explicit review decisions, deterministic assurance, and change-versus-failure behavior survived inspection and probes. However, an empty `baseline-a` batch records `baseline-b`’s provider index revision, violating revision-bound provenance; see M3-R1. |
| 7. Close-out integration | FAIL | PR #75 is merged; exact-merge hosted CI and fixture reproducibility are green. GitHub reports all children of #13/#14 closed. Retrieval parent #14 is not eligible for milestone closure while M3-R1 remains open. |

## Findings

1. **M3-R1 — major; blocking: yes — Lifecycle binding uses the default baseline’s provider identity.**

   **Location:** [lifecycle.py:324](</home/anthonygraca/CSU Fullerton Dropbox/Anthony Graca/cpsc-583-knowledge-representation/project/gherkin-knowledge-graph/backend/app/retrieval/lifecycle.py:324>), including `provider_index_revision` assignment at line 336; [local_embedding.py:198](</home/anthonygraca/CSU Fullerton Dropbox/Anthony Graca/cpsc-583-knowledge-representation/project/gherkin-knowledge-graph/backend/app/discovery/local_embedding.py:198>). Contract: `docs/stories/AI-03.md:96`.

   **Expected:** Binding candidates to a manifest uses and preserves the provider identity for that manifest’s selected baseline.

   **Actual — observed:** With default provider construction and a valid `baseline-a` manifest:

   - Local discovery returns candidates whose index revision equals `binding_for("baseline-a")`, but `bind()` raises `MixedIndexContext` because `provider.index_revision` resolves to default `baseline-b`. The `baseline-b` control succeeds.
   - CocoIndex reproduces the same false rejection using its real adapter with recorded transport.
   - Binding local `CODE-001`, which returns no eligible candidates, succeeds but records `baseline-b`’s identity in `provider_index_revision` under the `baseline-a` manifest.

   These probes denied filesystem writes and network connections. Links, evidence, and findings remained unchanged. This is a reproduced defect, not a hypothesis.

   **Smallest correction/recheck:** Resolve the provider identity for `manifest.baseline` once, validate candidate identities against it, and preserve that identity for empty batches too. Exercise both real adapters across baseline-a → baseline-b → baseline-a, retain genuine mixed-context rejection, and verify empty-result provenance. Rerun affected checks and independent integration review before closing M3.

## Check verification

- Directly observed `gh run view 43683744000 --json databaseId,conclusion,status,headSha,jobs`: **completed/success**, exact merge SHA, all four jobs successful. `gh pr checks 75` also reports four passes. [Merge CI](https://github.com/anthonygraca/gherkin-knowledge-graph/actions/runs/43683744000), [PR #75](https://github.com/anthonygraca/gherkin-knowledge-graph/pull/75).
- Fetched hosted job logs: **552 backend passed / 4 skipped**, fixture reproducibility passed, **177 Cucumber scenarios / 1,704 steps passed**, strict resolution passed, frontend build and **14 tests passed**, Ruff checks passed.
- Independently verified **93/93 evidence-manifest hashes**. Parsed retained offline and live Cucumber reports: successful completion, no retries, and matching embedded specification text.
- Independently reran Ruff lint/format, commit-reference validation (**11 commits**), and strict step-resolution: **PASS**.
- Read-only probes checked provider contracts, baseline assurance against both labeled oracles, review identity refusal, capture/accept/reject isolation, and instruction-like rationale handling. Review probes used an in-memory journal and make no durability claim.
- `git diff --check 827e487..6b80def` reports trailing whitespace in historical review Markdown; the cumulative whitespace check is therefore not clean.
- **Not freshly executed:** full local suites/browser flows, fixture regeneration or verification, live inference/CocoIndex retrieval, and persistence durability tests. Their retained evidence and hosted results were inspected.
- No files were edited, fixtures regenerated, commits created, or work delegated.
