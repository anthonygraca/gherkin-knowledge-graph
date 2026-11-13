# DT-03 — independent review, round 1

**Task:** DT-03 (#22), M1, owner B. **Submission 1 of 7.**
**Reviewer:** Codex, `gpt-6.1-sol`, `xhigh`, read-only — session `01a1d2d4-9cc6-7dd2-b772-761f67718f7f`,
2026-11-13T02:55:11Z → 02:58:57Z (226.49 s), exit 0; 82,688 CLI-reported tokens.
**Reviewed snapshot:** branch `feat/22-dt-03-links`, base
`590e776b67d9e340f9e68df04472222ee4fd0720`, captured 2026-11-13T02:53Z; 14/14 task hashes matched
before and after.
**Packet:** `docs/reviews/DT-03-review-prompt.md`, sha256
`38eb7a7899c6ae625ae0c52362f3b991800b7b7557e8fa7eb8cf2c4500cf0da0` (43,127 bytes).
**Verdict:** REQUEST_CHANGES — **R1** (state-mismatch diagnostic omitted affected link ids; SCN-605),
**R2** (packet `scan.py` dependency pointer was stale), **R3** (duplicate-id mapping claimed
cross-file coverage). All repaired for submission 2 (`docs/reviews/DT-03-review-2.md`).

The verdict below is copied verbatim from the reviewer's final message (raw file sha256
`31e743f399f7664276da468478846e6880f2e4a2eece0c3dabbaf9eb2cc2cae4` before path sanitization);
only absolute repository and run-directory paths are substituted with `<task_repo>` and
`<run_dir>`.

---

**REQUEST_CHANGES** — DT-03, submission 1 of 7.

Reviewed branch `feat/22-dt-03-links`, base `590e776b67d9e340f9e68df04472222ee4fd0720`, snapshot captured `2026-11-13T02:53Z`. All **14 task-file hashes matched before and after review**. The dependency-pointer discrepancy below remains unresolved. No files were changed.

| Criterion | Assessment | Evidence |
|---|---|---|
| SCN-601 accepted provenance | PASS | Both fixture baselines preserve accepted state, reviewer identity, and decision time. |
| SCN-602 proposal separation | PASS | REQ-002 has no accepted links; LNK-007 appears only among proposals. |
| SCN-603 invalid direction | PASS | Retained Git repository rejects LNK-900 and names the expected requirement → scenario direction. |
| SCN-604 unknown endpoint | PASS | Retained Git repository rejects the link and names SCN-999. |
| SCN-605 wrong review state | **FAIL** | File-level state mismatch rejects ingestion but omits the offending link’s identity. |
| SCN-606 repeatability | PASS | Repeated ingestion preserves link facts; inspected ingestion paths perform no writes. |
| Schema, duplicate IDs, absent files | PASS | Retained repository checks and additional boundary probes passed, including cross-file duplicates. |
| Revision and content hashes | PASS | Both baseline commits and independently hashed artifact blobs match the returned facts. |
| Exact dependency identity | **NOT VERIFIED** | Supplied `scan.py` pointer differs from both the working file and the declared base. |

1. **DT03-R1 — medium severity, blocking; SCN-605.**  
   At [links.py:81](<task_repo>/backend/app/ingestion/links.py:81>), an accepted-link file declaring `proposed` and containing proposed link `LNK-902` produces:

   ```text
   …:evidence/accepted-links.json: declares review_state 'proposed' but should be 'accepted'
   ```

   SCN-605 requires the error to name **the file and the link**. The existing test checks only the state phrase, and its verification mapping omits the link-name requirement.

   **Smallest correction/recheck:** include affected link IDs in this diagnostic; assert the filename and `LNK-902`; also retain coverage for a proposed member inside a file declaring `accepted`. Correct the mapping and rerun the focused checks.

2. **DT03-R2 — medium severity, blocking evidence discrepancy; snapshot integrity.**  
   The dependency pointer in [the review packet:803](<run_dir>/review-1-prompt.md:803) identifies `backend/app/ingestion/scan.py` as:

   ```text
   supplied: 6300e39d2bcf1305bd5c69ef337f4ae48999bb5134556a4b457befea4500556f
   observed: 2a602ee3668bd1560e42aa8870c6a1875b3977a082d449109892852c73e0a613
   ```

   The observed hash also matches `scan.py` at the declared base. This establishes a packet inconsistency, not an implementation edit.

   **Smallest correction/recheck:** OMP should confirm the intended dependency, correct the pointer, and resubmit a consistent snapshot/evidence identity. I requested clarification during review.

3. **DT03-R3 — low severity, nonblocking; verification-record accuracy.**  
   [DT-03.md:78](<task_repo>/docs/stories/DT-03.md:78>) maps duplicate IDs “within and across files” to a test that populates only `accepted-links.json`.

   **Correction/recheck:** add a cross-file case to that substantive test and update the execution record. My separate in-memory boundary probe confirmed that cross-file rejection currently works; this is a coverage-record gap.

I inspected raw logs under `<run_dir>/dt-03/`. They support the recorded **217 passes** in both runs, fixture verification, and clean quality checks. Independently, **66 tests passed**; one additional settings test could not set up because the sandbox has no writable temporary directory. Read-only checks against retained Git repositories, boundary probes, Ruff, formatting, whitespace, and proposed-message commitlint completed successfully.

Within this slice, proposal/acceptance/evidence separation, existing port behavior, offline defaults, contract-only 501s, and generated-file discipline remain intact. No later-milestone implementation is requested. This review does not attest human labeling, human link decisions, or stakeholder acceptance.