# AI-05 — labeled candidate retrieval evaluation

**Story:** AI-05 [#35] (parent F-09 #15). **Milestone:** M3.
**Snapshot:** base `65907ba` plus this uncommitted slice.
**Review:** pending at this record.

## Delivered

* `tools/evaluate_candidates.py` — measures a `CandidateDiscovery` provider against the hand-labeled
  `candidate-links.json`: recall@1/5/10, precision@5, MRR, false-candidate rate, with provider,
  model version, index revision, dataset hash, and per-source rows.
* `docs/stories/AI-05.feature` — canonical criteria; 3 Cucumber scenarios.
* Committed baseline report: `docs/reports/ai-05/evidence/candidate-benchmark.json` for the fake
  provider (offline; no model/network/vector service).

## Result (fake provider)

Recall@1 0.625, Recall@5/10 0.75, precision@5 0.75, MRR 0.75, false-candidate rate 0.25 on the
five labeled pairs. SCN-002's negative CODE-001 candidate is returned and counted as false, which is
the harness behavior under test. These are fixture-label measurements, not a model-quality claim.

## Verification

* `backend/tests/test_candidate_evaluation.py` — independent metric vectors.
* Cucumber `AI-05` — 3 scenarios passed.
* Backend/full suite and fixture checks recorded in the review packet.
