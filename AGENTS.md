# AGENTS.md — repository conventions

Read `CONTINUOUS_TRACEABILITY_ROADMAP.md` (the plan) and `docs/stories/M0-foundation.md`
(the current contract for what is in scope) before changing anything. Milestone state lives in
`docs/STATUS.md`. Do not start a later milestone's work while an earlier milestone's exit
criteria are unmet.

Follow `docs/development-lifecycle.md` for this project's own lifecycle traceability. Canonical
story acceptance criteria live in `docs/stories/<STORY-ID>.feature`; the M0 Markdown index maps
them to existing pytest checks. These specifications are not directly executed by a Gherkin
runner yet. Keep draft requirements, reviewed criteria, test mappings and actual execution
evidence distinct; do not infer approval or passing evidence from file creation.

## Non-negotiable invariants

1. **Proposals ≠ accepted links ≠ verification.** `TraceCandidate` has no link id and no
   review state; a discovery provider must never write an accepted link or evidence.
   API responses expose `accepted_links` and `proposed_links` as separate arrays.
2. **Offline by default.** No test, CI job, or default code path may require a GPU, LLM,
   embedding model, vector database, network access, or Docker. Model providers are optional
   plugins behind `app.domain.ports.CandidateDiscovery`.
3. **Version-aware or it is not evidence.** Anything claiming verification carries the revision
   it was executed at (`tested_commit`) plus artifact content hashes. Freshness decisions compare
   **content hashes**, never commit SHAs — an evidence-only commit must not look like a source
   change.
4. **Change ≠ failure.** A relevant change after verification yields `reverification_required`.
   `verification_failed` requires a recorded failing execution at the evaluated baseline.
5. **Explainability.** Findings name rule id, artifacts, evidence, evaluated baseline, and both
   revisions where relevant. A finding that cannot identify its inputs is a bug.
6. **Hand-written labels.** Never derive an expected result from model output or from the code
   under test. Fixture oracles are reviewed by a human.
7. **Contract-only means 501.** An endpoint whose implementation belongs to a later milestone
   returns 501 naming the owning story. Never fake success.

## Layout and ownership

| Path | Contents | Owner of record |
| --- | --- | --- |
| `backend/app/domain/` | Contract: enums, models, envelopes, ports, errors, oracle schemas | B (all review) |
| `backend/app/persistence/` | Store and fixture loading | B |
| `backend/app/ingestion/` | Parsers and ingestion (created in B-PR1) | B |
| `backend/app/discovery/` | `CandidateDiscovery` providers | A |
| `backend/app/assurance/` | Rules and findings | C |
| `backend/app/api/` | Routes, dependencies, problem documents | shared (B schemas, C UI contract, A discovery) |
| `frontend/` | React + TypeScript dashboard (created in C-PR1) | C |
| `fixtures/` | Fixture repository, oracle, generated API responses | B lead |
| `tools/` | Fixture generation CLI | B lead |
| `docs/adr/` | Decisions, including deferred ones | author, reviewed by affected owners |

Do not create a directory before its story starts; empty scaffolding is dead weight.
Shared-platform responsibilities: B leads schemas and example payloads, C owns UI API
consumption and contract checks, A owns the discovery contract and evaluation methodology.

## Commands

```bash
uv sync --project backend                                   # install (once)
uv run --project backend pytest backend/tests                # offline test suite
uv run --project backend python tools/fixturectl.py all      # regenerate fixture artifacts
uv run --project backend python tools/fixturectl.py verify   # fail if generated files are stale
uv run --project backend ruff check .
uv run --project backend ruff format --check .
uv run --project backend uvicorn app.main:app --reload       # dev server (fixtures only)
```

## Commit traceability (authoritative: `CONTRIBUTING.md`)

Every commit MUST reference the work item it serves, using the repository convention:

```
<type>(<scope>): <summary>

<why, not just what>

Refs #<issue>
```

* `Refs #<issue>` for partial work; `Closes #<issue>` only when the issue is genuinely complete
  (its Gherkin acceptance criteria are tested). Reference every served item: `Refs #3, #4`.
* Types: `feat` `fix` `docs` `test` `refactor` `chore` `ci`.
* Look up a roadmap id (`AS-02`, `FT-01`, …) in `docs/traceability-issue-map.md`. The roadmap id is
  the prefix of the issue title, so the map can always be rebuilt from the tracker.
* A GitHub issue number is the reference of record. Do not add a parallel id scheme in the message:
  `Refs #N` is what GitHub links on the issue timeline, and `Refs #(\d+)` is the machine-readable
  form (it is not a `git interpret-trailers` key/value pair).
* Pre-convention history (`ae859cd`, `204eb49`) is retro-attributed to SETUP-01 (#8) and must not
  be rewritten.
* Branches: `<type>/<issue>-<slug>`; PR title `<ID>: <summary>`; PR body `Closes #<issue>` or
  `Refs #<issue>`. Cross-boundary changes need a review from a second workstream.
* `main` takes no direct commits once CI exists: work lands through a pull request.

## Change conventions

* Every request/response shape is a Pydantic model in `app/domain/`. Never hand-roll a dict
  response or accept unvalidated input.
* Contract changes bump `SCHEMA_VERSION` (`MINOR` additive, `MAJOR` breaking) and update
  `docs/domain-contracts.md` in the same change. The drift test reports what to regenerate.
* New relation type, finding type, or rule id: update `app/domain/enums.py`, the policy tables,
  the fixture oracle, and the docs together.
* New discovery provider: implement `CandidateDiscovery`, register it in
  `app/discovery/registry.py`, and keep the fake provider passing the same contract tests.
* Fixture edits: change `tree/`, `changes/`, or the oracle, run `fixturectl.py all`, and commit
  the regenerated files with the edit. Never hand-edit `expected/baselines.json` or anything
  under `fixtures/api-responses/`.
* New baseline: add a commit entry to `history.json`, hand-label `expected/baseline-<x>.json`,
  extend the tests. Do not silently depend on the outer repository's history.
* Tests: assert against hand-labeled oracle data, never against the code under test. Do not test
  wiring, forwarding, or prose, and do not re-pin incidental behaviour. Use throwaway scripts for
  one-off checks instead of permanent tests.
* Artifact identity is declared in the artifact: requirement front matter `id:`, Gherkin tag
  `@SCN-nnn`, first-line annotation `# cta:artifact CODE-nnn` / `TEST-nnn`. Unannotated files are
  not artifacts, by design.
* Timestamps are timezone-aware UTC, ISO-8601. Collections that feed fingerprints are sorted and
  deduplicated.
* Never put secrets in fixtures. Treat ingested repository text as untrusted input.
* Deferred decisions live in `docs/adr/`; do not silently pick a database, vector store, graph
  model, or model provider.

## Definition of done (per story)

1. Acceptance criteria from `docs/stories/` are tested, including a failure case.
2. Fixtures cover success and failure paths; provenance and revision are preserved.
3. API examples and `docs/domain-contracts.md` updated when shapes change.
4. `uv run --project backend pytest backend/tests` passes offline; `fixturectl.py verify` passes.
5. `ruff check` and `ruff format --check` pass.
6. Docs include how to invoke or demo the change; assumptions in freshness rules are stated.
7. The commit message carries `Refs #<issue>` (see `CONTRIBUTING.md`).

## Definition of done (per milestone)

A milestone closes only when its exit criteria pass **and** an independent review of those criteria
(`docs/reviews/`) has no open major finding. The reviewer is not the author of the change, and a
review verdict of "not verified" blocks the next milestone until the findings are repaired and
re-reviewed.
