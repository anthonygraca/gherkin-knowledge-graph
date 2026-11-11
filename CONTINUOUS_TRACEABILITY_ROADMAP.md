# Continuous Traceability Assurance — Project Roadmap & Coding-Agent Handoff

**Status:** Proposed; implementation status unknown until the repository is inspected.  
**Version:** 0.1 · **Date:** 2026-11-10  
**Audience:** Three developers and coding agents such as Codex.  
**Working name:** Gherkin Digital Thread / Continuous Traceability Assurance (CTA).

> This is a planning and handoff document, not a claim that any component exists. A coding agent must first inspect its working directory and report what is present before changing code.

## 1. Mission and target demonstration

Build an inspectable digital thread connecting software **requirements → Gherkin scenarios → source code → automated tests → execution evidence**, then continuously identify incomplete traceability, failed verification, and evidence that may need reverification following code changes. Add local embedding-based discovery to propose *candidate* missing links, with human review and provenance.

**The first end-to-end demonstration:** Given a synthetic requirement `REQ-001`, show its linked Gherkin scenario, implementation, test, and baseline-specific evidence. Change the implementation at a second Git baseline; detect the change and report `reverification_required` without claiming the requirement has failed. The whole demo must run without a DGX Spark, hosted LLM, or live embedding service.

### Non-goals for the MVP
- Automatic proof that requirements are satisfied by semantic similarity.
- Automatic approval or merging of AI-suggested links or code changes.
- Immediate connectors to DOORS, Jama, GitHub Enterprise, or MBSE platforms.
- Deploying a multi-node vLLM cluster before the core domain functionality exists.
- A production-grade regulated compliance platform.

### Architectural principles
1. **Facts, proposals, and verification are separate.** A proposed link is not an accepted link; an accepted link is not verified behavior.
2. **Offline-first.** Contributors can develop and test with synthetic fixtures and fake adapters.
3. **Provider independence.** Embedding and LLM backends are optional plugins behind stable interfaces.
4. **Version-aware evidence.** Every relevant artifact and verification result is tied to a source revision or immutable content fingerprint.
5. **Explainability.** Every assurance finding identifies artifacts, provenance, baseline, triggering rule, and evidence.
6. **Reproducibility.** A small labeled synthetic repository serves as the shared test oracle.
7. **Vertical slices.** Integrate thin, end-to-end behavior before adding breadth.

## 2. Three parallel workstreams

| Workstream | Owner | Responsibilities | Independent demonstration | Does not depend on |
|---|---|---|---|---|
| **A — Semantic discovery** | Developer A / technical lead | `CandidateDiscovery` interface, fake provider, local EmbeddingGemma 2 adapter, indexing/retrieval, retrieval evaluation | Given `SCN-001`, return ranked candidate source artifacts from fixture data (fake first, local model later) | Live DGX Sparks, shared Qdrant, finished UI |
| **B — Digital thread** | Developer B | Artifact ingestion, Gherkin/Markdown/Git parsers, artifact and link storage, revision/provenance model, thread API | Import synthetic repo and query `REQ-001` across scenarios, source and tests | Embedding model, LLM, UI |
| **C — Assurance + UI** | Developer C | Deterministic rules, findings, human link review, React/TypeScript dashboard, API consumers | Load fixture API and demonstrate gaps, reverification findings, and reviewer decisions | Live inference, finished database, production services |

**Shared platform responsibilities (assign explicit owners):** Developer B leads schemas and example payloads; Developer C owns UI API consumption and contract checks; Developer A owns discovery contract and evaluation methodology. All three review cross-boundary changes.

## 3. Proposed modular architecture

```text
Synthetic Git repo / later real repositories
       |  requirements, .feature files, source, tests, CI evidence
       v
 [Ingestion adapters]  ----------------------------+
       |                                            |
       v                                            v
 [Artifact + relationship store] <---- [Link review / decision API]
       |                 ^                         ^
       |                 |                         |
       v                 |                         |
 [Deterministic assurance engine]        [Candidate discovery API]
       |                                            ^
       v                                            |
 [Findings API]                             [Fake provider] OR
       |                                    [EmbeddingGemma 2 + local
       v                                     vector index (+ optional LLM)]
 [React/TypeScript dashboard]
```

