# PR 1 resource and outcome metrics

## Task and quality

| Field | Value |
| --- | --- |
| Slice | PR 1 — hosted LLM capability and provider integration |
| Served issue | AI-01 #30 (closed; follow-up provider boundary) |
| Milestone ceiling | M3; no M2 implementation |
| Acceptance slice | `PR1-AC-1` … `PR1-AC-8` in `IMPLEMENTATION.md` |
| Final snapshot | base `60dcc1f`; branch `feat/30-hosted-ai-provider`; code/docs/tests/story files; report/evidence |
| Review submissions | **5 of 7 — APPROVE at submission 4** (implementation) and **submission 5** (post-approval live probe/test change and evidence) |
| Confirmed defects found before review | 5 local corrections: missing JSON-schema `supported=false` on error; configured model could masquerade as observed; mixed embedding index shapes accepted; fake embeddings failed above 32 dimensions; in-repository report refusal returned exit 1 instead of the documented usage error |
| Confirmed review findings | PR1-R1 (credential redaction; three rounds to close), PR1-R2 (invalid embedding indices), PR1-R3 (unobserved model identity), PR1-R4 (numeric overflow), PR1-R5 (logging URL credentials) |
| Unresolved items | live embeddings, general endpoint/model compatibility, and concurrency limit remain `NOT RUN`/`unknown`; no vector index, retrieval pipeline, or GraphRAG |

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
| live capability probe (observed model) | exit 0; chat/schema 200; embeddings unavailable |
| live chat test (observed model) | exit 0; 1 passed (0.55 s) |
| live embeddings test | **NOT RUN**; endpoint connection refused |

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
| Review 5 | 85,412 tokens; 155 s; 16:29:16 → 16:31:51Z |
| Live probe | 11 s; chat 553.3 ms / 54 tokens; schema 92 tokens |
| Live chat test | 0.55 s; 1 passed |
| Run end | 2026-11-13T16:35Z (records/commit) |
| OMP delegates | none |
| OMP advisory calls | none |
| OMP usage/cost | unavailable; not claimed |
| Codex review calls | 5 completed |
| Codex tokens | 436,661 CLI-reported |
| Comparator baseline | none; no quality or resource benefit is claimed |

## Interpretation limits

The mission's coordination experiment asks whether OMP-led delivery with focused Codex advice plus
mandatory acceptance review improves quality or resource use. This run has no matched Codex-led
baseline, no OMP usage/cost telemetry, and one slice. It can report outcomes and observed resources,
but it cannot establish a benefit or a saving. Independent review found real defects in each of the
first three submissions (four findings, then one remaining redaction bypass, then two report/logging
bypasses) before approving the fourth; the fifth approved the post-approval live probe/test change
and evidence. That is a quality observation about this slice, not a controlled comparison. Live chat and schema-constrained JSON were observed post-approval
(553.3 ms, 54 tokens for chat; 92 tokens for schema JSON); embeddings were unavailable. That is an
observation at one configuration, not a general quality, capacity, or latency claim.
