# AI-07 PR 2 — live CocoIndex code retrieval (synthetic fixture only)

**Captured:** 2026-11-14T02:18Z · **Story:** AI-07 [#66].
**Data handling:** only `fixtures/banking-demo/` synthetic content was indexed and queried. No
proprietary repository or credential was sent to the embedding endpoint.

## Environment observed

| Item | Observed |
| --- | --- |
| `ccc version` | `0.2.43` |
| MCP protocol | `2024-11-05` |
| Embedding model | `embeddinggemma-2:270m-q8_0-text` (768 dims) |
| Ollama endpoint | `localhost:11434`; the pinned model was already listed by `/api/tags`. The run did **not** start a port-forward. |
| CTA base revision | `e4bbd82` (PR 2 working tree uncommitted) |
| Isolated state | `COCOINDEX_CODE_DIR` and `COCOINDEX_CODE_RUNTIME_DIR` under `/tmp`, project-local index per snapshot |
| Snapshot A | `baseline-a` commit `316057b`; 12 files / 16 chunks; index `sha256:9a5a80d7…` (9,527,296 bytes) |
| Snapshot B | `baseline-b` commit `14d02c5`; 12 files / 17 chunks; index `sha256:245d9d5a…` |

Both indexes live in the snapshot's `.cocoindex_code/target_sqlite.db`; they are disposable and not
committed. Raw daemon logs stay outside Git.

## Retrieval results (hand-labeled cases)

Labels: `fixtures/banking-demo/expected/code-retrieval.json`
(`sha256:694bba1a…`). Lexical and CocoIndex used the same snapshot, queries, eligible files, and
labels.

| Baseline | Method | Recall@1 | Recall@5 | Precision@5 | MRR | False candidate rate | Mean latency |
| --- | --- | --- | --- | --- | --- | --- | --- |
| baseline-a | lexical | 0.6667 | 1.0 | 0.5556 | 1.0 | 0.4444 | 0.638 ms |
| baseline-a | CocoIndex live | 0.6667 | 1.0 | 0.4167 | 1.0 | 0.5833 | 950.9 ms |
| baseline-b | lexical | 0.5000 | 1.0 | 0.6667 | 1.0 | 0.3333 | 0.805 ms |
| baseline-b | CocoIndex live | 0.5000 | 1.0 | 0.5000 | 1.0 | 0.5000 | 1006.9 ms |

**Reading:** on this tiny, four-artifact corpus both methods retrieve every relevant artifact in the top
5; CocoIndex did not improve Recall@1 and returned more irrelevant code/test artifacts, at ~1 s per
query versus sub-millisecond lexical search. This is a negative result for CocoIndex on this
benchmark, not evidence of general inferiority: four authoritative files, title-only queries, and one embedding
model cannot characterize larger or differently phrased corpora. The benchmark harness is the
deliverable; a larger labeled corpus belongs to PR 4.

## Snapshot binding

CTA computes `snapshot:sha256:<digest>` over repository, commit, eligible paths, and authoritative
content hashes. CocoIndex reports no index identity over MCP; the capture does not invent one.
Baseline-a binding `3a8ea30c…`; baseline-b `2552a742…`.

Evidence: `../evidence/live-eval-baseline-a.json`, `../evidence/live-eval-baseline-b.json`,
`live-run-manifest.json`, `../evidence/index-digests.txt`.
