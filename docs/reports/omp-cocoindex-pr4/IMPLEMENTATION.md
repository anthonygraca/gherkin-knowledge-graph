# AI-09 PR 4 — evidence-grounded retrieval benchmark

**Story:** AI-09 [#70] (parent F-09 #15). **Milestone:** M4-style evidence; does not close M4.
**Snapshot:** `3ece0f9` plus this uncommitted slice.
**Benchmark:** `evidence/rag-benchmark.json`; labels `evidence-answers.json` (hand-derived from the
M1/M2 fixture oracle), code labels `code-retrieval.json`.

## Comparison

| Arm | Method | Result |
| --- | --- | --- |
| A | lexical code retrieval | Recall@1 0.6667 (a) / 0.5000 (b), MRR 1.0, ~0.6 ms |
| B | CocoIndex code retrieval | Recall@1 same as A; lower precision, more false candidates, ~1 s/query |
| C | accepted-graph answers | status/links/evidence/findings/paths/citations/revisions all 1.0 against 4 labeled cases |
| D | hybrid graph + lexical candidates | authoritative fields identical to C; candidates separate; citation 1.0 |

A/B use the same four-file snapshots and code labels. C/D receive accepted-graph information that
A/B do not; their comparison is separate. The CocoIndex result on this corpus is negative and is
reported as such.

## Metrics

* C/D: status 1.0, accepted-link 1.0, proposed-link 1.0, evidence 1.0, findings 1.0, forbidden
  findings 1.0, path 1.0, citation 1.0, revision 1.0, unsupported assertions 0.0.
* Report records code-label, answer-label, and code-evaluation hashes; versions and limitations.
* No M3/M4 closure claim.

## Verification

`tools/evaluate_rag.py` generated `evidence/rag-benchmark.json`; Cucumber `AI-09` 4 scenarios pass;
the benchmark is reproducible from the committed labels and the AI-07 live/lexical captures.
