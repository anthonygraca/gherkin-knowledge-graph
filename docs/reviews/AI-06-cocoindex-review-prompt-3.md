# AI-06 implementation review — submission 3 of 7 (repairs after review 2)

## 1. Snapshot and prior verdict

**Slice:** RAG mission PR 1 (CocoIndex variant). **Story:** AI-06
([#56](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/56)); parent F-08 #14.
**Base:** `a674fb910bb31b866dd7417e45842cfa26a0b265`. **Branch:** `feat/56-cocoindex-code`.
**Submission:** 3 of 7. **Reviewer:** `gpt-6.1-sol`, reasoning effort `high`, read-only.

**Prior verdict:** submission 2 — **REQUEST_CHANGES**, three open findings (`AI06-R1`, `R2`, `R5`);
R3/R4/R6/R7/R8 closed. Verdict `docs/reviews/AI-06-cocoindex-review-2.md`, sha256
`383db6a56f1fcf17d1389b9d730e111c87f086772f30e8729dc51916b3fb675d`; packet 2 sha256
`01350df6229b298c81a32af3c91e50773ddb780f55d6365c7de5724f086e0ec2`. All three open findings are
repaired below; the five closed findings remain untouched in substance.

**Criteria:** `docs/stories/AI-06.feature`, sha256
`02e256a655ef410e5c5086c9a9c2742ec5710e925ebcff932d7a4ca2380d02c3` (unchanged from submission 2).
M1 remains satisfied; M2 is not implemented; the M3 ordering conflict is recorded. PR 1 still does
not register a provider, change the API/schema/fixtures, or claim AI-02/AI-03/AI-05/M3 closure.

**Proposed commit:** `feat(discovery): [issue #56] add optional CocoIndex Code search contract`,
body `Refs #56`. `commitlint --message-file` exits 0.

## 2. Finding dispositions

### AI06-R1 — isolation validation vs subprocess path resolution (major) — repaired

The reviewer showed that validation resolved relative paths against the caller's cwd while the child
ran in the snapshot, allowing a relative runtime path to resolve to the shared default for the child.

Repairs:

* `validate_isolated_state` now rejects any non-absolute
  `COCOINDEX_CODE_DIR`/`COCOINDEX_CODE_RUNTIME_DIR` **before** resolution or process start
  (`cocoindex_mcp.py`, validation).
* `StdioMcpTransport.__init__` resolves the pair once and overwrites the child environment with the
  resolved absolute strings, so every `ccc` subprocess receives the same validated paths.
* The probe builds `isolated_environment` from the validated resolved pair and passes it to
  `ccc version/status/doctor` and `StdioMcpTransport(environment=...)`; it no longer relies on the
  raw parent strings.
* Regressions:
  * `test_stdio_transport_rejects_relative_state_paths` — caller and snapshot are different
    directories; a relative runtime path that would resolve to shared state, and a relative state
    path, are both rejected.
  * `test_stdio_transport_passes_resolved_absolute_state_paths` — the stub records the child's
    `COCOINDEX_CODE_DIR`/`RUNTIME_DIR`; both are absolute and equal the resolved paths.
  * `test_stdio_transport_requires_isolated_state` still covers missing/default/project-local state.

### AI06-R2 — incompatible schemas still pass validation (major) — repaired

The reviewer showed non-nullable string-array filters, `offset.maximum=0`, and `query.maxLength=1`
were accepted.

Repairs in `_validate_search_tool`:

* `languages`/`paths` must accept **null** as well as an array of strings:
  `anyOf: [array-of-string, null]` or `type: ["array","null"]` with string items. A direct
  non-nullable array is rejected because the adapter sends `null` for omitted filters.
* `offset` must accept non-negative integers and must **not** declare a `maximum` (the adapter's
  supported range is unbounded above; the observed 0.2.43 schema has no maximum).
* `query.maxLength` (if present) must allow at least 2,000 characters; `query.minLength` (if
  present) must allow one character.
* Filter `maxItems` (if present) must allow at least 10 filters.
* `limit` still must allow 1..100; `required` is exactly `["query"]`.

New regression rows in `test_stdio_transport_rejects_incompatible_search_schema_shapes`: direct
array filters (both fields), `offset.maximum=0`, `query.maxLength=1`, filter `maxItems=5`; the
reviewed real schema still passes `test_stdio_transport_accepts_the_reviewed_schema_shape`.

### AI06-R5 — structured content masks malformed/contradictory text (major) — repaired

The reviewer showed valid `structuredContent` alongside text containing an invalid hit or
`success=false`, and explicit `content:null`, could succeed.

Repairs in `_payload`:

* Distinguishes absent from explicit-null fields using key presence. `content: null` and
  `structuredContent: null` are rejected; an absent field is allowed only when the other
  representation is valid.
* Every supplied representation is validated: `content` must be a non-empty list with exactly one
  text block whose JSON is an object; `structuredContent` must be an object carrying `success`.
* If both are supplied, they must be **equal**; any disagreement (including `success=false` text
  vs successful structured content, or an invalid hit in one) is `cocoindex-protocol-error`.
* Structured-only results remain accepted; matching text+structured results are accepted.

Regressions: `test_stdio_transport_rejects_contradictory_or_explicit_null_envelopes`
(`content-null`, `structured-null`, `conflicting-structured`, `structured-metadata`) and
`test_stdio_transport_accepts_matching_text_and_structured_content`.

## 3. Changed-file manifest (since submission 2)

Unchanged since submission 2 (hash-pinned; review as previously verified):
`backend/app/discovery/cocoindex.py` `7de622c6…`; `registry.py` `d045edcc…`; `settings.py`
`b4b1d331…`; `docs/setup.md` `f0567350…`; `docs/traceability-issue-map.md` `f561f5d2…`;
`backend/tests/fixtures/cocoindex-search-response.json` `0b627f1f…`;
`docs/stories/AI-06.feature` `02e256a6…`;
`backend/tests/test_live_cocoindex_integration.py` `61c1f47a…`.

Changed in this submission:

```text
b340388f7f35d1110419a84d3b631a887f352d2ef4d4e65acc81cdaf1378fb2b   919  backend/app/discovery/cocoindex_mcp.py
b994f7e3fc47a145364803032fc59f019b4ac810fd3d1cc3f04eb1df3b94f0af   708  tools/probe_cocoindex.py
059d827e8890da0c1a3ac664fa763d084f904e21b96a00ff9394a135fc566c0a  1349  backend/tests/test_cocoindex_client.py
56934177befdfb856125e307eca5e168b31995836e7d7c2a574f691eeeb0daa9   197  docs/stories/AI-06.md
1e4bec52fe541bdf4d82e51ef416e3d9edf329f2cad7aa52633155a2fe9bdde4   338  docs/STATUS.md
959f50e8bef5c87453151a7204093fbabcbd67ccf53f3800bd9d5f1945869bb8   213  docs/reports/omp-cocoindex-pr1/IMPLEMENTATION.md
f6694fb85c2f1a341e2a58ea42e151828c094197c91fe2f40a2cf32ce530c029    87  docs/reports/omp-cocoindex-pr1/METRICS.md
e549e8c57d0c43a6f1eb5be47e76331f6dbf19f66c82ce7efa5b032282bd3729    73  docs/reports/omp-cocoindex-pr1/PROMPT_LOG.md
a5f42b9fcbe543e33496d8981bd4d20a5bdfd64a7d9d748633d1a61f25ad5a45   124  docs/reports/omp-cocoindex-pr1/capabilities/live-smoke.md
1d5df241ade324bca0743a2d5089fff922a6314d55c53c16e75c63b786e73aaf   151  docs/reports/omp-cocoindex-pr1/capabilities/live-summary.json
1e2386053c095d9f0aa6b169d53f7f190726f8eaf17ddfc3e1a36925b346a203   114  docs/reports/omp-cocoindex-pr1/capabilities/live-run-manifest.json
```

New evidence copies: `evidence/round3-live-test.log`, `evidence/round3-probe-summary.txt`,
`evidence/final-round3-*`. Unrelated working-tree changes (`.gitignore`, `prompts/`, `.agents/`,
`.omp/`, `skills-lock.json`) remain excluded.

## 4. Evidence (round 3)

| Check | Result | Capture |
| --- | --- | --- |
| Backend suite | **382 passed, 3 skipped**, exit 0 | `evidence/final-round3-pytest-full.log` |
| CocoIndex contracts | **97 passed**, exit 0 | `evidence/final-round3-cocoindex-tests.log` |
| Live pytest (opt-in) | **1 passed**, exit 0 | `evidence/round3-live-test.log` |
| Fixture drift | exit 0 | `evidence/final-round3-fixturectl.log` |
| ruff / format / diff | exit 0 / 0 / 0 | `evidence/final-round3-ruff-*.log`, `evidence/final-round3-git-diff-check.log` |
| Network denial proof | probe exit 1 (`Network is unreachable`) | `evidence/final-round3-network-probe.log` |
| Network-denied suite | **382 passed, 3 skipped**, exit 0 | `evidence/final-round3-pytest-network-denied.log` |
| Live probe | all six steps ok; 3 hits; search 877.7 ms; exit 0 | `evidence/round3-probe-summary.txt`, `capabilities/live-summary.json`, `capabilities/live-run-manifest.json` |

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

Decide whether this exact snapshot closes `AI06-R1`, `R2`, `R5` and satisfies the AI-06 PR 1 slice,
the 11 scenarios, and repository invariants. Treat summaries/hashes/logs as claims to check. Inspect
the changed files and evidence; run read-only targeted checks if useful. Do not edit, install,
regenerate, commit, or delegate. Do not demand PR 2, API changes, `.feature` indexing, GraphRAG, M2,
or M3 closure. Check absolute isolation paths in the child, nullable/constraint schema validation,
whole-envelope agreement, offline default, proposal/accepted/evidence separation, untrusted text,
and commit references. Return **APPROVE**, **REQUEST_CHANGES**, or **NEEDS_INPUT** with stable
finding IDs (`AI06-Rn`), severity, affected criterion/invariant, and the smallest acceptable
evidence/repair.
