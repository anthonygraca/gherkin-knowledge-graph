# PG-01 metrics

| Measure | Value | Source |
| --- | --- | --- |
| Independently constructed repositories indexed | 2 (external-recipes, external-twin) | `benchmark.json` |
| Frameworks represented with authoritative matching metadata | 1 (Cucumber-JS 13.3.0) | report manifest |
| Feature/scenario/step discovery vs hand labels | exact at v1, v2, twin v1 | `benchmark.json` |
| Untagged scenario ratio (recipes v1) | 3 / 4 | `benchmark.json` |
| Step-definition resolution correctness | 23/23 matched, 0 fabricated | report import |
| Cross-repository identity collisions | 0 | `benchmark.json` |
| Revision-isolation failures | 0 | tests |
| Required changes to indexed repositories | 0 | hash/status audit |
| Setup effort | one-time `npm ci`/`uv sync`; no project config | `docs/setup.md` |
| Query correctness probes | 41 portable tests + 6 Cucumber scenarios | pytest/BDD |
| Unknown/abstention accuracy | no report -> `not_available`, 0 findings | tests/benchmark |
| Unintended test executions during indexing | 0 (sentinel absent) | SCN-1206 |
| Benchmark wall time | ~2 s (two builds + 8 indexes + report import) | local run |
