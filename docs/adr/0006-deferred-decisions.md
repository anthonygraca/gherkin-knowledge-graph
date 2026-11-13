# ADR 0006 — Deferred decisions and their revisit triggers

**Status:** Accepted · 2026-11-10

## Context

Roadmap §11 lists open decisions that must be recorded as ADRs instead of blocking M0. This ADR
records each decision, the default already in force, and the concrete trigger that reopens it.

## Decisions held open

| # | Decision | Default in force | Rationale | Revisit trigger |
| --- | --- | --- | --- | --- |
| 1 | Storage engine | Fixture JSON read-only store (`FixtureStore`); `ArtifactRepository` port defined | Tests need no database; the port keeps the swap cheap | B-PR1 adopts SQLite (roadmap's MVP choice). Move to PostgreSQL or a graph database only when queries (traversal, blast radius, time ranges) actually need it — not on principle |
| 2 | Artifact granularity | File level | Simpler identity and hashing; a file change over-reports rather than under-reports | A concrete finding class needs sub-file resolution (then hashes must stay stable across unrelated edits) |
| 3 | Embedding provider and index | `fake` provider only; optional hosted/local providers sit behind ADR-0007 | Offline-first; retrieval quality must not be a prerequisite for domain work | AI-02 (M3) selects a local model; verify the exact model identifier, instructions, runtime compatibility, and licence at implementation time rather than trusting any prior example. Never mix embeddings from different models or index revisions in one collection |
| 4 | Graph semantics | Three relation types (`verified_by`, `implemented_by`, `exercised_by`), direction fixed per type | Smallest vocabulary the oracle and rules need | A story needs a new relation: add enum member + docs + oracle + tests in one change (additive, MINOR) |
| 5 | Frontend stack | None yet; roadmap suggests React + TypeScript + Vite + Vitest | An empty scaffold is dead weight; C-PR1 creates it with the first real view | C-PR1. Record the chosen tooling in an ADR if it diverges from the roadmap |
| 6 | Authentication and roles | None | Single-developer offline demo; review actions are unimplemented (501) | AS-06 lands: reviewer identity must be enforced, not just recorded |
| 7 | Containerisation | None | No required services; adding Docker would violate the offline-by-default rule | A real deployment target exists (M4 shared hosting) |
| 8 | Rename continuity for artifacts | Rename = new artifact | Honest and simple at this size | Renames become common → add `renamed_from` provenance (additive) |
| 9 | CI integration for repositories under assurance | None; CI only validates this project | Roadmap CI-01 is P2 | CI-01 (M4): revision-triggered assurance, findings diffing, and commit-trailer to story linking |

## Consequences

* No code may assume a database, a model, or an identity provider exists.
* Interfaces (`ArtifactRepository`, `CandidateDiscovery`, `AssuranceEvaluator`, `ReviewService`) are
  the seams where these choices will land, so the deferred decisions stay reversible.
* Commit trailers (`Story:`, `Feature:`, `Issue:`, `Workstream:`) are already machine-readable so
  CI-01 can join commits to stories without a migration.
