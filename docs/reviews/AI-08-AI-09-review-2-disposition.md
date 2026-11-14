# Disposition of AI-08/AI-09 review 2

Verdict: **REQUEST_CHANGES** (`docs/reviews/AI-08-AI-09-review-2.md`). Submission 3 addresses:

| Finding | Repair |
| --- | --- |
| R3 benchmark overstates metrics | `claims_ok` now checks required and forbidden answer tokens per labeled case; `findings_ok` requires exact finding-type equality; labels include required/forbidden answer tokens. Fabricated “all tests passed” or an extra finding now lowers the score. |
| R7 failure explanation misattributes evidence | `verification_failed` prose uses the finding’s `evidence_ids`, not every historical failed row. |
| R6 formatting | `cta_bridge.py` formatted; `ruff format --check .` clean. |
| R1/R2/R4/R5 | closed by review 2; unchanged. |

The answer-label file changed for exact findings/tokens; the owner preapproval recorded in
`AI-09-oracle-owner-review.md` covers this session’s refinements, with the new hash recorded.
