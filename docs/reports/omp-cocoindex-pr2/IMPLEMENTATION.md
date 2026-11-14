# AI-07 PR 2 — artifact-aware discovery using CocoIndex Code

**Story:** AI-07 [#66](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/66) (parent
F-08 [#14](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/14)). **Milestone:** M3.
**Workstream:** A, with shared integration for domain/API/docs.
**Snapshot:** `e4bbd82` plus this uncommitted slice; schema `0.4.0`.
**Independent review:** APPROVE at submission 5 of 7 (`docs/reviews/AI-07-review-5.md`).

## Delivered

* `app/domain/retrieval.py` — additive typed request/response/hit contracts with no link, review,
  evidence, or finding field.
* `app/discovery/code_index.py` — immutable `CodeSnapshot` built from authoritative artifacts and
  committed blobs; deterministic `LexicalCodeIndex`; CocoIndex hit→artifact mapping; unresolved
  hits; `CodeDiscovery` service; `CocoIndexCandidateDiscovery` provider.
* `POST /api/retrieval/code` — provenance-rich lexical/CocoIndex proposals, explicit
  `not_available`, typed 503 on configured-provider failure.
* `CandidateDiscovery` gains an optional `baseline`; `POST /api/discovery` passes it; the
  `cocoindex` provider appears only when live CocoIndex is configured and opted in.
* `tools/evaluate_code_retrieval.py`, `fixtures/banking-demo/expected/code-retrieval.json` — labeled
  evaluation with lexical vs CocoIndex metrics.
* ADR 0010, canonical `docs/stories/AI-07.feature`, Cucumber bindings, and live synthetic evidence.

## Key invariants

* **No mutation.** Discovery only reads; accepted/proposed links, artifacts, evidence, and findings
  are unchanged (SCN-2306, injection scenario).
* **Baseline-bound.** `revision`/`content_hash` come from the authoritative artifact record;
  `index_binding` is a CTA-computed snapshot digest, not a CocoIndex index identity. A live project
  checked out at another commit is rejected (`CrossBaselineError`).
* **No invented artifacts.** Unknown paths, hash mismatches, and out-of-range lines are explicit
  unresolved hits.
* **Offline default.** `FakeCandidateDiscovery` remains the default; CocoIndex requires explicit
  project root + live opt-in + isolated state.
* **Score semantics.** `raw_score` is the method's value; `score` is clamped to the existing 0..1
  candidate contract and is not a probability.

## Verification (actual commands; suite counts recorded in METRICS)

| Check | Result |
| --- | --- |
| `uv run --project backend pytest backend/tests -q` | 466 passed, 3 opt-in skips |
| `uv run --project backend pytest backend/tests/test_code_retrieval.py -q` | 12 passed |
| `uv run --project backend python tools/fixturectl.py verify` | exit 0 |
| `uv run --project backend ruff check .` / `ruff format --check .` | clean / 83 files formatted |
| `git diff --check` | exit 0 |
| Cucumber suite + strict gate | 101 scenarios / 834 results passed; gate ok (101 cases) |
| Live CocoIndex evaluation | baseline-a and baseline-b on the synthetic fixture; see `capabilities/live-smoke.md` |

## Evaluation summary

| Baseline | Method | Recall@1 | Precision@5 | MRR | False rate | Mean latency |
| --- | --- | --- | --- | --- | --- | --- |
| a | lexical | 0.6667 | 0.5556 | 1.0 | 0.4444 | 0.638 ms |
| a | CocoIndex | 0.6667 | 0.4167 | 1.0 | 0.5833 | 950.9 ms |
| b | lexical | 0.5000 | 0.6667 | 1.0 | 0.3333 | 0.805 ms |
| b | CocoIndex | 0.5000 | 0.5000 | 1.0 | 0.5000 | 1006.9 ms |

Negative result on this six-file corpus: no Recall@1 gain and more false candidates at ~1 s/query.
The harness supports a larger PR 4 benchmark; no general claim is made.

## Limitations

* `.feature`/requirement semantic indexing is out of scope; CocoIndex Code is a code corpus.
* Queries use scenario title + stable template, not full step text.
* The lexical comparator is token overlap, not BM25; both are baselines, not research claims.
* Live evidence is one synthetic repository, one embedding model, two commits.
* AI-02/AI-03/AI-05/AI-06 remain open; this slice does not close them.
