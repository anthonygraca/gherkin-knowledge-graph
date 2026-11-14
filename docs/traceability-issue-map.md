# Roadmap ids → GitHub issues

Two levels of the tracker, per `CONTRIBUTING.md`:

| Level | GitHub shape | Contains |
| --- | --- | --- |
| **Feature** (`F-nn`) | issue type `Feature`, no milestone | a collection of **user stories** (sub-issues) |
| **User story** (roadmap id, e.g. `AS-02`) | label `user-story`, sub-issue of its feature, one milestone | Given/When/Then **scenarios** as its acceptance criteria |
| **Task / Bug** | issue type `Task` / `Bug`, sub-issue of the story it serves | implementation slices; free-form titles |

A story's Gherkin scenarios are the definition of done: they become the automated tests, and the
story closes only when they pass offline. Proposals, tasks, and stories are separate kinds — a
review finding or an implementation slice is never a substitute for a story id.

Canonical criteria now live in `docs/stories/<STORY-ID>.feature`, following
[the development lifecycle](development-lifecycle.md). The M0 story index provides explicit
mappings to existing pytest checks; there is no direct Gherkin runner execution yet. Story
delivery, scenario specification, test execution and engineering approval are separate records.
This issue map identifies delivery work, not proof that every criterion was executed or accepted.

## How milestones fit

A **milestone** is one of the roadmap's delivery slices (`CONTINUOUS_TRACEABILITY_ROADMAP.md` §7),
each with its own exit criteria. It answers "in which slice does this story's acceptance criteria
pass?", so it is assigned to **user stories**, never to features:

| Milestone | Issue milestone # | Exit (roadmap §7) |
| --- | --- | --- |
| M0 — Contract + fixture foundation | #3 | clone → documented command → deterministic offline tests; mock APIs return schema-valid fixture data |
| M1 — AI-free vertical slice | #1 | demo the `REQ-001` thread and one intentionally missing link end to end, offline |
| M2 — Version-aware continuous assurance | #2 | baseline A → B yields a justified `reverification_required` finding, never a false failure |
| M3 — Local semantic discovery | not created yet | fake and real providers pass the same contract tests; retrieval measured, never treated as ground truth |
| M4 — Continuous integration and research comparison | not created yet | reproducible benchmark report with methodology, limitations, and runtime/cost |

A feature therefore spans slices and carries a `**Slices:**` line instead of a milestone: F-08
Retrieval has AI-01 in M0 and AI-02/AI-03 in M3. Stories whose slice has no milestone object yet
(M3, M4) name it in their body; create the two missing milestones if you want that filtering.

## Features

