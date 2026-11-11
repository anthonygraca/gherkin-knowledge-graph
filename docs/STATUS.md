# Status

```text
Date:                2026-11-10
Current branch:      main — M0 implementation is the commits after ae859cd; rebased onto the
                     upstream main that added CONTRIBUTING.md and the user-story issue form
Milestone:           M0 — implementation complete, exit gate NOT satisfied
Independent review:  docs/reviews/M0-review.md — verdict "M0 not verified"
                     (R1, R2, R3 major; R4, R5, R6, R7 minor)
Tests executed:      uv run --project backend pytest backend/tests -q  →  92 passed (offline)
                     uv run --project backend python tools/fixturectl.py verify  →  exit 0
                     uv run --project backend ruff check . && ruff format --check .  →  clean
Current API/schema version: 0.1.0
Tracker:             docs/traceability-issue-map.md (features → user stories → tasks)
Environment:         Python ≥3.11, uv, git ≥2.28; no GPU, LLM, vector store, Docker, or network
                     during tests
```

## What exists

* Reproducible fixture history for `banking-demo`: four commits, fixed SHAs, tags `baseline-a`
  and `baseline-b`, verified identical across builds in the same environment.
* Hand-labeled oracle covering coverage gaps, a pending proposal, a superseded requirement, a
  reverification case, and a confirmed failure — with explicit negative expectations.
* Domain contracts: artifacts, links, evidence, candidates, findings, envelopes, ports, error
  codes, severity policy, stable finding fingerprints.
* Mock services: fixture-backed `FixtureStore`, `SampleFindingsSource` (findings replay), and the
  fixture `CandidateDiscovery` provider. All offline.
* API: reads and discovery implemented; three endpoints frozen as contracts and returning 501
  with the owning story.
* 92 offline tests, including proof that committed generated fixtures are what the generator
  produces and proof that the fixture's own suite passes at `baseline-a` and fails exactly twice
  at `baseline-b`.

## Open findings that block M1

The independent review is ground truth. Reproduce before repairing; do not declare the milestone
complete while a major finding is open.

All seven findings below have repair commits and regression tests on branch
`feat/8-m0-foundation` (PR #38). **M0 still requires a re-review**: a milestone closes only when an
independent review of its exit criteria has no open *major* finding, and that re-review has not
happened yet.

| Finding | Severity | What it meant | Repair | Regression test |
| --- | --- | --- | --- | --- |
| R1 | major | `FixtureStore` did not satisfy the declared `ArtifactRepository` port and routes depended on the concrete class | Store implements the port (`baselines`, `resolve_baseline`, `get_artifact`, `list_artifacts`, `list_links`, `list_evidence`, `changed_artifacts`); routes depend on `RepositoryDep`; the two fixture-only surfaces are named in code | `test_contract_boundaries.py::test_consumer_can_read_everything_through_the_port_alone`, `::test_store_satisfies_the_artifact_repository_port` |
| R2 | major | `ThreadResponse` accepted a non-accepted link inside `accepted_links` | `validate_link_partition` is applied to `ThreadResponse` and `BaselineSnapshot`; the loader rejects a mispartitioned file | `::test_thread_response_rejects_a_proposal_inside_accepted_links`, `::test_thread_response_rejects_an_accepted_link_inside_proposals`, `::test_loader_rejects_a_mispartitioned_thread_file` |
| R3 | major | `verify` reported success for a tampered or deleted `expected/baselines.json` | `compare_file` replaces the directory walker for the manifest, with explicit absence handling; CLI gains `--baselines` | `test_fixture_drift.py::test_drift_detection_fails_when_the_baseline_manifest_is_tampered`, `::test_drift_detection_fails_when_the_baseline_manifest_is_missing` |
| R4 | minor | Thread and sample-findings loaders served files declaring an unsupported `schema_version` | Shared `require_supported_schema_version` used by the snapshot, thread, findings, and candidate-index loaders | `::test_served_responses_reject_an_unsupported_schema_version`, `::test_snapshot_and_index_versions_are_enforced` |
| R5 | minor | The generator inherited `GIT_DEFAULT_HASH`, so baselines differed under another object format | `GIT_DEFAULT_HASH=sha1` pinned in the generator environment and documented | `test_fixture_repo.py::test_generator_pins_the_object_format` |
| R6 | minor | The fingerprint test took its expected value from the production helper | Three independently computed fingerprint vectors with duplicate and out-of-order ids | `test_domain_contracts.py::test_fingerprint_matches_an_independently_computed_vector` |
| R7 | minor | The review prompt's fixture-test command failed collection | Prompt now runs pytest from each worktree root and explains why | — (documentation; exercised manually) |

Unverified by review (state honestly in any report): that the oracle labels were reviewed by a
human rather than authored by the generator's session; general staleness/failure classification for
inputs other than the fixture's `REQ-001` case; hosted Linux CI; and side-effect freedom for future
provider plugins. (Cross-environment reproducibility was R5 and is now pinned.)

## Next tasks (in order)

| # | Task | Issue | Acceptance condition |
| --- | --- | --- | --- |
| 1 | **Re-review M0** against the repair commits (prompt: `docs/reviews/M0-review-prompt.md`, section "For a re-review after repairs") | #18, #19 | Every R1–R7 finding reported `repaired` with command output; no open major finding |
| 2 | Land the review verdict and close the M0 stories | #18, #19 | PR #38 no longer a draft; FT-01/FT-02 acceptance criteria demonstrably pass; the milestone exit gate is recorded in this file |
| 3 | Then start B-PR1 / C-PR1 / A-PR1 in parallel | #20, #21, #23 / #2, #26 / #30 | See `docs/stories/M0-foundation.md` for the per-stream acceptance conditions |

M1 does not start before task 1 passes: a milestone closes only when an independent review has no
open major finding (`AGENTS.md`, milestone definition of done).

## Verification commands (copy/paste)

```bash
uv sync --project backend
uv run --project backend python tools/fixturectl.py verify
uv run --project backend pytest backend/tests -q
uv run --project backend uvicorn app.main:app --reload   # then GET /api/threads/REQ-001?baseline=baseline-b
```
