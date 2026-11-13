# DT-04 metrics

| Measure | Value |
| --- | --- |
| Task | DT-04 (#23), M1, owner B (shared API integration) |
| Coordinator model | `vllm/deepseek-ai/DeepSeek-V4.1-Flash-1017`; thinking `max` (run input) |
| Implementation window (observed) | 2026-11-13T03:12Z → 2026-11-13T03:43Z |
| OMP delegations / advisory calls | none |
| Codex preflight | reuse of the run-level probe (no new probe) |
| Codex acceptance calls | 2 (round 1 REQUEST_CHANGES, round 2 APPROVE) |
| Codex tokens, acceptance | 132,667 + 136,441 (CLI-reported totals) |
| Test growth | 219 → 227 passing (+8) |
| Fixture regeneration | 8 input files (schema_version only) + 13 generated files; baseline SHAs changed |
| Checks | full suite 227 passed (also under OS-level network denial); `fixturectl verify` exit 0; ruff check/format exit 0; `git diff --check` exit 0; HTTP probes for health/inventory/thread/ingestion/404/501 |
| Rework before first review | focused-test corrections during the cutover (superseded selectors, snapshot loader check) |
| Quota / cost | not exposed; not claimed |
