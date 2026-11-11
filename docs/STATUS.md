# Status

```text
Date:                2026-11-11
Current branch:      feat/8-m0-foundation — M0 implementation, the R1–R7 repairs, and the
                     independent re-review records
Milestone:           M0 — implementation complete; exit gate pending the re-review verdict
Independent review:  docs/reviews/M0-review.md — first review: "M0 not verified"
                     docs/reviews/M0-rereview-1.md — re-review round 1 (GPT-6.1 Sol, reasoning
                     effort xhigh): NEEDS_INPUT. R1–R7 all repaired; AC-1.1…AC-1.8 and
                     AC-2.1…AC-2.5 all PASS; sole blocker R8 (no recorded human review of the
                     hand-labeled oracle), now attested at docs/reviews/M0-oracle-human-review.md
Tests executed:      uv run --project backend pytest backend/tests -q  →  107 passed (offline;
                     also 107 passed under an OS-level network denial)
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
* 107 offline tests (92 at the first review; the repair commits added 15), including proof that
  committed generated fixtures are what the generator produces and proof that the fixture's own
  suite passes at `baseline-a` and fails exactly twice at `baseline-b`.

## Open findings that block M1

The independent review is ground truth. Reproduce before repairing; do not declare the milestone
complete while a major finding is open.

All seven findings below have repair commits and regression tests on branch
`feat/8-m0-foundation` (PR #38). Re-review round 1 dispositioned R1–R7 as repaired and passed
every M0 acceptance criterion, and raised one new blocking evidence gap — R8, no recorded human
review of the hand-labeled oracle. That attestation is now recorded at
`docs/reviews/M0-oracle-human-review.md`. **M0 still requires the final re-review verdict**: a
milestone closes only when an independent review of its exit criteria has no open *major*
finding, and round 2 is where that verdict will land.

| Finding | Severity | What it meant | Repair | Regression test |
| --- | --- | --- | --- | --- |
| R1 | major | `FixtureStore` did not satisfy the declared `ArtifactRepository` port and routes depended on the concrete class | Store implements the port (`baselines`, `resolve_baseline`, `get_artifact`, `list_artifacts`, `list_links`, `list_evidence`, `changed_artifacts`); routes depend on `RepositoryDep`; the two fixture-only surfaces are named in code | `test_contract_boundaries.py::test_consumer_can_read_everything_through_the_port_alone`, `::test_store_satisfies_the_artifact_repository_port` |
| R2 | major | `ThreadResponse` accepted a non-accepted link inside `accepted_links` | `validate_link_partition` is applied to `ThreadResponse` and `BaselineSnapshot`; the loader rejects a mispartitioned file | `::test_thread_response_rejects_a_proposal_inside_accepted_links`, `::test_thread_response_rejects_an_accepted_link_inside_proposals`, `::test_loader_rejects_a_mispartitioned_thread_file` |
| R3 | major | `verify` reported success for a tampered or deleted `expected/baselines.json` | `compare_file` replaces the directory walker for the manifest, with explicit absence handling; CLI gains `--baselines` | `test_fixture_drift.py::test_drift_detection_fails_when_the_baseline_manifest_is_tampered`, `::test_drift_detection_fails_when_the_baseline_manifest_is_missing` |
| R4 | minor | Thread and sample-findings loaders served files declaring an unsupported `schema_version` | Shared `require_supported_schema_version` used by the snapshot, thread, findings, and candidate-index loaders | `::test_served_responses_reject_an_unsupported_schema_version`, `::test_snapshot_and_index_versions_are_enforced` |
| R5 | minor | The generator inherited `GIT_DEFAULT_HASH`, so baselines differed under another object format | `GIT_DEFAULT_HASH=sha1` pinned in the generator environment and documented | `test_fixture_repo.py::test_generator_pins_the_object_format` |
| R6 | minor | The fingerprint test took its expected value from the production helper | Three independently computed fingerprint vectors with duplicate and out-of-order ids | `test_domain_contracts.py::test_fingerprint_matches_an_independently_computed_vector` |
| R7 | minor | The review prompt's fixture-test command failed collection | Prompt now runs pytest from each worktree root and explains why | — (documentation; exercised manually) |
| R8 | major (evidence gap) | Round 1 raised: no recorded human review of the hand-labeled oracle (`AGENTS.md` invariant 6) | Repository-owner attestation recorded (`docs/reviews/M0-oracle-human-review.md`), tied to the three files' sha256 values at `191c829`; final disposition in round 2 | — (human record, not an automated test) |

Unverified by review (state honestly in any report): general staleness/failure classification for
inputs other than the fixture's `REQ-001` case; hosted Linux CI; and side-effect freedom for
future provider plugins. (Cross-environment reproducibility was R5 and is now pinned; the
hand-labeled oracle's human review is now attested by the repository owner at revision
`191c829` — see `docs/reviews/M0-oracle-human-review.md`.)

## Next tasks (in order)

| # | Task | Issue | Acceptance condition |
| --- | --- | --- | --- |
| 1 | **Re-review M0** against the repair commits (prompt: `docs/reviews/M0-review-prompt.md`, section "For a re-review after repairs"). Round 1 done: R1–R7 repaired, all M0 acceptance criteria PASS, R8 raised; the owner's oracle attestation is recorded. Round 2 must carry the final verdict. | #18, #19 | Every R1–R7 finding reported `repaired` with command output; no open major finding |
| 2 | Land the review verdict and close the M0 stories | #18, #19 | PR #38 no longer a draft; FT-01/FT-02 acceptance criteria demonstrably pass; the milestone exit gate is recorded in this file |
| 3 | Then start B-PR1 / C-PR1 / A-PR1 in parallel | #20, #21, #23 / #2, #26 / #30 | See `docs/stories/M0-foundation.md` for the per-stream acceptance conditions |

M1 does not start before task 1 passes: a milestone closes only when an independent review has no
open major finding (`AGENTS.md`, milestone definition of done). This session stopped at M0 and
made no push; no M1 work has started.

## Verification commands (copy/paste)

```bash
uv sync --project backend
uv run --project backend python tools/fixturectl.py verify
uv run --project backend pytest backend/tests -q
uv run --project backend uvicorn app.main:app --reload   # then GET /api/threads/REQ-001?baseline=baseline-b
```
