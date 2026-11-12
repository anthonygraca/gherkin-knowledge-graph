# SETUP-01 commit-reference enforcement — independent review, round 2

**Task:** SETUP-01 (#8) follow-up slice; **submission 2 of 7** (round 1 = REQUEST_CHANGES at
2026-11-12T03:44:42Z; findings R1/R2 repaired before this submission).
**Reviewer:** Codex, model `gpt-6.1-sol`, reasoning effort `xhigh`, read-only sandbox —
`codex exec` session `01a1cde9-154d-70a3-9e83-f28dc17182c4`, 2026-11-12T03:59:26Z → 04:02:44Z
(198.0 s), exit 0; usage 814,167 input (717,312 cached) / 8,524 output (3,322 reasoning).
**Reviewed snapshot (v2):** HEAD `a82e466491b8352262f497f79e0e0d172a571c50` plus the frozen working
tree; the reviewer confirmed all seven slice hashes and all manifest file hashes; packet v2 sha256
`71592f0ad9faf2311119e31f922bbd3a6cb9601abeddfbe2e4676777cb115261` (55,960 bytes); round-2 manifest
`evidence/manifest-round2.json` sha256
`34ebf5c37dd17bf863c57589406f41e99252e821087df5127c17bf11806720e1`.
**Verdict:** APPROVE — R1 closed, R2 closed, all eight scenarios PASS, no new blocking finding.
**Nonblocking limitations (reviewer, NOT VERIFIED):** hosted execution including the `edited`
trigger; required-status-check configuration; the post-commit `--base f34ae07 --head HEAD` audit —
publication follow-ups outside this snapshot approval.
**Dispositions:** R1 was independently re-verified (YAML plus the unchanged-head/two-base
reproduction against the scope-excluding base vs the adoption baseline). R2 is closed on record
provenance; the reviewer notes the recapture, not the earlier session-shell execution, is what the
record explicitly attests.
**Commits after approval (record-only pairs per the packet):** commit 1 = the slice
(`ci(traceability): [issue #8] enforce commit references in CI`); commit 2 = this review-record
pair; commit 3 = reports, evidence, and `docs/STATUS.md`.

The verdict below is copied verbatim from the reviewer's final message (raw file sha256
`2d5dfb60e7c49691a8d41a01cc8b401e08ca528915d616a737f7e7f0937c5f1e`, 3,513 bytes); only the absolute repository path is substituted with `<task_repo>` in this
committed copy.

---

**APPROVE** — submission 2 satisfies the SETUP-01 follow-up slice. R1 and R2 are closed; no new blocking finding was established.

Reviewed HEAD `a82e466491b8352262f497f79e0e0d172a571c50` plus the frozen working tree. All seven slice hashes and all 34 manifest file hashes match. The [round-2 manifest](<<task_repo>/docs/reports/omp-setup-01-commitlint/evidence/manifest-round2.json>) has SHA-256 `34ebf5c37dd17bf863c57589406f41e99252e821087df5127c17bf11806720e1`. No files were changed.

- **R1 — Major, formerly blocking; SCN-305: CLOSED.** [ci.yml:9](<<task_repo>/.github/workflows/ci.yml:9>) includes `edited` alongside the default activities. The configuration now schedules base-dependent lint following retargeting, consistent with [GitHub’s event documentation](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#pull_request) and [edited-event schema](https://github.com/octokit/webhooks/blob/main/payload-schemas/api.github.com/pull_request/edited.schema.json). I independently verified the YAML and reproduced the unchanged-head/two-base result: exit 0 with the invalid ancestor excluded, exit 1 when applicable.
- **R2 — Minor, nonblocking; record provenance: CLOSED.** The failed lookup remains byte-identical. The amendment identifies the successful lookup’s later recapture, and the corrected `-v` invocation matches the retained focused log. This does not independently attest the claimed earlier successful execution.

| Criterion | Result | Supporting observation |
|---|---|---|
| SCN-301 | PASS | Scoped/unscoped subjects and proposed-message validation succeed. |
| SCN-302 | PASS | Body-only reference fails with the required-format diagnostic. |
| SCN-303 | PASS | Unknown references fail; feature rows, prose duplicates and foreign links are excluded. |
| SCN-304 | PASS | Invalid ancestor is reported; adoption baseline is exempt. |
| SCN-305 | PASS | Exact topic range selected; retarget trigger repaired. |
| SCN-306 | PASS | Invalid merge/side-branch messages fail; conforming merge succeeds. |
| SCN-307 | PASS | Historical map governs despite a repaired working-tree map. |
| SCN-308 | PASS | Missing revisions and real shallow history return operational exit 2 without success output. |

I independently ran **20 message/parser tests**, **12 read-only history probes**, YAML validation, positive/negative message validation, full-history lint (**four commits**), the current base-to-HEAD audit (**one checkpoint commit**), Ruff lint/format, and `git diff --check`. All matched expected outcomes.

The retained evidence supports **28 focused passes**, **135 full-suite passes**, **135 network-denied passes**, and successful fixture verification. I accepted those as matching-content evidence; I did not recreate temporary repositories or regenerate fixtures.

Product ports, schemas, proposal/acceptance separation, freshness semantics, 501 behavior and generated fixtures are unchanged. No invariant regression was established.

Hosted execution—including `edited`—required-check configuration, and the future post-slice-commit range audit remain **NOT VERIFIED**, as publication follow-ups outside this snapshot approval. This verdict does not close issue #8 or attest human labeling or link decisions.