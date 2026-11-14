# Advisory request — refine the six remaining CTA stories before implementation

You are Codex advising the CTA maintainer, not implementing and not performing acceptance review.
Do not edit files, install dependencies, run the suite, or delegate. Read-only. Return one Markdown
document.

## Repository snapshot

- Repository: `anthonygraca/gherkin-knowledge-graph`, base `140e98c` plus uncommitted advisory docs only.
- Schema `0.5.0`; offline default; `FakeCandidateDiscovery` is the only default provider.
- M0/M1/M2 engineering gates satisfied. M3 has no GitHub milestone object.
- Lifecycle (`docs/development-lifecycle.md`, `AGENTS.md`): every story needs canonical
  `docs/stories/<ID>.feature` with a unique `@SCN-nnn` per scenario, a Markdown companion with
  source/rationale/scope/dependencies/owner/GitHub issue/verification plan/review disposition, and
  independent acceptance review before implementation acceptance. Issue prose is not the canonical
  specification.
- Existing scenario IDs run through `@SCN-2603` (AI-05). Use a **new non-colliding range**, e.g.
  `@SCN-3001+`, and do not renumber existing scenarios.
- Invariants: proposals ≠ accepted links ≠ evidence; accepted links are not verification; a passing
  test is configuration-specific; LLM output is never authoritative; revisions + content hashes;
  change ≠ failure; offline default; honest contracts (501/typed errors, no fake success); no
  secrets/untrusted repository instructions; no deployment.
- Existing implementation: typed Artifact/TraceLink/VerificationEvidence/AssuranceFinding; immutable
  fixture store; M2 deterministic rules and findings; AI-07 code retrieval; AI-08 answers; AI-09
  benchmark. `POST /api/links/{link_id}/review` is a 501 contract stub.
- Deferred decisions (`docs/adr/0006`): no auth/roles yet; AS-06 must enforce reviewer identity, not
  just record it. AI-02 must select/verify an actual local model, runtime, licence, hardware.
  ADR 0008 adopted CocoIndex Code for source-code indexing; AI-03's original CTA-owned embedding
  index may conflict with that and needs an explicit scope disposition.
- CI only validates this project today; CI-01/02 are P2/M4-style automation. PR 4 benchmark exists but
  does not close M4. M3/M4 closure requires owner disposition and independent milestone review.

## Task

For each issue below, produce:

1. **Readiness verdict:** ready-after-spec / needs-design-decision / blocked, and why.
2. **Unresolved decisions** with a recommended default and the smallest honest assumption. Flag any
   decision that only the owner can make; do not invent approval.
3. **Canonical Gherkin** with stable new `@SCN` IDs: normal, failure, and boundary scenarios. Keep
   each scenario executable against the real app or deterministic fixtures; no placeholder steps.
4. **Companion notes:** scope, non-goals, dependencies, verification approach, ADR/schema impact.
5. **Dependency/order** across the six stories and which parent feature can close when.

Constraints to respect in your recommendations:

- Do not add authentication infrastructure unless you explicitly justify it; if the recommended
  default is a trusted-local-operator assumption, state the exact criterion wording and residual risk.
- AS-06 must use an append-only decision history and must not mutate the immutable fixture or change
  verification evidence/findings as a side effect of acceptance.
- AI-02 must mean local inference with no request leaving the machine; an external Ollama endpoint is
  not acceptable. If a model choice requires owner licence/hardware acceptance, say so.
- AI-03: recommend either a coherent CTA candidate-index incremental refresh (fake-provider testable,
  content-hash keyed, index revisions never mixed) or an explicit re-scope/supersession; do not leave
  the CocoIndex conflict implicit.
- CI-01/02 must distinguish tool failure from assurance findings, record the evaluated revision, and
  avoid committing generated findings to `main` without authorization. Prefer workflow artifacts/PR
  summary.
- AS-07 must display unavailable-provider state and provenance; do not treat a proposal as accepted.
- Keep schema additions additive and versioned; state whether `SCHEMA_VERSION` must bump.

## Issue bodies (verbatim from GitHub)

### Issue #28
AS-06 — Accept or reject proposed links with audit details

## User story (roadmap AS-06)

**As a** reviewer, **I want** to accept or reject proposed links with audit details, **so that** AI suggestions only become facts through a human decision.

**Feature:** #13 · **Priority:** P1 · **Milestone:** M3 · **Owner:** C

### Acceptance criteria (Gherkin)

```gherkin
Scenario: Reviewer accepts a semantic candidate link
  Given a proposed link between "SCN-001" and "CODE-001" exists
  When an authorized reviewer accepts the link
  Then its review state becomes "accepted"
  And reviewer identity, time, and provenance are recorded
  And requirement verification status is unchanged

Scenario: Reviewer rejects a proposal
  Given a proposed link between "REQ-002" and "SCN-002" exists
  When the reviewer rejects it with a reason
  Then its review state becomes "rejected"
  And the rejection reason is retained in the decision history
  And the link no longer counts as a pending review item
```

### Definition of done (roadmap §9)

