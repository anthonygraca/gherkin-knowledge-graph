# Codex Kickoff — Continuous Traceability Assurance

You are helping implement **Continuous Traceability Assurance (CTA)**, also called the **Gherkin Digital Thread** project.

**Before coding, read `CONTINUOUS_TRACEABILITY_ROADMAP.md` (or `docs/ROADMAP.md`) completely.** This is a plan, not evidence that the system has been implemented. Inspect the current working directory and repository first, report the actual state, and preserve existing work.

## Product
Connect requirements, Gherkin scenarios, source code, tests, Git revisions, and execution evidence in a queryable digital thread. Detect missing relationships, verification failures, and evidence that may require reverification after relevant changes. Later add embedding-based semantic discovery to **propose** links for human review.

## Three independent developers
- **A:** semantic discovery, fake adapter, local EmbeddingGemma 2 integration, retrieval evaluation.
- **B:** fixtures, artifact parsing, revision-aware storage, typed links, thread API.
- **C:** deterministic assurance, findings, human review, React dashboard.

## Non-negotiable architecture constraints
1. No GPU, DGX Spark, vLLM, remote LLM, or live embedding model required for normal offline development/tests.
2. Fake services and fixtures must have the same contracts as real adapters.
3. Keep **proposed**, **accepted**, and **verified** separate; embedding similarity is not proof.
4. Preserve commit SHA, source location, provenance, and evidence baseline.
5. Version-aware source changes may require reverification; do **not** equate them with failed verification.
6. Synthetic Git fixture contains real `baseline-a` and `baseline-b` revisions plus hand-labeled expected results.
7. Use small, testable PR-sized changes and document decisions that cross workstreams.

## Your first action
1. Inspect files, current branch, tests and tooling; state what exists and what is missing relative to the roadmap.
2. If empty/new, implement **Milestone M0 only**: repo scaffold; typed domain schemas and API examples; a reproducible banking-demo fixture generator with two Git baseline tags and expected outputs; fake `CandidateDiscovery`; automated offline tests; setup/README; optional AGENTS.md.
3. If already underway, identify the next incomplete milestone and implement the smallest useful vertical slice.
4. Run relevant tests, report exact results, changes, unresolved decisions, and three parallel follow-on assignments.

Do not deploy an LLM or select a production vector/graph database as a prerequisite for M0. If a decision is not necessary yet, document it as deferred rather than blocking progress.
