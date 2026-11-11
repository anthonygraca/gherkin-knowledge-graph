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

| Finding | Severity | What it means | Owning story |
| --- | --- | --- | --- |
| R1 | major | `FixtureStore` does not satisfy the declared `ArtifactRepository` port (different method names/signature), and routes depend on the concrete class, so a consumer written against the port cannot use the mock | FT-02 (#19) |
| R2 | major | `ThreadResponse` accepts a non-accepted link inside `accepted_links`; the invariant is enforced in the snapshot model but not at the response boundary | FT-02 (#19) |
| R3 | major | `fixturectl.py verify` reports success for a tampered or deleted `expected/baselines.json` (it compares two file paths with a directory walker) | FT-01 (#18) |
| R4 | minor | Thread and sample-findings loaders serve files declaring an unsupported `schema_version` | FT-02 (#19) |
| R5 | minor | The generator inherits `GIT_DEFAULT_HASH`, so baselines built under a different object format differ (pinning the format at `git init` is required) | FT-01 (#18) |
| R6 | minor | The fingerprint test takes its expected value from the production helper, so a SHA-1 mutation passes; an independent fixed vector is required | FT-02 (#19) |
| R7 | minor | The review prompt's direct fixture-test command fails collection unless run from the worktree root | FT-01 (#18) |

Unverified by review (state honestly in any report): that the oracle labels were reviewed by a
human rather than authored by the generator's session; general staleness/failure classification for
inputs other than the fixture's `REQ-001` case; hosted Linux CI; and side-effect freedom for future
provider plugins.

## Next tasks (in order)

| # | Task | Issue | Acceptance condition |
| --- | --- | --- | --- |
| 1 | Repair R1 — reconcile the port with the store and make routes consume the port | #19 | A consumer that imports only `ArtifactRepository` can read artifacts, links, evidence, and changed ids from the mock; `isinstance(store, ArtifactRepository)` holds |
| 2 | Repair R2, R4, R6 — enforce link partitioning and version support at the response boundary; add an independent fingerprint vector | #19 | A proposal placed in `accepted_links` is rejected by the loader; a mismatched `schema_version` raises the documented fixture error; a SHA-1 fingerprint mutation fails the suite |
| 3 | Repair R3, R5, R7 — manifest-aware `verify`, pinned object format, corrected review command | #18 | Tampering with or deleting `expected/baselines.json` makes `verify` exit non-zero and name the file; `GIT_DEFAULT_HASH=sha256` no longer changes the tags; the review command runs from the worktree root |
| 4 | Then start B-PR1 / C-PR1 / A-PR1 in parallel | #20, #21, #23 / #2, #26 / #30 | See `docs/stories/M0-foundation.md` for the per-stream acceptance conditions |

## Verification commands (copy/paste)

```bash
uv sync --project backend
uv run --project backend python tools/fixturectl.py verify
uv run --project backend pytest backend/tests -q
uv run --project backend uvicorn app.main:app --reload   # then GET /api/threads/REQ-001?baseline=baseline-b
```
