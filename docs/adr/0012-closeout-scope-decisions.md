# ADR 0012 — Close-out decisions for review, snapshot lifecycle, and CI assurance (proposed)

**Status:** Proposed; owner dispositions required · 2026-11-14
**Stories:** AS-06 (#28), AS-07 (#29), AI-02 (#31), AI-03 (#32), CI-01 (#36), CI-02 (#37)
**Source:** Codex advisory `docs/reports/omp-closeout/advice/closeout-advice.md`; issue bodies.

This ADR records the design defaults proposed during refinement. It is **not accepted** and must not
be treated as an approved product decision until the owner dispositions below are recorded.

## 1. AS-06 review identity and decision journal

Proposed: trusted-local-operator mode. Review writes require an operator identity configured at
application startup (outside the ingested repository); the server assigns it and rejects a
caller-supplied `reviewer_id` that differs. Review endpoints bind to loopback with browser-origin
restrictions. No authentication service is introduced. Unset identity disables review writes.

Residual risk: any process/person with access to the local account can act as the operator; this does
not authenticate a distinct human or support multiple reviewers.

Proposed persistence: an append-only application-owned journal outside the fixture and evaluated
repository; a review workspace projection overlays decisions on immutable baseline reads; baseline
reads/findings/evidence remain unchanged. Capture of a `TraceCandidate` is an explicit separate action;
discovery never writes a proposed link.

**Owner decision:** accept the trusted-local-operator limitation or require stronger identity.

## 2. AI-03 re-scope

ADR 0008 assigns source-code chunking, embeddings, incremental indexing, and vector storage to
CocoIndex. The original AI-03 obligation (“only changed artifacts re-embedded; unchanged vectors
retained”) cannot be substantiated through the MCP contract. Proposed re-scope: CTA owns content-hash
change planning, corpus cache keys, configuration-compatibility manifests, isolated snapshot
publication, and honest refresh reporting. CocoIndex internal embedding counts are reported as
`not_available`, never inferred.

**Owner decision:** adopt the re-scope/supersession, or keep the original obligation and accept that
AI-03 remains blocked until an observable backend capability exists.

## 3. CI assurance scope and report contract

Proposed: two explicit scopes — CTA portable self-assurance (`gherkin_executability` with attributable
Cucumber reports) and banking fixture requirement/evidence assurance. Reports are typed, revision-bound
(evaluator revision and evaluated revision), stored as workflow artifacts/job summaries, never committed
to branches. Exit `0` means evaluation completed (even with findings); exit `2` means tool failure and
must not be converted into a finding.

CI-02 uses the existing stable finding fingerprint and requires complete, comparable reports. Portable
source-locator identities are **not comparable** without an independently reviewed continuity mapping;
the diff refuses them rather than classifying displacement as resolved/new.

**Owner decision:** accept the two-scope framing and the portable-comparison limitation.

## 4. AI-02 local model

No model/runtime/licence decision is made here. The external Ollama endpoint does not satisfy the
“no request leaves the machine” criterion. Implementation remains blocked until the owner accepts a
concrete same-machine model manifest, weights digest, licence, and hardware configuration.
