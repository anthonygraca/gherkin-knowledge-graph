# Independent CTA implementation review — packet, submission 1 of 7

- **Task:** SETUP-01 follow-up slice — commit-reference enforcement (roadmap `SETUP-01`, GitHub issue #8).
- **Reviewer:** mandatory independent review, model `gpt-6.1-sol`, reasoning effort `xhigh`, read-only sandbox.
- **Coordinator (claims below):** OMP, model `vllm/deepseek-ai/DeepSeek-V4.1-Flash`, thinking `max`.
- **Packet assembled (UTC):** 2026-11-12T00:26:17Z. Snapshot frozen at assembly; in-scope files are not edited between this packet and the review call. Continue to treat the coordinator's summaries and test results as claims to check.
- **Repository (reviewed in place, read-only):** <task_repo>
- **External run directory (raw logs):** /tmp/cta-omp-setup-01

## 1. Story

**Story id and issue (verified against GitHub via `gh` at 2026-11-12T00:19Z):**

- Issue: **#8** — “SETUP-01 — Initial repository setup and commit↔issue traceability”
- URL: https://github.com/anthonygraca/gherkin-knowledge-graph/issues/8
- State: OPEN · Label: `user-story` · Milestone: **#3 “M0 — Contract + fixture foundation”** · Parent: **#7 “F-01 Foundation — fixture oracles, contracts, and repo conventions” (open)** · `updatedAt` 2026-11-11T03:40:23Z.
- Issue-map row (docs/traceability-issue-map.md, committed): `SETUP-01 | #8 | F-01 | M0 | shared | Initial repository setup and commit↔issue traceability`.
- No open PRs exist for this slice; no branch for it exists yet.

**Milestone ceiling:** M0 maintenance slice; no later-milestone product capability. This slice is a follow-up that implements the repository's existing commit-traceability obligation; it deliberately does **not** claim to close every criterion on #8 (`Refs #8`, never `Closes #8`).

**Owner:** shared platform. **Dependency:** the fixed adoption baseline `efa824b5b225db74c7ddba50365dad918d3212cc` (existing M0 merge) — frozen; its ancestors are exempt. Do not advance it.

**Provenance note (material context):** the in-scope files were authored by a prior session; its verification record and claims are inside the story record reproduced below. The coordinator resumed the slice, reproduced every claim on base `f34ae07`, and made **no content edits** to in-scope files. Independently, the repository owner replaced the previous `main` tip — the default-message merge commit `24810877f4d990c0755a46c6d79a5d0f6d318f42` (`Merge pull request #41 …`) — with the rewritten merge commit `f34ae0738f3c6e6709f4ba29d12f99348c5cc5b5` (“docs(lifecycle): [issue #39] merge the lifecycle traceability change into main”; parents `efa824b…`, `3b25cd1…`; body: “Amended subject: the initial merge landed with GitHub's default message, which the commit-reference rule rejects.”). Push evidence: GitHub Actions push run 43124897661 (main, head `f34ae07…`, conclusion success, 2026-11-12T00:07:03Z). Consequence: the current check passes on `main` history (`commitlint: checked 3 commit(s)`, exit 0) instead of failing on the old tip (reproduced: `commitlint --head 24810877f4d990c0755a46c6d79a5d0f6d318f42` → exit 1, flags `24810877f4d9`; see §5).

**Scope / non-goals (from the story record):** offline, standard-library-only commit-format and issue-map-registration checker; CI job wiring; convention updates in AGENTS.md/CONTRIBUTING.md; story criteria and record. **Not in scope:** schema or fixture changes, product features, runtime dependencies, GitHub writes, historical rewrites, automatic issue closure, branch-protection settings, or any change to `main`.

**Preservation boundaries (dirty work that must NOT ride in this slice's commits):** `README.md`, `prompts/omp-codex-agentic-loop.md`, `prompts/lifecycle-traceability-handoff.md`. They remain uncommitted, untouched, and outside the reviewed scope. Known observation, not a defect of this slice: `README.md`'s uncommitted rewrite still shows the pre-adoption commit example (`Refs #19` without the `[issue #N]` subject) and status text that predates the M0 re-review approval; it needs its own work item.

**Proposed commits (branch `ci/8-commit-reference-enforcement`, base `f34ae07`), all referencing #8 only:**

1. `ci(traceability): [issue #8] enforce commit references in CI` — the slice below (message validated with `--message-file`, exit 0; included verbatim in §5).
2. `docs(review): [issue #8] record the independent review of the commit-reference slice` — verdict copy + dispositions (record-only, post-approval).
3. `docs(reports): [issue #8] record the commit-reference slice verification and status checkpoint` — run reports, `docs/STATUS.md`, and a dated evidence block appended to `docs/stories/SETUP-01.md` (record-only, post-approval).

The coordinator will run `python tools/commitlint.py --base f34ae07 --head HEAD` over the created range and include its output in the implementation report. Please state any objection to these references, or to the record-only changes in commits 2–3.

**Reconciliation of tracker prose:** the body of issue #8 predates the owner's format decision and still phrases the obligation as “`Refs #<issue>` or `Closes #<issue>`”. The canonical behavioral criteria for this slice are the reviewed Gherkin file below, which the owner specified; the slice does not close #8.

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

**Canonical criteria:** `docs/stories/SETUP-01.feature` (below, verbatim; sha256 db2c154567aa96c9492de684c8fccc0b63488ff750987b456a99a7fc97b9c70f). There is no direct Gherkin runner binding in this repository; each scenario maps to substantive pytest selectors (map in the story record; executed node IDs in §5). Scenario IDs `SCN-301`…`SCN-308` are stable and unique.

**Refinement disposition:** frozen by the owner's explicit format and prospective-scope instruction; independent implementation review is this call. Criteria have not changed across rounds (this is round 1).

**Applicable repository constraints (AGENTS.md / CONTRIBUTING.md as at the snapshot):** offline by default (no network/GPU/LLM/services in tests or default paths); no secrets in fixtures (none touched); generated files under `fixtures/` must not be hand-edited (none touched); no schema change → no `SCHEMA_VERSION` bump; contract-only endpoints stay 501 (untouched); commit subjects for the new commits must themselves conform (they will be checked).

**Required checks for this slice:** focused pytest (`backend/tests/test_commitlint.py`), the full offline backend suite, `fixturectl.py verify`, `ruff check`, `ruff format --check`, `git diff --check`, and the three `tools/commitlint.py` modes (full history, `--message-file`, range audit post-commit).

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

- **Base:** `f34ae0738f3c6e6709f4ba29d12f99348c5cc5b5` (equals local `main` and `origin/main`, verified with `git rev-parse` and `git ls-remote`). Working tree is dirty; the slice is uncommitted.
- **Snapshot identity:** per-file SHA-256 below, computed at packet assembly. There is no task commit yet; the snapshot is the working tree at these hashes.

| Status | Path | SHA-256 | In slice? |
|---|---|---|---|
| ` M` | `.github/workflows/ci.yml` | `72a99fe2f0a45e24d1709b7b9e9a1840d32a2236876ae448d82163aa987b2cdd` | yes |
| ` M` | `AGENTS.md` | `468d2d2bd4fe3cd4f473c8c3de406108147b68ea21061aea200134133c9cd8a6` | yes |
| ` M` | `CONTRIBUTING.md` | `64ee54c3cff5e3cd10b5554b977db24466c8e9a6831cdf08eb7595732777151a` | yes |
| ` M` | `README.md` | `93b29debd0da44b249eb01d4acea34f9cc8d4f1cb5fbea77ff31dcba9ddfd419` | NO — preserved |
| `??` | `backend/tests/test_commitlint.py` | `12cb9504cde7fdfcd7a3dc394bd85978e03c7b58b46a7fabf0cc6a0c38431620` | yes |
| `??` | `docs/stories/SETUP-01.feature` | `db2c154567aa96c9492de684c8fccc0b63488ff750987b456a99a7fc97b9c70f` | yes |
| `??` | `docs/stories/SETUP-01.md` | `ea742d4b78265a4cc69a56e380fb3e5bab28c51efefd592091e95deb3eac0840` | yes |
| `??` | `prompts/lifecycle-traceability-handoff.md` | `7e54d0b1e6a16d45472e7195ed15ff36c28f8c5b99546a864d31527b2f8987e1` | NO — preserved |
| ` M` | `prompts/omp-codex-agentic-loop.md` | `90dbf541fee77796e6f78dbd5250005d01060d4e298599e297ca5e218719ea1d` | NO — preserved |
| `??` | `tools/commitlint.py` | `e39e523cba087db8ca97f9fbdc138bc476028b650ab00359aa15ffbe98714c29` | yes |

### Cumulative task diff of modified in-scope files (verbatim, vs `f34ae07`)

```diff
diff --git a/.github/workflows/ci.yml b/.github/workflows/ci.yml
index da30627..769bf3b 100644
--- a/.github/workflows/ci.yml
+++ b/.github/workflows/ci.yml
@@ -6,6 +6,33 @@ on:
   pull_request:
 
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
index 9a7ee90..d557455 100644
--- a/CONTRIBUTING.md
+++ b/CONTRIBUTING.md
@@ -46,17 +46,66 @@ files describe the synthetic repository evaluated by CTA, not CTA's own acceptan
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
+history; GitHub's synthetic test-merge commit is not a contribution. Push runs check all commits
+reachable from `main` after the adoption baseline. Missing revisions, a branch without the baseline,
+an unreadable issue map, or shallow history fail the check rather than silently passing.
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

### Full text of new in-scope files

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

(`docs/stories/SETUP-01.feature` is reproduced verbatim in §2; `docs/stories/SETUP-01.md` in §1.)

## 4. Implementation context

- `tools/commitlint.py` — stdlib only; `SUBJECT`/`REFERENCE` regexes; `known_issues()` reads only the “User stories” and “Task issues” tables of `docs/traceability-issue-map.md` and requires exact canonical issue links; `check_message()` validates the subject and optional `Refs`/`Closes` lines; `commits_to_check()` fails closed on shallow history, missing revisions, or a head/base without the adoption baseline, and excludes `LEGACY_BASELINE` plus (for `--base`) everything reachable from the base; `main()` exits 0/1/2 (pass / findings / operational). Merge-commit messages are checked like any other commit (no exceptions for platform defaults).
- `.github/workflows/ci.yml` — new `commit-reference` job: full-history checkout (`fetch-depth: 0`), checkout `ref` = the actual PR head sha (or `github.sha` on pushes), Python 3.12, runs `tools/commitlint.py --base <PR base sha>` on PRs and full-history mode on `main` pushes. No dependencies installed, no token, offline.
- `AGENTS.md`, `CONTRIBUTING.md` — adopt `<type>[(scope)]: [issue #N] <description>` as the subject convention; document the checker, the fixed adoption baseline, PR/push scopes, the synthetic-test-merge exclusion, the required-status-check administration step, and updated definition-of-done wording.
- Targeted follow-up reads available to you in the read-only repo: `docs/traceability-issue-map.md` (tables), `.github/workflows/ci.yml`, `backend/tests/conftest.py` (adds `tools/` to `sys.path`, line ~29), `docs/stories/SETUP-01.md`, `docs/STATUS.md`.
- Not touched: `fixtures/**` (generated files verified current), `backend/app/**`, any schema surface, `docs/req`…: none. All in-scope content is hand-written; no generated file changed.

## 5. Evidence (coordinator-run; logs in the external run directory)

| # | Command (repo root) | Exit | Observed |
|---|---|---|---|
| E1 | `uv run --offline --project backend pytest backend/tests/test_commitlint.py -q` | 0 | 28 passed, 1 pre-existing deprecation warning |
| E2 | `uv run --offline --project backend pytest backend/tests -q` | 0 | 135 passed (107 existing + 28 new) |
| E3 | `unshare -rn -- backend/.venv/bin/python -m pytest backend/tests -q` | 0 | 135 passed under OS-level network denial |
| E4 | `unshare -rn -- python3 -c "<socket connect probe>"` | 0 | `network denied: [Errno 101] Network is unreachable` (denial effective) |
| E5 | `uv run --offline --project backend python tools/fixturectl.py verify` | 0 | fixture generation reproducible; committed files current |
| E6 | `uv run --offline --project backend ruff check .` | 0 | all checks passed |
| E7 | `uv run --offline --project backend ruff format --check .` | 0 | 35 files already formatted |
| E8 | `git diff --check` | 0 | clean |
| E9 | `python3 tools/commitlint.py` (full history at `HEAD`=`f34ae07`) | 0 | `commitlint: checked 3 commit(s)` — `2e9d201`, `3b25cd1`, `f34ae07` all conform |
| E10 | `python3 tools/commitlint.py --message-file <proposed commit-1 message>` | 0 | `commitlint: checked 1 message(s)` |
| E11 | `python3 tools/commitlint.py --message-file <body-only-reference message>` | 1 | rejected: expected subject format (negative case) |
| E12 | `python3 tools/commitlint.py --head 24810877f4d990c0755a46c6d79a5d0f6d318f42` (pre-rewrite tip, still a local object) | 1 | `commitlint: 24810877f4d9: expected <type>[optional scope]: [issue #N] <description>; …` — the rule detects the exact commit the owner repaired |
| E13 | `python3 tools/commitlint.py --head <mistyped-41-char SHA>` | 2 | `fatal: Needed a single revision` — missing revisions fail closed, not silently pass (this was a genuine first-attempt typo, recorded as-is) |

Environment: Linux x86_64, Python 3.12.16 (backend venv), uv 0.13.7, git 2.56.0. Evidence scope: this Linux/Python environment only.

**Scenario → executed evidence:** the story record maps SCN-301…SCN-308 to selectors in `backend/tests/test_commitlint.py`; the 28 executed node IDs recorded at E1 are:

test_accepts_issue_linked_messages[ci: [issue #8] enforce traceability]
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

**Proposed commit-1 message (validated at E10):**

```text
ci(traceability): [issue #8] enforce commit references in CI

Adopt `<type>[(scope)]: [issue #N] <description>` for every new commit and
reject unlinked or unregistered references in CI and locally, while history
before the fixed adoption baseline stays exempt.

Refs #8
```

**Self-review notes (coordinator):** the subject regex rejects empty scopes/descriptions, zero-padded and non-numeric identifiers, unsupported types, and default `Merge pull request …`/`fixup!`-style subjects; body references are checked for syntax and registration; the issue map is read **at each checked commit**, so later map edits cannot rehabilitate an earlier bad reference; range selection excludes everything reachable from the PR base including diverged bases; shallow clones and missing revisions exit 2. Tests isolate global/system git config and use real temporary repositories, including a real two-parent merge and a `--depth 1` local clone. No test asserts prose or wiring.

**NOT RUN / limits (honest list):** hosted GitHub Actions execution of the new `commit-reference` job (the workflow is not on `main` yet; prior CI runs covered the previous workflow only); macOS/Git-2.54 environment of the original record (accepted limitation; the generator pins repo-relevant Git inputs); required-status-check branch protection (a repository administration step, not code); post-commit range audit (to be run and recorded after approval, before publication).

## 6. Reviewer instructions (verbatim)

> You are the independent CTA implementation reviewer using GPT-6.1 Sol xhigh. Decide whether this exact snapshot satisfies the supplied story, every applicable Gherkin criterion, and repository invariants. Treat OMP's summaries and test results as claims to check against the supplied artifacts and targeted source inspection. Check proposal/accepted/evidence separation, real port compatibility, revision/content-hash semantics, honest errors/501s, independent oracle expectations, offline defaults, and generated-file discipline where relevant. Do not demand implementation of a later milestone. Do not edit files, implement repairs, regenerate fixtures, commit, or delegate. Ask OMP for missing runtime evidence; distinguish observed defects from hypotheses and unavailable checks. Return an AC-by-AC PASS, FAIL, or NOT VERIFIED assessment and actionable findings with stable IDs, severity, blocking status, AC/invariant, path/line, expected/actual behavior, and smallest correction/recheck. Keep optional suggestions and unrelated pre-existing defects separate. Return exactly one verdict: APPROVE, REQUEST_CHANGES, or NEEDS_INPUT. APPROVE requires every applicable criterion/check to be satisfied, no unresolved blocker, and the exact snapshot identified. In later rounds verify prior dispositions and regressions while retaining the complete acceptance assessment. A passing process, passing tests, or exhausted review limit is not approval. Agent review cannot attest human labeling or human link decisions.
