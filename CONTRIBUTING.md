# Contributing

**Every commit traces to a work item.** This project exists to make software traceable; the repository should not violate its own rule.

## Work items

| Kind | GitHub shape | ID scheme | Example |
|---|---|---|---|
| Feature | issue type `Feature`; parent of its stories | `F-nn` | F-05 Assurance |
| User story | label `user-story`, filed as a **sub-issue of its Feature**, Given/When/Then acceptance criteria (issue form: *User story*) | roadmap ID (`AS-01`, `DT-03`, `SETUP-01`) | AS-02 |
| Task / Bug | issue types `Task` / `Bug`, sub-issue of the story they serve | free-form | baseline-diff task under AS-02 |

Keep the roadmap ID at the start of the issue title so issues and `CONTINUOUS_TRACEABILITY_ROADMAP.md` stay cross-referenceable.

## Lifecycle and acceptance specifications

Follow [the development lifecycle](docs/development-lifecycle.md): stakeholder need → system
obligation → story and behavioral acceptance criteria → design → implementation → verification
evidence → stakeholder validation → release and maintenance. The initial
[project definition](docs/project-definition.md) is a draft requiring owner/team review, not an
approved requirements baseline. Preserve the milestone prerequisites in `docs/STATUS.md`. The
adoption slice is **FT-03**
([#39](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/39)) —
[criteria](docs/stories/FT-03.feature), [record](docs/stories/FT-03.md); its criteria and the
draft project definition still need owner/team review.

For each newly refined story, store the canonical behavioral criteria in
`docs/stories/<STORY-ID>.feature`. Tag the Feature with the existing story ID and `@issue-N`,
and each scenario with a stable `@SCN-nnn`. Keep one current normative copy: after intake,
the GitHub issue and PR link to the reviewed feature-file revision. Preserve old AC labels when
migrating criteria, and record substantive changes as reviewed changes rather than silent edits.

Before implementation, identify the source obligation/rationale, owner, examples including a
failure case, design impact and intended verification method. Map every scenario to substantive
tests and retain actual results at the tested revision/configuration. A specification, test mapping,
approval and passing execution are separate records. Nonbehavioral obligations may need additional
inspection/analysis records; they are not fabricated test passes.

The M0 examples are [FT-01.feature](docs/stories/FT-01.feature) and
[FT-02.feature](docs/stories/FT-02.feature), with their
[pytest verification map](docs/stories/M0-foundation.md#acceptance-verification-map).
They currently have no direct Gherkin runner bindings. Selecting a runner and adding bindings
requires a scoped story/ADR; do not report unbound scenarios as executed. Fixture `.feature`
files describe the synthetic repository evaluated by CTA, not CTA's own acceptance contract.

## Commit messages

```text
<type>[(scope)]: [issue #N] <description>

<why, not just what>
```

- Scope is optional and, when present, uses parentheses: `ci(traceability): [issue #8] lint commits`
  or `ci: [issue #8] lint commits`. Use a nonempty lowercase scope without spaces.
- The subject must name one positive GitHub story/task issue number using the literal
  `[issue #N]` syntax, followed by a nonempty description. A reference only in the body is insufficient.
- Types: `feat` `fix` `docs` `test` `refactor` `chore` `ci`.
- One work item per commit where practical. Add `Refs #3, #4` in the body for additional served
  issues. `Refs #N` for the subject's issue is allowed but not required. Use `Closes #N` only when
  the entire issue is genuinely complete (acceptance criteria tested and required reviews complete).
- Register issues in the **User stories** or **Task issues** tables of
  [the issue map](docs/traceability-issue-map.md) before or in the same commit that references them.
  Feature-only references, PR numbers, duplicates mentioned only in prose, and unknown numbers fail.

### Commit-reference CI gate (SETUP-01, #8)

The **Commit references** job runs on pull requests and pushes to `main`, using the standard-library
Python tool `tools/commitlint.py`. It checks every applicable commit, including real merge commits,
against the subject format and the issue map **at that commit**. Optional `Refs`/`Closes` lines
are checked too. The check needs full local Git history but no package installation, API token,
GitHub API call, or network access. It verifies registration in the map; reviewers still establish
issue relevance, live tracker accuracy, acceptance, and whether `Closes` is justified.

The fixed adoption baseline is `efa824b5b225db74c7ddba50365dad918d3212cc` (the existing M0 merge).
That commit and all its ancestors are exempt; every later checked commit uses the new format,
including the commit introducing this check. Do not advance the baseline to hide failures or
rewrite old history. The older `ae859cd` and `204eb49` remain retro-attributed to SETUP-01.

PR runs check commits reachable from the actual PR head but absent from its base, excluding legacy
history; GitHub's synthetic test-merge commit is not a contribution. The `edited` activity is
included, so a PR retargeted to a different base is re-checked against its new base. Push runs
check all commits reachable from `main` after the adoption baseline. Missing revisions, a branch
without the baseline, an unreadable issue map, or shallow history fail the check rather than
silently passing.

Run locally from the repository root:

```bash
python tools/commitlint.py --message-file /tmp/commit-message.txt  # before committing
python tools/commitlint.py                                     # all post-baseline commits at HEAD
python tools/commitlint.py --base origin/main --head HEAD        # proposed PR range
```

For example, save this message and validate it with `--message-file` before `git commit -F`:

```text
ci(traceability): [issue #8] enforce commit references in CI

Reject unlinked future commits while preserving pre-adoption history.

Refs #8
```

Use a conforming subject for squash/merge commits too; edit the platform's proposed message before
merging. Default `Merge pull request ...`, `Revert ...`, and `fixup! ...` subjects fail. PR checks
cannot validate a future merge message; the push check validates the actual landed commit.
To block PR merges on failure, make **Commit references** a required status check in the `main`
branch ruleset/protection settings after the workflow lands. Adding the workflow does not change
those remote settings. See GitHub's [PR event semantics](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#pull_request).

## Branches

`<type>/<issue>-<slug>` — e.g. `feat/5-baseline-diff`. Once CI exists, `main` takes no direct commits.

## Pull requests

- Title: `<ID>: <summary>` — e.g. `AS-02: reverification_required rule`
- Body: `Closes #<issue>` (or `Refs #<issue>` while partial)
- Cross-boundary changes need a review from a second workstream (roadmap §2)

## Definition of done (roadmap §9)

Acceptance criteria tested; fixtures cover success and failure; provenance and revision preserved where applicable; API examples updated; tests pass offline; docs include the invocation or demo; simplifying assumptions documented.
