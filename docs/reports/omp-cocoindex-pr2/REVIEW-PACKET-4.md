# AI-07 PR 2 — independent review packet (submission 4 of 7)

## Snapshot

* Base `e4bbd82c4bb70c6dc13d7d59554b5525177234c8`; working tree uncommitted.
* Feature sha256 `721c7488f91da121a9aa6c6266882379c6b20b8c9d6da116e1fae3361b493dc3`.
* Labels sha256 `694bba1aafe74d7cc9c50ec71f97a89d3b2dc27ade4d3cd0d94abf37f772a344`.
* Report sha256 `781ea2ff750d65bc3933efee22dec97065dfc346ea2b7226f5dddc4287adea54`;
  schema `0.4.0`.

## Repair since submission 3

**AI07-R1 (medium residual): line separators were normalized.** `map_hits` now splits committed
text on LF only, retains CR and U+2028 inside lines, and applies only the adapter's documented
single-trailing-LF normalization. New tests:
`test_line_separators_are_preserved` (CRLF content changed to LF → unresolved) and
`test_unicode_line_separator_is_not_normalized` (U+2028 replaced by LF with a declared range 2–3 →
unresolved). A matching CRLF chunk would compare with its bytes intact.

R2/R5/N2 remain as accepted in review 3; no implementation changes in those areas.

## Evidence

| Check | Result |
| --- | --- |
| Backend suite | 466 passed, 3 opt-in skips |
| AI-07 retrieval tests | 21 passed |
| Cucumber + gate | 101 scenarios / 834 results passed; gate ok; report `sha256:781ea2ff…` |
| Live CocoIndex | both snapshots rerun; manifest implementation/evidence hashes updated |
| Ruff/format/diff/fixture | clean |

## Reviewer mandate

You are the independent CTA implementation reviewer using GPT-6.1 Sol high. Verify the R1
separator repair and confirm R2/R5/N2 remain satisfied. Do not demand GraphRAG or M2. Do not edit,
install, regenerate, commit, or delegate. Return PASS/FAIL/NOT VERIFIED with stable IDs and
APPROVE / REQUEST_CHANGES / NEEDS_INPUT.
