# AI-06 implementation review — submission 4 of 7 (repairs after review 3)

## 1. Snapshot and prior verdict

**Slice:** RAG mission PR 1 (CocoIndex variant). **Story:** AI-06
([#56](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/56)); parent F-08 #14.
**Base:** `a674fb910bb31b866dd7417e45842cfa26a0b265`. **Branch:** `feat/56-cocoindex-code`.
**Submission:** 4 of 7. **Reviewer:** `gpt-6.1-sol`, reasoning effort `high`, read-only.

**Prior verdict:** submission 3 — **REQUEST_CHANGES**: R1 closed; R2/R5 remained open. Verdict
`docs/reviews/AI-06-cocoindex-review-3.md`, sha256
`0e49c9b87b9577ec171be1b2e6c804e03dd07bc200f4d87390bd60ea85877aed`; packet 3 sha256
`86fb2d514699777b884e2804f2c9d7adb8a20e29edae925a416c53d672b0e05f`. Round 4 repairs are below.

**Criteria:** `docs/stories/AI-06.feature`, sha256
`02e256a655ef410e5c5086c9a9c2742ec5710e925ebcff932d7a4ca2380d02c3` (unchanged). M1 remains
satisfied; M2 not implemented; the M3 ordering conflict is recorded. No provider registration,
API/schema/fixture change, or AI-02/AI-03/AI-05/M3 closure.

**Proposed commit:** `feat(discovery): [issue #56] add optional CocoIndex Code search contract`,
body `Refs #56`; `commitlint --message-file` exits 0.

## 2. Finding dispositions

### AI06-R2 — unhandled schema assertions (major) — repaired

The reviewer reproduced acceptance of `offset.exclusiveMaximum=1`, `query.enum=["x"]`, and an outer
`paths.maxItems=0` that the adapter ignored.

Repairs in `cocoindex_mcp.py`:

* Added conservative keyword allowlists. Unknown assertion keywords are rejected with
  `cocoindex-capability-error` rather than ignored. Supported annotations are allowed; unlisted
  assertion keywords (`exclusiveMaximum`, `exclusiveMinimum`, `enum`, `const`, `pattern`, `format`,
  `multipleOf`, `uniqueItems`, `minItems`, `not`, `allOf`, `oneOf`, `$ref`, `if/then/else`, …) are
  not.
* `offset` rejects any `maximum` or `exclusiveMaximum` cap; it must accept a non-negative offset.
* Filter schemas are validated as a whole: the outer nullable schema, the array alternative, the
  null alternative, the string `items`, and `maxItems` on both the outer and array schemas. A
  non-nullable array is rejected because search sends `null` for omitted filters.
* `query.maxLength` must allow 2,000 characters and `minLength` must allow one; `limit` must allow
  1..100; `required` is exactly `["query"]`.
* A `type: ["array","null"]` JSON Schema form remains accepted; the reviewed 0.2.43 schema passes.

New regression rows in `test_stdio_transport_rejects_incompatible_search_schema_shapes`:
`offset.exclusiveMaximum=1`, `limit.exclusiveMaximum=100`, `query.enum`, `query.const`,
`query.pattern`, outer `paths.maxItems=0`, plus the earlier direct-array/nullability/maxItems cases.
`test_stdio_transport_accepts_the_reviewed_schema_shape` still passes.

### AI06-R5 — Python equality masks invalid text (major) — repaired

The reviewer showed `True == 1` let valid structured content hide text containing `success: 1` or
`start_line: true`; each text payload alone was rejected.

Repairs in `cocoindex_mcp.py`:

* Added `_same_json`, a strict JSON comparison: booleans only equal booleans (`True != 1`,
  `False != 0`); numbers compare numerically; dict/list/primitive types must match and recurse.
* Both supplied representations must be valid and strictly agree; otherwise
  `cocoindex-protocol-error` before selecting one.
* If both are strictly equal and invalid, normalization of the selected payload rejects them.
* Structured-only results and matching text+structured results remain accepted.

New regressions: `test_stdio_transport_rejects_differing_text_and_structured_payloads`
(`conflicting-structured`, `text-bool-success`, `text-bool-line`),
`test_client_rejects_matching_invalid_text_and_structured_payloads` (both equal with
`start_line: true`), and `test_stdio_transport_accepts_matching_text_and_structured_content`.

## 3. Changed-file manifest (since submission 3)

Unchanged since submission 3 (hash-pinned):
`backend/app/discovery/cocoindex.py` `7de622c6…`; `cocoindex_mcp.py` was changed (below);
`tools/probe_cocoindex.py` `b994f7e3…`; `registry.py` `d045edcc…`; `settings.py` `b4b1d331…`;
`test_live_cocoindex_integration.py` `61c1f47a…`; `docs/stories/AI-06.feature` `02e256a6…`;
`docs/adr/0008…` `98115f8a…`; `docs/cocoindex-integration.md` `6e257f2b…`; `docs/setup.md`
`f0567350…`; `docs/traceability-issue-map.md` `f561f5d2…`; fixture `0b627f1f…`.

Changed:

```text
91ba3d385af5df328bba68d3bf4fa7b1b5ff2518689f367b0561fb0864b13fbe   988  backend/app/discovery/cocoindex_mcp.py
a748641cb3148eba76e0625592e9b223735338c9855774fdd606e62e012f0c9c  1415  backend/tests/test_cocoindex_client.py
3fd2c6aa7ba05e195d2d1e638ec8e84b3d7a01e93b13db0074548b9d4428aeba   210  docs/stories/AI-06.md
3460fd52bab667bdf6fef9b591e78df36e63f7d95132ca711425f27908b9884e   343  docs/STATUS.md
3688884110874d700840bf2cb6c7e5b6f82e7ca20426ee20ec8435745fcf4b4c   226  docs/reports/omp-cocoindex-pr1/IMPLEMENTATION.md
c6171573d29bc47cfd136dd6f95cff5b8468c1b83216ef9bb401894ca56ed0b7    88  docs/reports/omp-cocoindex-pr1/METRICS.md
99b8563f6f9701b56dcd6b22732095d64553f13a3e26176b0c0819261b190cd2    76  docs/reports/omp-cocoindex-pr1/PROMPT_LOG.md
4fbd1e0cb5c6a3f74c691ff5265ce2eaa7a00c4c149ad94463e41c6d35526f1e   124  docs/reports/omp-cocoindex-pr1/capabilities/live-smoke.md
ca911d243c7665f989f45e48a79e76c3b572b5de84a84a9c687fd72add197f04   151  docs/reports/omp-cocoindex-pr1/capabilities/live-summary.json
4562ef4d128997781a2350b68d92bfa2dfb4b67d40d7d8bab88351b47024f419   114  docs/reports/omp-cocoindex-pr1/capabilities/live-run-manifest.json
```

New evidence copies: `evidence/round4-live-test.log`, `evidence/round4-probe-summary.txt`,
`evidence/final-round4-*`. Unrelated working-tree changes (`.gitignore`, `prompts/`, `.agents/`,
`.omp/`, `skills-lock.json`) remain excluded.

## 4. Evidence (round 4)

| Check | Result | Capture |
| --- | --- | --- |
| Backend suite | **392 passed, 3 skipped**, exit 0 | `evidence/final-round4-pytest-full.log` |
| CocoIndex contracts | **107 passed**, exit 0 | `evidence/final-round4-cocoindex-tests.log` |
| Live pytest (opt-in) | **1 passed**, exit 0 | `evidence/round4-live-test.log` |
| Fixture drift | exit 0 | `evidence/final-round4-fixturectl.log` |
| ruff / format / diff | exit 0 / 0 / 0 | `evidence/final-round4-ruff-*.log`, `evidence/final-round4-git-diff-check.log` |
| Network denial proof | probe exit 1 (`Network is unreachable`) | `evidence/final-round4-network-probe.log` |
| Network-denied suite | **392 passed, 3 skipped**, exit 0 | `evidence/final-round4-pytest-network-denied.log` |
| Live probe | all six steps ok; 3 hits; search 857.0 ms; exit 0 | `evidence/round4-probe-summary.txt`, `capabilities/live-summary.json`, `capabilities/live-run-manifest.json` |

Live configuration: isolated `fixtures/banking-demo` worktree at `baseline-a`
`0f8607b29d1ccb423062d856835f5310c9f54aa3`; CocoIndex 0.2.43; MCP `2024-11-05`;
`embeddinggemma-2:270m-q8_0-text` (768 dims); 12 files/16 chunks; hits `src/__init__.py` 1–1,
`src/transfers.py` 1–29, `src/accounts.py` 1–10, verified against the snapshot; `index_identity=null`.
Isolated daemon PID/index hash unchanged at the after-snapshot; the manifest records that the
startup background index may finish later. Raw report/capture digests are in the manifest.

**NOT RUN:** baseline-b isolation/refresh (PR 2), `.feature` semantic retrieval, retrieval-quality
metrics (AI-05), chat/GraphRAG, M2 explanations, production data handling; default-suite live test
skips.

## 5. Reviewer instructions

Decide whether this exact snapshot closes `AI06-R2` and `R5` and satisfies the AI-06 PR 1 slice,
the 11 scenarios, and repository invariants. Treat summaries/hashes/logs as claims to check.
Inspect the changed files and evidence; run read-only targeted checks if useful. Do not edit,
install, regenerate, commit, or delegate. Do not demand PR 2, API changes, `.feature` indexing,
GraphRAG, M2, or M3 closure. Check conservative schema assertions, strict envelope agreement,
offline default, proposal/accepted/evidence separation, untrusted text, and commit references.
Return **APPROVE**, **REQUEST_CHANGES**, or **NEEDS_INPUT** with stable finding IDs (`AI06-Rn`),
severity, affected criterion/invariant, and the smallest acceptable evidence/repair.
