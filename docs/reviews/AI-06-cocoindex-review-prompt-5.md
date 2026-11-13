# AI-06 implementation review — submission 5 of 7 (repairs after review 4)

## 1. Snapshot and prior verdict

**Slice:** RAG mission PR 1 (CocoIndex variant). **Story:** AI-06
([#56](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/56)); parent F-08 #14.
**Base:** `a674fb910bb31b866dd7417e45842cfa26a0b265`. **Branch:** `feat/56-cocoindex-code`.
**Submission:** 5 of 7. **Reviewer:** `gpt-6.1-sol`, reasoning effort `high`, read-only.

**Prior verdict:** submission 4 — **REQUEST_CHANGES**: R1/R3/R4/R6/R7/R8 closed; R2/R5 remained
open with field-specific/numeric variants. Verdict `docs/reviews/AI-06-cocoindex-review-4.md`,
sha256 `b17b8b9f3e46874b917a5ab6804ecf378c63e6fe87dd36666ee33fc74cc17c12`; packet 4 sha256
`81fb74fdf6b4cd7c3e45797c5f1945c02a4bab663c1e498920f95c9d5b2f3645`.

**Criteria:** `docs/stories/AI-06.feature`, sha256
`02e256a655ef410e5c5086c9a9c2742ec5710e925ebcff932d7a4ca2380d02c3` (unchanged). M1 remains
satisfied; M2 not implemented; the M3 ordering conflict is recorded. No provider registration,
API/schema/fixture change, or AI-02/AI-03/AI-05/M3 closure.

**Proposed commit:** `feat(discovery): [issue #56] add optional CocoIndex search contract`, body
`Refs #56`; `commitlint --message-file` exits 0.

## 2. Finding dispositions

### AI06-R2 — permitted assertions still ignored (major) — repaired

The reviewer reproduced `query.anyOf=[{"const":"x"}]`, `offset.anyOf=[{"maximum":0}]`, outer
`paths.type="array"` alongside the nullable union, and outer `paths.items=false`.

Repairs:

* Replaced the shared property allowlist with field-specific sets:
  * `query`: `type`, `maxLength`, `minLength` only.
  * `limit`: `type`, `minimum`, `maximum` only.
  * `offset`: `type`, `minimum` only (no maximum/anyOf).
  * `refresh_index`: `type` only.
* Filter schemas:
  * `anyOf` form allows only `anyOf` + `maxItems` (+ annotations); an outer `type` or `items` is
    rejected because it would exclude null/every array.
  * Direct `type: ["array","null"]` form allows `type`, `items`, `maxItems`; a non-nullable array
    is not accepted because search sends `null` for omitted filters.
  * Array alternative allows `type`, `items`, `maxItems`; null alternative only `type`; items only
    `type: string`.
* Regressions added to `test_stdio_transport_rejects_incompatible_search_schema_shapes`:
  `query.anyOf`, `offset.anyOf`, `limit.anyOf`, `refresh_index.anyOf`, outer `paths.type`, outer
  `paths.items`, plus the earlier `exclusiveMaximum`/`enum`/`const`/`pattern`/`maxItems` rows.
  The reviewed 0.2.43 schema still passes
  `test_stdio_transport_accepts_the_reviewed_schema_shape`.

### AI06-R5 — numeric equality masks invalid fields (major) — repaired

The reviewer reproduced `start_line: 1.0` (and `total_returned`/`offset` floats) in text alongside
valid structured content succeeding.

Repairs:

* `_payload` now validates **every supplied representation independently** via
  `normalize_search_payload(payload, request, ...)` before selecting one. The exact integer rules
  (line numbers, counts, offset) therefore apply to both text and structured content.
* Strict JSON agreement remains for differing representations; matching text+structured and
  structured-only remain accepted.
* Regressions: `test_stdio_transport_rejects_float_fields_in_text_alongside_valid_structured`
  (`start_line`, `total_returned`, `offset`) and
  `test_client_rejects_matching_float_fields_in_both_representations`; the boolean/int and
  matching-envelope cases remain.

## 3. Changed-file manifest (since submission 4)

Unchanged (hash-pinned): `backend/app/discovery/cocoindex.py` `7de622c6…`;
`backend/app/discovery/registry.py` `d045edcc…`; `settings.py` `b4b1d331…`;
`tools/probe_cocoindex.py` `b994f7e3…`; `test_live_cocoindex_integration.py` `61c1f47a…`;
`docs/stories/AI-06.feature` `02e256a6…`; ADR/integration guide/setup/map as previously verified;
fixture `0b627f1f…`.

Changed:

```text
0913d9e02abd42287ab7c33606755c58c0320be7af274882f737ed93200aec1e  1008  backend/app/discovery/cocoindex_mcp.py
13d5c536812e2927d8b0b0563df156da41f2a615aa9a052ebde6baa0439acf9f  1484  backend/tests/test_cocoindex_client.py
e81ba640cde44c63b8ba90de1607c3831ef3c2f999dff873320878a4157d0d8b   223  docs/stories/AI-06.md
be6cc2221b1a3795a6de83c8edf7cb7199cebdda6ca4c9c46f67c17de0cf122f   349  docs/STATUS.md
30e628f02cd93ba8d0ee71d66ffea4ee4fd07632ee8327db5abcbd78ea1014ef   238  docs/reports/omp-cocoindex-pr1/IMPLEMENTATION.md
48b17841a0fd0e90440ccdd4aea9e5e9b06300db6a41140361785ebf6d30268c    89  docs/reports/omp-cocoindex-pr1/METRICS.md
9577d3df882654b0b603745e582e739065a6e4ebff0ea25349027f7ca97a94fe    79  docs/reports/omp-cocoindex-pr1/PROMPT_LOG.md
8322104b0fc41f0fa9ebf21d425fc738f61115693b1cdd81fe6438da9e583487   124  docs/reports/omp-cocoindex-pr1/capabilities/live-smoke.md
71bafbbd1e404410bf7d4bc753a8d310eb33b2a67165efdb11424d897e369add   151  docs/reports/omp-cocoindex-pr1/capabilities/live-summary.json
e95e762dae6c2795a98f77ec66c3934e6f9fa1a91ae4a11d3988a94fbe6927da   114  docs/reports/omp-cocoindex-pr1/capabilities/live-run-manifest.json
```

New evidence copies: `evidence/round5-live-test.log`, `evidence/round5-probe-summary.txt`,
`evidence/final-round5-*`. Unrelated working-tree changes remain excluded.

## 4. Evidence (round 5)

| Check | Result | Capture |
| --- | --- | --- |
| Backend suite | **402 passed, 3 skipped**, exit 0 | `evidence/final-round5-pytest-full.log` |
| CocoIndex contracts | **117 passed**, exit 0 | `evidence/final-round5-cocoindex-tests.log` |
| Live pytest (opt-in) | **1 passed**, exit 0 | `evidence/round5-live-test.log` |
| Fixture drift | exit 0 | `evidence/final-round5-fixturectl.log` |
| ruff / format / diff | exit 0 / 0 / 0 | `evidence/final-round5-ruff-*.log`, `evidence/final-round5-git-diff-check.log` |
| Network denial proof | probe exit 1 (`Network is unreachable`) | `evidence/final-round5-network-probe.log` |
| Network-denied suite | **402 passed, 3 skipped**, exit 0 | `evidence/final-round5-pytest-network-denied.log` |
| Live probe | all six steps ok; 3 hits; search 886.4 ms; exit 0 | `evidence/round5-probe-summary.txt`, `capabilities/live-summary.json`, `capabilities/live-run-manifest.json` |

Live configuration: isolated `fixtures/banking-demo` worktree at `baseline-a`
`0f8607b29d1ccb423062d856835f5310c9f54aa3`; CocoIndex 0.2.43; MCP `2024-11-05`;
`embeddinggemma-2:270m-q8_0-text` (768 dims); 12 files/16 chunks; hits `src/__init__.py` 1–1,
`src/transfers.py` 1–29, `src/accounts.py` 1–10, verified against the snapshot; `index_identity=null`.
Isolated daemon PID/index hash unchanged at the after-snapshot; the manifest records that the
startup background index may finish later.

**NOT RUN:** baseline-b isolation/refresh (PR 2), `.feature` semantic retrieval, retrieval-quality
metrics (AI-05), chat/GraphRAG, M2 explanations, production data handling; default-suite live test
skips.

## 5. Reviewer instructions

Decide whether this exact snapshot closes `AI06-R2` and `R5` and satisfies the AI-06 PR 1 slice,
the 11 scenarios, and repository invariants. Treat summaries/hashes/logs as claims to check.
Inspect the changed files and evidence; run read-only targeted checks if useful. Do not edit,
install, regenerate, commit, or delegate. Do not demand PR 2, API changes, `.feature` indexing,
GraphRAG, M2, or M3 closure. Check field-specific schema assertions, independent payload
normalization, offline default, proposal/accepted/evidence separation, untrusted text, and commit
references. Return **APPROVE**, **REQUEST_CHANGES**, or **NEEDS_INPUT** with stable finding IDs
(`AI06-Rn`), severity, affected criterion/invariant, and the smallest acceptable evidence/repair.
