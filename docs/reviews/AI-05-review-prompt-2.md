# Independent acceptance review — AI-05 (submission 2)

## Snapshot

* Base `65907ba`; working tree uncommitted.
* Feature sha256 `878ff14a24a19c777881011f56c13f7abd00f2fff7220cca9a5b4d611c913bca`.
* Baseline report sha256 `60a1927b19b4f299d7331a515012b7764bf8a93eda781377f8086bba3c95d51f`;
  dataset hash `sha256:713c7095…`.
* Dataset: `fixtures/banking-demo/expected/candidate-links.json` (hand-labeled).

## Repairs since submission 1

* **R1:** SCN-2602 now creates a second dataset version (`model_version` variant), runs the tool
  against it, and asserts the original hash is retained while the new report carries the variant
  hash. The steps do not merely set a flag.
* **R2:** `dataset_snapshot(path)` reads bytes once and uses those bytes for both
  `CandidateIndexFile` validation and the recorded hash. A regression test monkeypatches a second,
  different read and asserts it is never used.

## Evidence

| Check | Result |
| --- | --- |
| Backend suite | 481 passed, 3 opt-in skips |
| AI-05 tests | 3 passed |
| Cucumber + gate | 115 scenarios / 957 results passed; strict gate ok; report sha256 55f70a1b… |
| Metrics | Recall@1 0.625, @5/@10 0.75, precision@5 0.75, MRR 0.75, false rate 0.25 |
| Fixture/ruff/format | clean |

## Reviewer mandate

You are the independent CTA implementation reviewer using GPT-6.1 Sol high. Verify R1 and R2, the
independent metric arithmetic, offline fake operation, and provenance. Do not edit, install,
regenerate, commit, or delegate. Return PASS/FAIL/NOT VERIFIED with stable IDs and
APPROVE / REQUEST_CHANGES / NEEDS_INPUT.
