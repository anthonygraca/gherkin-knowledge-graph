# AI-07 PR 2 — independent review packet (submission 1)

## Story and traceability

* **Story:** AI-07 [#66](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/66), parent
  F-08 [#14]. Milestone M3; PR 2 of the owner's RAG/CocoIndex mission.
* **Base:** `e4bbd82c4bb70c6dc13d7d59554b5525177234c8`; working tree uncommitted at review time.
* **Canonical criteria:** `docs/stories/AI-07.feature`,
  sha256 `73d62ed9a23125bb1c1b9820aad10e4a92219701eb2aa9b5cff70b032bb0d457`.
* **Refinement disposition:** owner supplied PR 2 scope/proof requirements in the mission prompt;
  OMP drafted the Gherkin. Exact-scenario owner review is not separately recorded; this independent
  review is mandatory. Issue creation is not scenario approval.
* **Non-goals:** GraphRAG, chat answers, M2 policy changes, closing AI-02/03/05/06, second framework.
* **Schema:** `0.4.0` (additive retrieval contracts); fixtures regenerated.

## Implementation

* `app/domain/retrieval.py` — `CodeRetrievalRequest/Response`, `RetrievalHit`, `UnresolvedHit`.
* `app/discovery/code_index.py` — `CodeSnapshot` (authoritative artifacts + committed blobs),
  lexical comparator, CocoIndex mapping, unresolved hits, `CodeDiscovery`, provider adapter.
* `app/api/retrieval_routes.py` — additive `POST /api/retrieval/code`; typed 503 on provider failure.
* `app/discovery/registry.py` — `cocoindex` provider listed only when configured/opted in; optional
  `baseline` on `CandidateDiscovery`.
* `tools/evaluate_code_retrieval.py` + hand-labeled
  `fixtures/banking-demo/expected/code-retrieval.json`
  (`sha256:694bba1aafe74d7cc9c50ec71f97a89d3b2dc27ade4d3cd0d94abf37f772a344`).
* ADR 0010; AI-07 feature and Cucumber bindings.

Key invariants: no accepted link/evidence/finding writes; hit→artifact mapping requires the
authoritative path and content hash; `index_binding` is a CTA snapshot digest, not a CocoIndex index
ID; a live project at a different commit is rejected; unconfigured CocoIndex is `not_available`.

## Evidence

| Check | Result |
| --- | --- |
| Backend suite | 466 passed, 3 opt-in skips |
| AI-07 retrieval tests | 12 passed |
| Cucumber + strict gate | 101 scenarios / 834 results (430 Gherkin + 404 hooks) passed; strict gate ok (101 cases); report `sha256:781ea2ff…` |
| Fixture verify / ruff / format / git diff --check | clean |
| Live CocoIndex | baseline-a and baseline-b synthetic snapshots; metrics in `capabilities/live-smoke.md` |
| Live manifest | `capabilities/live-run-manifest.json` |

Live evaluation is a negative result on this corpus: Recall@1 equal to lexical (0.6667 / 0.5000),
lower precision and more false candidates, ~1 s/query vs sub-millisecond lexical. The harness is
the deliverable; no general claim is made.

AC mapping: SCN-2301..2308 → `backend/tests/test_code_retrieval.py` and Cucumber `AI-07.feature`;
live evidence → `evidence/live-eval-baseline-{a,b}.json`.

## Reviewer mandate

You are the independent CTA implementation reviewer using GPT-6.1 Sol high. Decide whether this
snapshot satisfies AI-07's canonical criteria and repository invariants. Verify the actual CocoIndex
0.2.43 contract was reused (not cloned/loosened); that hits map only through authoritative paths and
hashes; baseline/snapshot isolation; unresolved and not-available behavior; that no accepted link,
review state, evidence, or finding can be written; raw-score semantics; offline independence;
untrusted retrieved text; and that the live evidence is attributable and correctly reported,
including the negative result. Do not demand GraphRAG or M2 changes. Do not edit, install,
regenerate, commit, or delegate. Return criterion-by-criterion PASS/FAIL/NOT VERIFIED with stable
finding IDs and APPROVE / REQUEST_CHANGES / NEEDS_INPUT.
