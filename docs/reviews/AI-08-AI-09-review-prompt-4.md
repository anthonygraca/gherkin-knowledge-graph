# Independent acceptance review — AI-08/AI-09 (submission 4)

## Snapshot

* Base `3ece0f9`; working tree uncommitted.
* AI-08 feature sha256 `3f78b5da2eafbf9f3ee85b1084c12996659109755339b8dfd101ed711d6ceda5`.
* AI-09 feature sha256 `f97f2996333605f43c131d42300e055837178d8d6e2a703aeb0c30b6b0ac5594`.
* Labels sha256 `cae8be443fdd5ee594e09bd39c896261bd742933c279e53706677506a56ab522`.
* Benchmark sha256 `f773a0830e0f450c9b17d77f1a2dfdae93ae28049b4ceb3219225ae4c1ad4eb1`.
* Owner attestation/preapproval: `docs/reviews/AI-09-oracle-owner-review.md`.

## Repair since submission 3

**R3:** labeled `required_answer_tokens`/`forbidden_answer_tokens` are now enforced per case through
`answer_claims_match`; tests mutate a passing claim and assert the score drops. Exact finding-set
equality remains. No other behavior changed.

## Evidence

| Check | Result |
| --- | --- |
| Backend suite | 478 passed, 3 opt-in skips |
| Benchmark tests | 2 passed |
| Cucumber + gate | 112 scenarios / 933 results passed; strict gate ok; report sha256 0e266578… |
| C/D unsupported claim rate | 0.0 |
| Fixture/ruff/format/diff | clean |

## Reviewer mandate

You are the independent CTA implementation reviewer using GPT-6.1 Sol high. Verify R3 by mutating
an answer and confirming the labeled token checks lower the score; confirm the prior closed findings
remain. Do not demand M3/M4 closure. Do not edit, install, regenerate, commit, or delegate. Return
PASS/FAIL/NOT VERIFIED with stable IDs and APPROVE / REQUEST_CHANGES / NEEDS_INPUT.
