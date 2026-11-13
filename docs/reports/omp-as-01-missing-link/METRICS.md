# AS-01 metrics

| Measure | Value |
| --- | --- |
| Task | AS-01 (#2), M1, owner C (shared API integration) |
| Coordinator model | `vllm/deepseek-ai/DeepSeek-V4.1-Flash-1017`; thinking `max` (run input) |
| Implementation window (observed) | 2026-11-13T03:56Z → 2026-11-13T04:09Z |
| OMP delegations / advisory calls | none |
| Codex preflight | reuse of the run-level probe (no new probe) |
| Codex acceptance calls | 1 (round 1 APPROVE) |
| Codex tokens, acceptance | 106,974 (CLI-reported total) |
| Test growth | 227 → 233 passing (+6) |
| Checks | focused 7 passed; full suite 233 passed (also under OS-level network denial); `fixturectl verify` exit 0; ruff check/format exit 0; `git diff --check` exit 0; HTTP probe of evaluate (success, tag/SHA, 404, 400) |
| Rework before first review | none |
| Quota / cost | not exposed; not claimed |