**Initial technology choices (not prerequisites):** Python 3.11+, FastAPI/Pydantic, pytest; React + TypeScript, Vite, Vitest; SQLite for first local artifact/link store; Git CLI or library for fixture revision inspection. Later, evaluate PostgreSQL and a graph database. For embedding retrieval, start with a fake provider, then local Sentence Transformers and Qdrant local mode. A centralized vLLM/Qdrant deployment on a four-DGX Spark homelab is a later option, not a required dependency. Verify the exact EmbeddingGemma 2 model identifier, model instructions, runtime compatibility, and terms during AI-02 implementation rather than assuming a prior example is production-ready.

### Boundary interfaces (conceptual)
- **`ArtifactRepository`**: ingest/upsert artifact versions; fetch by stable ID and revision; traverse typed accepted links; list changed artifacts between baselines.
- **`CandidateDiscovery`**: `discover(artifact_id, top_k) -> list[TraceCandidate]`. Fake and real adapters share the same response contract.
- **`AssuranceEvaluator`**: `evaluate(baseline, policy) -> list[Finding]`. Pure rules over repository snapshots and evidence; no model calls.
- **`ReviewService`**: accept/reject a proposed link with reviewer, timestamp, reason, and immutable decision history.

**Keep semantic candidates separate from accepted digital-thread edges until reviewed.** A discovery service must not write an accepted edge directly.

## 4. Minimum domain contract

Define JSON Schemas or Pydantic models and commit example payloads during foundation work.

| Model | Required information |
|---|---|
| `Artifact` | `artifact_id`, `artifact_type` (`requirement`, `scenario`, `source`, `test`), `title`, `source_uri`, `repository`, `revision`, `content_hash`, `locator`, optional `metadata` |
| `TraceLink` | `link_id`, `source_id`, `target_id`, `relation_type` (e.g., `verified_by`, `implemented_by`, `exercised_by`), `review_state` (`proposed`, `accepted`, `rejected`), `provenance`, timestamps |
| `VerificationEvidence` | `evidence_id`, `test_id`, optional `scenario_id`, `result` (`passed`, `failed`, `skipped`), `tested_commit`, `executed_at`, `run_uri` |
| `TraceCandidate` | `source_id`, `target_id`, `proposed_relation_type`, `rank`, `score`, `discovery_provider`, `model_version`, `index_revision`, optional `rationale` |
| `AssuranceFinding` | `finding_id`/stable fingerprint, `finding_type`, `status`, `severity`, `artifact_ids`, `evaluated_baseline`, `evidence_ids`, `explanation`, `rule_id` |

**Important semantics:** An implementation change after recorded verification is a reason for *impact assessment or reverification*, not proof of failure. An unchanged code file does not itself prove verification is current if other dependencies or environments changed. Initial rules should declare and test their simplifying assumptions.

### Initial API contract

```text
GET  /health
GET  /api/artifacts/{artifact_id}
GET  /api/threads/{artifact_id}?baseline=...
POST /api/ingestion/run
POST /api/discovery
POST /api/links/{link_id}/review
POST /api/assurance/evaluate
GET  /api/findings?baseline=...
```

Document exact request/response examples and error behavior before independent implementation. Generate OpenAPI from FastAPI; write API tests against examples. Endpoints above are *proposed*, not already implemented.

## 5. Shared synthetic repository and ground truth

Create `fixtures/banking-demo/` as a deliberately small engineering repository, with real, reproducible Git baseline tags or SHAs:

```text
fixtures/banking-demo/
  requirements/REQ-001.md
  requirements/REQ-002.md
  requirements/REQ-003.md
  features/withdrawals.feature
  features/transfers.feature
  src/accounts.py
  src/transfers.py
  tests/test_accounts.py
  tests/test_transfers.py
  evidence/verification-runs.json
  evidence/accepted-links.json
  expected/baseline-a.json
  expected/baseline-b.json
  expected/candidate-links.json
```

**Fixture cases and oracle:**
1. Healthy chain with passing evidence at evaluated baseline.
2. Requirement without an accepted Gherkin scenario link → `missing_verification_link`.
3. Scenario without accepted implementation link → `missing_implementation_link`.
4. A code change after the most recent relevant test execution → `reverification_required` (do not mark failed).
5. Explicit failing test at current baseline → `verification_failed`.
6. Semantically plausible but unreviewed proposed link → `candidate_pending_review`.
7. Superseded requirement with legacy relationships → `lifecycle_review_required` (stretch).

