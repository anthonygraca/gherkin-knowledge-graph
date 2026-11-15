## Verdict

**REQUEST_CHANGES**

At `e463e9e3b496a6f60644d90c52e04da6f50f7dff`, R1 and R3 are repaired. R2 remains partially repaired: an existing-pointer storage read can escape untyped after staging. Required hosted conclusions could not be independently observed.

## Criterion assessment

| Canonical scenario | Assessment | Basis |
|---|---|---|
| SCN-3301 | PASS | Exact change sets, resolved revisions, artifact locators and hashes retained; no inferred embedding count. All eight fixture source/test hashes match Git blobs. |
| SCN-3302 | PASS | Evidence-only content preserves cache identity, changes the commit binding, and permits reuse without adapter execution. Retained acceptance evidence confirms unchanged assurance meaning. |
| SCN-3303 | PASS | Model changes invalidate configuration/cache identity while preserving the original manifest. |
| SCN-3304 | FAIL | Adapter failure, concurrent-reader isolation, rollback and retry pass. The normative typed-storage-failure obligation remains incomplete under R2. |
| SCN-3305 | PASS | Mixed bindings are rejected; compatible results preserve provider provenance and contiguous ranks. Candidate selection does not shrink the manifest corpus. |
| SCN-3306 | PASS | Counts and unavailable embedding metrics are honest. Controlled key-construction cost is included; exact-binding hits retain historical measurements. |

## Findings

1. **AI03-ACC-R1 — Major; repaired/closed; nonblocking.**

   **Path/line:** `backend/app/retrieval/lifecycle.py:164`, `:482`, `:514`.

   **Expected:** Validate canonical filename/binding, repository, resolved baseline/commit, derived identities, stored corpus key and requested context.

   **Actual:** Inspection and memory-only mutation probes confirm rejection through direct reads, baseline reads and exact-binding refresh. Listings omit corrupt or arbitrarily renamed snapshots.

   **Correction/recheck:** None required.

2. **AI03-ACC-R2 — Major; partially repaired; blocking.**

   **Path/line:** `backend/app/retrieval/lifecycle.py:416`.

   **Expected:** Publication storage failures produce typed `RetrievalUnavailable`, preserve previous published state, and clean unpublished staging.

   **Actual:** Staging, reader isolation, initial-write typing, pointer-write rollback and retry are repaired. However, `previous_pointer = pointer.read_bytes()` executes **after staging and outside the exception boundary**. An independent memory-only probe injecting `PermissionError` there observed the raw exception escaping after the staged write, without cleanup. The API’s generic exception handler would classify this as `500 internal-error`, rather than `503 retrieval-unavailable`.

   This is reachable when refreshing an already-published baseline with a new configuration and no `previous_baseline`.

   **Smallest correction/recheck:** Read the previous pointer within typed storage-error handling, preferably before staging; ensure subsequent failures clean staging. Inject this read failure, verify the typed result and unchanged previous publication, then remove the failure and retry.

3. **AI03-ACC-R3 — Minor; repaired/closed; nonblocking.**

   **Path/line:** `backend/app/retrieval/lifecycle.py:148`.

   **Expected/actual:** Timing starts before planning and key construction. Charging exactly 250 ms to corpus-key construction produced `elapsed_ms=250.0`; an exact-binding hit returned the original measurement unchanged.

   **Correction/recheck:** None required.

4. **AI03-ACC-R4 — Major verification gap; blocking.**

   **Path/reference:** `.github/workflows/ci.yml:11`; [hosted run 43679892961](https://github.com/anthonygraca/gherkin-knowledge-graph/actions/runs/43679892961).

   **Expected:** Independently observe all required hosted check conclusions on the submitted head.

   **Actual:** `gh run view` and `gh pr checks` failed connectivity; direct web retrieval also failed. The supplemental, untracked `hosted-ci-final-run.json` names the correct head and reports all four jobs successful, but direct verification remains unobserved.

   **Smallest recheck:** Retrieve the run/check conclusions through working GitHub access and confirm the head and all required jobs.

## Check verification

- Confirmed HEAD and inspected the requested base-to-head diff, canonical criteria, companion contract, specification approval, ADRs, prior findings, repair record, implementation, tests, routes and Cucumber bindings/bridge.
- **Independent memory-only probes:** content planning; corruption/context rejection; model invalidation; corpus retention; evidence-only reuse; concurrent-reader isolation; publication rollback/reopen/retry; initial-write failure; final-visibility rollback; timing; mixed-context rejection and compatible provenance.
- **Cucumber report:** 177 cases, 1,704 passing results; all six AI-03 cases passed on attempt 0. Embedded AI-03 source matches this snapshot. Strict step-resolution gate passed.
- **Evidence integrity:** all 83 `final-manifest.sha256` entries matched.
- **Checks rerun:** Ruff lint passed; formatting passed for 106 files; commit-reference validation passed for seven commits.
- **Retained reports:** backend **551 passed, 4 skipped**; fixture verification current/reproducible; frontend **14 passed** and production build successful. These writing suites were not rerun.
- **Cumulative whitespace check:** failed on trailing whitespace in `AI-02-spec-review.md`, `AS-06-acceptance-2.md` and `AS-07-acceptance-1.md`. The retained empty report does not establish a clean cumulative diff.
- An additional TestClient probe stalled and was interrupted; no API execution result is claimed for the pointer-read failure.
- **Hosted checks:** supplemental capture reports success for Commit references, Offline tests, Cucumber/step-resolution, and Frontend checks. Actual hosted conclusions remain independently unobserved.
- No files edited, fixtures regenerated, commits created, or work delegated.
