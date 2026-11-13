# AS-01 implementation record — missing verification-link findings

| Field | Value |
| --- | --- |
| Story | AS-01 — [#2](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/2), verified OPEN 2026-11-13T03:56:41Z (`gh issue view`, milestone "M1 — AI-free vertical slice") |
| Canonical criteria | [AS-01.feature](../../stories/AS-01.feature), sha256 `835b6d313960624402eccdcf4b51ca5c87ee790ec0249df7a7e72a0ec95a8c85` |
| Brief / verification map | [AS-01.md](../../stories/AS-01.md) |
| Branch / base | `feat/2-as-01-missing-verification` from `c43541b29d62186a4aa7fee32fed98720fc5f921` (DT-04 merge) |
| Contract version | `SCHEMA_VERSION = 0.2.0`, `PACKAGE_VERSION = 0.1.0` (no shape change) |
| Submission | **1 of 7** — **APPROVE** (2026-11-13T04:09Z); one nonblocking test-strength finding AS01-R1 |
| Snapshot captured | 2026-11-13T04:02Z (approved snapshot) |

## What changed

| Path | sha256 | Purpose |
| --- | --- | --- |
| `backend/app/assurance/rules.py` | `adf0fd7707f95343f4cd75ce9f476598cf368fb53e0dc88988a953df18f4d008` | `DeterministicAssuranceEvaluator` (M1 missing-verification rule) |
| `backend/app/api/deps.py` | `fb9b493481e405cb86d964744378bb04c4a2436ae4ddfcf91b0bbaa7dc9f45a9` | Evaluator dependency |
| `backend/app/api/routes.py` | `04300928d42b6afb3cf192bd26c709242bf6c7d3a67e4c679ef813e93f8a29db` | Implemented evaluate route; assurance tag |
| `backend/app/main.py` | `7ebd1e5f9a943fd027167ec8e23c0e236efd12f09e34ab9c598a29643ce0bd7e` | Wires the evaluator |
| `backend/tests/test_assurance_rules.py` | `d8c528bb854ae9bb7b7125b12276073590bac77846a6f7819265729c0f52d764` | Seven oracle/error tests |
| `backend/tests/test_api_contract.py` | `67f903e59a723ef0991ba671cdd7d7041677b16463478984c5c1cb8e47626ebf` | Evaluate removed from the contract-only cases |
| `docs/stories/AS-01.feature` | `835b6d313960624402eccdcf4b51ca5c87ee790ec0249df7a7e72a0ec95a8c85` | Canonical criteria (SCN-701…705) |
| `docs/stories/AS-01.md` | `dbfb4dee6da40c3ae5059a02adaed584d0a05b89e4960d08513c14e0d7cf26ba` | Brief, assumptions, map |
| `docs/api-contracts.md` | `8134ad961dbbd6ee2031977b2893efad82ba7c21e35febe6563b27eda9be27a0` | Evaluate success example; 501 list updated |
| `docs/domain-contracts.md` | `9a33f65da79f96148b36ee03ebc4f8dbe05cfa8e039297e36d922a073e94c165` | M1 rule subset statement |
| `docs/architecture.md` | `386e5241c5d91a39dc8e9a83d1e1906ab1eda9c6cc9184d4ca518803a8161e89` | Assurance status |
| `docs/STATUS.md` | `137dd46fc3ad31634b1bb41095349523be0908eacac53b9ec2531752f0399b0b` | DT-04 landed; AS-01 active |

No fixture, generated response, or contract-shape change.

## Acceptance results

| Criterion | Check | Result |
| --- | --- | --- |
| SCN-701 missing verification | `tests/test_assurance_rules.py::test_evaluate_matches_the_oracle_missing_verification_finding` (both baselines: rule, type, severity, ids, evidence, fingerprint, explanation, SHA) | PASS |
| SCN-702 proposal does not count | `::test_evaluate_does_not_count_proposals` | PASS |
| SCN-703 healthy requirement | `::test_evaluate_leaves_a_covered_requirement_alone` | PASS |
| SCN-704 explainability/pinning | the oracle comparison at baseline-b plus `::test_evaluate_by_tag_and_sha_identical` | PASS |
| SCN-705 error cases | `::test_unknown_baseline_is_404`, `::test_unknown_policy_is_400` | PASS |

## HTTP probe (observed)

The app was started on port 8012, exercised, and stopped:

```text
POST /api/assurance/evaluate {"baseline":"baseline-a"} → 200
  FND-8e701f84ea44fa6c, missing_verification_link, high, ["REQ-002"],
  evaluated_baseline 0f8607b29d1ccb423062d856835f5310c9f54aa3
POST baseline-b by tag and by SHA → byte-identical 200 responses
POST {"baseline":"baseline-z"} → 404 baseline-not-found
POST {"baseline":"baseline-a","policy":"invented"} → 400 invalid-request
```

The shell exit was 143 because the probe stopped the server it started; every request returned the
recorded status/body. The server is stopped.

## Review round 1 — APPROVE (submission 1 of 7)

Reviewer: Codex `gpt-6.1-sol`, `xhigh`, read-only; session `01a1d313-f157-7880-8425-0bfc2b9953cf`;
2026-11-13T04:04:19Z → 04:09:09Z (290.31 s), exit 0; 15/15 source hashes matched.
Verdict: `docs/reviews/AS-01-review.md`.

* SCN-701…705: PASS. The oracle finding, fingerprint, severity, artifact/evidence ids, explanation,
  and resolved SHA match; tag/SHA responses are identical.
* Proposal/acceptance/evidence separation, deterministic ordering, offline operation, and the
  reviewed findings replay passed inspection.
* Nonblocking **AS01-R1 (low)**: the test's revision assertion compares `evaluated_baseline` to
  `artifact_revisions["REQ-002"]`; both could be wrong together. Owner OMP/C; repair by comparing
  both to `committed_manifest.tags[baseline]` before the M1 exit review.
* Reviewer limits: full-suite execution and fixture verification were not rerun (read-only); the
  submitted ASGI checks and retained logs were used.

Approval covers the identified snapshot. It does not attest human labeling, human link decisions,
refinement sign-off, stakeholder acceptance, or milestone completion.

## Commands and outcomes (as captured)

```text
captured_start=2026-11-13T04:01:09Z
pytest backend/tests -q                          exit 0  233 passed, 1 warning in 7.62s
fixturectl.py verify                             exit 0  reproducible and committed files current
ruff check .                                     exit 0  All checks passed
ruff format --check .                            exit 0  all files formatted
git diff --check                                 exit 0
captured_end=2026-11-13T04:01:18Z

network denial at 2026-11-13T04:01:18Z: `unshare -rn backend/.venv/bin/python -m pytest
backend/tests -q` → exit 0, 233 passed.
```

## Self-review

* **Rule scope:** only accepted `verified_by` links whose target exists as a scenario satisfy
  verification; proposals are not consulted. The oracle's REQ-002 finding is reproduced exactly,
  including its fingerprint and explanation.
* **Pinning/explainability:** `evaluated_baseline` and `artifact_revisions` carry the resolved SHA;
  tag and SHA requests are identical; findings sort by fingerprint.
* **Honesty:** `GET /api/findings` still replays the reviewed sample; the API docs state the M1
  subset and the remaining rules. Unknown baseline/policy use documented problems.
* **Offline:** pure reads + policy tables; no model, network, or mutation.

Known limits: M2 rules, the full findings endpoint switch, and review mutations remain later work.

## Independent review

**APPROVE** — submission 1 of 7, snapshot captured 2026-11-13T04:02Z, reviewer `gpt-6.1-sol` at
`xhigh`, 15/15 hashes confirmed. Verdict: `docs/reviews/AS-01-review.md`. One nonblocking
test-strength finding (AS01-R1) is tracked for repair before the M1 exit review. Commit, PR, CI,
and merge state are recorded separately after landing; this approval does not close #2 by itself.
