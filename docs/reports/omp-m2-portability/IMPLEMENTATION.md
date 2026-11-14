# PG-01 — portable read-only Gherkin ingestion and repository-scoped queries

**Served issue:** [PG-01, #63](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/63)
(feature F-12 [#59](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/59), milestone
M2). **Owner:** Workstream B (portability owner). **Snapshot:** local `main` at `4659e01` plus this
uncommitted slice; contract schema `0.3.0`.
**Independent review:** submitted once (`docs/reports/omp-m2-milestone/review-1.md`, submission 1 of 7).

## Delivered

* `backend/app/domain/portable.py` — annotation-free repository contracts (snapshot, feature,
  scenario, step, outline instance, definitions, resolutions, executions, query envelopes).
* `backend/app/ingestion/portable.py` — official `gherkin-official` 43.0.0 parsing from a pinned
  commit, repository-scoped deterministic identity, symlink/submodule/encoding/size guards,
  diagnostics instead of silent drops, and a tree digest.
* `backend/app/ingestion/cucumber_messages.py` — Cucumber Messages NDJSON adapter. Definitions and
  resolutions come from the framework's own `stepDefinitionIds`; `source` envelope hashes bind the
  report to the indexed revision.
* `backend/app/persistence/portable.py` — per-process registry, revision isolation, append-only
  report import, coverage counts, extracted/matched/observed relations, executability findings.
* `backend/app/api/portable_routes.py`, `backend/app/cli.py` — the eleven query endpoints and the
  JSON CLI.
* `fixtures/external-recipes/`, `fixtures/external-twin/` — independently styled projects that never
  adopted CTA tags, annotations, requirements, or links. `tools/external_fixture.py` builds their
  deterministic Git histories; `expected/inventory.json` is hand-counted.
* `tools/portable_benchmark.py`, `docs/reports/omp-m2-portability/benchmark.json` — reproducible
  benchmark.
* `bdd/step_definitions/portable.steps.js` and `docs/stories/PG-01.feature` — the six canonical
  scenarios execute through Cucumber.

## Invariants and how they are held

* **Read-only.** Indexing reads blobs through `git ls-tree`/`git cat-file`; there is no write path.
  Tests and the benchmark hash every tracked file before/after and compare `git status`.
* **No code execution.** The adapter reads a report; it never invokes a project step or hook. The
  twin fixture's `Before` hook would write `sentinel.txt` if it ran; SCN-1206 asserts it does not.
* **Unknown is not undefined.** `bindings` answers `not_available` with a reason when no report was
  imported; `executable-findings` stays empty. `undefined_step` requires the framework's empty
  `stepDefinitionIds`.
* **Repository-scoped identity.** Keys are `<repo_id>:<path>#SCN-L<line>`; both fixtures share
  `features/browse.feature` and `@SCN-001`, and their keys do not intersect.
* **Content, not SHA.** A report is accepted only when every `source` envelope hash equals the
  feature content hash at the requested revision (`test_report_from_a_different_revision_is_rejected`).

## Verification (actual commands)

| Command | Exit | Result |
| --- | --- | --- |
| `uv run --project backend pytest backend/tests/test_portable_ingestion.py -q` | 0 | 18 passed |
| `uv run --project backend pytest backend/tests/test_portable_api.py -q` | 0 | 7 passed |
| `uv run --project backend pytest backend/tests -q` | 0 | 443 passed, 3 opt-in skips |
| `uv run --project backend python tools/portable_benchmark.py --out docs/reports/omp-m2-portability/benchmark.json` | 0 | see below |
| `(cd bdd && npm run bdd)` (full suite) | 0 | PG-01 (7) and GT-03 (2) scenarios passed within 78/78 scenarios |

Benchmark facts (hand labels vs parsed):

| Fixture | Ref | Features | Scenarios | Outlines | Instances | Steps | Untagged | Match |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| external-recipes | v1 | 2 | 4 | 1 | 2 | 15 | 3 | exact |
| external-recipes | v2 | 3 | 5 | 1 | 2 | 19 | 4 | exact |
| external-twin | v1 | 1 | 1 | 0 | 0 | 2 | 0 | exact |

* Identity collisions: **0**; `distinct_keys=true`.
* Repository modifications: **0**; `git status` unchanged; `hooks_executed=false`.
* Re-index tree digest: identical across runs for every ref.
* Imports require a provenance sidecar naming the tested commit; the same report bytes cannot be
  rebound to another revision (review-1 R04).
* Without a report: `availability=not_available`, 0 definitions, 0 resolutions, 0 findings.
* With the captured report: 13 definitions, 23/23 matched resolutions, 5 executions (all passed),
  step coverage 15/15, tested commit `55d3d74a…` (v1).
* v2 report: 4 undefined steps in `ratings.feature`, reported from real framework metadata; four
  `undefined_step` findings (`test_undefined_steps_require_framework_evidence`).

## Limitations

* One framework adapter (`cucumber-messages`, Cucumber-JS 13.3.0). A second framework is P2/M3 and
  explicitly unverified.
* Scenario identity is locator-based; edits, moves, renames, and reordering produce new keys. No
  continuity reconciliation is claimed.
* The registry is per-process: the API indexes on demand and does not persist across restarts.
* Report attribution compares feature source hashes only; a run that covered a subset is accepted
  for the files it covered, and unexecuted scenarios show as coverage gaps.
* The two external fixtures are independently styled but written for this benchmark; they are not a
  second real third-party codebase.
