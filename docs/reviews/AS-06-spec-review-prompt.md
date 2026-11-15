# AS-06 specification review request

You are the independent specification reviewer for CTA story AS-06 (#28), milestone M3. This is a
**specification freeze review**, not an implementation or acceptance review. Do not edit files, run
tests, implement anything, commit, or delegate. Read-only inspection only.

## Inputs

- Canonical draft: `docs/stories/AS-06.feature` (refinement draft; 11 scenarios SCN-3001…SCN-3011).
- Companion: `docs/stories/AS-06.md`.
- Accepted owner decisions: `docs/adr/0012-closeout-scope-decisions.md` §1 (trusted-local-operator,
  loopback writes, server-assigned identity, journal outside fixture, workspace projection).
- Repository invariants: `AGENTS.md`; roadmap AS-06 and F-07; the GitHub issue body reproduced
  below (authoritative intake, not current normative wording).
- Existing contracts that the story must fit: `backend/app/domain/models.py`,
  `backend/app/domain/api.py`, `backend/app/domain/errors.py`, `docs/domain-contracts.md`, and the
  existing `POST /api/links/{link_id}/review` 501 stub in `backend/app/api/routes.py`.

GitHub issue #28 intake (verbatim):

```text
As a reviewer, I want to accept or reject proposed links with audit details, so that AI suggestions only become facts through a human decision.

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

Definition of done:
- POST /api/links/{link_id}/review implemented, replacing the 501 contract stub
- Immutable decision history (append-only), not an in-place status overwrite
- Test asserts verification status and evidence are untouched by acceptance
```

## What to decide

Assess only whether the canonical specification is ready to freeze for implementation:

1. Is every scenario observable, deterministic, and testable through real API/UI/persistence
   surfaces without inventing outcomes from the implementation under test?
2. Are success, failure, boundary, concurrency, restart, and immutability paths covered without
   contradictory expectations?
3. Does it preserve the repository invariants (proposals ≠ accepted links ≠ evidence; findings and
   baseline reads immutable; no Git writes; append-only decisions)?
4. Are ambiguous terms resolved or explicitly delegated (e.g. how a review binds to a baseline, how
   an existing fixture proposal without a capture snapshot is version-bound, what "snapshot" means,
   how response shapes identify operator/time/hashes, what happens on duplicate capture)?
5. Does it avoid over-specifying implementation while still pinning the externally observable
   contract?
6. Are scenario IDs stable, unique, and correctly ranged?

## Output format

Return exactly one Markdown document:

- `## Verdict` — `APPROVE` or `REVISE`.
- `## Findings` — numbered `AS06-SPEC-R<n>` entries; each with severity (`blocking`/`nonblocking`),
  the scenario or section, the ambiguity/contradiction, and the smallest precise wording or
  contract change that repairs it. Do not raise implementation-style findings.
- `## Scenario assessment` — one row per scenario ID with PASS/FAIL/NOT VERIFIED for
  specification readiness.
- `## Freeze conditions` — what must be true before removing `@refinement-draft` (empty if APPROVE).

APPROVE only when no blocking ambiguity or contradiction remains.
