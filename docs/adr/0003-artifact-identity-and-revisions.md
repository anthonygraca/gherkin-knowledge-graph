# ADR 0003 — Artifact identity, revisions, and the content-hash freshness key

**Status:** Accepted · 2026-11-10

## Context

Roadmap §11 leaves the identity strategy open: stable logical id plus revision-specific record, and
how renamed files are handled. Roadmap §1 requires every artifact and verification result to be
tied to a source revision or immutable content fingerprint. Freshness questions ("has anything
relevant changed since this evidence was recorded?") must be answerable between two baselines.

## Decision

* **Identity is declared in the artifact**: requirement front matter `id:`, Gherkin tag
  `@SCN-nnn`, first-line annotation `# cta:artifact CODE-nnn` / `TEST-nnn`. Unannotated files are
  not artifacts. The declaration is what makes a parser's output checkable against the fixture
  snapshot instead of being taken on faith.
* **Ids are stable** across revisions: `REQ-001` names the same requirement at `baseline-a` and
  `baseline-b`; each revision gets its own artifact record with its own `revision` and
  `content_hash`.
* **`revision`** is the commit the artifact was read at: provenance and drill-down.
* **`content_hash`** is `sha256:<hex>` of the artifact bytes at that revision: the freshness key.
* **`locator`** is `"<path>"`, or `"<path>#<anchor>"` when several artifacts share a file (a
  scenario inside a `.feature` file).
* **Freshness compares content hashes**, never commit SHAs.

The last point is load-bearing: each fixture baseline is two commits (source, then evidence), so the
tagged revision differs from the tested revision while the *content* the evidence covered is
identical. SHA comparison would report staleness immediately after recording evidence; hash
comparison reports it only when the bytes actually change.

## Consequences

* A file rename is a new artifact. That is honest but loses continuity; if renames become common,
  add an explicit `renamed_from` provenance field (additive, MINOR).
* A scenario's `content_hash` is the hash of the whole feature file, so editing any scenario in a
  file marks all scenarios in it as changed. Deliberate: file-level granularity is the stated M0/M2
  assumption, and over-reporting change is safer than missing it.
* The evidence commit does not invalidate evidence, and a source change does — both are tested.

## Alternatives considered

* Hash only the AST or a normalized form. Rejected for now: harder to explain, and comments are
  legitimate changes to a fixture-level review.
* Compare commit SHAs with an explicit "ignore evidence-only commits" rule. Rejected: brittle
  heuristics where a hash comparison is exact.
* Identity by path (`src/accounts.py` as the id). Rejected: the roadmap requires stable logical ids
  that survive file moves, and paths are already carried by `locator`.

## Revisit when

Sub-file granularity (functions/classes) is justified by a concrete finding class, or rename
continuity becomes a practical need.
