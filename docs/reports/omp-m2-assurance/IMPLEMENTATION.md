# M2 version-aware assurance — DT-05, DT-06, AS-02, AS-03, AS-05

**Served issues:** [DT-05 #24](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/24),
[DT-06 #25](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/25),
[AS-02 #3](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/3),
[AS-03 #4](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/4),
[AS-05 #27](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/27). Milestone M2.
**Snapshot:** local `main` at `4659e01` plus this uncommitted slice; schema `0.3.0`.
**Independent review:** not yet submitted at the time of this record.

## Delivered

* `app/assurance/rules.py` now evaluates all six rules. Precedence is implemented, not implicit:
  an applicable failing latest run suppresses reverification for that scenario; a stale pass never
  becomes a failure; missing links are independent of evidence.
* `ArtifactRepository.artifacts_at(revision)` and `impacted_links(baseline, previous)` added to the
  port; `IngestedStore` implements them. `label_of(commit)` resolves a source commit to its baseline
  name by content equality so findings say "passed at baseline-a" instead of a bare SHA.
* `GET /api/findings` now evaluates the rule set; the recorded-sample replay
  (`SampleFindingsSource`) was deleted rather than left beside a second source of truth.
* Dashboard drill-down: each finding expands to rule id, evaluated baseline, artifact revisions,
  evidence id with tested commit and execution time, explanation, and a distinct meaning line for
  reverification vs confirmed failure. `frontend/src/App.tsx`, tests in `App.test.tsx`.
* Canonical features created: `docs/stories/DT-05.feature`, `DT-06.feature`, `AS-02.feature`,
  `AS-03.feature`, `AS-05.feature` (unique `@SCN-2001…2042` ids).

## Acceptance evidence

| Story | Check | Result |
| --- | --- | --- |
| DT-05 | `backend/tests/test_m2_assurance.py::test_evidence_is_append_only_and_pinned_to_the_tested_commit` | pass |
| DT-05 | Cucumber `DT-05.feature` (4 scenarios) | pass |
| DT-06 | `::test_change_set_is_content_hash_based_and_matches_the_oracle`, `::test_impacted_links_reach_the_changed_artifacts` | pass |
| DT-06 | Cucumber `DT-06.feature` (3 scenarios) | pass |
| AS-02 | `::test_evaluated_findings_equal_the_hand_labeled_oracle[baseline-b]` | pass (6 findings, field-by-field) |
| AS-02 | Cucumber `AS-02.feature` (3 scenarios) | pass |
| AS-03 | `::test_reverification_and_failure_never_collapse`, `::test_baseline_a_has_no_failure_or_reverification` | pass |
| AS-03 | Cucumber `AS-03.feature` (2 scenarios) | pass |
| AS-05 | `frontend/src/App.test.tsx` drill-down tests for both finding types | 12 frontend tests pass |
| AS-05 | Browser demonstration | recorded in `docs/reports/omp-m2-bdd/browser/` after the HTTP/browser run |

## Oracle result (baseline-b, exactly as labelled)

| Finding | Artifacts | Evidence |
| --- | --- | --- |
| `missing_verification_link` | REQ-002 | — |
| `missing_implementation_link` | SCN-002 | — |
| `candidate_pending_review` | REQ-002, SCN-002 | — |
| `lifecycle_review_required` | REQ-003 | — |
| `reverification_required` | CODE-001, REQ-001, SCN-001 | EV-001 |
| `verification_failed` | REQ-003, SCN-003, TEST-002 | EV-003 |

Baseline-a has the first four and neither `reverification_required` nor `verification_failed`.
Explanations, severities, `evaluated_baseline`, `artifact_revisions`, and fingerprints match the
hand-labeled files; `test_m2_assurance.py` compares them field by field.

## Commands

```text
uv run --project backend pytest backend/tests -q           443 passed, 3 skipped
uv run --project backend python tools/fixturectl.py verify exit 0
(cd frontend && npm test)                                  13 passed
(cd frontend && npm run build)                             built
```

## Limitations

* File-level change granularity; renames are new artifacts; no environment/toolchain modelling;
  only the latest run per scenario is considered (ADR 0005).
* `artifacts_at` reads the tested commit through Git; an unreadable commit is treated as
  non-applicable evidence, never as failure.
* AS-05 browser-level Cucumber bindings are pending; the drill-down is verified by component tests
  and a recorded browser demonstration.
