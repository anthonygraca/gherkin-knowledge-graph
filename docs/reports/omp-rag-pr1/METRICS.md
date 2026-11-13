# PR 1 resource and outcome metrics

## Task and quality

| Field | Value |
| --- | --- |
| Slice | PR 1 — hosted LLM capability and provider integration |
| Served issue | AI-01 #30 (closed; follow-up provider boundary) |
| Milestone ceiling | M3; no M2 implementation |
| Acceptance slice | `PR1-AC-1` … `PR1-AC-8` in `IMPLEMENTATION.md` |
| Final snapshot | base `60dcc1f`; branch `feat/30-hosted-ai-provider`; code/docs/tests/story files; report/evidence |
| Review submissions | **4 of 7 — APPROVE** (no open finding) |
| Confirmed defects found before review | 5 local corrections: missing JSON-schema `supported=false` on error; configured model could masquerade as observed; mixed embedding index shapes accepted; fake embeddings failed above 32 dimensions; in-repository report refusal returned exit 1 instead of the documented usage error |
| Confirmed review findings | PR1-R1 (credential redaction; three rounds to close), PR1-R2 (invalid embedding indices), PR1-R3 (unobserved model identity), PR1-R4 (numeric overflow), PR1-R5 (logging URL credentials) |
| Unresolved items | live compatibility, schema support, embedding endpoint, context window, and concurrency limit are `NOT RUN`/`unknown`; no vector index, retrieval pipeline, or GraphRAG |

## Checks at the approved snapshot

| Check | Result |
| --- | --- |
| `uv sync --project backend --frozen` | exit 0; 25 packages checked |
| `pytest backend/tests -q` | exit 0; 285 passed, 2 skipped |
| network-denied `pytest backend/tests -q` | exit 0; 285 passed, 2 skipped; socket probe denied |
| `fixturectl.py verify` | exit 0; reproducible/current |
| `ruff check .` | exit 0 |
| `ruff format --check .` | exit 0; 57 files |
| `git diff --check` | exit 0 |
| offline capability probe | exit 0; `probed=false`, sanitized |
| live capability probe | **NOT RUN**; configuration absent |

## Resources

| Measure | Value |
| --- | --- |
| Run start | 2026-11-13T06:57:34Z (baseline inspection) |
| Preflight | 2026-11-13T07:24:33Z |
| Approved-snapshot gates | 2026-11-13T08:01:16Z |
| Review 1 | 91,486 tokens; 189 s; 07:32:17 → 07:35:26Z |
| Review 2 | 92,552 tokens; 113 s; 07:45:15 → 07:47:08Z |
| Review 3 | 79,113 tokens; 169 s; 07:54:20 → 07:57:09Z |
| Review 4 | 88,098 tokens; 131 s; 08:04:05 → 08:06:16Z |
| Run end | 2026-11-13T08:10Z (records/commit) |
| OMP delegates | none |
| OMP advisory calls | none |
| OMP usage/cost | unavailable; not claimed |
| Codex review calls | 4 completed |
| Codex tokens | 351,249 CLI-reported |
| Comparator baseline | none; no quality or resource benefit is claimed |

## Interpretation limits

The mission's coordination experiment asks whether OMP-led delivery with focused Codex advice plus
mandatory acceptance review improves quality or resource use. This run has no matched Codex-led
baseline, no OMP usage/cost telemetry, and one slice. It can report outcomes and observed resources,
but it cannot establish a benefit or a saving. Independent review found real defects in each of the
first three submissions (four findings, then one remaining redaction bypass, then two report/logging
bypasses) before approving the fourth; that is a quality observation about this slice, not a
controlled comparison. The live provider is `NOT RUN`, so no hosted-inference quality or latency
claim is possible.
