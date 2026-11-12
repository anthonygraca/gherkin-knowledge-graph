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
