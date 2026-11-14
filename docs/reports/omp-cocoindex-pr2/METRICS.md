# AI-07 PR 2 metrics

| Measure | Value |
| --- | --- |
| Backend tests | 466 passed, 3 opt-in skips |
| AI-07 retrieval tests | 12 passed |
| Cucumber acceptance (all slices) | 101 scenarios / 834 results (430 Gherkin steps + 404 hook steps), all passed |
| AI-07 Cucumber scenarios | 8 passed |
| Lexical mean latency (baseline-a) | 0.638 ms |
| CocoIndex mean latency (baseline-a) | 950.9 ms |
| Lexical mean latency (baseline-b) | 0.805 ms |
| CocoIndex mean latency (baseline-b) | 1006.9 ms |
| Recall@1, lexical vs CocoIndex (a) | 0.6667 vs 0.6667 |
| Precision@5, lexical vs CocoIndex (a) | 0.5556 vs 0.4167 |
| False candidate rate, lexical vs CocoIndex (a) | 0.4444 vs 0.5833 |
| Recall@1, lexical vs CocoIndex (b) | 0.5000 vs 0.5000 |
| Precision@5, lexical vs CocoIndex (b) | 0.6667 vs 0.5000 |
| Index build A / B | 12.6 s / 8.1 s; 16 / 17 chunks |
| External index identity | unavailable by MCP contract; CTA snapshot bindings recorded |
| Live endpoint | local Ollama `embeddinggemma-2:270m-q8_0-text`; synthetic content only |
| Unresolved hits | `src/__init__.py`, `conftest.py` (not annotated artifacts) |
| Mutation attempts | 0 accepted links, 0 evidence, 0 findings written |
| Cucumber report | `sha256:781ea2ff750d65bc3933efee22dec97065dfc346ea2b7226f5dddc4287adea54` |
