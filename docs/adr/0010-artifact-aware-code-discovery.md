# ADR 0010 — Artifact-aware code discovery over CocoIndex Code

**Status:** Accepted · 2026-11-14 · **Story:** AI-07 ([#66](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/66))

## Context

AI-06 PR 1 delivered a bounded CocoIndex Code adapter (`CocoIndexSearchClient`,
`StdioMcpTransport`) that returns non-authoritative code chunks with `index_identity=None`.
PR 2 must turn those chunks into reviewable `TraceCandidate` proposals tied to CTA's authoritative
artifacts and exact Git baseline, without writing accepted links or evidence.

CocoIndex Code indexes code/test chunks; it does not parse Gherkin scenarios as first-class
semantic units. CTA owns artifact identity, links, evidence, and assurance policy.

## Decision

* **Two retrieval methods over one snapshot.** A deterministic lexical token-overlap baseline and
  the approved CocoIndex client both read the same eligible `source`/`test` artifacts at one commit.
  The lexical method is the offline comparator and fallback; it is not a research result.
* **Mapping is authoritative.** A hit resolves only when its path is a source/test artifact at the
  requested commit and the committed blob hash equals the artifact's `content_hash`. Unknown paths,
  hash mismatches, and out-of-range lines are explicit `UnresolvedHit`s. Multiple chunks map to one
  artifact by taking the best raw score; chunks are never promoted to new artifacts.
* **Snapshot binding, not index identity.** `index_binding` is
  `snapshot:sha256:<digest>` over repository name, commit, eligible paths, and their authoritative
  hashes. CocoIndex 0.2.43 reports no index revision; CTA does not invent one.
* **Scores are reported, not calibrated.** `raw_score` is the method's value. The existing
  `TraceCandidate.score` is the same value clamped to 0..1 and is documented as not a probability.
* **Live project is commit-pinned.** A configured `CTA_CCC_PROJECT_ROOT` must be checked out at the
  requested commit; otherwise retrieval raises a cross-baseline error. The project-local index is
  per checkout; CTA refuses to relabel one checkout's results as another baseline.
* **Additive contracts.** `POST /api/retrieval/code` returns the rich provenance view.
  `CandidateDiscovery` gains an optional `baseline` argument; `POST /api/discovery` passes it.
  The `cocoindex` provider appears only when live CocoIndex is configured and opted in.
* **No mutation.** Discovery has no writer. A code hit is not an accepted link, evidence, finding,
  or proof of implementation correctness.

## Consequences

* Fixture and lexical evaluation remain offline. A live CocoIndex evaluation is opt-in; unavailable
  live evidence is `NOT RUN`, never an empty success.
* Query construction currently uses the scenario title with a stable template (`ai07-code-query-v1`);
  adding scenario steps/feature context is a future, evaluated change.
* Gherkin/requirement semantic retrieval is out of scope; CocoIndex Code is a code corpus.
* A second framework/index or a scenario-aware chunker requires a new reviewed story.
