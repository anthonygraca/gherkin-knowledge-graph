# Status

```text
Date:                2026-11-10
Current branch:      main (uncommitted working tree of M0 work at time of writing; see git log)
Milestone completed: M0 — Contract + fixture foundation
Implemented stories: FT-01, FT-02 (foundation). Platform tasks M0-P1, M0-P2, M0-P3.
Tests executed:      uv run --project backend pytest backend/tests -q  →  92 passed
                     uv run --project backend python tools/fixturectl.py verify  →  exit 0
                     uv run --project backend ruff check … && ruff format --check …  →  clean
Current API/schema version: 0.1.0
Environment requirements: Python ≥3.11, uv, git ≥2.28. No GPU, no LLM, no vector store, no Docker,
                     no network during tests.
```

## What exists

* Reproducible fixture history for `banking-demo`: four commits, fixed SHAs, tags `baseline-a`
  and `baseline-b`, verified identical across builds.
* Hand-labeled oracle: coverage gaps, a pending proposal, a superseded requirement, a
  reverification case, and a confirmed failure — plus explicit negative expectations.
* Domain contracts: artifacts, links, evidence, candidates, findings, envelopes, ports, error
  codes, severity policy, stable finding fingerprints.
* Mock services: fixture-backed `FixtureStore`, `SampleFindingsSource` (findings replay), and the
  fixture `CandidateDiscovery` provider. All offline.
* API: reads and discovery implemented; three endpoints frozen as contracts and returning 501
  with the owning story.
* Tests: 92 offline tests, including proof that the committed generated fixtures are what the
  generator produces, and proof that the fixture's own suite passes at `baseline-a` and fails
  exactly twice at `baseline-b`.

## Known gaps (deliberate, owned by later stories)

| Gap | Owner |
| --- | --- |
| No rule engine: findings are a replay of reviewed samples | AS-01…AS-03 (C-PR1) |
| No ingestion, no SQLite store, threads only for requirement roots | DT-01, DT-02, DT-04 (B-PR1) |
| No link review/audit trail | AS-06 (C, M1/M2) |
| No frontend | AS-04, AS-05 (C-PR1) |
| No real embedding model; retrieval quality unmeasured | AI-02, AI-03, AI-05 (A, M3) |
| No baseline-to-baseline findings diffing | CI-02 (M4) |

## Unresolved decisions

Recorded in `docs/adr/0006-deferred-decisions.md`: storage engine (SQLite for MVP, PostgreSQL/graph
later), embedding provider and index, graph semantics beyond the three relation types, artifact
granularity below file level, frontend stack details, and authentication. None block M1.

## Next three tasks

| # | Owner | Task | Acceptance condition |
| --- | --- | --- | --- |
| 1 | B | **B-PR1** (DT-01, DT-02, DT-04): parse requirements and Gherkin into the same `Artifact` contract, persist in SQLite or memory, serve `REQ-001`'s thread from parsed data | `GET /api/threads/REQ-001` returns the same artifact set, accepted links, and evidence as the fixture thread for `baseline-a`, and the fixture oracle tests still pass |
| 2 | C | **C-PR1** (AS-01, AS-04, AS-05): deterministic `missing_verification_link` and `missing_implementation_link` rules over the store, findings served from the engine rather than replayed, one dashboard view | `GET /api/findings?baseline=baseline-a` equals the hand-labeled oracle exactly (both missing-link findings present, `REQ-001` absent), and `REQ-001` has no finding |
| 3 | A | **A-PR1** (AI-01): harden and document the `CandidateDiscovery` contract, add provider configuration tests, prepare the retrieval-evaluation dataset (labels already in `expected/candidate-links.json`) | Fake provider passes the contract tests; an evaluation harness reports recall@k against the labeled positives and negatives without any model dependency |

Integration gate for all three: pass on a clean machine in fake/offline mode; no stream blocked by
another stream's real implementation.

## Verification commands (copy/paste)

```bash
uv sync --project backend
uv run --project backend python tools/fixturectl.py verify
uv run --project backend pytest backend/tests -q
uv run --project backend uvicorn app.main:app --reload   # then GET /api/threads/REQ-001?baseline=baseline-b
```
