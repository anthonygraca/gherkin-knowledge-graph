## Verdict

**REQUEST_CHANGES.** The merged snapshot’s assurance evidence, research records, story approvals, invariants, and hosted checks are green, but M4 exit criteria 1–2 are not fully satisfied. The diff accepts a portable report whose declared identity is forged to `stable_fingerprint` (M4-R1), the evaluator silently completes instead of producing an incomplete diagnostic when a historical commit is unreadable (M4-R2), and a non-UTF-8 report crashes the diff instead of returning `findings-not-comparable` (M4-R3). The remaining findings are nonblocking test/evidence-delivery gaps.

## M4 exit criteria

| # | Criterion | Result | Evidence |
|---|---|---|---|
| 1 | Revision-triggered assurance | **FAIL** | The merge-run banking and self reports are correct: 17 and 44 inputs, 6 and 0 findings, report digests recomputed, all input revisions bound, 41 feature hashes matching `git show 1731aed:`, 31 execution sources matching, coverage 174 executed / 0 skipped / 32 unknown. Publication is artifact/summary only with `contents: read`. However, an unreadable historical commit is silently skipped in `_evaluate` and the CLI writes `tool_outcome=completed`, exit 0, rather than an incomplete diagnostic (M4-R2), so the “exit 2 is a tool failure / completeness” rule is not fully met. |
| 2 | Comparable finding diff | **FAIL** | Fresh CLI comparisons produce 2 new / 4 unchanged / 0 resolved forward, 0/4/2 reverse, 0/4/0 self; payload retention and the twelve canonical invalid examples pass; declared `source_locator` reports are refused. But a `gherkin_executability` report with `identity_kind` changed to `stable_fingerprint` is accepted and classified (0/0/1 observed), and a non-UTF-8 report exits 1 with a traceback instead of `findings-not-comparable` (M4-R1, M4-R3). |
| 3 | Reproducible benchmark/report | **PASS** | AI-09 `rag-benchmark.json` and `IMPLEMENTATION.md` record A lexical, B CocoIndex, C accepted-graph, and D hybrid arms; hand-labeled inputs and hashes; latency/runtime observations; explicit small-corpus and comparison limits; a negative CocoIndex result and positive graph/hybrid agreement; no general retrieval claim. AI-05/AI-07/AI-08 records and approvals are present. |
| 4 | Optional scope honesty | **PASS** | Default `ai_mode=fake`; CI-01 asserts no model provider; live AI-02/AI-07/AI-09 evidence is opt-in and retained separately; no shared DGX/K3s/remote-hosted model claim; ADR 0012 §4 and ADR 0008 prohibit the shared path. |
| 5 | Story approvals and integration | **PASS** | CI-01/CI-02 acceptance-6 at `0aa9c6a`; code is identical at `0aa9c6a` and `1731aed`; AI-05 review-3, AI-07 review-5, and AI-08/AI-09 review-4 are APPROVE. Issues #36/#37 are closed. F-10 #16 remains open but eligible: both sub-stories are accepted and no open major finding exists. |
| 6 | Invariants | **PASS** | Proposals/accepted links/evidence remain separate; golden findings distinguish `reverification_required` from `verification_failed`; report model and input manifest bind evaluated and historical revisions; self-assurance produces no requirement verdict and the diff creates no evidence, links, or review state. M4-R1 affects malformed-input acceptance, not state mutation. |
| 7 | Evidence | **PASS** | Final backend 553 passed / 4 skipped; Cucumber 203 scenarios / 1,972 steps; strict gate 203 cases; fixture verify and Ruff clean; inventory 41 files; hosted run 43716166621 (push, head `1731aed`) six jobs success; `gh pr checks 78` six pass; `final-manifest.sha256` 53/53 hashes match both the working tree and the merged snapshot. Nonblocking: merge-run JSON is untracked/not in the manifest and STATUS is stale (M4-R6); the final close-out report may follow. |

## Findings

### M4-R1 — Refuse gherkin-scope reports regardless of declared identity kind

**Severity:** High (P1) · **Blocking:** Yes · **Confidence:** 0.95  
**Path:** `backend/app/assurance/reporting.py:442-447`

