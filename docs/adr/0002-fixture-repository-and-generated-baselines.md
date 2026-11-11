# ADR 0002 — Fixture strategy: generated history, hand-labeled oracle, drift-checked samples

**Status:** Accepted · 2026-11-10

## Context

The project needs a small engineering repository with *real* Git baselines and known traceability
findings, usable as the shared test oracle by three workstreams (roadmap §5). Constraints: never
depend on the surrounding repository's commit history; never invent expected results from model
output; keep the fixture small enough to review by hand; keep tests deterministic offline.

## Decision

1. **Declarative history.** `fixtures/banking-demo/history.json` lists commits in order: id,
   message, date, overlay directory, tags. Overlays are plain directory trees copied over the work
   tree; `{{TOKEN}}` placeholders are rendered during the copy (commit SHAs, discovery identity).
   Unknown tokens fail the build.
2. **Deterministic generation.** `tools/fixturectl.py build` initialises a nested repository in
   `fixtures/banking-demo/.build/repo` (git-ignored) with fixed author/committer identity, dates,
   messages, and a fixed initial branch, so commit SHAs are identical on every machine and git
   version. Verified by two tests: rebuild-in-another-directory equality and equality with the
   committed manifest.
3. **Two commits per baseline.** The source revision is committed first, then a commit that records
   the CI evidence for it, and the *tag* points at the evidence commit. Evidence therefore
   references the revision that was actually executed while remaining visible when the tag is
   evaluated.
4. **Hand-labeled oracle.** `expected/baseline-<x>.json` (findings, healthy artifacts, change
   summary) and `expected/candidate-links.json` (candidate index with positive/negative labels) are
   written and reviewed by humans.
5. **Generated, committed API samples.** `materialize` scans each tagged revision, stamps oracle
   findings with revisions and fingerprints, assembles threads, and calls the real discovery
   provider to produce the sample responses under `fixtures/api-responses/`. These are committed so
   a fresh clone serves the API and client tests with no Python setup, and `verify` (CI + tests)
   fails closed if they drift from the generator.
6. **Links inside the fixture repository, one review state per file.** `evidence/accepted-links.json`
   and `evidence/proposed-links.json`; the `FixtureLinkFile` model rejects a file containing more
   than one review state, so a proposal can never ride along with accepted facts.

## Consequences

* Any fixture content edit changes the SHAs and requires `fixturectl.py all` plus committing the
  regenerated files. The drift failure message says exactly that.
* Deletions and renames are not expressible in overlays yet (add-only); acceptable for a fixture
  whose delta is two files. If it becomes a limitation, add an explicit `delete`/`rename` list
  rather than switching to patches.
* Reviewing a fixture change means reviewing `history.json` + overlays + the oracle diff; the
  generated diff is mechanical.

## Alternatives considered

* **Commit the generated nested repository** (or a tarball). Rejected: it hides the history behind
  an opaque blob, and git-in-git handling inside the outer repository is fragile.
* **One commit per baseline** with evidence kept outside the repository. Rejected: the roadmap
  places evidence in the fixture tree, and keeping evidence under version control makes the
  "evidence exists at this baseline" question answerable from a checkout alone.
* **Deriving expected findings from the assurance code once it exists.** Rejected outright — it
  would make the oracle a tautology and the fixture useless for independent verification.
* **Hand-writing the materialized responses.** Rejected: revisions and content hashes cannot be
  hand-maintained, and drift between oracle and API samples would be invisible.

## Revisit when

A second fixture repository is needed (parameterise the CLI by fixture name), a baseline needs an
environment change (evidence must then record the environment fingerprint), or the delta grows
enough that overlays should support deletions and renames.
