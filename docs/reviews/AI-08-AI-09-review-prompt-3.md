# Independent acceptance review — AI-08/AI-09 (submission 3)

## Snapshot

* Base `3ece0f9`; working tree uncommitted.
* AI-08 feature sha256 `3f78b5da2eafbf9f3ee85b1084c12996659109755339b8dfd101ed711d6ceda5`.
* AI-09 feature sha256 `f97f2996333605f43c131d42300e055837178d8d6e2a703aeb0c30b6b0ac5594`.
* Answer labels sha256 `cae8be443fdd5ee594e09bd39c896261bd742933c279e53706677506a56ab522`.
* Benchmark sha256 `f773a0830e0f450c9b17d77f1a2dfdae93ae28049b4ceb3219225ae4c1ad4eb1`.
* Owner attestation + preapproval: `docs/reviews/AI-09-oracle-owner-review.md`.

## Repairs since submission 2

* **R3:** labels now carry required/forbidden answer tokens and exact finding sets; the benchmark
  checks them. A fabricated “all tests passed” claim or an extra finding fails `claims_ok`/`findings_ok`.
* **R7:** failure prose uses the `verification_failed` finding’s evidence IDs only.
* **R6:** formatting check passes.
* R1/R2/R4/R5 closed in review 2.

## Evidence

| Check | Result |
| --- | --- |
| Backend suite | 476 passed, 3 opt-in skips |
| AI-08 tests | 10 passed |
| Cucumber + gate | 112 scenarios / 933 results passed; strict gate ok; report sha256 27001df404fece892be14cf973250b8cb7d2cd17278549c71d3755008516f5e2 |
| Benchmark | C/D exact agreement 1.0; unsupported claim rate 0.0; semantic false-candidate rate 0.25 (proxy) |
| Fixture/ruff/format/diff | clean |

## Reviewer mandate

You are the independent CTA implementation reviewer using GPT-6.1 Sol high. Verify R3 and R7 and
confirm the previously closed findings. Do not demand M4 closure or new capabilities. Do not edit,
install, regenerate, commit, or delegate. Return PASS/FAIL/NOT VERIFIED with stable IDs and
APPROVE / REQUEST_CHANGES / NEEDS_INPUT.
