# ADR 0012 — Close-out decisions for review, snapshot lifecycle, and CI assurance

**Status:** Accepted (owner-disposed 2026-11-14) · 2026-11-14
**Stories:** AS-06 (#28), AS-07 (#29), AI-02 (#31), AI-03 (#32), CI-01 (#36), CI-02 (#37)
**Source:** Codex advisory `docs/reports/omp-closeout/advice/closeout-advice.md`; issue bodies.

This ADR records the design defaults proposed during refinement. The owner preapproved the
dispositions below for the close-out mission; they are accepted product decisions, not
implementation assumptions. Later decisions that cannot be derived from this record require a
separate ADR amendment.

## 1. AS-06 review identity and decision journal

**Accepted:** trusted-local-operator mode. Review writes require an operator identity configured at
application startup (outside the ingested repository); the server assigns it and rejects a
caller-supplied `reviewer_id` that differs. Review endpoints bind to loopback with browser-origin
restrictions. No authentication service is introduced. Unset identity disables review writes.

Residual risk: any process/person with access to the local account can act as the operator; this does
not authenticate a distinct human or support multiple reviewers.

**Accepted persistence:** an append-only application-owned journal outside the fixture and evaluated
repository; a review workspace projection overlays decisions on immutable baseline reads; baseline
reads/findings/evidence remain unchanged. Capture of a `TraceCandidate` is an explicit separate action;
discovery never writes a proposed link.

**Owner decision:** accepted (trusted-local-operator limitation accepted; no stronger identity).

## 2. AI-03 re-scope

ADR 0008 assigns source-code chunking, embeddings, incremental indexing, and vector storage to
CocoIndex. The original AI-03 obligation (“only changed artifacts re-embedded; unchanged vectors
retained”) cannot be substantiated through the MCP contract. **Accepted re-scope:** CTA owns
content-hash change planning, corpus cache keys, configuration-compatibility manifests, isolated
snapshot publication, and honest refresh reporting. CocoIndex internal embedding counts are reported
as `not_available`, never inferred. This supersedes the embedding-count and retained-vector wording
for AI-03; ADR 0008 and the roadmap are amended by the AI-03 change to state the same boundary.

**Owner decision:** accepted the re-scope/supersession.

## 3. CI assurance scope and report contract

**Accepted:** two explicit scopes — CTA portable self-assurance (`gherkin_executability` with
attributable Cucumber reports) and banking fixture requirement/evidence assurance. Reports are typed,
revision-bound (evaluator revision and evaluated revision), stored as workflow artifacts/job
summaries, never committed to branches. Exit `0` means evaluation completed (even with findings);
exit `2` means tool failure and must not be converted into a finding.

CI-02 uses the existing stable finding fingerprint and requires complete, comparable reports. Portable
source-locator identities are **not comparable** without an independently reviewed continuity mapping;
the diff refuses them rather than classifying displacement as resolved/new.

**Owner decision:** accepted the two-scope framing and the portable-comparison limitation.

## 4. AI-02 local model

**Accepted:** select and provision a permissively licensed, same-machine, CPU-capable local
EmbeddingGemma 2 runtime/model. No shared DGX, K3s, remote Ollama, hosted endpoint, proxy, or request
leaving the machine. Record the exact model, weights digest, runtime, licence, hardware, and measured
limits. The external Ollama endpoint used for the AI-06 smoke does not satisfy the “no request leaves
the machine” criterion.

The concrete model manifest is recorded in `docs/reports/omp-closeout/AI-02-MODEL-MANIFEST.md` at
implementation time; this ADR fixes the selection criteria, not a vendor SKU guessed before the
weights and licence are verified.
