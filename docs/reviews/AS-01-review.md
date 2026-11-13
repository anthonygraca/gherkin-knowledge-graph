# AS-01 — independent review, round 1 (approval)

**Task:** AS-01 (#2), M1, owner C. **Submission 1 of 7.**
**Reviewer:** Codex, `gpt-6.1-sol`, `xhigh`, read-only — session `01a1d313-f157-7880-8425-0bfc2b9953cf`,
2026-11-13T04:04:19Z → 04:09:09Z (290.31 s), exit 0; 106,974 CLI-reported tokens.
**Reviewed snapshot:** branch `feat/2-as-01-missing-verification`, base
`c43541b29d62186a4aa7fee32fed98720fc5f921`, captured 2026-11-13T04:02Z; all 15 task hashes matched
before and after; manifest sha256
`cb2b4398d98cd81a1c807c6e3c19c061e8bd9c3fd7472b42629337f26b0cf144`.
**Packet:** `docs/reviews/AS-01-review-prompt.md`, sha256
`d31f663b7871dbbfe056e86daa232edc72ce25b5151e16b8149dc1ad28525d9c` (37,682 bytes).
**Verdict:** **APPROVE** — SCN-701…705 PASS; no blocking finding. One nonblocking finding
(AS01-R1) asks the test to bind the pinned revision to the manifest tag rather than comparing two
returned fields; it is recorded for repair before the M1 exit review.
**Nonblocking (AS01-R1, low):** strengthen `test_assurance_rules.py`'s revision assertion to compare
against `committed_manifest.tags[baseline]`; owner OMP/C; required before M1 exit approval.
Approval covers the identified snapshot only; it does not attest human labeling, human link
decisions, refinement sign-off, stakeholder acceptance, or milestone completion.

The verdict below is copied verbatim from the reviewer's final message (raw file sha256
`10f216eacd9fbcea259c524e0e86f49b709be4ec3de9dc96a983f76b59cf9ca3` before path sanitization);
only absolute repository and run-directory paths are substituted with `<task_repo>` and
`<run_dir>`.

---

**APPROVE — AS-01, submission 1 of 7.**

Reviewed branch `feat/2-as-01-missing-verification`, base `c43541b29d62186a4aa7fee32fed98720fc5f921`, snapshot captured `2026-11-13T04:02Z`. All **15 supplied hashes matched before and after review**. [Manifest](<run_dir>/manifest.txt) SHA-256: `cb2b4398d98cd81a1c807c6e3c19c061e8bd9c3fd7472b42629337f26b0cf144`. No files changed.

| Criterion | Assessment | Verified behavior |
|---|---|---|
| SCN-701 | PASS | Baseline-a produces the oracle’s missing-verification finding for REQ-002. |
| SCN-702 | PASS | LNK-007 remains proposed and does not satisfy coverage. |
| SCN-703 | PASS | Accepted LNK-001 → SCN-001 prevents this finding for REQ-001. |
| SCN-704 | PASS | Findings carry the correct rule, severity, requirement revision, resolved commit and independently checked fingerprint. Tag/SHA responses match. |
| SCN-705 | PASS | Unknown baseline returns 404 `baseline-not-found`; unknown policy returns 400 `invalid-request`. |

No blocking implementation findings. Inspection and probes confirmed behavioral repository-port compatibility, deterministic ordering, proposal/acceptance/evidence separation, and offline operation. The evaluator creates no verification evidence or freshness/failure classifications. `GET /api/findings` preserves the reviewed replay; link review remains an honest AS-06 501. Shapes and generated fixtures are unchanged. Oracle-label substance matches the recorded human-attestation revision; subsequent differences are schema-version-only.

Independent checks passed: seven submitted assurance cases through an adapted ASGI client, additional port/API boundary probes, 19 domain tests, Ruff, formatting, whitespace and proposed-message validation. [Retained execution records](<run_dir>/gates.txt) and raw logs support 233 passes in both normal and reported network-denied runs, plus successful fixture verification.

Review limitations: full-suite execution and fixture verification require writes and were not rerun. Pytest capture/settings fixtures encountered the read-only restriction. Ordinary threaded ASGI dispatch timed out; independent API checks used inline synchronous dispatch in memory while retaining routing, validation, serialization and error handling.

Optional test improvement, separate from acceptance:

- **AS01-R1 — low, nonblocking; SCN-704 / independent expectations.** At [test_assurance_rules.py:54](<task_repo>/backend/tests/test_assurance_rules.py:54>), the revision assertion compares two returned fields. Both could contain the same incorrect SHA. Bind both fields to `committed_manifest.tags[baseline]` and rerun the parameterized test. The current implementation’s revisions passed independent checks.

Approval covers this implementation snapshot. It does not attest human labeling, human link decisions, refinement sign-off, stakeholder acceptance or milestone completion.