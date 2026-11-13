# AS-04 metrics

| Measure | Value |
| --- | --- |
| Task | AS-04 (#26), M1, owner C |
| Coordinator model | `vllm/deepseek-ai/DeepSeek-V4.1-Flash-1017`; thinking `max` (run input) |
| Implementation window (observed) | 2026-11-13T04:13Z → 2026-11-13T04:22Z |
| OMP delegations / advisory calls | none |
| Codex preflight | reuse of the run-level probe (no new probe) |
| Codex acceptance calls | 3 (round 1 REQUEST_CHANGES, round 2 NEEDS_INPUT, round 3 APPROVE) |
| Codex tokens, acceptance | 109,521 + 295,809 + 108,468 (CLI-reported totals) |
| Backend tests | 233 passed (also under OS-level network denial) |
| Frontend tests | 10 passed; build succeeded (dist ~231 kB JS, ~2 kB CSS) |
| Browser demonstration | 4 screenshots, 2 baselines, proposal thread, 390×844 viewport, 0 console errors |
| Checks | `fixturectl verify` exit 0; ruff check/format exit 0; `git diff --check` exit 0; `npm run build`/`npm test` exit 0 |
| Rework before first review | AS01-R1 test-strength repair applied on this branch (test-only) |
| Quota / cost | not exposed; not claimed |
