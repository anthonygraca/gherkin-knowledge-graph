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
<type>(<scope>): <summary>

<why, not just what>

Refs #<issue>
```

- `Refs #N` for partial work; `Closes #N` only when the issue is genuinely complete (acceptance criteria tested).
- Types: `feat` `fix` `docs` `test` `refactor` `chore` `ci`.
- One work item per commit where practical; reference each served item (`Refs #3, #4`).
- Pre-convention history, retro-attributed to SETUP-01: `ae859cd` (Initial commit), `204eb49` (user-story issue form).

## Branches

`<type>/<issue>-<slug>` — e.g. `feat/5-baseline-diff`. Once CI exists, `main` takes no direct commits.

## Pull requests

- Title: `<ID>: <summary>` — e.g. `AS-02: reverification_required rule`
- Body: `Closes #<issue>` (or `Refs #<issue>` while partial)
- Cross-boundary changes need a review from a second workstream (roadmap §2)

## Definition of done (roadmap §9)

Acceptance criteria tested; fixtures cover success and failure; provenance and revision preserved where applicable; API examples updated; tests pass offline; docs include the invocation or demo; simplifying assumptions documented.
