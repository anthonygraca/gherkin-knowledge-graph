## Verdict

**REQUEST_CHANGES**

All six canonical scenario examples pass at the working-tree snapshot based on `827e487`. Two major gaps in the normative publication contract block acceptance.

## Criterion assessment

| Scenario ID | Assessment | Evidence |
|---|---|---|
| SCN-3301 | PASS | Exact changed/unchanged sets confirmed against the actual fixture repository. Both resolved commits and artifact hashes are available; hashes independently match committed bytes. |
| SCN-3302 | PASS | Cache identity excludes commits; bindings include them. Evidence-only reuse preserves assurance meaning. An in-memory probe confirmed zero adapter calls. |
| SCN-3303 | PASS | Weights changes alter configuration/cache identity; the previous immutable manifest remains readable. |
| SCN-3304 | PASS | The specified adapter failure is typed, publishes no baseline-b snapshot, preserves baseline-a, and provides no fallback. Broader publication failure handling fails below. |
| SCN-3305 | PASS | Mixed batches return `409 mixed-index-context` without candidates. Compatible results have contiguous ranks, CTA bindings, and retained provider provenance. `TraceCandidate` is unchanged. |
| SCN-3306 | PASS | Reports contain measured non-negative timing, artifact counts, snapshot/configuration identity, and `null`/`not_available` embedding counts. Timing coverage has the minor discrepancy below. |

All six scenarios are present in `final-cucumber.ndjson`, each with one attempt and exclusively passing step results. Its captured AI-03 feature matches the current file.

## Findings

1. **AI03-ACC-R1 — Major; blocking — Structurally valid corrupt manifests are served.**

   **Path/line:** [lifecycle.py:404](</home/anthonygraca/CSU Fullerton Dropbox/Anthony Graca/cpsc-583-knowledge-representation/project/gherkin-knowledge-graph/backend/app/retrieval/lifecycle.py:404>); related reads at lines 233–247.

   **Expected:** The normative companion, `docs/stories/AI-03.md:59`, prohibits serving corrupt snapshots. Stored configuration, content hashes, cache key, binding, and requested context must agree.

   **Actual:** Reads validate field shapes only. In a read-only probe with storage replaced by a Python dictionary, changing an artifact hash and weights digest while retaining the original identity fields produced a manifest returned by both `get()` and an exact-binding refresh. A baseline-b pointer referencing baseline-a also returned baseline-a without rejection.

   **Smallest correction/recheck:** Validate derived identities and requested binding/baseline when reading. Ensure an invalid existing snapshot cannot subsequently produce a successful publication response. Recheck altered content/configuration, mismatched filename/binding, and a cross-baseline pointer.

2. **AI03-ACC-R2 — Major; blocking — Pointer publication failure leaves a usable snapshot.**

   **Path/line:** [lifecycle.py:383](</home/anthonygraca/CSU Fullerton Dropbox/Anthony Graca/cpsc-583-knowledge-representation/project/gherkin-knowledge-graph/backend/app/retrieval/lifecycle.py:383>).

   **Expected:** `docs/stories/AI-03.md:57` requires a failed refresh to publish neither a pointer nor a usable snapshot.

   **Actual:** `_publish()` exposes the immutable snapshot before replacing the pointer. Injecting an `OSError` during baseline-b pointer publication caused refresh to raise while leaving baseline-b retrievable through `get(binding)`. Baseline-a remained intact, but the failed refresh had published usable state. The storage error also escaped untyped.

   **Smallest correction/recheck:** Make publication visibility transactional across snapshot reads/listing and pointer replacement, and report storage failure through a typed error. Inject pointer replacement failure and confirm no baseline-b snapshot is readable, including after reopening the store or retrying.

3. **AI03-ACC-R3 — Minor; nonblocking — Elapsed time excludes promised key construction.**

   **Path/line:** [lifecycle.py:164](</home/anthonygraca/CSU Fullerton Dropbox/Anthony Graca/cpsc-583-knowledge-representation/project/gherkin-knowledge-graph/backend/app/retrieval/lifecycle.py:164>).

   **Expected:** `docs/stories/AI-03.md:76` includes cache-key construction in the measured publication phase.

   **Actual:** Configuration digest, initial corpus collection, cache key, and binding are computed at lines 144–156, before timing starts.

   **Smallest correction/recheck:** Start timing before that work for new publications, retaining historical measurements on exact-binding hits. Verify the boundary with a controlled clock.

## Check verification

- Inspected the cumulative diff against `827e487`, implementation, approved specifications, tests, API/domain contracts, Cucumber bindings, and bridge operation.
- Independently confirmed baseline-a→b classifications and all eight source/test artifact hashes against committed blob bytes.
- Supplied backend report: **535 passed, 4 skipped**.
- Supplied Cucumber report: **177 scenarios passed, 1704 steps passed**.
- Independently ran the strict report gate: **177 test cases / 1704 results; passed**.
- Evidence manifest: **all listed checksums matched**.
- Independently ran Ruff lint, format check, and `git diff --check 827e487`: **passed**.
- Supplied fixture verification report: **current and reproducible**.
- Used memory-only probes for reuse, exact-binding hits, adapter failure, manifest corruption, and publication failure.
- Backend/Cucumber suites and fixture generation were not rerun because they write files. No repository edits, regeneration, commits, or delegation occurred.
- Hosted CI for this uncommitted snapshot was **not observed**.