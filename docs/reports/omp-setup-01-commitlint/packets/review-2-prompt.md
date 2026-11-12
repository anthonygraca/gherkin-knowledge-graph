# Independent CTA implementation review — packet, submission 2 of 7 (round 2)

- **Task:** SETUP-01 follow-up slice — commit-reference enforcement (roadmap `SETUP-01`, GitHub issue #8).
- **Reviewer:** mandatory independent review, model `gpt-6.1-sol`, reasoning effort `xhigh`, read-only sandbox.
- **Coordinator (claims below):** OMP, model `vllm/deepseek-ai/DeepSeek-V4.1-Flash`, thinking `max`.
- **Packet assembled (UTC):** 2026-11-12T03:59:07Z. Snapshot frozen at assembly; no in-scope file is edited between this packet and the review call.
- **Repository (reviewed in place, read-only):** <task_repo>
- **External run directory (raw logs):** /tmp/cta-omp-setup-01
- **Round history:** submission 1 = attempt 1 (2026-11-12T00:26:39Z, no verdict — workspace out of credits) + attempt 2 (03:37:53Z→03:44:42Z, exit 0,**REQUEST_CHANGES**: R1 blocking, R2 nonblocking; all eight scenarios PASS) → repaired (see §0). This is **submission 2 of 7**.
- **Snapshot v2 identity (slice, in-scope for the proposed commit 1):** `.github/workflows/ci.yml` `3bc4fc40e752fd182b326fe25fd6b8b700531ec9fa5f660a844561db752bf924`, `AGENTS.md` `468d2d2bd4fe3cd4f473c8c3de406108147b68ea21061aea200134133c9cd8a6`, `CONTRIBUTING.md` `89b45205c979923102f81b95fa3a22b220529a2c037839860edc8a3b888aced6`, `tools/commitlint.py` `e39e523cba087db8ca97f9fbdc138bc476028b650ab00359aa15ffbe98714c29`, `backend/tests/test_commitlint.py` `12cb9504cde7fdfcd7a3dc394bd85978e03c7b58b46a7fabf0cc6a0c38431620`, `docs/stories/SETUP-01.feature` `db2c154567aa96c9492de684c8fccc0b63488ff750987b456a99a7fc97b9c70f`, `docs/stories/SETUP-01.md` `ea742d4b78265a4cc69a56e380fb3e5bab28c51efefd592091e95deb3eac0840`. Changed versus round 1: `ci.yml` (R1 fix) and `CONTRIBUTING.md`; the other five files are unchanged.

## 0. Round 1 verdict and dispositions

**Your round-1 verdict (verbatim; raw sha256 `257acec1b808910cb46fc0e1c62b8172bf470352f2cf62eea18356e42bf2b882`; committed copy `docs/reviews/SETUP-01-review.md`):**

> **REQUEST_CHANGES** — the CLI criteria pass, but the CI workflow misses PR target changes.
> 
> Reviewed at `2026-11-12T03:43:49Z`: HEAD `a82e466491b8352262f497f79e0e0d172a571c50` plus the uncommitted slice. All ten dirty-file hashes match packet §3. The original 49,619-byte packet matches SHA-256 `2c684345a35370199ece5dbf6f9b7ae2f2daf82ae0aa797aa31032e784388315`. No files were changed.
> 
> **R1 — Major, blocking: rerun commit lint when a PR’s target changes.**
> 
> - **Location:** [ci.yml:6](<<task_repo>/.github/workflows/ci.yml:6>), together with the base-dependent invocation at line 28.
> - **Obligation:** SETUP-01’s CI integration must check the commits applicable to the actual PR head and base; related criterion SCN-305.
> - **Expected:** Changing the target branch schedules lint against the new base.
> - **Actual:** The bare `pull_request:` declaration runs for `opened`, `synchronize`, and `reopened`, excluding `edited`. Base changes are represented by the edited event. Consequently, CI does not schedule validation of the newly applicable range. This conclusion follows from the configuration and documented event semantics; hosted behavior was not exercised. ([GitHub Actions events](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#pull_request), [edited-event schema](https://github.com/octokit/webhooks/blob/main/payload-schemas/api.github.com/pull_request/edited.schema.json))
> - **Reproduction:** Using a retained test repository, the unchanged head passes against a base containing an unlinked ancestor, then fails against the adoption baseline because that ancestor becomes applicable. The range calculation correctly detects the difference.
> - **Smallest correction/recheck:** Include `edited` alongside the existing default activity types. Inspect the revised trigger and repeat the same-head/two-base case. Actual hosted event execution remains a publication follow-up.
> 
> The complete canonical acceptance assessment is:
> 
> | Criterion | Result | Evidence |
> |---|---|---|
> | SCN-301 | PASS | Scoped/unscoped subjects and proposed-message validation succeed. |
> | SCN-302 | PASS | Body-only reference fails with the required-format diagnostic. |
> | SCN-303 | PASS | Unknown references fail; feature rows and prose duplicates are excluded. |
> | SCN-304 | PASS | Earlier invalid commit is reported; legacy baseline is exempt. |
> | SCN-305 | PASS — CLI | Diverged-base selection includes exactly the two expected topic commits. CI lifecycle gap is R1. |
> | SCN-306 | PASS | Invalid merge and side-branch messages fail; conforming merge succeeds. |
> | SCN-307 | PASS | Historical map mismatch fails despite the repaired working-tree map. |
> | SCN-308 | PASS | Missing revisions and a real shallow repository return operational exit 2 without claiming success. |
> 
> I independently ran 20 message/parser pytest cases, nine read-only retained-history probes, message validation, full-history lint (**four commits**), the current `f34ae07..HEAD` range (**one checkpoint commit**), Ruff lint/format, and `git diff --check`. All matched their expected outcomes.
> 
> The supplied raw logs support **28 focused passes**, **135 full-suite passes**, **135 network-denied passes**, and successful fixture verification. Those complete runs were accepted as matching-snapshot evidence; I did not recreate temporary repositories or regenerate fixtures.
> 
> **R2 — Minor, nonblocking: checkpoint provenance needs reconciliation.**
> 
> [PROMPT_LOG.md:33](<<task_repo>/docs/reports/omp-setup-01-commitlint/PROMPT_LOG.md:33>) claims successful `gh` verification, while the retained `issue8.log` records exit 4 because authentication was unavailable. I requested the successful result; none was supplied during this review. Independently, the public [issue #8](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/8) supports the story association. Attach the successful historical result or append an erratum, preserving the raw log. Also record the focused log’s actual `-v` invocation rather than `-q`. These are record discrepancies outside the implementation slice.
> 
> Product ports, schemas, proposal/acceptance separation, freshness semantics, 501 behavior, and generated fixtures are unchanged. No invariant regression was established, and this review makes no new human-labeling attestation.
> 
> Hosted execution, required-check configuration, and the future slice-commit range audit remain unverified. I have no objection to the proposed #8 references or record-only commits 2–3; those records should preserve the tested revisions and distinguish this verdict from future execution evidence.

**Coordinator dispositions:**

- **R1 (major, blocking) — repaired and rechecked.** Validated: GitHub's default `pull_request` activity
  types are `opened`, `synchronize`, `reopened`; a retargeted base fires `edited`. The trigger in
  `.github/workflows/ci.yml` is now:

  ```yaml
  on:
    push:
      branches: [main]
    pull_request:
      # Base-branch retargeting fires `edited`, not `synchronize`; the newly applicable
      # commit range must be checked again (independent review finding R1).
      types: [opened, synchronize, reopened, edited]
  ```

  `CONTRIBUTING.md` now adds: "The `edited` activity is included, so a PR retargeted to a different
  base is re-checked against its new base." Recheck (same head, two bases):
  `probes/r1_two_base_repro.py` → base excluding the unlinked ancestor = exit 0; base = adoption
  baseline (ancestor applicable) = exit 1 flagging `65daeff2…` (`evidence/repair1-r1-repro.log`).
  Trigger structure validated with PyYAML (`evidence/repair1-yaml-check.log`). Hosted event
  execution remains a publication follow-up.
- **R2 (minor, nonblocking) — repaired in the records.** `evidence/issue8-verified.log` attaches the
  successful `gh` verification (the retained `evidence/issue8.log` stays unmodified; the exit-4
  failure was the eval subprocess lacking `GH_TOKEN`, explained in `PROMPT_LOG.md` §5). The
  `-v` invocation is now recorded for E1 (an earlier `-q` run gave the same 28 passes).
- **Regressions:** none expected — the R1 fix touches only the workflow trigger and one sentence of
  prose; the checker, tests, and story files are unchanged from the snapshot you already verified.

## 1. Story

**Story id and issue (verified against GitHub via `gh`, 2026-11-12T00:19:29Z and re-captured 2026-11-12T03:51:46Z):** **#8** — "SETUP-01 — Initial repository setup and commit↔issue traceability"; https://github.com/anthonygraca/gherkin-knowledge-graph/issues/8; OPEN · label `user-story` · milestone **#3 "M0"** · parent **#7 "F-01 Foundation"**; `updatedAt` 2026-11-11T03:40:23Z. Issue-map row (committed): `SETUP-01 | #8 | F-01 | M0 | shared`.

**Milestone ceiling:** M0 maintenance slice; no later-milestone capability. Follow-up slice; `Refs #8`, never `Closes #8`.

**Owner:** shared platform. **Dependency:** fixed adoption baseline `efa824b…` (ancestors exempt; not advanced).

**Provenance:** the slice was authored by a prior session (record in §1 story file); the coordinator resumed and re-verified it (round 1) and repaired R1/R2 (round 2). No content changes were made by the coordinator to the five unchanged slice files.

**Preserved dirty work (not in this slice):** `README.md`, `prompts/omp-codex-agentic-loop.md`, `prompts/lifecycle-traceability-handoff.md`.

**Proposed commits (branch `ci/8-commit-reference-enforcement`, base `f34ae07`; checkpoint `a82e466` already on the branch contains records only):**

1. `ci(traceability): [issue #8] enforce commit references in CI` — the slice (message unchanged from round 1; revalidated at freeze). Now includes the R1 fix.
2. `docs(review): [issue #8] record the independent review of the commit-reference slice` — verdict copies + dispositions (record-only).
3. `docs(reports): [issue #8] record the commit-reference slice verification and run records` — amended reports, evidence, STATUS (record-only).

### Story record (full text of `docs/stories/SETUP-01.md`, sha256 ea742d4b78265a4cc69a56e380fb3e5bab28c51efefd592091e95deb3eac0840)

# SETUP-01 — commit-reference enforcement follow-up

**Story:** [SETUP-01, #8](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/8).
**Owner:** shared platform. **Milestone:** M0 maintenance; no later product capability.
**Source:** the owner's request to add CI commit-reference lint from this point forward and use
`<type>[optional scope]: [issue #x] <description>`. This implements the repository's existing
commit-to-work-item traceability obligation. It is a follow-up slice, not a restatement or closure
of every acceptance criterion on the original setup issue.

The canonical behavioral criteria for this slice are in [SETUP-01.feature](SETUP-01.feature).
The owner specified the format and prospective scope. Independent review and hosted CI results
must be recorded separately; neither this specification nor a local test pass asserts those approvals.
Use `Refs #8` when delivering this slice, not `Closes #8` on the basis of this slice alone.

## Design and scope

`tools/commitlint.py` uses Python's standard library and local Git history. The primary issue comes
from the subject; optional body references can name additional served issues. Registration is checked
against the story/task tables in the issue map at each commit. This is an offline registration check,
not live GitHub verification or proof that an issue's intent matches the implementation.

The adoption baseline is the existing M0 merge, `efa824b5b225db74c7ddba50365dad918d3212cc`.
Its ancestors are exempt. New history, including real merge commits, must conform. The CI workflow
checks actual PR heads against their bases and checks all post-adoption history on `main` pushes.
It excludes only GitHub's synthetic PR test merge, not actual contributor merge commits.

No schema or fixture changes, product features, runtime dependencies, GitHub writes, historical
rewrites, automatic issue closure, or branch-protection changes belong to this implementation.
The required-status-check setting is a separate repository administration step documented in
[CONTRIBUTING.md](../../CONTRIBUTING.md#commit-reference-ci-gate-setup-01-8).

## Verification map

These are substantive pytest checks, not direct Gherkin bindings. All selectors below are in
`backend/tests/test_commitlint.py`; the temporary Git repositories and expected outcomes are
hand-specified independently of the linter's output.

| Scenario | Test selectors | Evidence scope |
| --- | --- | --- |
| SCN-301 | `test_accepts_issue_linked_messages`; `test_message_file_can_be_checked_before_commit` | Optional scope, primary issue, supplementary references, pre-commit validation. |
| SCN-302 | `test_rejects_untraceable_messages` | Missing/malformed subjects, invalid numbers, unsupported types, temporary/default merge messages. |
| SCN-303 | `test_issue_map_accepts_only_story_and_task_entries`; `test_rejects_untraceable_messages` | Registered local story/task IDs, wrong repository links, unknown primary/supplementary references. |
| SCN-304 | `test_grandfathers_legacy_history_but_checks_every_new_commit` | Real temporary Git history; a good HEAD does not conceal an earlier invalid commit. |
| SCN-305 | `test_pr_range_excludes_diverged_base_and_includes_all_branch_commits` | Branch range selection after divergence. |
| SCN-306 | `test_real_merge_commits_must_follow_the_convention`; `test_side_branch_failure_is_not_hidden_by_a_valid_merge` | Real two-parent merges, valid and invalid cases, side-branch ancestry. |
| SCN-307 | `test_range_uses_issue_map_at_each_commit` | Historical map content, independent of later working-tree changes. |
| SCN-308 | `test_missing_revisions_and_shallow_history_fail_closed` | Missing head/base and a real shallow clone produce operational failures. |

Run the focused verification with:

```bash
uv run --offline --project backend pytest backend/tests/test_commitlint.py -q
python tools/commitlint.py --message-file /tmp/commit-message.txt
python tools/commitlint.py
```

The broader offline suite, fixture verification, and Ruff gates remain required. Real GitHub Actions
execution, remote issue accuracy, and required-check configuration must be verified on GitHub after
publication; local test results do not establish them.

## Local verification record

Recorded at `2026-11-11T22:47:40.631331+00:00` for the uncommitted working tree based on
`efa824b5b225db74c7ddba50365dad918d3212cc`, with the relevant file hashes below. These results
include the new uncommitted files; they are not results for the unchanged base commit.

| Command | Observed result |
| --- | --- |
| `uv run --offline --project backend pytest backend/tests/test_commitlint.py -q` | 28 passed. |
| `uv run --offline --project backend pytest backend/tests -q` | 135 passed; existing FastAPI/TestClient deprecation warning. |
| `uv run --offline --project backend python tools/fixturectl.py verify` | Exit 0; fixture generation reproducible and committed artifacts current. |
| `uv run --offline --project backend ruff check .` | All checks passed. |
| `uv run --offline --project backend ruff format --check .` | 35 files already formatted. |
| `python tools/commitlint.py --message-file /tmp/cta-commitlint-message.txt` | Exit 0; the proposed `ci(traceability): [issue #8] enforce commit references in CI` message passed. |
| `python tools/commitlint.py` | Exit 0; zero post-adoption commits yet. New-history behavior is exercised by the temporary-repository tests above. |
| `git diff --check` | Exit 0. |

| Artifact | SHA-256 |
| --- | --- |
| `tools/commitlint.py` | `e39e523cba087db8ca97f9fbdc138bc476028b650ab00359aa15ffbe98714c29` |
| `backend/tests/test_commitlint.py` | `12cb9504cde7fdfcd7a3dc394bd85978e03c7b58b46a7fabf0cc6a0c38431620` |
| `.github/workflows/ci.yml` | `72a99fe2f0a45e24d1709b7b9e9a1840d32a2236876ae448d82163aa987b2cdd` |
| `docs/stories/SETUP-01.feature` | `db2c154567aa96c9492de684c8fccc0b63488ff750987b456a99a7fc97b9c70f` |

No commit, publication, independent approval, or hosted check was produced in this implementation
session. The story association comes from the repository's issue map; live issue contents were
unavailable to this session. Required-check configuration remains unverified.


## 2. Acceptance

**Canonical criteria:** `docs/stories/SETUP-01.feature` (below, verbatim; sha256 db2c154567aa96c9492de684c8fccc0b63488ff750987b456a99a7fc97b9c70f). No criteria changed between rounds. No direct Gherkin runner; scenario→pytest selector mapping as before. R1 is the CI half of SCN-305's implementation ("Pull request history is selected from the actual branch") — the range logic passed round 1; the missing re-trigger on retargeting is now fixed.

**Applicable repository constraints:** unchanged from round 1 (offline default; no fixtures/schema changes; no `SCHEMA_VERSION` bump; commit subjects conform; generated files untouched).

**Required checks:** focused pytest, full offline suite (+ network-denied run in round 1), `fixturectl verify`, ruff check/format, `git diff --check`, commitlint modes (all rerun at this freeze — §5).

### Canonical criteria (full text)

```gherkin
# Follow-up acceptance slice for SETUP-01 (#8): commit-reference enforcement.
# Verified by pytest selectors in SETUP-01.md; no direct Gherkin runner bindings.
@SETUP-01 @issue-8 @M0
Feature: SETUP-01: Enforce traceability for new commits
  As a contributor, I want every new commit to name a registered work item
  so reviewers can trace repository changes to their intended purpose.

  Rule: New commit subjects identify their primary story or task

    @SCN-301
    Scenario: A contributor uses the new subject format
      Given issue 8 is registered as a story in the issue map
      When a commit message is "ci(traceability): [issue #8] enforce commit references"
      Then commit lint succeeds
      And the same message without the optional scope also succeeds

    @SCN-302
    Scenario: A body-only reference cannot replace the subject reference
      Given a commit subject is "ci: enforce commit references"
      And its body contains "Refs #8"
      When commit lint checks the message
      Then it fails and describes the required subject format

    @SCN-303
    Scenario: A reference must identify a registered story or task
      Given issue 999 is absent from the story and task tables
      When issue 999 appears in the required subject reference or a body reference line
      Then commit lint fails
      And feature rows and duplicate numbers mentioned only in prose are not valid work items

  Rule: Adoption preserves historical commits and checks every new contribution

    @SCN-304
    Scenario: A correct final commit does not hide an earlier invalid commit
      Given a legacy commit without an issue reference is the fixed adoption baseline
      And an invalid new commit follows it
      And a valid new commit follows the invalid commit
      When commit lint checks the new history
      Then it reports the invalid new commit
      And it does not report the legacy commit

    @SCN-305
    Scenario: Pull request history is selected from the actual branch
      Given a topic branch and its target both contain the adoption baseline
      And both branches contain independent later commits
      When commit lint checks the topic head excluding the target history
      Then it checks every topic commit absent from the target
      And it excludes commits already reachable from the target

    @SCN-306
    Scenario: Real merge commits and their side branches retain traceability
      Given a new merge commit integrates a topic branch
      When either the merge message or a topic commit lacks the required issue reference
      Then commit lint fails
      And a conforming merge with conforming topic commits succeeds

  Rule: Validation uses attributable local inputs and fails on missing history

    @SCN-307
    Scenario: A later map edit cannot repair an invalid historical reference
      Given a new commit references an issue absent from its own issue map
      And the working tree later adds that issue
      When commit lint checks the commit
      Then it fails using the map at that commit

    @SCN-308
    Scenario: Missing Git history is not a passing check
      Given a selected revision is unavailable or the repository is shallow
      When commit lint checks the history
      Then it fails with an operational error
      And it does not claim the selected commits passed
```

## 3. Snapshot and diffs

- **Base:** `f34ae0738f3c6e6709f4ba29d12f99348c5cc5b5` (= `main` = `origin/main`). **HEAD:** `a82e466491b8352262f497f79e0e0d172a571c50` (record-only checkpoint).
- **Snapshot identity:** the working tree at the SHA-256 values below (freeze manifest; also `evidence/manifest-round2.json`).

| Status | Path | SHA-256 | Role |
|---|---|---|---|
| ` M` | `README.md` | `93b29debd0da44b249eb01d4acea34f9cc8d4f1cb5fbea77ff31dcba9ddfd419` | preserved |
| `??` | `prompts/lifecycle-traceability-handoff.md` | `7e54d0b1e6a16d45472e7195ed15ff36c28f8c5b99546a864d31527b2f8987e1` | preserved |
| ` M` | `prompts/omp-codex-agentic-loop.md` | `90dbf541fee77796e6f78dbd5250005d01060d4e298599e297ca5e218719ea1d` | preserved |
| ` M` | `docs/STATUS.md` | `8ed28ad3dacbf2cbe1820b43d2fd2a17792e37b56e522899977bb02ad10c30dd` | records |
| ` M` | `docs/reports/omp-setup-01-commitlint/IMPLEMENTATION.md` | `b3fa79c9fcb682ce5318dc5be357afb9ace5abb205b60d2972832ca64dc7440f` | records |
| ` M` | `docs/reports/omp-setup-01-commitlint/METRICS.md` | `77a9466f99d9cb40e4759560c5e2aecabdf664ee4f4ccb4ca800c30c38b0d065` | records |
| ` M` | `docs/reports/omp-setup-01-commitlint/PROMPT_LOG.md` | `2b627c82d0df728e1809e730b64adf5715050710370c815d31d7cfe4c38d5149` | records |
| `??` | `docs/reports/omp-setup-01-commitlint/evidence/freeze2-commitlint-message.log` | `1630d2eb2413f7ec84b7d9e91a48b4bed16cd441f82dd77dd7aed9f3aa8698a1` | records |
| `??` | `docs/reports/omp-setup-01-commitlint/evidence/freeze2-commitlint.log` | `a87ebb8891853de91edeec0a5af255dee506ac71acf9a40c10de1558ee59dd0a` | records |
| `??` | `docs/reports/omp-setup-01-commitlint/evidence/freeze2-diff-check.log` | `ba85614b577efe0d2fd81833ad581f4ba68f80ac2d835550fac976a8776b3026` | records |
| `??` | `docs/reports/omp-setup-01-commitlint/evidence/freeze2-fixture-verify.log` | `78f958ec7c280b98b4baab91868cc58b271d55642a095bbad5b21c2cfe2296a2` | records |
| `??` | `docs/reports/omp-setup-01-commitlint/evidence/freeze2-ruff-check.log` | `97483a17400c71949235e7cd23632f7602e6dea1c85b9fe8c5aef11e300b2ca8` | records |
| `??` | `docs/reports/omp-setup-01-commitlint/evidence/freeze2-ruff-format.log` | `9b4d3f1547ae2f04fe388907d3f42d20bbf23f969d59d19c208276fbdac1d9f1` | records |
| `??` | `docs/reports/omp-setup-01-commitlint/evidence/freeze2-suite-full.log` | `303d7628683cab2f2321b6e3d2aec2bca1ee9abf079424c419536e19852c044d` | records |
| `??` | `docs/reports/omp-setup-01-commitlint/evidence/issue8-verified.log` | `1a003afec5aa04c0a1aa39ce7bfe57f68ea29e93258fdf5dcfc8c59f8d557743` | records |
| `??` | `docs/reports/omp-setup-01-commitlint/evidence/repair1-commitlint.log` | `a87ebb8891853de91edeec0a5af255dee506ac71acf9a40c10de1558ee59dd0a` | records |
| `??` | `docs/reports/omp-setup-01-commitlint/evidence/repair1-diff-check.log` | `ba85614b577efe0d2fd81833ad581f4ba68f80ac2d835550fac976a8776b3026` | records |
| `??` | `docs/reports/omp-setup-01-commitlint/evidence/repair1-fixture-verify.log` | `78f958ec7c280b98b4baab91868cc58b271d55642a095bbad5b21c2cfe2296a2` | records |
| `??` | `docs/reports/omp-setup-01-commitlint/evidence/repair1-r1-repro.log` | `cd7a4ab98bc6a457a38642e88b3737ef959f31790dddfbb1f5e89fd8c35b3c3b` | records |
| `??` | `docs/reports/omp-setup-01-commitlint/evidence/repair1-ruff-check.log` | `97483a17400c71949235e7cd23632f7602e6dea1c85b9fe8c5aef11e300b2ca8` | records |
| `??` | `docs/reports/omp-setup-01-commitlint/evidence/repair1-ruff-format.log` | `9b4d3f1547ae2f04fe388907d3f42d20bbf23f969d59d19c208276fbdac1d9f1` | records |
| `??` | `docs/reports/omp-setup-01-commitlint/evidence/repair1-suite-full.log` | `97c416416e2821c6c49790e4a50dc95b807e6276adee12ee19e1f822e2c756de` | records |
| `??` | `docs/reports/omp-setup-01-commitlint/evidence/repair1-yaml-check.log` | `2f7f42664e3a82bfc28c4b903a39b8bc60e3a8466d28e19364e238b9dc7b5a7e` | records |
| `??` | `docs/reports/omp-setup-01-commitlint/evidence/review-1b-stderr.log` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | records |
| `??` | `docs/reports/omp-setup-01-commitlint/evidence/review-1b-summary.json` | `bf6dca2864511040fbc8a06ddb070d80523ea7b32c25159cf1fdb8233cd1f264` | records |
| `??` | `docs/reports/omp-setup-01-commitlint/packets/review-1-addendum.md` | `ea63f82b0700e9ab7c97821edffd307bb71b43d819adb6e6f428e285bf0b6f12` | records |
| `??` | `docs/reports/omp-setup-01-commitlint/probes/r1_two_base_repro.py` | `3983a5b39024c77ad0d5b2be7d75ea5c54dc6d929f93213f0cd3b0b8946021fd` | records |
| `??` | `docs/reports/omp-setup-01-commitlint/probes/yaml_check.py` | `fa211b5971a891e3b28d9f1de0a1c7dfa34d410b08e54698839faef7027f8f03` | records |
| `??` | `docs/reviews/SETUP-01-review.md` | `f32d18303eadf61bb039dfa32d80ea8447f5ed74c2b16ec26039e7032352bc62` | records |
| ` M` | `.github/workflows/ci.yml` | `3bc4fc40e752fd182b326fe25fd6b8b700531ec9fa5f660a844561db752bf924` | slice |
| ` M` | `AGENTS.md` | `468d2d2bd4fe3cd4f473c8c3de406108147b68ea21061aea200134133c9cd8a6` | slice |
| ` M` | `CONTRIBUTING.md` | `89b45205c979923102f81b95fa3a22b220529a2c037839860edc8a3b888aced6` | slice |
| `??` | `backend/tests/test_commitlint.py` | `12cb9504cde7fdfcd7a3dc394bd85978e03c7b58b46a7fabf0cc6a0c38431620` | slice |
| `??` | `docs/stories/SETUP-01.feature` | `db2c154567aa96c9492de684c8fccc0b63488ff750987b456a99a7fc97b9c70f` | slice |
| `??` | `docs/stories/SETUP-01.md` | `ea742d4b78265a4cc69a56e380fb3e5bab28c51efefd592091e95deb3eac0840` | slice |
| `??` | `tools/commitlint.py` | `e39e523cba087db8ca97f9fbdc138bc476028b650ab00359aa15ffbe98714c29` | slice |

### Cumulative task diff of modified slice files (vs `f34ae07`, includes the R1 fix)

```diff
diff --git a/.github/workflows/ci.yml b/.github/workflows/ci.yml
index da30627..92ed4f0 100644
--- a/.github/workflows/ci.yml
+++ b/.github/workflows/ci.yml
@@ -4,8 +4,38 @@ on:
   push:
     branches: [main]
   pull_request:
+    # Base-branch retargeting fires `edited`, not `synchronize`; the newly applicable
+    # commit range must be checked again (independent review finding R1).
+    types: [opened, synchronize, reopened, edited]
 
 jobs:
+  commit-reference:
+    name: Commit references
+    runs-on: ubuntu-latest
+    permissions:
+      contents: read
+    steps:
+      - uses: actions/checkout@v4
+        with:
+          fetch-depth: 0
+          # Lint actual PR commits, not GitHub's synthetic test-merge message.
+          ref: ${{ github.event.pull_request.head.sha || github.sha }}
+          persist-credentials: false
+
+      - uses: actions/setup-python@v5
+        with:
+          python-version: "3.12"
+
+      - name: Validate new commit subjects and issue references offline
+        env:
+          COMMIT_BASE: ${{ github.event.pull_request.base.sha }}
+        run: |
+          if [ -n "$COMMIT_BASE" ]; then
+            python tools/commitlint.py --base "$COMMIT_BASE"
+          else
+            python tools/commitlint.py
+          fi
+
   offline:
     name: Offline contract, fixture, and API tests
     runs-on: ubuntu-latest
diff --git a/AGENTS.md b/AGENTS.md
index db64b53..d145231 100644
--- a/AGENTS.md
+++ b/AGENTS.md
@@ -60,6 +60,7 @@ uv run --project backend python tools/fixturectl.py all      # regenerate fixtur
 uv run --project backend python tools/fixturectl.py verify   # fail if generated files are stale
 uv run --project backend ruff check .
 uv run --project backend ruff format --check .
+python tools/commitlint.py                                  # post-adoption commit references
 uv run --project backend uvicorn app.main:app --reload       # dev server (fixtures only)
 ```
 
@@ -68,23 +69,26 @@ uv run --project backend uvicorn app.main:app --reload       # dev server (fixtu
 Every commit MUST reference the work item it serves, using the repository convention:
 
 ```
-<type>(<scope>): <summary>
+<type>[(scope)]: [issue #N] <description>
 
 <why, not just what>
-
-Refs #<issue>
 ```
 
-* `Refs #<issue>` for partial work; `Closes #<issue>` only when the issue is genuinely complete
-  (its Gherkin acceptance criteria are tested). Reference every served item: `Refs #3, #4`.
+* The subject's `[issue #N]` is required; scope is optional, e.g.
+  `ci(traceability): [issue #8] enforce commit references` or `ci: [issue #8] lint commits`.
+* Optional body `Refs #N` lines identify additional served items, e.g. `Refs #3, #4`.
+  `Closes #N` is allowed only when the entire issue's criteria and required reviews are complete.
 * Types: `feat` `fix` `docs` `test` `refactor` `chore` `ci`.
 * Look up a roadmap id (`AS-02`, `FT-01`, …) in `docs/traceability-issue-map.md`. The roadmap id is
   the prefix of the issue title, so the map can always be rebuilt from the tracker.
-* A GitHub issue number is the reference of record. Do not add a parallel id scheme in the message:
-  `Refs #N` is what GitHub links on the issue timeline, and `Refs #(\d+)` is the machine-readable
-  form (it is not a `git interpret-trailers` key/value pair).
-* Pre-convention history (`ae859cd`, `204eb49`) is retro-attributed to SETUP-01 (#8) and must not
-  be rewritten.
+* A GitHub issue number is the reference of record. `tools/commitlint.py` checks the subject and
+  optional body references against story/task entries in the issue map at each checked commit.
+  It runs offline in CI; live issue accuracy and relevance remain review responsibilities.
+* The fixed adoption baseline `efa824b5b225db74c7ddba50365dad918d3212cc` and its ancestors are
+  exempt. Do not advance the baseline or rewrite history to satisfy the new format.
+  `ae859cd` and `204eb49` retain their historical SETUP-01 (#8) attribution.
+* Validate message files before committing and the full new range before publishing. Real merge
+  and squash commits follow the same format; GitHub's synthetic PR test merge is excluded.
 * Branches: `<type>/<issue>-<slug>`; PR title `<ID>: <summary>`; PR body `Closes #<issue>` or
   `Refs #<issue>`. Cross-boundary changes need a review from a second workstream.
 * `main` takes no direct commits once CI exists: work lands through a pull request.
@@ -124,7 +128,7 @@ Refs #<issue>
 4. `uv run --project backend pytest backend/tests` passes offline; `fixturectl.py verify` passes.
 5. `ruff check` and `ruff format --check` pass.
 6. Docs include how to invoke or demo the change; assumptions in freshness rules are stated.
-7. The commit message carries `Refs #<issue>` (see `CONTRIBUTING.md`).
+7. The commit subject carries `[issue #N]` and passes the commit-reference check (see `CONTRIBUTING.md`).
 
 ## Definition of done (per milestone)
 
diff --git a/CONTRIBUTING.md b/CONTRIBUTING.md
index 9a7ee90..c816c91 100644
--- a/CONTRIBUTING.md
+++ b/CONTRIBUTING.md
@@ -46,17 +46,68 @@ files describe the synthetic repository evaluated by CTA, not CTA's own acceptan
 ## Commit messages
 
 ```text
-<type>(<scope>): <summary>
+<type>[(scope)]: [issue #N] <description>
 
 <why, not just what>
-
-Refs #<issue>
 ```
 
-- `Refs #N` for partial work; `Closes #N` only when the issue is genuinely complete (acceptance criteria tested).
+- Scope is optional and, when present, uses parentheses: `ci(traceability): [issue #8] lint commits`
+  or `ci: [issue #8] lint commits`. Use a nonempty lowercase scope without spaces.
+- The subject must name one positive GitHub story/task issue number using the literal
+  `[issue #N]` syntax, followed by a nonempty description. A reference only in the body is insufficient.
 - Types: `feat` `fix` `docs` `test` `refactor` `chore` `ci`.
-- One work item per commit where practical; reference each served item (`Refs #3, #4`).
-- Pre-convention history, retro-attributed to SETUP-01: `ae859cd` (Initial commit), `204eb49` (user-story issue form).
+- One work item per commit where practical. Add `Refs #3, #4` in the body for additional served
+  issues. `Refs #N` for the subject's issue is allowed but not required. Use `Closes #N` only when
+  the entire issue is genuinely complete (acceptance criteria tested and required reviews complete).
+- Register issues in the **User stories** or **Task issues** tables of
+  [the issue map](docs/traceability-issue-map.md) before or in the same commit that references them.
+  Feature-only references, PR numbers, duplicates mentioned only in prose, and unknown numbers fail.
+
+### Commit-reference CI gate (SETUP-01, #8)
+
+The **Commit references** job runs on pull requests and pushes to `main`, using the standard-library
+Python tool `tools/commitlint.py`. It checks every applicable commit, including real merge commits,
+against the subject format and the issue map **at that commit**. Optional `Refs`/`Closes` lines
+are checked too. The check needs full local Git history but no package installation, API token,
+GitHub API call, or network access. It verifies registration in the map; reviewers still establish
+issue relevance, live tracker accuracy, acceptance, and whether `Closes` is justified.
+
+The fixed adoption baseline is `efa824b5b225db74c7ddba50365dad918d3212cc` (the existing M0 merge).
+That commit and all its ancestors are exempt; every later checked commit uses the new format,
+including the commit introducing this check. Do not advance the baseline to hide failures or
+rewrite old history. The older `ae859cd` and `204eb49` remain retro-attributed to SETUP-01.
+
+PR runs check commits reachable from the actual PR head but absent from its base, excluding legacy
+history; GitHub's synthetic test-merge commit is not a contribution. The `edited` activity is
+included, so a PR retargeted to a different base is re-checked against its new base. Push runs
+check all commits reachable from `main` after the adoption baseline. Missing revisions, a branch
+without the baseline, an unreadable issue map, or shallow history fail the check rather than
+silently passing.
+
+Run locally from the repository root:
+
+```bash
+python tools/commitlint.py --message-file /tmp/commit-message.txt  # before committing
+python tools/commitlint.py                                     # all post-baseline commits at HEAD
+python tools/commitlint.py --base origin/main --head HEAD        # proposed PR range
+```
+
+For example, save this message and validate it with `--message-file` before `git commit -F`:
+
+```text
+ci(traceability): [issue #8] enforce commit references in CI
+
+Reject unlinked future commits while preserving pre-adoption history.
+
+Refs #8
+```
+
+Use a conforming subject for squash/merge commits too; edit the platform's proposed message before
+merging. Default `Merge pull request ...`, `Revert ...`, and `fixup! ...` subjects fail. PR checks
+cannot validate a future merge message; the push check validates the actual landed commit.
+To block PR merges on failure, make **Commit references** a required status check in the `main`
+branch ruleset/protection settings after the workflow lands. Adding the workflow does not change
+those remote settings. See GitHub's [PR event semantics](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#pull_request).
 
 ## Branches
 
```

### Full text of new slice files (unchanged from round 1)

`tools/commitlint.py` (sha256 e39e523cba087db8ca97f9fbdc138bc476028b650ab00359aa15ffbe98714c29):

```python
#!/usr/bin/env python3
"""Offline commit format and issue-map validation for SETUP-01 (#8)."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

# The last commit before adoption. Never advance this to exempt later failures.
LEGACY_BASELINE = "efa824b5b225db74c7ddba50365dad918d3212cc"
ISSUE_MAP = "docs/traceability-issue-map.md"
ISSUE_URL = "https://github.com/anthonygraca/gherkin-knowledge-graph/issues/"
SUBJECT = re.compile(
    r"(?:feat|fix|docs|test|refactor|chore|ci)"
    r"(?:\([a-z0-9][a-z0-9._/-]*\))?: "
    r"\[issue #(?P<issue>[1-9][0-9]*)\] (?P<description>\S(?:[^\r\n]*\S)?)"
)
REFERENCE = re.compile(r"(?:Refs|Closes) #[1-9][0-9]*(?:, #[1-9][0-9]*)*")
EXPECTED = "<type>[optional scope]: [issue #N] <description>"


class LintError(RuntimeError):
    """Invalid Git range or unavailable traceability input; never silently skip it."""


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=False
    )
    if result.returncode:
        raise LintError(result.stderr.strip() or f"git {args[0]} failed")
    return result.stdout.rstrip("\n")


def known_issues(markdown: str) -> set[int]:
    """Read the issue column of story/task tables, excluding features and prose."""
    issues: set[int] = set()
    section = ""
    link = re.compile(r"\[#([1-9][0-9]*)\]\(" + re.escape(ISSUE_URL) + r"\1\)")
    for line in markdown.splitlines():
        if line.startswith("## "):
            section = line[3:].strip()
        if section not in {"User stories", "Task issues"} or not line.startswith("|"):
            continue
        columns = line.split("|")
        if len(columns) > 3 and (match := link.fullmatch(columns[2].strip())):
            issues.add(int(match[1]))
    if not issues:
        raise LintError(f"{ISSUE_MAP} has no recognized story/task issue entries")
    return issues


def check_message(message: str, issues: set[int]) -> list[str]:
    lines = message.splitlines()
    subject = lines[0] if lines else ""
    match = SUBJECT.fullmatch(subject)
    if not match:
        return [f"expected {EXPECTED}; e.g. ci(traceability): [issue #8] lint commits"]
    referenced = {int(match["issue"])}
    errors = []
    for line in lines[1:]:
        if re.match(r"^(?:Refs|Closes)\b", line):
            if not REFERENCE.fullmatch(line):
                errors.append(f"malformed reference line: {line!r}; use Refs #8 or Closes #8")
            else:
                referenced.update(int(number) for number in re.findall(r"#([0-9]+)", line))
    for issue in sorted(referenced - issues):
        errors.append(f"issue #{issue} is not a story/task in {ISSUE_MAP}")
    return errors


def resolve_commit(repo: Path, revision: str) -> str:
    return git(repo, "rev-parse", "--verify", "--end-of-options", f"{revision}^{{commit}}")


def commits_to_check(repo: Path, head: str, base: str | None, legacy_baseline: str) -> list[str]:
    if git(repo, "rev-parse", "--is-shallow-repository") == "true":
        raise LintError("full Git history is required; fetch with fetch-depth: 0")
    head_sha = resolve_commit(repo, head)
    legacy_sha = resolve_commit(repo, legacy_baseline)
    # Old branches can lint without rewriting history, but must include the adoption baseline.
    if git(repo, "merge-base", legacy_sha, head_sha) != legacy_sha:
        raise LintError("head must contain the adoption baseline; update the branch first")
    exclusions = [legacy_sha]
    if base is not None:
        base_sha = resolve_commit(repo, base)
        if git(repo, "merge-base", legacy_sha, base_sha) != legacy_sha:
            raise LintError("base must contain the adoption baseline")
        # PR bases can diverge from head; exclude their reachable history, not just HEAD~1.
        exclusions.append(base_sha)
    return git(repo, "rev-list", "--reverse", head_sha, "--not", *exclusions).splitlines()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd(), help="Git repository root")
    parser.add_argument("--base", help="exclude commits already reachable from this PR base")
    parser.add_argument("--head", default="HEAD", help="tip to check (default: HEAD)")
    parser.add_argument(
        "--message-file", type=Path, help="check a proposed message before committing"
    )
    args = parser.parse_args(argv)
    if args.message_file is not None and (args.base is not None or args.head != "HEAD"):
        parser.error("--message-file cannot be combined with a revision range")

    try:
        failures = []
        if args.message_file is not None:
            issues = known_issues((args.repo / ISSUE_MAP).read_text(encoding="utf-8"))
            failures = check_message(args.message_file.read_text(encoding="utf-8"), issues)
            count = 1
        else:
            commits = commits_to_check(args.repo, args.head, args.base, LEGACY_BASELINE)
            count = len(commits)
            for commit in commits:
                # Check the map at the commit being judged, not an unrelated working tree.
                issues = known_issues(git(args.repo, "show", f"{commit}:{ISSUE_MAP}"))
                message = git(args.repo, "show", "-s", "--format=%B", commit)
                failures.extend(
                    f"{commit[:12]}: {error}" for error in check_message(message, issues)
                )
        if failures:
            for failure in failures:
                print(f"commitlint: {failure}", file=sys.stderr)
            return 1
        print(f"commitlint: checked {count} {'message(s)' if args.message_file else 'commit(s)'}")
        return 0
    except (LintError, OSError, UnicodeError) as error:
        print(f"commitlint: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
```

`backend/tests/test_commitlint.py` (sha256 12cb9504cde7fdfcd7a3dc394bd85978e03c7b58b46a7fabf0cc6a0c38431620):

```python
"""SETUP-01 (#8): enforce future commit traceability without rewriting legacy history."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import commitlint
import pytest

ISSUE_MAP = """## Features
| F-01 | [#7](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/7) |
## User stories
| SETUP-01 | [#8](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/8) |
| FT-02 | [#19](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/19) |
The closed duplicate #33 must not become an allowed reference.
## Task issues
| Repair | [#5](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/5) |
"""


@pytest.mark.parametrize(
    "message",
    [
        "ci: [issue #8] enforce traceability",
        "fix(contracts): [issue #19] reject invalid proposals\n\nWhy this matters.\n\nRefs #8",
        "test(api/contracts): [issue #5] cover failure\n\nRefs #8, #19",
        "docs: [issue #8] explain the convention\n\nCloses #5",
    ],
)
def test_accepts_issue_linked_messages(message: str) -> None:
    assert commitlint.check_message(message, {5, 8, 19}) == []


@pytest.mark.parametrize(
    "message",
    [
        "ci: enforce traceability\n\nRefs #8",  # Old body-only reference is insufficient.
        "ci: [issue #0] invalid identifier",
        "ci: [issue #08] invalid identifier",
        "ci: [issue #N] placeholder",
        "ci: [issue #8] ",
        "ci(): [issue #8] empty scope",
        "unknown: [issue #8] unsupported type",
        "ci: [#8] wrong reference syntax",
        "ci: [issue #999] unregistered issue",
        "ci: [issue #8] valid subject\n\nRefs #999",
        "ci: [issue #8] valid subject\n\nRefs #8, #N",
        "ci: [issue #8] valid subject\n\nCloses #0",
        "fixup! ci: [issue #8] temporary commit",
        "Merge pull request #8 from example/branch",
        "",
    ],
)
def test_rejects_untraceable_messages(message: str) -> None:
    assert commitlint.check_message(message, {5, 8, 19})


def test_issue_map_accepts_only_story_and_task_entries() -> None:
    assert commitlint.known_issues(ISSUE_MAP) == {5, 8, 19}
    foreign_map = ISSUE_MAP.replace("anthonygraca/gherkin-knowledge-graph", "someone/else")
    with pytest.raises(commitlint.LintError):
        commitlint.known_issues(foreign_map)
    with pytest.raises(commitlint.LintError):
        commitlint.known_issues("missing issue tables")


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def commit(repo: Path, message: str) -> str:
    git(repo, "add", ".")
    git(repo, "commit", "--allow-empty", "-m", message)
    return git(repo, "rev-parse", "HEAD")


@pytest.fixture
def history(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, str]:
    # Isolate the synthetic history from the developer's signing/hooks/default branch settings.
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_SYSTEM", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_COUNT", "0")
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-b", "main")
    git(repo, "config", "user.name", "Commit lint tests")
    git(repo, "config", "user.email", "commitlint@example.invalid")
    git(repo, "config", "commit.gpgsign", "false")
    (repo / "docs").mkdir()
    (repo / commitlint.ISSUE_MAP).write_text(ISSUE_MAP, encoding="utf-8")
    legacy = commit(repo, "legacy message without a reference")
    monkeypatch.setattr(commitlint, "LEGACY_BASELINE", legacy)
    return repo, legacy


def test_grandfathers_legacy_history_but_checks_every_new_commit(history, capsys) -> None:
    repo, legacy = history
    assert commitlint.main(["--repo", str(repo)]) == 0
    bad = commit(repo, "forgot the issue")
    commit(repo, "ci: [issue #8] valid final commit")
    assert commitlint.main(["--repo", str(repo)]) == 1
    errors = capsys.readouterr().err
    assert bad[:12] in errors
    assert legacy[:12] not in errors


def test_pr_range_excludes_diverged_base_and_includes_all_branch_commits(history) -> None:
    repo, legacy = history
    git(repo, "checkout", "-b", "topic")
    first = commit(repo, "ci: [issue #8] topic change")
    second = commit(repo, "test: [issue #8] topic evidence")
    git(repo, "checkout", "main")
    commit(repo, "ci: [issue #8] independent base change")
    assert commitlint.commits_to_check(repo, "topic", "main", legacy) == [first, second]
    assert commitlint.main(["--repo", str(repo), "--base", "main", "--head", "topic"]) == 0


@pytest.mark.parametrize(
    ("merge_message", "expected"),
    [("Merge branch 'topic'", 1), ("chore(merge): [issue #8] integrate the change", 0)],
)
def test_real_merge_commits_must_follow_the_convention(history, merge_message, expected) -> None:
    repo, _ = history
    git(repo, "checkout", "-b", "topic")
    commit(repo, "ci: [issue #8] topic change")
    git(repo, "checkout", "main")
    git(repo, "merge", "--no-ff", "topic", "-m", merge_message)
    assert commitlint.main(["--repo", str(repo)]) == expected


def test_side_branch_failure_is_not_hidden_by_a_valid_merge(history, capsys) -> None:
    repo, _ = history
    git(repo, "checkout", "-b", "topic")
    bad = commit(repo, "unlinked branch change")
    git(repo, "checkout", "main")
    git(repo, "merge", "--no-ff", "topic", "-m", "chore: [issue #8] merge topic")
    assert commitlint.main(["--repo", str(repo)]) == 1
    assert bad[:12] in capsys.readouterr().err


def test_range_uses_issue_map_at_each_commit(history) -> None:
    repo, _ = history
    (repo / commitlint.ISSUE_MAP).write_text(ISSUE_MAP.replace("#19", "#29"), encoding="utf-8")
    commit(repo, "ci: [issue #19] reference absent from this snapshot")
    # A later working-tree edit must not make the bad historical reference pass.
    (repo / commitlint.ISSUE_MAP).write_text(ISSUE_MAP, encoding="utf-8")
    assert commitlint.main(["--repo", str(repo)]) == 1


def test_message_file_can_be_checked_before_commit(history, tmp_path: Path) -> None:
    repo, _ = history
    message = tmp_path / "message.txt"
    message.write_text("ci: [issue #8] lint future commits\n", encoding="utf-8")
    assert commitlint.main(["--repo", str(repo), "--message-file", str(message)]) == 0
    message.write_text("missing reference", encoding="utf-8")
    assert commitlint.main(["--repo", str(repo), "--message-file", str(message)]) == 1


def test_missing_revisions_and_shallow_history_fail_closed(history, tmp_path: Path) -> None:
    repo, _ = history
    assert commitlint.main(["--repo", str(repo), "--head", "missing"]) == 2
    assert commitlint.main(["--repo", str(repo), "--base", "missing"]) == 2
    shallow = tmp_path / "shallow"
    git(repo, "clone", "--depth", "1", repo.as_uri(), str(shallow))
    assert commitlint.main(["--repo", str(shallow)]) == 2
```

(`docs/stories/SETUP-01.feature` in §2; `docs/stories/SETUP-01.md` in §1.)

### Records changed in round 2 (readable in the repo)

`docs/reviews/SETUP-01-review.md` (round-1 verdict), amended `IMPLEMENTATION.md` (§9 dispositions, E1 correction), `PROMPT_LOG.md` (§5 amendment), `METRICS.md` (round-1 amendment), `docs/STATUS.md`, plus the new evidence/probe/packet files listed in the manifest above (or `probes/` for the two probe scripts).

## 4. Implementation context

Unchanged from round 1 except the trigger fix in §0. `tools/commitlint.py` is stdlib-only; `known_issues()` reads only the story/task tables; `check_message()` validates subject + `Refs`/`Closes` lines; `commits_to_check()` fails closed (shallow history, missing revisions, head/base without the baseline) and excludes the baseline plus everything reachable from a PR base; merge messages are checked like any other commit; exits 0/1/2. CI job: full-history checkout, actual PR head ref, Python 3.12, no installs, offline; PRs use `--base <base sha>`, `main` pushes use full-history mode; `edited` now included. Not touched: `fixtures/**`, `backend/app/**`, schemas, generated files.

## 5. Evidence

Round-1 table E1–E13 (unchanged files; still valid) plus the round-2 recheck and the final freeze gates:

| # | Command | Exit | Result | Evidence |
|---|---|---|---|---|
| E1 | focused pytest `-v` (earlier `-q` same result) | 0 | 28 passed | `evidence/focused-verbose.log` |
| E2 | full suite `-q` | 0 | 135 passed | `evidence/suite-full.log` |
| E3/E4 | network-denied suite + denial probe | 0 | 135 passed; denial effective | `evidence/suite-nonet.log`, `evidence/nonet-probe.log` |
| E5–E8 | fixture verify; ruff check; ruff format; `git diff --check` | 0 | reproducible; clean; 35 files; clean | `evidence/fixture-verify.log`, `evidence/ruff-check.log`, `evidence/ruff-format.log`, `evidence/diff-check.log` |
| E9–E11 | commitlint full history / message ok / message bad | 0 / 0 / 1 | 4 commits checked; message ok; negative rejected | `evidence/commitlint-*.log` |
| E12/E13 | pre-rewrite tip rejected; missing revision fails closed | 1 / 2 | `24810877f4d9` flagged; `Needed a single revision` | `evidence/commitlint-pre-rewrite-tip.log`, `evidence/commitlint-missing-revision.log` |
| F1 | `probes/r1_two_base_repro.py` (same head, two bases) | 0 | base=unlinked → exit 0; base=baseline → exit 1 (flag `65daeff2…`) | `evidence/repair1-r1-repro.log` |
| F2 | `probes/yaml_check.py` (trigger structure) | 0 | `pull_request.types == [opened, synchronize, reopened, edited]` | `evidence/repair1-yaml-check.log` |
| F3 | freeze battery (suite / fixture / ruff×2 / diff-check / commitlint / message) | all 0 | 135 passed; all clean; 4 commits; message ok | `evidence/freeze2-*.log` |

**Prior-round independent checks (from your verdict, which I do not restate as mine):** 20 message/parser pytest cases; nine read-only retained-history probes; message validation; full-history lint (four commits); `f34ae07..HEAD` range (one checkpoint commit); ruff lint/format; `git diff --check`.

**Scenario → executed node IDs (E1):** test_accepts_issue_linked_messages[ci: [issue #8] enforce traceability]
test_accepts_issue_linked_messages[fix(contracts): [issue #19] reject invalid proposals\n\nWhy this matters.\n\nRefs #8]
test_accepts_issue_linked_messages[test(api/contracts): [issue #5] cover failure\n\nRefs #8, #19]
test_accepts_issue_linked_messages[docs: [issue #8] explain the convention\n\nCloses #5]
test_rejects_untraceable_messages[ci: enforce traceability\n\nRefs #8]
test_rejects_untraceable_messages[ci: [issue #0] invalid identifier]
test_rejects_untraceable_messages[ci: [issue #08] invalid identifier]
test_rejects_untraceable_messages[ci: [issue #N] placeholder]
test_rejects_untraceable_messages[ci: [issue #8] ]
test_rejects_untraceable_messages[ci(): [issue #8] empty scope]
test_rejects_untraceable_messages[unknown: [issue #8] unsupported type]
test_rejects_untraceable_messages[ci: [#8] wrong reference syntax]
test_rejects_untraceable_messages[ci: [issue #999] unregistered issue]
test_rejects_untraceable_messages[ci: [issue #8] valid subject\n\nRefs #999]
test_rejects_untraceable_messages[ci: [issue #8] valid subject\n\nRefs #8, #N]
test_rejects_untraceable_messages[ci: [issue #8] valid subject\n\nCloses #0]
test_rejects_untraceable_messages[fixup! ci: [issue #8] temporary commit]
test_rejects_untraceable_messages[Merge pull request #8 from example/branch]
test_rejects_untraceable_messages[]
test_issue_map_accepts_only_story_and_task_entries
test_grandfathers_legacy_history_but_checks_every_new_commit
test_pr_range_excludes_diverged_base_and_includes_all_branch_commits
test_real_merge_commits_must_follow_the_convention[Merge branch 'topic'-1]
test_real_merge_commits_must_follow_the_convention[chore(merge): [issue #8] integrate the change-0]
test_side_branch_failure_is_not_hidden_by_a_valid_merge
test_range_uses_issue_map_at_each_commit
test_message_file_can_be_checked_before_commit
test_missing_revisions_and_shallow_history_fail_closed

**NOT RUN / limits:** hosted execution of the new job or its `edited` trigger (workflow not landed); required-status-check configuration; the post-commit `--base f34ae07 --head HEAD` slice audit (runs after approval).

## 6. Reviewer instructions (verbatim)

> You are the independent CTA implementation reviewer using GPT-6.1 Sol xhigh. Decide whether this exact snapshot satisfies the supplied story, every applicable Gherkin criterion, and repository invariants. Treat OMP's summaries and test results as claims to check against the supplied artifacts and targeted source inspection. Check proposal/accepted/evidence separation, real port compatibility, revision/content-hash semantics, honest errors/501s, independent oracle expectations, offline defaults, and generated-file discipline where relevant. Do not demand implementation of a later milestone. Do not edit files, implement repairs, regenerate fixtures, commit, or delegate. Ask OMP for missing runtime evidence; distinguish observed defects from hypotheses and unavailable checks. Return an AC-by-AC PASS, FAIL, or NOT VERIFIED assessment and actionable findings with stable IDs, severity, blocking status, AC/invariant, path/line, expected/actual behavior, and smallest correction/recheck. Keep optional suggestions and unrelated pre-existing defects separate. Return exactly one verdict: APPROVE, REQUEST_CHANGES, or NEEDS_INPUT. APPROVE requires every applicable criterion/check to be satisfied, no unresolved blocker, and the exact snapshot identified. In later rounds verify prior dispositions and regressions while retaining the complete acceptance assessment. A passing process, passing tests, or exhausted review limit is not approval. Agent review cannot attest human labeling or human link decisions.
