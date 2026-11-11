# Lifecycle specification migration: author verification

**Status:** Author checks recorded; independent and stakeholder review not performed in this session.
**Recorded after execution:** 2026-11-11T22:39:03Z (clock observation immediately following collection of the completed suite output).
**Work items served:** SETUP-01 (#8), FT-01 (#18), FT-02 (#19).
**Tested code revision:** `efa824b5b225db74c7ddba50365dad918d3212cc`.

The lifecycle documents and feature files are uncommitted working-tree changes. No commit or
approval is invented for them. The selected backend/test/fixture/tool inputs were byte-compared
with HEAD and were unchanged; the document versions checked below are identified by hashes.
This record does not alter the independently approved M0 snapshot or certify new product behavior.

## Checks and observed results

| Check | Observed result |
| --- | --- |
| Existing backend suite | 107 passed, 1 pre-existing deprecation warning, 3.57 seconds reported by pytest. |
| Fixture verification | Fixture generation reproducible; committed generated files current. |
| Ruff lint | All checks passed. |
| Ruff format | 33 files already formatted. |
| Migration comparison | All 13 scenario titles/steps exactly match the original M0 Markdown criteria after indentation normalization; AC labels retained. |
| Trace-map structure | All 13 scenarios have unique IDs and mapping rows; all 20 distinct referenced pytest selectors exist. This structural check does not establish semantic test adequacy. |
| Documentation links / whitespace | Local linked paths resolve; `git diff --check` clean at check time. |

The backend suite stalled inside the filesystem sandbox, including an isolated existing health
TestClient test that timed out after 20 seconds. The initial stalled suite was interrupted. The
full suite then passed outside the sandbox after explicit execution approval. No product-code
change was made to obtain that pass. Root cause of the sandbox stall was not established.

The completed invocation was:

```bash
timeout 120s uv --cache-dir /tmp/cta-lifecycle-uv-cache run --offline --project backend pytest backend/tests -q
```

Fixture, lint and format checks used the same `uv --cache-dir /tmp/cta-lifecycle-uv-cache run
--offline --project backend` prefix with `python tools/fixturectl.py verify`, `ruff check .`
and `ruff format --check .`. The cache path is an execution-environment accommodation, not a
product dependency. No OS-level network-denial experiment was performed in this session.

Observed suite output excerpt:

```text
107 passed, 1 warning in 3.57s
```

The warning concerned deprecated httpx usage through Starlette TestClient. No dependency
migration was attempted as part of this specification/process change.

## Evaluated input identity

The runtime/check environment was Linux, Python 3.12.16, pytest 8.4.2, FastAPI 0.162.4,
Starlette 1.10.0, AnyIO 4.16.0, Pydantic 2.14.3 and Ruff 0.17.4, as observed locally.

Selected source/fixture inputs: 73 tracked files returned by
`git ls-files backend/app backend/tests fixtures tools/fixturectl.py backend/pyproject.toml backend/uv.lock`.
Their fingerprint is `sha256:9e9749f46d525272f842a29eb34316c2d1f0a4524b309c37aa1fc827e9b1da79`.
It is SHA-256 of UTF-8 compact JSON containing sorted unique `[repository-relative path,
SHA-256 hex of file bytes]` pairs, with JSON separators `(',', ':')` and `ensure_ascii=True`.
The selected bytes all matched the tested HEAD revision. This scoped fingerprint is not a claim
about unselected environment inputs or the whole working tree.

Document/specification content at author-check time:

| Path | SHA-256 |
| --- | --- |
| `docs/development-lifecycle.md` | `sha256:4f5588246519421885aa644c7e86c900ac69b44b36f34fa30dcd26243d7d6ce9` |
| `docs/project-definition.md` | `sha256:3c66e0e12820bc7fa82746680f3cc8a10e8c50ec7a051956d3969edde8147f71` |
| `docs/stories/FT-01.feature` | `sha256:7f4ec106b8fcc6f18b9ad77d87be50d549968626ea2242b90debd599249cca86` |
| `docs/stories/FT-02.feature` | `sha256:a6c4a9a149789b3a5bbef6f44dcd20fdaa77fad0d13668c537f2528f44fe8cca` |
| `docs/stories/M0-foundation.md` | `sha256:a0c5dc09021092d0228bc0cb3e53d8924b451e29f7e22816a8a948fb5bc68431` |
| `.github/ISSUE_TEMPLATE/user-story.yml` | `sha256:518d526983275287bfb14396fbf9b9bb151fa7350ec42caedd7e6e443c20b517` |
| `AGENTS.md` | `sha256:abea3577bad4a39ab92a7196a23a1a69e5904078a717d2f98eaded2f6ec48434` |
| `CONTRIBUTING.md` | `sha256:af96e6e5528ca3bf48deb55f3fd51ecc49b539f2e7b5e9f8780ca781596bd9c3` |
| `CONTINUOUS_TRACEABILITY_ROADMAP.md` | `sha256:80271c87fcca6eeab339c88a46562876a45bcf12176fb2f86a1e362939319451` |
| `docs/STATUS.md` | `sha256:1a003a81318e338cd7f0173c7e8b6b3c6c4a7a88532a2350abc21ba04c5594b2` |
| `docs/traceability-issue-map.md` | `sha256:28e9614ca466b8dcab8c3f80ffbf52a857b0eb696fcb7ff29e99c0d832586e56` |

These hashes identify the checked versions. Subsequent edits need their own impact assessment;
a different commit alone does not establish changed content.

## Limits and remaining dispositions

No Gherkin parser/runner dependency or direct step bindings were added. The feature files were
checked for faithful extraction, identity and mappings, and existing pytest behavior was rerun.
They were not executed as Gherkin scenarios. Historical runs do not gain the new scenario IDs
retroactively. No new fixtures, expected results or accepted engineering links were created.

The project definition, candidate requirement allocations and migration mappings still need
owner/team review. That review must assess meaning and adequacy, not only these structural
checks. This is an author verification record, not an independent milestone review or a
stakeholder acceptance decision. M0 landing prerequisites and later-milestone gates remain in force.

## Prospective attribution and later edits

Recorded 2026-11-11 after the checks above. The adoption work continues as story **FT-03**
([#39](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/39)) — see
[FT-03.feature](../stories/FT-03.feature) and [FT-03.md](../stories/FT-03.md). That story was
created after this record; the "Work items served" line above keeps the attributions that applied
when it was written and is not rewritten.

Edits made when the story was established, after the checks in this record:

| Path | Edit | Effect on the checks above |
| --- | --- | --- |
| `CONTINUOUS_TRACEABILITY_ROADMAP.md` | FT-03 backlog row and adoption sentence | Attribution text only |
| `docs/traceability-issue-map.md` | FT-03 row | Attribution text only |
| `docs/STATUS.md` | Branch/landing reconciliation; FT-03 reference | Status text only |
| `CONTRIBUTING.md`, `docs/development-lifecycle.md` | FT-03 pointer | Attribution text only |

The hashes above identify the versions that were checked. The edited versions were not re-checked
by this record; the re-checked migration results (fidelity, mapping resolution, identity) are
recorded in [FT-03.md](../stories/FT-03.md). Separately, `AGENTS.md` and `CONTRIBUTING.md` were
later edited by the commit-reference follow-up slice (SETUP-01, #8) while it remains uncommitted;
those commit-convention edits are not part of this migration.
