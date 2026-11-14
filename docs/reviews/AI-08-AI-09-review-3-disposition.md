# Disposition of AI-08/AI-09 review 3

Verdict **REQUEST_CHANGES** (`docs/reviews/AI-08-AI-09-review-3.md`), only R3 remained.

**R3 repaired:** `tools/evaluate_rag.py` now reads `required_answer_tokens` and
`forbidden_answer_tokens` from each labeled case through `answer_claims_match`. New tests
`backend/tests/test_rag_benchmark.py` assert that the fabricated “all its tests passed” claim fails
while the real failure/abstention wording passes. The benchmark was regenerated; C/D
`unsupported_claim_rate=0.0` on the real answers. Exact finding-type equality already rejected the
unexpected-finding mutation in review 3.

All other findings were closed in review 3 and are unchanged.
