# Expanded M2 metrics

| Measure | Value | Source |
| --- | --- | --- |
| Backend tests | 438 passed, 3 opt-in skips | final run |
| Frontend tests | 13 passed | final run |
| Cucumber scenarios / steps | 93 scenarios passed; 396 Gherkin steps + 372 hook steps | `omp-m2-bdd/evidence/cucumber-messages.ndjson` |
| Strict gate | ok (93 test cases) | `step-resolution.mjs` |
| Feature files executed | 19 (all applicable M0/M1/M2 acceptance features) | `feature-inventory.json` |
| Features declared not executed | 12, each with a reason | `feature-inventory.json` |
| M2 rules implemented | 6 / 6 | `app/assurance/rules.py` |
| Oracle mismatches | 0 | `test_m2_assurance.py` |
| Portable fixture repositories | 2 | `benchmark.json` |
| Discovery vs hand labels | exact at three revisions | `benchmark.json` |
| Repository modifications during indexing | 0 | `benchmark.json` |
| Cross-repo identity collisions | 0 | `benchmark.json` |
| Matched resolutions with captured report | 23/23 | `benchmark.json` |
| Undefined findings without report | 0 | `benchmark.json` |
| Schema version | 0.3.0 | `backend/app/version.py` |
| Issues created | 6 (#58–#63) | GitHub |
| Issues closed / PRs / pushes | 0 | — |
| Independent review submissions | 7 of 7; final verdict APPROVE (`review-7.md`) | review records |
| Final status | engineering gate SATISFIED (APPROVE, submission 7) | `APPROVAL.md` |
| Subagents used | 0 | session |
| Network steps | 2 dependency installs | `uv.lock`, `bdd/package-lock.json` |