The comparison guard trusts the report’s self-declared `identity_kind`. A `gherkin_executability` report uses portable `artifact_keys` (source locators), but if that field is changed to `stable_fingerprint` and `report_digest` is recomputed, `assurance diff` accepts it. Observed with a failed self-assurance probe: the genuine `source_locator` report is refused with exit 2, while the same report with `identity_kind=stable_fingerprint` returns exit 0 with 0 new / 0 resolved / 1 unchanged. The contract says any source-locator report must be refused because no reviewed continuity mapping exists; scope `gherkin_executability` is the portable/source-locator scope, so the guard must not rely on the claim alone.

Smallest correction: treat the scope as source-locator scope in `_validate_report`, and add a Cucumber case that flips `identity_kind` on a self report and expects exit 2, `findings-not-comparable`, and no classification.

```python
    if (
        report.identity_kind is IdentityKind.SOURCE_LOCATOR
        or report.scope is AssuranceScope.GHERKIN_EXECUTABILITY
    ):
```

### M4-R2 — Fail incomplete when a historical commit is unreadable

**Severity:** High (P1) · **Blocking:** Yes · **Confidence:** 0.85  
**Path:** `tools/assurance.py:234-240`

The historical-input loop catches every exception from `store.artifacts_at(row.tested_commit)` and executes `continue`. The rule engine’s `_artifacts_at` also catches the same failure and returns `None`, so the evidence is treated as unknown; the CLI still writes `tool_outcome=completed` and exits 0. A `verification_failed` or `reverification_required` finding can therefore be suppressed while the report claims completeness. The report contract (`docs/assurance-report-contract.md` §1.3 “Unreadable required ingestion input”, and “Historical input coverage”) requires an incomplete diagnostic with the unavailable input recorded (`available=false`, `digest=null`), `failure_stage=input`, `failure_code=input-unreadable`, and no findings. The accepted banking fixture is unaffected because both historical commits (`9efce693…`, `d11f4eee…`) are readable; the defect is the untriggered code path.

Smallest correction: record an unavailable `historical_artifact` input, retain the already-known partial inputs, and raise `_CliFailure(stage=FailureStage.INPUT, code="input-unreadable")`; add a CLI/BDD case with an evidence row whose `tested_commit` is absent. Recheck: exit 2, incomplete envelope, no findings, unavailable historical entry present.

### M4-R3 — Refuse non-UTF-8 report files instead of crashing the diff

**Severity:** Medium (P2) · **Blocking:** Yes · **Confidence:** 0.99  
**Path:** `backend/app/assurance/reporting.py:371-375`

`load_report` catches `OSError` and `json.JSONDecodeError`, but `Path.read_text("utf-8")` raises `UnicodeDecodeError` for a non-UTF-8 file. `_diff` catches only `ReportsNotComparable`, so `assurance diff` exits 1 with a traceback. Observed: a report containing byte `0xff` produced `UnicodeDecodeError` and exit 1; the same file containing invalid JSON produced exit 2 with the correct `findings-not-comparable` diagnostic. Invalid UTF-8 is malformed input and must be refused under criterion 2.

Smallest correction: catch `UnicodeDecodeError` and raise `ReportsNotComparable` naming the side; add a Cucumber case with invalid UTF-8 bytes.

```python
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
```

### M4-R4 — Assert diff revisions against the compared reports

**Severity:** Low (P3) · **Blocking:** No · **Confidence:** 0.99  
**Path:** `bdd/step_definitions/ci.steps.js:533-538`

The retained test asserts `payload.previous_revision` equals `this.results.diff.diff.previous_revision`, which is the same value; the assertion cannot fail. A regression that swapped or hardcoded the diff revisions would still pass the Cucumber suite. The acceptance-6 record independently verified the revisions, and the product code sets them correctly, so this is a verification gap rather than a current behavioral defect.

Smallest correction: compare against the saved reports’ `evaluated_revision` values.

```javascript
  assert.equal(
    payload.previous_revision,
    this.results.reports['baseline-a'].evaluated_revision,
  );
  assert.equal(
    payload.current_revision,
    this.results.reports['baseline-b'].evaluated_revision,
  );
```

### M4-R5 — Return exit 2 when diff output cannot be written

**Severity:** Low (P3) · **Blocking:** No · **Confidence:** 0.95  
**Path:** `tools/assurance.py:608-614`

