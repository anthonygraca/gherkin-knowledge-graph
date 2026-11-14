# AI-07 PR 2 — independent review packet (submission 3 of 7)

## Snapshot

* Base `e4bbd82c4bb70c6dc13d7d59554b5525177234c8`; working tree uncommitted.
* Feature `docs/stories/AI-07.feature` sha256
  `721c7488f91da121a9aa6c6266882379c6b20b8c9d6da116e1fae3361b493dc3`.
* Labels sha256 `694bba1aafe74d7cc9c50ec71f97a89d3b2dc27ade4d3cd0d94abf37f772a344`;
  owner attestation `docs/reviews/AI-07-R7-owner-review.md`.
* Report `sha256:895eba62…`; schema `0.4.0`.

## Repairs since submission 2

| Finding | Repair |
| --- | --- |
| R2 empty binding | Discovery route now calls `provider.binding_for(payload.baseline)` when no candidates; new public-endpoint test uses a stub provider and asserts `snapshot:request-baseline`. |
| R5 incomplete audits | Bridge audit now includes deterministic findings; SCN-2306 asserts `audit.findings`; SCN-2308 retains the audit and asserts all four collections; SCN-2307 uses a rejection capture that returns same-store before/after state and asserts no link/finding change. |
| R1 newline/range residual | Comparison now only strips trailing newlines (`rstrip("\n")`); fabricated leading newlines and a wrong declared range are unresolved. New test covers both. |
| N2 lexical + malformed config | Explicit lexical skips CocoIndex model reads; malformed embedding shapes are ignored and report `embedding=unavailable`; test covers `embedding: []`. |

## Evidence

| Check | Result |
| --- | --- |
| Backend suite | 462 passed, 3 opt-in skips |
| AI-07 tests | 19 passed |
| Cucumber + gate | 101 scenarios / 834 results passed; gate ok; report `sha256:895eba62…` |
| Live CocoIndex | both snapshots rerun after strict byte comparison; manifest updated |
| Fixture/ruff/format/diff | clean |

## Reviewer mandate

You are the independent CTA implementation reviewer using GPT-6.1 Sol high. Verify R2, R5, the R1
newline/range residual, and N2; confirm the public endpoint binding, same-store audits for normal,
injection, and rejection paths, strict committed-line comparison, and lexical independence from
CocoIndex settings. Do not demand GraphRAG or M2. Do not edit, install, regenerate, commit, or
delegate. Return PASS/FAIL/NOT VERIFIED with stable IDs and APPROVE / REQUEST_CHANGES / NEEDS_INPUT.
