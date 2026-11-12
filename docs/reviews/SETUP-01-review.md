# SETUP-01 commit-reference enforcement — independent review, round 1

**Task:** SETUP-01 (#8) follow-up slice; **submission 1** (attempt 2 — attempt 1 failed *without a
verdict* on 2026-11-12T00:26:39Z when the workspace had no credits; infrastructure failure, no
submission consumed).
**Reviewer:** Codex, model `gpt-6.1-sol`, reasoning effort `xhigh`, read-only sandbox —
`codex exec` session `01a1cdd5-57e9-76a2-b48a-9a6dae4e4674`, 2026-11-12T03:37:53Z → 03:44:42Z
(409.7 s), exit 0.
**Reviewed snapshot:** HEAD `a82e466491b8352262f497f79e0e0d172a571c50` plus the uncommitted slice;
packet v1.1 = v1 (sha256 `2c684345a35370199ece5dbf6f9b7ae2f2daf82ae0aa797aa31032e784388315`) plus
`packets/review-1-addendum.md` (sha256 `3d9ea9b997a651ff5dd352c35a34dde4929722294453a2d241d686504abd3a33`).
The reviewer re-verified all ten dirty-file hashes and changed no files.
**Verdict:** REQUEST_CHANGES — R1 (major, blocking: the bare `pull_request` trigger omitted `edited`,
so a PR retargeted to a new base was never re-checked) and R2 (minor, nonblocking: two record
discrepancies). All eight scenarios PASS.
**Dispositions (coordinator):** R1 repaired in `.github/workflows/ci.yml`
(`types: [opened, synchronize, reopened, edited]`) plus a clarifying `CONTRIBUTING.md` sentence;
recheck evidence `probes/r1_two_base_repro.py`, `evidence/repair1-r1-repro.log`,
`evidence/repair1-yaml-check.log`. R2 repaired in the records: `evidence/issue8-verified.log`
attaches the successful `gh` verification, the retained `evidence/issue8.log` stays unmodified with
an erratum in `PROMPT_LOG.md`, and `IMPLEMENTATION.md` E1 now names the captured `-v` invocation.
Resubmission is **submission 2 of 7**.

The verdict below is copied verbatim from the reviewer's final message (raw file sha256
`257acec1b808910cb46fc0e1c62b8172bf470352f2cf62eea18356e42bf2b882`); only the absolute repository path is substituted with `<task_repo>` in this committed copy.

---

**REQUEST_CHANGES** — the CLI criteria pass, but the CI workflow misses PR target changes.

Reviewed at `2026-11-12T03:43:49Z`: HEAD `a82e466491b8352262f497f79e0e0d172a571c50` plus the uncommitted slice. All ten dirty-file hashes match packet §3. The original 49,619-byte packet matches SHA-256 `2c684345a35370199ece5dbf6f9b7ae2f2daf82ae0aa797aa31032e784388315`. No files were changed.

**R1 — Major, blocking: rerun commit lint when a PR’s target changes.**

- **Location:** [ci.yml:6](<<task_repo>/.github/workflows/ci.yml:6>), together with the base-dependent invocation at line 28.
- **Obligation:** SETUP-01’s CI integration must check the commits applicable to the actual PR head and base; related criterion SCN-305.
- **Expected:** Changing the target branch schedules lint against the new base.
- **Actual:** The bare `pull_request:` declaration runs for `opened`, `synchronize`, and `reopened`, excluding `edited`. Base changes are represented by the edited event. Consequently, CI does not schedule validation of the newly applicable range. This conclusion follows from the configuration and documented event semantics; hosted behavior was not exercised. ([GitHub Actions events](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#pull_request), [edited-event schema](https://github.com/octokit/webhooks/blob/main/payload-schemas/api.github.com/pull_request/edited.schema.json))
- **Reproduction:** Using a retained test repository, the unchanged head passes against a base containing an unlinked ancestor, then fails against the adoption baseline because that ancestor becomes applicable. The range calculation correctly detects the difference.
- **Smallest correction/recheck:** Include `edited` alongside the existing default activity types. Inspect the revised trigger and repeat the same-head/two-base case. Actual hosted event execution remains a publication follow-up.

The complete canonical acceptance assessment is:

| Criterion | Result | Evidence |
|---|---|---|
| SCN-301 | PASS | Scoped/unscoped subjects and proposed-message validation succeed. |
| SCN-302 | PASS | Body-only reference fails with the required-format diagnostic. |
| SCN-303 | PASS | Unknown references fail; feature rows and prose duplicates are excluded. |
| SCN-304 | PASS | Earlier invalid commit is reported; legacy baseline is exempt. |
| SCN-305 | PASS — CLI | Diverged-base selection includes exactly the two expected topic commits. CI lifecycle gap is R1. |
| SCN-306 | PASS | Invalid merge and side-branch messages fail; conforming merge succeeds. |
| SCN-307 | PASS | Historical map mismatch fails despite the repaired working-tree map. |
| SCN-308 | PASS | Missing revisions and a real shallow repository return operational exit 2 without claiming success. |

I independently ran 20 message/parser pytest cases, nine read-only retained-history probes, message validation, full-history lint (**four commits**), the current `f34ae07..HEAD` range (**one checkpoint commit**), Ruff lint/format, and `git diff --check`. All matched their expected outcomes.

The supplied raw logs support **28 focused passes**, **135 full-suite passes**, **135 network-denied passes**, and successful fixture verification. Those complete runs were accepted as matching-snapshot evidence; I did not recreate temporary repositories or regenerate fixtures.

**R2 — Minor, nonblocking: checkpoint provenance needs reconciliation.**

[PROMPT_LOG.md:33](<<task_repo>/docs/reports/omp-setup-01-commitlint/PROMPT_LOG.md:33>) claims successful `gh` verification, while the retained `issue8.log` records exit 4 because authentication was unavailable. I requested the successful result; none was supplied during this review. Independently, the public [issue #8](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/8) supports the story association. Attach the successful historical result or append an erratum, preserving the raw log. Also record the focused log’s actual `-v` invocation rather than `-q`. These are record discrepancies outside the implementation slice.

Product ports, schemas, proposal/acceptance separation, freshness semantics, 501 behavior, and generated fixtures are unchanged. No invariant regression was established, and this review makes no new human-labeling attestation.

Hosted execution, required-check configuration, and the future slice-commit range audit remain unverified. I have no objection to the proposed #8 references or record-only commits 2–3; those records should preserve the tested revisions and distinguish this verdict from future execution evidence.