# ADR 0004 — Proposals versus accepted links, and the fake discovery contract

**Status:** Accepted · 2026-11-10

## Context

Roadmap principle 1: facts, proposals, and verification are separate. Roadmap §3: a discovery
service must not write an accepted edge directly, and `CandidateDiscovery` must have one contract
shared by fake and real adapters. Roadmap §11 leaves graph semantics and relation types open.

## Decision

* **The proposal type cannot express acceptance.** `TraceCandidate` has `source_id`, `target_id`,
  `proposed_relation_type`, `rank`, `score`, `discovery_provider`, `model_version`,
  `index_revision`, optional `rationale` — no link id, no review state, no evidence id. A test
  asserts those field names are absent, so the property is enforced by the type, not by code review.
* **Separate containers everywhere.** `ThreadResponse` exposes `accepted_links` and `proposed_links`
  as separate arrays; the fixture stores them in separate files with the review state enforced per
  file.
* **Discovery is source-anchored.** `discover(artifact_id, top_k=…, relation_types=…)` returns
  candidates whose `source_id` is that artifact, ranked from 1 after filtering and trimming.
  Reverse lookups are a caller concern for now.
* **One provider registry, fake first.** `fake` is the only registered provider in M0; an unknown
  name is a 400 listing what is registered. Real providers (AI-02, M3) register behind the same
  port and must pass the same contract tests.
* **`index_revision` is a content fingerprint** of the exact payload that produced the candidates
  (provider, model version, and each candidate's source/target/relation/score/rationale), excluding
  evaluation labels. Candidates from different index revisions are never mixed.
* **Evaluation labels never affect retrieval.** `positive`/`negative` labels live in the fixture
  index for AI-05 and are not returned or filtered on: a plausible-but-wrong suggestion must reach a
  reviewer. A test asserts no accepted link in the fixture matches a negative-labeled candidate.

## Consequences

* There is no code path by which discovery can accept a link, so "AI suggested it" cannot silently
  become "it is true".
* Accepting a link (AS-06) is a separate, audited act with reviewer identity and reason, and it
  still does not change verification status.
* Deferring reverse discovery means "what implements this scenario" queries are expressed from the
  scenario side until a caller needs the reverse direction.

## Alternatives considered

* A single `links` array with a state field. Rejected: every consumer would have to filter, and one
  missed filter silently promotes proposals.
* Storing candidates as `proposed` links immediately. Rejected: it conflates a transient retrieval
  result with a recorded decision; the fixture demonstrates the intended flow — a candidate was
  recorded as `LNK-007` with discovery provenance and left pending review.
* Scoring in the provider with a fixed threshold. Rejected: thresholds belong to the reviewer or a
  policy, not to the adapter, and a filtered false positive is unmeasurable.

## Revisit when

A real provider lands (AI-02): it must satisfy the same contract tests, and any additional provider
state (index path, model revision) must be reported through the existing fields rather than new ones
that the fake cannot populate.