**Fixture discipline:** Do not invent expected results from the embedding model's output. Hand-label the ground truth and include negative examples. Use deterministic offline findings and tests. For Git history, if fixture files are stored inside the main repo, provide a script that generates a small *nested fixture repository* with tags `baseline-a` and `baseline-b`; never silently depend on the parent's commit history.

## 6. Backlog — features and stories

Priority: **P0** is AI-free MVP; **P1** adds candidate discovery/review; **P2** adds repository-change automation and extended evaluation.

| Feature | Story | Description / demonstrable result | Owner | Priority |
|---|---|---|---|---|
| F-01 Foundation | FT-01 | As a developer, I want labeled fixture repos and baseline oracles so I can test without external systems. | B lead | P0 |
| F-01 Foundation | FT-02 | As a developer, I want versioned API/domain contracts plus mock responses so I can build independently. | B lead | P0 |
| F-02 Ingestion | DT-01 | As a systems engineer, I want requirements and Gherkin scenarios parsed into stable artifacts. | B | P0 |
| F-02 Ingestion | DT-02 | As an engineer, I want source and test artifacts tied to path and Git revision. | B | P0 |
| F-03 Links | DT-03 | As an engineer, I want typed, provenance-aware traceability links. | B | P0 |
| F-03 Links | DT-04 | As a reviewer, I want to retrieve the thread associated with a requirement. | B | P0 |
| F-04 Evidence | DT-05 | As a verification engineer, I want test outcomes associated with exact tested commits. | B | P0 |
| F-04 Evidence | DT-06 | As an engineer, I want changed artifacts and impacted accepted links between baselines. | B | P0 |
| F-05 Assurance | AS-01 | As a systems engineer, I want missing coverage/link findings. | C | P0 |
| F-05 Assurance | AS-02 | As a verification engineer, I want potential stale-evidence findings after relevant changes. | C | P0 |
| F-05 Assurance | AS-03 | As a reviewer, I want failed, missing, and potentially stale evidence kept distinct. | C | P0 |
| F-06 UI | AS-04 | As a lead, I want a summary of findings and coverage counts. | C | P0 |
| F-06 UI | AS-05 | As a reviewer, I want drill-down into findings and their evidence. | C | P0 |
| F-07 Review | AS-06 | As a reviewer, I want to accept/reject proposed links with audit details. | C | P1 |
| F-07 Review | AS-07 | As a reviewer, I want useful behavior when AI is offline and clear fake/real provenance. | C | P1 |
| F-08 Retrieval | AI-01 | As a developer, I want fake and real `CandidateDiscovery` implementations behind one interface. | A | P0 |
| F-08 Retrieval | AI-02 | As a developer, I want local EmbeddingGemma 2 inference without shared DGX services. | A | P1 |
| F-08 Retrieval | AI-03 | As a developer, I want revision-aware incremental embedding refresh. | A | P1 |
| F-09 Discovery | AI-04 | As a systems engineer, I want ranked candidate code/scenario/requirement links, labeled as proposals. | A | P1 |
| F-09 Discovery | AI-05 | As a researcher, I want labeled precision/recall and recall@k evaluation of retrieval. | A | P1 |
| F-10 Automation | CI-01 | As a developer, I want assurance to run when a repo revision changes. | Shared | P2 |
| F-10 Automation | CI-02 | As a reviewer, I want new, unchanged, and resolved findings between baselines. | Shared | P2 |

### Representative executable acceptance criteria

**AS-01 — missing scenario link**
```gherkin
Scenario: Requirement has no accepted verification scenario
  Given requirement "REQ-002" exists
  And no accepted verification scenario is linked to "REQ-002"
  When assurance evaluates baseline "baseline-a"
  Then a "missing_verification_link" finding is produced for "REQ-002"
```

**AS-02 — potential staleness, not failure**
```gherkin
Scenario: Implementation changed since verification
  Given "SCN-001" verifies "REQ-001"
  And a test for "SCN-001" passed at baseline "baseline-a"
  And a relevant linked implementation changed at baseline "baseline-b"
  And no later matching verification evidence exists
  When assurance evaluates baseline "baseline-b"
  Then a "reverification_required" finding is produced
  And the finding identifies both baselines and the changed artifact
  And "REQ-001" is not marked "verification_failed"
```

**AS-06 — proposal approval is not verification**
```gherkin
Scenario: Reviewer accepts a semantic candidate link
  Given a proposed link between "SCN-001" and "CODE-001" exists
  When an authorized reviewer accepts the link
  Then its review state becomes "accepted"
  And reviewer identity, time, and provenance are recorded
  And requirement verification status is unchanged
```

