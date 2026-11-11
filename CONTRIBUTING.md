# Contributing

**Every commit traces to a work item.** This project exists to make software traceable; the repository should not violate its own rule.

## Work items

| Kind | GitHub shape | ID scheme | Example |
|---|---|---|---|
| Feature | issue type `Feature`; parent of its stories | `F-nn` | F-05 Assurance |
| User story | label `user-story`, filed as a **sub-issue of its Feature**, Given/When/Then acceptance criteria (issue form: *User story*) | roadmap ID (`AS-01`, `DT-03`, `SETUP-01`) | AS-02 |
| Task / Bug | issue types `Task` / `Bug`, sub-issue of the story they serve | free-form | baseline-diff task under AS-02 |

Keep the roadmap ID at the start of the issue title so issues and `CONTINUOUS_TRACEABILITY_ROADMAP.md` stay cross-referenceable.

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
