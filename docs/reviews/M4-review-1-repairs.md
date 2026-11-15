# M4 milestone review 1 — repair record

**Snapshot:** merged main `1731aed` (PR #78); the independent M4 review verdict is
`docs/reviews/M4-review-1.md`. The review was performed by the repository reviewer agent after the
Codex workspace credit exhaustion recorded in `docs/reports/omp-closeout/evidence/codex-credit-blocker.md`.
This record is an author disposition; code/tests/evidence are the proof.

| Finding | Disposition | Evidence |
|---|---|---|
| **M4-R1** — forged `identity_kind` accepts portable reports | Repaired. Comparison refuses `gherkin_executability` scope as well as declared `source_locator` identity, so flipping `identity_kind` cannot bypass the continuity restriction. Added SCN-3505 examples for forged stable identity and non-UTF-8 input. | `backend/app/assurance/reporting.py` `_validate_report`; `docs/stories/CI-02.feature`; `bdd/step_definitions/ci.steps.js`; targeted 28/28. |
| **M4-R2** — unreadable historical commit completed silently | Repaired. The evaluator's historical-input loop records an unavailable `historical_artifact` with a null digest, retains the known artifact/link/evidence/policy inputs, and returns an incomplete diagnostic (`input` / `input-unreadable`) with exit 2 and no findings. | `tools/assurance.py`; `backend/tests/test_assurance_cli.py::test_unreadable_historical_commit_is_incomplete`. |
| **M4-R3** — non-UTF-8 report crashed the diff | Repaired. `load_report` catches `UnicodeDecodeError` and returns `findings-not-comparable` with the invalid side/no classification. SCN-3505 includes a non-UTF-8 example. | `backend/app/assurance/reporting.py`; BDD; `test_non_utf8_report_is_refused`. |
| **M4-R4** — diff revision assertion was tautological | Repaired. The BDD assertion now compares the diff's previous/current revisions with the saved reports' `evaluated_revision` fields. | `bdd/step_definitions/ci.steps.js`. |
| **M4-R5** — diff output/summary failures exited 1 | Repaired. Diff output/summary publication is wrapped and returns exit 2 with the publication diagnostic while the successful comparison remains on stdout. | `tools/assurance.py` `_diff`; `test_diff_publication_failure_returns_two`. |
| **M4-R6** — merge-run evidence untracked; STATUS stale | Repaired with this record: the merge-run JSON is committed and pinned, the final manifest includes it, and STATUS names the merged snapshot and final run. | `docs/reports/omp-closeout/evidence/hosted-ci-m4-main-run.json`; manifest; `docs/STATUS.md`. |

**Verification:** backend 556 passed / 4 skipped; full Cucumber 205 scenarios / 1990 steps passed;
targeted M4 28/28; strict gate, fixture verify, Ruff, format, and whitespace clean. Hosted CI on the
repair head and the M4 re-review follow.