**AI-04 — contract-level candidate discovery**
```gherkin
Scenario: Discover likely implementation from an unlinked scenario
  Given the candidate-discovery provider is "fake"
  And "SCN-001" has no accepted implementation link
  When candidates are requested for "SCN-001"
  Then "CODE-001" is returned as a proposed link
  And the response includes its provider and index revision
  And no link is automatically accepted
```

## 7. Milestones and independent exit criteria

### M0 — Contract + fixture foundation (all three; B coordinates)
**Deliver:** repository layout, setup guide, fixture generator, tagged baselines, labeled expected outputs, Pydantic contracts, OpenAPI stub/examples, fake candidate provider, sample findings response, initial CI workflow.

**Exit:** A new developer can clone, run a documented command, and execute deterministic tests with no network or AI services. Mock APIs return schema-valid fixture data. Everyone can begin independently.

### M1 — AI-free vertical slice (B + C; A maintains adapter)
**Deliver:** ingestion of one requirement, one Gherkin scenario, code, test, and an accepted relationship chain; `GET /api/threads/{id}`; rule `missing_verification_link`; UI shows a thread and finding.

**Exit:** Demo `REQ-001` digital thread and one intentionally missing link end-to-end; all tests run without GPU/embedding dependency.

### M2 — Version-aware continuous assurance (B + C)
**Deliver:** Git baseline comparison, test execution evidence, `reverification_required` rule, failure vs missing vs stale distinction, findings drill-down.

**Exit:** A baseline A → B change creates a justified reverification finding but does not falsely report verification failure; evidence identifies the tested commit and changed source artifact.

### M3 — Local semantic discovery (A leads; B + C integrate)
**Deliver:** local model adapter, normalized document/query formatting, local vector index, `POST /api/discovery`, proposed-link review workflow, evaluation report against labeled fixtures.

**Exit:** Fake and real providers pass the same contract tests. Real retrieval results are measured against the benchmark, not treated as ground truth. Offline fake mode still works.

### M4 — Continuous integration and research comparison (all)
**Deliver:** revision-triggered assurance workflow, baseline findings diff, optional shared model hosting, comparison between explicit-link-only, embedding-assisted, and optionally LLM-assisted methods.

**Exit:** Reproducible benchmark report with methodology, known limitations, runtime/cost observations and measurable benefit or lack thereof from AI.

**Ordering:** M0 precedes independent development. M1/M2 do not wait for M3. Start M3 work in parallel after M0, but merge through contracts only.

## 8. Proposed repository structure (create only if absent)

```text
continuous-traceability/
  AGENTS.md                   # Codex conventions and project invariants
  README.md
  docs/
    ROADMAP.md                # this document
    architecture.md
    domain-contracts.md
    adr/
  backend/
    app/
      api/
      domain/
      ingestion/
      assurance/
      discovery/
      persistence/
    tests/
  frontend/
    src/
    tests/
  fixtures/
    banking-demo/
    api-responses/
    expected/
  tools/
    generate_fixture_repo.py
  scripts/
  pyproject.toml              # or backend/pyproject.toml; choose once
  docker-compose.yml          # optional; no required AI services
  .github/workflows/ci.yml
```

Separate workstream packages to minimize conflicts. A simple monorepo is preferable initially to multiple service repos; logical boundaries do not require separate deployables.

## 9. Testing, quality gates, and definition of done

**Layer 1: default offline (required for every PR):** parser unit tests; rule tests; API schema/contract tests; fake discovery tests; UI component tests; fixture-based baseline comparisons. Must not download model weights or require Spark, Docker, cloud, or Qdrant server.

**Layer 2: optional local integration:** SQLite, local Qdrant mode or in-memory vectors, real HTTP endpoints, generated fixture Git history. May run on a laptop.

**Layer 3: optional AI evaluation:** EmbeddingGemma 2 or other model, retrieval quality benchmark (recall@1/5/10, precision@k, false candidate rate), latency and index-refresh behavior. Version the evaluation dataset and model details.

**Every story is done only when:** acceptance criteria are tested; fixtures cover success and failure; source provenance and revision are preserved when applicable; API examples are updated; tests pass offline; docs include an invocation/demo; code is reviewed. Explicitly document any assumptions in freshness rules.

