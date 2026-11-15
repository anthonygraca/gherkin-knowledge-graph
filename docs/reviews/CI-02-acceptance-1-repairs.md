# CI-02 acceptance review 1 — repair record

**Snapshot:** `4df96be` (submission 1) repaired on the feature branch; the acceptance reviewer's
findings are in `docs/reviews/CI-02-acceptance-1.md`. This is an author disposition, not evidence;
the code, tests, and retained reports are the evidence.

| Finding | Disposition | Evidence |
|---|---|---|
| **CI02-ACC-R1** — loading normalized payloads before digest verification | Repaired. `load_report` validates the supplied `report_digest` over the raw parsed object before Pydantic validation; `ReportFinding` no longer sorts/deduplicates payload lists. Identity normalization remains confined to the fingerprint. Reordered/deduplicated payloads with a matching digest compare unchanged and retain the supplied values; a stale digest is refused. The BDD payload step now compares complete before/after payloads. | `backend/app/domain/assurance_report.py`; `backend/app/assurance/reporting.py` `load_report`; `bdd/step_definitions/ci.steps.js`; direct probes. |
| **CI02-ACC-R2** — completed report accepted an unavailable required input | Repaired. A completed `AssuranceReport` requires every required input to be available and digested; `_validate_report` repeats the check. A mutated report is refused with `findings-not-comparable` and no classification. | `assurance_report.py` `_consistent`; `reporting.py` `_validate_report`. |
| **CI02-ACC-R3** — only the first invalid input identified | Repaired. `load_report_pair` collects load failures from both sides; `compare_reports` collects validation failures from both. Dual failures return `invalid_input="both"` and no classification. | `reporting.py`; `tools/assurance.py` `_diff`; dual-invalid probes. |
| **CI02-ACC-R4** — unsupported report versions accepted | Repaired. `report_version` is constrained to the literal `"1.0"` (and the input manifest version likewise); an unsupported version is refused. SCN-3505 now includes `an unsupported report version`. | `assurance_report.py`; `docs/stories/CI-02.feature`; `bdd/step_definitions/ci.steps.js`. |

**Verification:** final full acceptance suite 203 scenarios / 1972 steps passed, including the new
CI-02 example; backend 553 passed / 4 skipped; strict gate, fixture verify, Ruff and format clean.
Hosted CI on the repaired head is recorded on PR #78; the reviewer must observe it.

## Second acceptance pass (submission 2)

- **CI02-ACC-R5:** a completed report now requires the full mandatory input-kind set for its scope
  (requirement assurance: artifact, accepted/proposed link sets, evidence set, fixture manifest,
  policy; self-assurance: execution report, provenance sidecar, feature, policy), each present and
  marked required. Removing an entry, replacing `inputs` with `[]`, or downgrading a mandatory entry
  is a contract refusal.
- **CI02-ACC-R3:** `load_comparable_pair` loads and semantically validates both sides before
  returning; load-stage and semantic-stage failures are collected across both inputs, so mixed
  failures return `invalid_input="both"` with both reasons.
