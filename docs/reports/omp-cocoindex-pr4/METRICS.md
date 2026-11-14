| Measure | Value |
| --- | --- |
| Code arms | A lexical; B CocoIndex live on synthetic snapshots |
| A/B labels | same hand-labeled `code-retrieval.json` |
| C/D answer labels | 4 cases from `evidence-answers.json` |
| C/D agreement | 1.0 for status, links, exact findings, evidence, exact paths, citations, revisions |
| Unsupported answer claims | 0.0 |
| Semantic false-candidate rate (D) | 0.25 (proxy against code labels) |
| CocoIndex result | negative on this corpus (no Recall@1 gain; more false candidates; ~1 s/query) |
| M3/M4 closure | not claimed |