**Security and correctness:** No secrets in fixtures. Treat indexed repository text as untrusted input. No unreviewed AI result should be promoted to accepted link or verification evidence. Never silently mix embeddings from different models/index versions in one vector collection.

## 10. First parallel pull requests after M0

- **A-PR1 (Developer A):** `CandidateDiscovery` protocol, a JSON-fixture implementation, provider configuration, contract tests; no real embedding dependency. Return candidates for `SCN-001`.
- **B-PR1 (Developer B):** Parse a Markdown requirement and tagged `.feature` scenario into normalized `Artifact`s; return a minimal `REQ-001` thread using SQLite or in-memory persistence.
- **C-PR1 (Developer C):** Evaluate a fixture-provided thread for missing scenario links, expose a mock findings API, and display one finding in the UI.

**Integration gate:** All three PRs pass on a new machine in fake/offline mode. Do not block merging any one stream on the availability of other streams' real implementations.

## 11. Open decisions (record as ADRs instead of blocking M0)

1. **Artifact granularity:** file-level source initially; functions/classes later if justified.
2. **Storage:** SQLite for MVP, migrate or add graph DB when graph queries require it.
3. **Identity strategy:** stable logical artifact ID plus revision-specific record; define how renamed files are handled.
4. **Evidence freshness policy:** what changes count as relevant and how to treat environment/dependency changes.
5. **Embedding provider:** local EmbeddingGemma 2 text-only as an evaluation candidate; compare Qwen variant if needed. Confirm current model/runtime specifications before implementation.
6. **Graph semantics:** accepted relations vs candidate proposals; directionality and allowed relation types.
7. **Team workflow:** conventional PR review, one story per PR when practical, and contract changes reviewed by affected owners.

## 12. Instructions for a new Codex session

A coding agent should begin with the following workflow:

1. Read this document and inspect the actual repository (`pwd`, files, existing tests). **Do not assume this architecture or any milestone has been implemented.**
2. Report what exists, what is missing, and any conflicts with the plan. Preserve existing functionality.
3. If the repository is empty, implement only **M0** first. Do not start full AI integration or choose a graph database prematurely.
4. Establish schemas, deterministic fixture history, mocks, tests, and developer commands before creating substantial application code.
5. Use `AGENTS.md` for repo-specific coding conventions. Prefer small, reviewable patches.
6. Run the narrowest relevant tests and, when feasible, the offline suite. Report commands and results honestly.
7. At the end, summarize changed files, tests, unresolved decisions, and an exact next task for another developer.

### Copy/paste kickoff prompt

> You are the coding agent for a new project called **Continuous Traceability Assurance (CTA)**. Read `CONTINUOUS_TRACEABILITY_ROADMAP.md` (or `docs/ROADMAP.md`) in full. Our product connects requirements, Gherkin scenarios, implementation, tests, Git revisions, and verification evidence, and flags gaps or potentially stale evidence. The team has three parallel workstreams: A semantic discovery, B digital-thread ingestion/storage, C assurance/UI. **Offline/mock-first operation is mandatory; do not require any GPU, vLLM server, LLM, or embedding model for default development and tests.** Candidate semantic links must never be treated as accepted or verified relationships.
>
> First inspect the repository and tell me what is actually present. If this is an empty/new repository, implement **Milestone M0 only**: repository scaffold, versioned domain schemas/contracts, a synthetic banking fixture repo with real baseline-a/b Git history and labeled expected outcomes, deterministic fake discovery data, offline tests, and setup documentation. Make sensible small decisions and record them as ADRs. Do not invent external services or claim model inference works without testing it. Then run the tests and report files changed, results, and the three independently assignable follow-on PRs (A-PR1, B-PR1, C-PR1). If the repository already contains work, identify the next incomplete milestone and propose the smallest safe vertical slice before editing.

## 13. Session continuity template

Update this section after each coding session, or keep it in `docs/STATUS.md`:

```text
Date:
Current branch / commit:
Milestone completed or underway:
Implemented stories:
Tests executed and results:
Current API/schema version:
Unresolved decisions / known gaps:
Environment requirements:
Next three tasks (owner + acceptance condition):
```

**Definition of project success for the first release:** A reviewer can inspect a reproducible, revision-specific requirement-to-verification thread and distinguish confirmed failures, coverage gaps, potentially stale evidence, and unreviewed semantic suggestions—without depending on a permanently online AI cluster.