`_diff` calls `write_atomic(args.output, …)` and `_summary(…)` without catching `OSError`. Observed: a valid comparison with `--output /proc/…` exits 1 with a `FileNotFoundError` traceback; `--summary /proc/…` prints the diff to stdout and then exits 1. The M4 exit convention uses exit 2 for tool/publication failure, and the CLI already has `_publication_failure` for the evaluate/self-assure paths. The workflow does not use the diff output, so this is nonblocking.

Smallest correction: wrap the output/summary writes in `try/except OSError` and return `_publication_failure(exc)`; add a case for an unwritable `--output`.

### M4-R6 — Commit and hash-pin the merge-run evidence

**Severity:** Low (P3) · **Blocking:** No · **Confidence:** 0.99  
**Artifacts:** `docs/reports/omp-closeout/evidence/hosted-ci-m4-main-run.json` (untracked), `docs/STATUS.md:5-8`

The merge-run JSON for 43716166621 is present and matches `gh run view` (push, head `1731aed`, six success jobs), but it is untracked. `final-manifest.sha256` has 53 entries, all matching the snapshot, but it pins the pre-merge run 43713557672 rather than 43716166621. `docs/STATUS.md` still says “merge pending” and cites the pre-merge run. The final close-out report may follow this review, so this is not blocking, but the merge-run evidence should be committed and included in the final manifest; STATUS should name the merged snapshot and run 43716166621.

## Check verification

**Observed**

- `git rev-parse HEAD` = `1731aedb912d16c5e0bbfdd5c22c460ce2e0d1c2`; `git diff --stat 0aa9c6a..1731aed -- backend tools bdd .github frontend fixtures` is empty, so the CI-01/CI-02 acceptance-6 code snapshot is identical to the merged snapshot.
- `gh run view 43716166621 --json …`: `conclusion=success`, `event=push`, `headSha=1731aed…`, six jobs all success. `gh pr checks 78`: all six checks pass (PR run 43715269408 at `79746ba`).
- Downloaded merge-run artifacts `14162597699` (banking) and `14163081480` (self). Recomputed report digests match; banking report has 17 inputs, 6 oracle-matching findings, 10 artifacts, 2 historical IDs; self report has 44 inputs, 41 feature IDs, 0 findings, 31 execution sources, coverage 174 executed / 0 skipped / 32 unknown. All required input revisions bind correctly; all 41 feature digests match `git show 1731aed:<path>`; all 31 source digests match the feature inputs.
- `sha256sum -c docs/reports/omp-closeout/evidence/final-manifest.sha256`: 53/53 OK against both the working tree and the `1731aed` snapshot. Final backend log 553 passed / 4 skipped; Cucumber 203 scenarios / 1,972 steps; CI-01 9 executions, CI-02 17, AI-09 4, no failing executions; strict gate 203 cases / 1,972 results; fixture verify and Ruff clean; inventory 41 files with CI-01/CI-02 executed.
- Fresh `/tmp` banking evaluations and CLI diffs: 2 new / 4 unchanged / 0 resolved forward, 0/4/2 reverse, 0/4/0 self; findings match the baseline-b oracle.
- Probes: invalid JSON is refused with exit 2 and `findings-not-comparable`; declared `source_locator` self reports are refused; invalid UTF-8 exits 1 with `UnicodeDecodeError` (M4-R3); a self report with `identity_kind` flipped to `stable_fingerprint` is accepted and classified (M4-R1); unwritable diff `--output`/`--summary` exits 1 (M4-R5).

**Not observed / not rerun**

- Full local pytest, Cucumber, frontend build/tests, fixture regeneration, and live AI-02/AI-07 CocoIndex runs were not rerun; their retained evidence and hosted job conclusions were inspected.
- Rendered GitHub job summaries and full hosted logs were not inspected beyond `gh run view`, `gh pr checks`, and the downloaded assurance artifacts.
- The `0aa9c6a` hosted artifacts were not downloaded by this review; the acceptance-6 records state they were inspected, and this review downloaded the `1731aed` merge-run artifacts.
- The final close-out report is not present; the merge-run JSON is not committed or in the final manifest (M4-R6). No repository files were edited; probes wrote only to `/tmp`.