| Roadmap | Issue | Title |
| --- | --- | --- |
| F-01 | [#7](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/7) | Foundation — fixture oracles, contracts, and repo conventions |
| F-02 | [#9](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/9) | Ingestion — requirements, Gherkin, source and tests as artifacts |
| F-03 | [#10](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/10) | Links — typed, provenance-aware links and thread traversal |
| F-04 | [#11](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/11) | Evidence — verification runs pinned to the tested revision |
| F-05 | [#1](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/1) | Assurance — deterministic findings for coverage gaps and stale evidence |
| F-06 | [#12](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/12) | UI — thread and findings dashboard |
| F-07 | [#13](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/13) | Review — human decisions, honest offline behaviour |
| F-08 | [#14](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/14) | Retrieval — one `CandidateDiscovery` contract, fake and local adapters |
| F-09 | [#15](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/15) | Discovery — ranked proposals and measured retrieval quality |
| F-10 | [#16](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/16) | Automation — revision-triggered assurance and baseline diff |
| F-11 | [#58](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/58) | Executable Gherkin traceability — runtime, legacy migration, and executable graph |
| F-12 | [#59](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/59) | Portable repository ingestion — read-only Gherkin indexing for external projects |

## User stories

| Roadmap | Issue | Feature | Slice | Owner | Title |
| --- | --- | --- | --- | --- | --- |
| SETUP-01 | [#8](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/8) | F-01 | M0 | shared | Initial repository setup and commit↔issue traceability |
| FT-01 | [#18](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/18) | F-01 | M0 | B lead | Deterministic fixture repository and hand-labeled oracle |
| FT-02 | [#19](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/19) | F-01 | M0 | B lead | Versioned contracts with fixture-backed mock responses |
| FT-03 | [#39](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/39) | F-01 | M0 | shared | Lifecycle traceability and canonical Gherkin acceptance specifications (maintenance slice; no later-milestone capability) |
| DT-01 | [#20](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/20) | F-02 | M1 | B | Requirements and Gherkin scenarios parsed into artifacts |
| DT-02 | [#21](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/21) | F-02 | M1 | B | Source and test artifacts tied to path and revision |
| DT-03 | [#22](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/22) | F-03 | M1 | B | Typed, provenance-aware links with review state |
| DT-04 | [#23](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/23) | F-03 | M1 | B | Retrieve the thread for a requirement |
| DT-05 | [#24](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/24) | F-04 | M2 | B | Test outcomes tied to exact tested commits |
| DT-06 | [#25](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/25) | F-04 | M2 | B | Changed artifacts and impacted links between baselines |
| AS-01 | [#2](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/2) | F-05 | M1 | C | Missing coverage/link findings |
| AS-02 | [#3](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/3) | F-05 | M2 | C | Potential stale-evidence findings after relevant changes |
| AS-03 | [#4](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/4) | F-05 | M2 | C | Failed, missing, and stale evidence kept distinct |
| AS-04 | [#26](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/26) | F-06 | M1 | C | Summary of findings and coverage counts |
| AS-05 | [#27](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/27) | F-06 | M2 | C | Drill-down into findings and their evidence |
| AS-06 | [#28](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/28) | F-07 | M3 | C | Accept or reject proposed links with audit details |
| AS-07 | [#29](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/29) | F-07 | M3 | C | Useful behaviour when no provider is available |
| AI-01 | [#30](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/30) | F-08 | M0 | A | Fake and real providers behind one interface |
| AI-02 | [#31](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/31) | F-08 | M3 | A | Local EmbeddingGemma 2 inference, no shared services |
| AI-03 | [#32](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/32) | F-08 | M3 | A | Revision-aware incremental embedding refresh |
| AI-04 | [#34](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/34) | F-09 | M0 | A | Ranked candidate links labelled as proposals |
| AI-05 | [#35](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/35) | F-09 | M3 | A | Labeled precision/recall and recall@k evaluation |
| AI-06 | [#56](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/56) | F-08 | M3 | A | CocoIndex Code semantic code-search capability and integration contract (implementation-approach story; not in roadmap §6) |
| CI-01 | [#36](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/36) | F-10 | M4 | shared | Assurance runs when a repository revision changes |
| CI-02 | [#37](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/37) | F-10 | M4 | shared | New, unchanged, and resolved findings between baselines |
| GT-01 | [#60](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/60) | F-11 | M2 | shared | Cucumber runtime integration and executable acceptance harness |
| GT-02 | [#61](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/61) | F-11 | M2 | shared | Migrate historical CTA acceptance specifications to executable Cucumber |
| GT-03 | [#62](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/62) | F-11 | M2 | shared | Ingest step definitions, matches, and executions into the graph |
| PG-01 | [#63](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/63) | F-12 | M2 | B | Portable read-only Gherkin ingestion and repository-scoped queries |

`#33` is a closed duplicate of AI-03 (`#32`), created when a batch issue-creation call was
interrupted after the request had already succeeded server-side.

**F-11/F-12 and GT-01/GT-02/GT-03/PG-01** were created on 2026-11-13 from the owner's expanded-M2
direction. They are new stories with distinct identities; `DT-05`, `DT-06`, `AS-02`, `AS-03`, and
`AS-05` keep their original meanings. Their canonical criteria live in `docs/stories/<ID>.feature`.
Refinement disposition: drafted by OMP against the repository lifecycle; independent acceptance
review is required before any claim of approval. GT-02 currently records pending migration for
`AS-04`, `AS-05`, and `SETUP-01` in `docs/feature-inventory.json`; the issue stays open until those
bindings exist or an owner accepts the declared exclusions.

**AI-06 (#56)** was created on 2026-11-13 by the RAG mission as an implementation-approach story
under F-08. It is not a roadmap §6 backlog story: it adopts CocoIndex Code for semantic *code*
search and does not amend AI-01/AI-02/AI-03/AI-04/AI-05 criteria. Its canonical criteria live in
[AI-06.feature](stories/AI-06.feature); the roadmap's M3 entry still describes the original local
model/index approach. Promoting AI-06 into roadmap §6 is an owner disposition, not an inference
from this map row. M3 has no GitHub milestone object yet, so the row names the slice in its body.

## Task issues

| Task | Issue | Parent story |
| --- | --- | --- |
| Baseline diff: artifacts changed between `baseline-a` and `baseline-b` | [#5](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/5) | AS-02 (#3) |
| `reverification_required` rule, never `verification_failed` | [#6](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/6) | AS-02 (#3) |
| Research design: hypotheses, benchmark inputs, and the CI / simple-storage / graph comparison plan | [#40](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/40) | F-10 (#16) — feature-level research-planning task; no owning story yet |

## Keeping this map honest

Titles carry the roadmap id as a prefix, so the map can be rebuilt by listing issues; if a number
here disagrees with GitHub, GitHub wins and this file is the bug. Regenerate it whenever issues are
created, renumbered, or closed.
