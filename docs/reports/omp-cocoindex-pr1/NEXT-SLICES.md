# Next slices — independently assignable briefs (not started)

These briefs are proposals for the next mission runs. They are not implementation, approval, or
permission to start. Each requires its own verified issue and reviewed `.feature` criteria before
code changes. PR 1 is approved only as the AI-06 capability/contract/live-smoke slice.

## PR 2 — artifact-aware discovery using CocoIndex Code

**Verified mapping to re-check at start:** AI-06 [#56](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/56)
(capability story), parent F-08 [#14](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/14);
AI-04 [#34](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/34) is closed at the M0
ranked-proposal contract; AI-02 [#31](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/31)
(local inference, "no request leaves the machine") and AI-03 [#32](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/32)
(revision-aware refresh) remain open; AI-05 [#35](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/35)
owns retrieval metrics.

**Product decision to record:** CocoIndex Code replaces the planned CTA-owned source-code
embedding/vector pipeline for *code* retrieval. Do **not** close AI-02 by the external-Ollama
approach, and do **not** close AI-03 without proving its canonical refresh criteria through the
CocoIndex index lifecycle. Create a new story (for example AI-07) or an explicitly reviewed AI-06
slice extension; the canonical `.feature` must be reviewed before coding.

**Scope**

1. Resolve the requested baseline tag/SHA to the exact commit. Create or use a distinct immutable
   worktree and project-local index per snapshot; never retarget a shared index. Record repository
   identity, revision, content hashes, CocoIndex version, model, isolated state/runtime, index hash,
   and timestamps.
2. Load the authoritative requirement/scenario text from the CTA store. Use a deterministic lexical
   baseline for `.feature` artifacts; CocoIndex Code's corpus does not establish scenario-aware
   parsing.
3. Build a reproducible query (stable template version). Run the deterministic lexical code-search
   baseline over the same snapshot and eligible file set.
4. Call the AI-06 client with explicit limit/paths/languages/refresh. Normalize each hit to a
   canonical artifact ID through the authoritative path/revision/content-hash mapping. Unresolved
   hits are explicit unresolved results/errors; never invent an artifact or relation. Deduplicate
   multiple chunks per artifact transparently.
5. Return `TraceCandidate` values through `CandidateDiscovery` and additive `POST /api/discovery`
   behavior (provider `cocoindex`), reporting rank, score as reported (not a probability), artifact
   IDs, revision/hash, retrieval method, model/index provenance, and uncertainty. If the response
   shape changes, bump `SCHEMA_VERSION` and update docs/clients together; keep
   `accepted_links`/`proposed_links` separate.
6. Write no accepted link, review state, evidence, finding, or verification claim.

**Proof:** fake CocoIndex response + lexical comparator contract tests offline; baseline-a SCN-001
ranked source candidates; baseline-b snapshot differs and cross-baseline results are rejected or
explicitly labelled; unresolved/ambiguous mapping cases; `.feature` limitation documented; live
evaluation only with opt-in. Measure recall@k/precision@k/MRR/false-candidate rate/latency/freshness/
contamination against independently hand-labeled cases.

**Exit:** provenance-rich, reviewable source-code candidates without mutation; every result tied to
the requested baseline or explicitly rejected/cross-baseline; at least one real live evaluation if
available.

**Gates:** M1 satisfied; M2 open; the M3/AGENTS ordering conflict remains recorded. No M2/M3
closure claim.

## PR 3 — GraphRAG evidence retrieval

**Verified mapping to re-check at start:** requires a new story issue with human-reviewed
`.feature` criteria. M1's accepted-link and thread contracts exist; the M1 gate is satisfied. PR 3
consumes only accepted links and actual evidence; do not add a graph database.

**Scope**

1. Resolve the baseline commit. Identify the requirement by stable ID (CTA-store lexical fallback);
   report which method found it. CocoIndex may retrieve related code, never replace requirement
   identity.
2. Expand only through accepted links. Proposed links are a separate labelled set and are never
   traversed as accepted.
3. Retrieve scenarios, implementation/test artifacts, and execution evidence with revisions/hashes.
   Optional CocoIndex code candidates stay outside the authoritative graph path.
4. Record every graph path: artifact sequence, link IDs, review state, baseline, evidence IDs.
5. Filter to the evaluated baseline or explicitly report a cross-baseline comparison.
6. Build a bounded context; label retrieved repository text untrusted.
7. If authorized, use a typed `ChatGenerationProvider` (fake/real) with timeout/schema validation
   and a citation whitelist. Validate every cited artifact/link/evidence ID; reject or downgrade
   unsupported citations.
8. Deterministic assurance decides findings; the model only explains. No model configured =>
   deterministic summary or explicit `NOT RUN`, never a fabricated explanation.
9. Return a typed additive response separating authoritative graph context from semantic
   candidates. Include question, baseline, answer, artifact/link/evidence IDs, source URIs/revisions,
   retrieval method, model/index provenance, uncertainty/abstention. Name the owning story; do not
   hide it in discovery.

**Required distinctions:** no evidence ≠ absent implementation; proposed ≠ accepted coverage;
passing test ≠ universal satisfaction; accepted link ≠ evidence; reverification ≠ failure; old
evidence ≠ automatically invalid.

**Proof:** REQ-001 answer matches the M1 thread with accepted link IDs/revisions/evidence; REQ-002
abstains from a verification claim; prompt-injection probes cannot create links/evidence/citations.
Chat inference is optional only if the approved story permits an explanation-free path; otherwise
record `NOT RUN` and do not close the story.

**Gates:** M1 satisfied; M2 not required unless Test D is added (then wait for M2). No GraphRAG
output presented as M1 approval. No deployment.

## PR 4 — evaluation and workflow integration

Deliver a reproducible benchmark over the synthetic banking repository with comparable inputs:
lexical code retrieval (A), CocoIndex code retrieval (B), accepted-graph traversal (C), and hybrid
retrieval (D). For A/B use identical corpus/snapshot/queries/labels; for C/D analyze the additional
accepted-graph information explicitly. Measure the metrics named in the mission, record versions,
model tags, index identity, Git SHA, query template, LLM model/prompt and usage when used, and
re-run stochastic calls enough to characterize variability. No fabricated metrics or improvement
claims; a negative result is valid. PR 4 does not close M4. M2 finding explanations wait for M2;
M2 must never depend on Ollama/CocoIndex/live LLM.