- `POST /api/links/{link_id}/review` implemented, replacing the 501 contract stub
- Immutable decision history (append-only), not an in-place status overwrite
- Test asserts verification status and evidence are untouched by acceptance


### Issue #29
AS-07 — Useful behaviour when no discovery provider is available, with clear provenance

## User story (roadmap AS-07)

**As a** reviewer, **I want** useful behaviour when the AI is offline and clear fake/real provenance, **so that** the tool stays usable without the model.

**Feature:** #13 · **Priority:** P1 · **Milestone:** M3 · **Owner:** C

### Acceptance criteria (Gherkin)

```gherkin
Scenario: Discovery provider unavailable
  Given the configured discovery provider is not registered
  When the reviewer requests candidates
  Then the response is a 400 problem naming the failed provider
  And the response lists the providers that are registered
  And the candidate panel states that no provider is available
  And accepted links and evidence remain fully usable

Scenario: Provenance is visible for every proposal
  Given a candidate produced by the "fake" provider
  When the proposal is displayed
  Then the provider name, model version, and index revision are shown
  And a proposal produced by a real model is distinguishable from a fixture proposal
```

### Definition of done (roadmap §9)

- Provider failure surfaces as a problem document and a UI state, never as a finding or an empty success
- Provenance (`provider`, `model_version`, `index_revision`) displayed wherever a proposal appears
- Offline fake mode documented as the default development path


### Issue #31
AI-02 — Local EmbeddingGemma 2 inference without shared DGX services

## User story (roadmap AI-02)

**As a** developer, **I want** local model inference without shared DGX services, **so that** semantic discovery works on a laptop with no cluster.

**Feature:** #14 · **Priority:** P1 · **Milestone:** M3 · **Owner:** A

### Acceptance criteria (Gherkin)

```gherkin
Scenario: Local provider behind the existing contract
  Given a local embedding model is installed
  When the shared contract tests run against the local provider
  Then they pass unchanged
  And no request leaves the machine

Scenario: Model details are recorded with every candidate
  Given the local provider produced a candidate
  Then the candidate reports the model version and the index revision it came from
```

### Definition of done (roadmap §9)

- Model identifier, instructions, runtime compatibility, and licence verified at implementation time (roadmap §3 caveat), not assumed from an example
- Fake provider remains the default; tests never require the model
- Documented invocation, hardware expectations, and failure modes


### Issue #32
AI-03 — Revision-aware incremental embedding refresh

## User story (roadmap AI-03)

**As a** developer, **I want** revision-aware incremental embedding refresh, **so that** re-indexing only what changed stays cheap and honest.

**Feature:** #14 · **Priority:** P1 · **Milestone:** M3 · **Owner:** A

### Acceptance criteria (Gherkin)

```gherkin
Scenario: Only changed artifacts are re-embedded
  Given an index built for "baseline-a"
  When the repository moves to "baseline-b"
  Then only artifacts whose content_hash changed are re-embedded
  And unchanged artifacts keep their existing vectors
  And the new index revision differs from the previous one

Scenario: Index revisions are never mixed
  Given candidates produced from two different index revisions
  When results are combined
  Then they are rejected or reported separately, never merged into one ranked list
```

### Definition of done (roadmap §9)

- Refresh keyed on `content_hash`; cost measured and reported (items embedded, wall time)
- Index revision reported in every response that carries candidates
- Incremental path tested without a model, using the fixture index


### Issue #36
CI-01 — Run assurance when a repository revision changes

## User story (roadmap CI-01)

**As a** developer, **I want** assurance to run when a repository revision changes, **so that** gaps are reported continuously instead of during review.

**Feature:** #16 · **Priority:** P2 · **Milestone:** M4 · **Owner:** shared

### Acceptance criteria (Gherkin)

```gherkin
Scenario: Revision-triggered assurance
  Given a repository revision change
  When the assurance workflow runs
  Then ingestion, evaluation, and finding storage run for that revision
  And the workflow reports findings without requiring a model
  And the run records the revision it evaluated
```

### Definition of done (roadmap §9)

- Workflow defined and documented; runs offline for this repository
- Evaluated revision recorded with the findings
- Failure of the workflow distinguishes tool failure from assurance findings


### Issue #37
CI-02 — New, unchanged, and resolved findings between baselines

## User story (roadmap CI-02)

**As a** reviewer, **I want** new, unchanged, and resolved findings between baselines, **so that** I can focus on what actually changed.

**Feature:** #16 · **Priority:** P2 · **Milestone:** M4 · **Owner:** shared

### Acceptance criteria (Gherkin)

```gherkin
Scenario: Findings diff between two baselines
  Given findings for "baseline-a" and "baseline-b"
  When the diff is computed
  Then findings present at both baselines are reported unchanged via their stable fingerprint
  And findings only at "baseline-b" are reported new
  And findings present only at "baseline-a" are reported resolved
```

### Definition of done (roadmap §9)

- Diff uses the baseline-independent fingerprint; the fixture yields 2 new and 4 unchanged findings for baseline-b
- Both compared revisions are reported; a diff without them is refused
- Documented in the report format used by M4's benchmark


