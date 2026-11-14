# Independent acceptance review — AI-05 candidate evaluation (submission 1)

## Snapshot

* Base `65907ba`; working tree uncommitted.
* Canonical `docs/stories/AI-05.feature` sha256
  `878ff14a24a19c777881011f56c13f7abd00f2fff7220cca9a5b4d611c913bca`.
* Baseline report `docs/reports/ai-05/evidence/candidate-benchmark.json` sha256
  `60a1927b19b4f299d7331a515012b7764bf8a93eda781377f8086bba3c95d51f`.
* Dataset `fixtures/banking-demo/expected/candidate-links.json` (hand-labeled, 5 pairs).

## Delivered

`tools/evaluate_candidates.py` measures a `CandidateDiscovery` provider against the labeled index:
recall@1/5/10, precision@5, MRR, false-candidate rate, per-source rows, provider/model/index/dataset
hashes. Offline fake provider. `docs/stories/AI-05.feature` (3 scenarios) and Cucumber bindings;
independent metric-vector tests in `backend/tests/test_candidate_evaluation.py`.

## Evidence

| Check | Result |
| --- | --- |
| Backend suite | 480 passed, 3 opt-in skips |
| AI-05 tests | 2 passed |
| Cucumber + gate | 115 scenarios / 957 results passed; strict gate ok; report sha256 11ba627b260248f1605e3decf6c3a3016fbac16493f327f8524db216ce33af47 |
| Fixture/ruff/format | clean |

## Reviewer mandate

You are the independent CTA implementation reviewer using GPT-6.1 Sol high. Verify the metrics are
computed independently, the dataset hash and provider/index provenance are recorded, negative
candidates affect the false-candidate rate, no model/network is required, and reports retain their
dataset revision. Do not edit, install, regenerate, commit, or delegate. Return PASS/FAIL/NOT
VERIFIED and APPROVE / REQUEST_CHANGES / NEEDS_INPUT.
