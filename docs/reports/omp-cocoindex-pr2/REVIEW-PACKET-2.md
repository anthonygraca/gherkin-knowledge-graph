# AI-07 PR 2 — independent review packet (submission 2 of 7)

## Snapshot

* Base `e4bbd82c4bb70c6dc13d7d59554b5525177234c8`; working tree uncommitted.
* Canonical feature `docs/stories/AI-07.feature`,
  sha256 `721c7488f91da121a9aa6c6266882379c6b20b8c9d6da116e1fae3361b493dc3`.
* Labels `fixtures/banking-demo/expected/code-retrieval.json`,
  sha256 `694bba1aafe74d7cc9c50ec71f97a89d3b2dc27ade4d3cd0d94abf37f772a344`.
  Owner attestation: `docs/reviews/AI-07-R7-owner-review.md` (verbatim statement + hash).
* Schema `0.4.0`; fixtures regenerated.

## Repairs since submission 1

| Finding | Repair and evidence |
| --- | --- |
| R1 stale/fabricated chunks | `map_hits` compares `hit.content` to the committed line range; mismatch → unresolved. `validate_project_root` checks HEAD, tracked cleanliness, and every snapshot file hash. Tests: fabricated content unresolved; cross-baseline/dirty root rejected. |
| R2 empty-result binding | `CocoIndexCandidateDiscovery.binding_for(baseline)`; discovery route uses it when no candidates remain. Test asserts per-baseline bindings. |
| R3 cross-baseline API | Global handlers: `CrossBaselineError` → 409 `cross-baseline`; `SnapshotError` → 422 `snapshot-invalid`. |
| R4 unverified model identity | `configured_model_version(settings)` reads the isolated global or project CocoIndex settings; reports `embedding=unavailable` when absent. Test with a different model and missing state. |
| R5 weak Cucumber assertions | Bridge returns a same-store before/after audit for links, evidence, artifacts; steps assert `all_unchanged`. Fabricated content is unresolved. SCN-2303 uses the built repo HEAD at baseline-b as the wrong checkout. |
| R6 live attribution | `capabilities/live-run-manifest.json` binds implementation/evaluator hashes, exact invocation/env aliases, label hash, evidence hashes, and both snapshot bindings. |
| R7 human oracle review | `docs/reviews/AI-07-R7-owner-review.md` records the owner's attestation and hash. |
| R8 unequal corpus | CocoIndex requests now pass the four authoritative artifact paths as `paths`, matching lexical. Test asserts the request paths. |
| N1 filter/truncation | Lexical filters relation types before applying `top_k`; test `top_k=1`, `exercised_by` → TEST-001. |
| N2 lexical blocked by live config | The route builds the live client only when the request wants CocoIndex; explicit lexical remains available. |

## Evidence

| Check | Result |
| --- | --- |
| Backend suite | 466 passed, 3 opt-in skips |
| AI-07 retrieval tests | 16 passed |
| Cucumber suite + gate | 101 scenarios / 834 results (430 Gherkin + 404 hooks) passed; gate ok; report `sha256:781ea2ff…` |
| Fixture verify / ruff / format / git diff --check | clean |
| Live CocoIndex | baseline-a/b snapshots; manifest and metrics under `capabilities/` |
| Negative live result | Recall@1 equal to lexical; lower precision/more false candidates; ~1 s/query |

## Reviewer mandate

You are the independent CTA implementation reviewer using GPT-6.1 Sol high. Verify each repair and
the untouched invariants: authoritative hit mapping (bytes + line range + hash), per-baseline
provenance, public error contracts, configured model identity, same-store no-mutation evidence,
equal eligible corpus, offline default, and honest live attribution. Do not demand GraphRAG or M2
changes. Do not edit, install, regenerate, commit, or delegate. Return PASS/FAIL/NOT VERIFIED per
criterion with stable finding IDs and APPROVE / REQUEST_CHANGES / NEEDS_INPUT.
