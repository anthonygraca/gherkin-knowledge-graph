# DT-04 — independent review, round 1

**Task:** DT-04 (#23), M1, owner B. **Submission 1 of 7.**
**Reviewer:** Codex, `gpt-6.1-sol`, `xhigh`, read-only — session `01a1d2f7-d05c-7f41-93c7-932192b55230`,
2026-11-13T03:33:38Z → 03:39:39Z (360.93 s), exit 0; 132,667 CLI-reported tokens.
**Reviewed snapshot:** branch `feat/23-dt-04-thread`, base
`0970f7aa3334d88b3b19e29fae446e0eeb84593d`, captured 2026-11-13T03:29Z; 51/51 manifest hashes
matched before and after.
**Packet:** `docs/reviews/DT-04-review-prompt.md`, sha256
`5d933330c1797c319f9c2eb74fccdd16186bd6efbec51be36c4b73a02584417a` (102,026 bytes).
**Verdict:** REQUEST_CHANGES — R1 (missing-repository ingestion misreported as an unknown baseline;
blocking), R2 (evaluate status text; nonblocking), R3 (SCN-611 mapping; nonblocking). All repaired
for submission 2 (`docs/reviews/DT-04-review-2.md`).

The verdict below is copied verbatim from the reviewer's final message (raw file sha256
`2f92b89e33188c671816e918030f397d432c6ecd544e4b41d9ed39dff1a36244` before path sanitization);
only absolute repository and run-directory paths are substituted with `<task_repo>` and
`<run_dir>`.

---

**REQUEST_CHANGES — DT-04, submission 1 of 7.**

Reviewed branch `feat/23-dt-04-thread`, base `0970f7aa3334d88b3b19e29fae446e0eeb84593d`, snapshot captured `2026-11-13T03:29Z`. All **51 manifest hashes matched before and after review**. No files were changed.

| Acceptance criterion | Assessment | Evidence |
|---|---|---|
| SCN-611 fully linked thread | PASS | Correct artifacts, LNK-001…003 and EV-001; tag/SHA responses agree. |
| SCN-612 proposal-only thread | PASS | REQ-002 has no accepted links; LNK-007 appears only in proposals. |
| SCN-613 assembled from ingestion | PASS | Threads work with example/snapshot reads denied; schema is 0.2.0. |
| SCN-614 root errors | PASS | Unknown root returns `artifact-not-found`; CODE-001 returns `thread-not-found`, both 404. |
| SCN-615 ingestion results | PASS | Both baselines produce expected counts and commit-derived run IDs. |
| SCN-616 artifact inventory | PASS | All ten artifacts are returned; filtering and baseline handling are correct. |
| Documented configuration errors | **FAIL** | Missing-repository ingestion returns the wrong problem; DT04-R1. |

Proposal/accepted/evidence separation, behavioral port compatibility, artifact revision/hash semantics, evidence-reference validation, offline defaults, schema bump, and unchanged oracle-label substance passed inspection and probes. Assurance and review endpoints still return their required 501 responses.

1. **DT04-R1 — Medium; blocking. Missing repository is misreported as an unknown baseline.**  
   **Location:** [ingested.py:143](<task_repo>/backend/app/persistence/ingested.py:143>).  
   **Contract:** Documented ingestion errors and story DoD.  
   With `fixture_repo_path` pointing to an absent directory, `POST /api/ingestion/run` returns **404 `baseline-not-found`**, with the misleading detail “git is not installed.” Expected: **500 `fixture-data-missing`**, including the build instruction. Reads correctly produce that expected error.  
   `ingest()` resolves the revision before reaching `_ingest()`’s repository-existence check. Check repository availability before resolution. Recheck ingestion with an absent repository, and preserve 404 for an unknown revision in an existing repository.

2. **DT04-R2 — Low; nonblocking. New documentation claims assurance rules execute today.**  
   **Locations:** [routes.py:141](<task_repo>/backend/app/api/routes.py:141>), [api-contracts.md:125](<task_repo>/docs/api-contracts.md:125>).  
   **Invariant:** Honest distinction between implemented behavior and contract-only capability.  
   These descriptions say `POST /api/assurance/evaluate` runs implemented rules; it returns 501. State its current contract-only status and owning stories. Recheck the documentation and generated OpenAPI description; no assurance implementation is requested.

3. **DT04-R3 — Low; nonblocking. SCN-611’s automated mapping overstates thread tag/SHA coverage.**  
   **Location:** [DT-04.md:85](<task_repo>/docs/stories/DT-04.md:85>).  
   **Criterion:** SCN-611; accurate verification mapping.  
   The cited tag/SHA test requests `/api/artifacts/REQ-001`, not the thread endpoint. Thread equality passed independent probes and retained HTTP captures. Extend the existing thread test to compare tag/SHA bodies at baseline-b, then update the mapping.

Retained raw logs under `<run_dir>/dt-04/` support **224 passes** in normal and network-denied runs and successful fixture verification. Independently, 19 domain tests, targeted store/evidence probes, Ruff, formatting, whitespace, and proposed-message commitlint passed. The full suite was not independently rerun because its temporary-file operations require writes. Standard TestClient stalled; ASGI probes used inline thread dispatch, and the unmodified store independently reproduced DT04-R1.

This review does not attest human labeling, human link decisions, refinement sign-off, stakeholder acceptance, or milestone completion.