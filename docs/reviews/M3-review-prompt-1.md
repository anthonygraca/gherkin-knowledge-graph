# M3 milestone review — submission 1

## Scope

**Milestone:** M3 — Local semantic discovery (roadmap §7), including the close-out review,
provider-honesty, retrieval-lifecycle, and local-inference stories.
**Canonical roadmap:** `CONTINUOUS_TRACEABILITY_ROADMAP.md` §7 M3.
**Close-out dispositions:** `docs/adr/0012-closeout-scope-decisions.md`.
**Merged snapshot:** `main` at `6b80def6a1e9de6c1583e5206563410d1b84b726` (merge of PR #75).
**Hosted CI on the merge commit:** run `43683744000` — all four jobs successful. Verify it directly
with `gh run view 43683744000 --json databaseId,conclusion,status,headSha,jobs` and
`gh pr checks 75`. The approved close-out code head is `e3a729d`; the final docs head is `329a4afe`.
**Snapshot note:** the top STATUS block predates the merge; use PR #75, the merge commit, the
acceptance records, and the evidence files as the current state. A post-merge status/review record
will follow this review.

This is an **independent milestone review**, not a story acceptance re-review. Inspect the actual
repository; do not edit, implement, commit, regenerate fixtures, or delegate. Read-only commands are
allowed. Network access is available for read-only `gh` verification.

## M3 exit criteria and deliverables

Verify, at minimum:

1. **One provider contract.** Fake and real `CandidateDiscovery` implementations pass the same
   contract tests; providers stay behind the port; no domain path requires a model.
2. **Offline fake mode.** The default suite, CI, and every non-live path work without a model,
   network, vector database, Docker, CocoIndex daemon, or GPU. `fake` remains the default.
3. **Measured real retrieval.** Real retrieval is measured against the labeled benchmark and
   reported as an observation, not ground truth; methodology, known limitations, and the negative or
   positive result are stated without a general claim.
4. **M3 deliverables.** Local adapter, normalized document/query formatting, local vector/index
   integration, `POST /api/discovery` proposals, the review workflow, and the evaluation report are
   present and accepted within their stories.
5. **M3 story approvals.** AI-01, AI-04, AI-05, AI-06, AI-07, AI-08, AI-09, AS-06, AS-07, AI-02,
   and AI-03 have independent acceptance approvals with no open major finding. The close-out
   reviews are `AS-06-acceptance-2.md`, `AS-07-acceptance-3.md`, `AI-02-acceptance-3.md`, and
   `AI-03-acceptance-4.md`; the earlier M3 approvals are in `docs/reviews/`.
6. **Invariants.** Proposals, accepted links, and verification evidence remain separate; discovery
   never writes an accepted link/evidence; change is not failure; revision-bound provenance;
   untrusted model/repository text cannot change review state or policy.
7. **Close-out integration.** The four close-out stories are merged; the final hosted CI and
   fixture/reproducibility checks are green; the M3 parent features (#13 review, #14 retrieval) have
   all children accepted and are eligible for closure.

## Evidence to inspect

* `docs/STATUS.md` M3 sections; `CONTINUOUS_TRACEABILITY_ROADMAP.md` M3; ADR 0012; ADR 0008.
* `docs/reviews/AS-06-acceptance-2.md`, `docs/reviews/AS-07-acceptance-3.md`,
  `docs/reviews/AI-02-acceptance-3.md`, `docs/reviews/AI-03-acceptance-4.md`.
* Earlier M3 acceptance/approval records in `docs/reviews/` (AI-01, AI-04/AI-05, AI-06, AI-07,
  AI-08/AI-09).
* `docs/reports/omp-cocoindex-*`, `docs/reports/omp-closeout/`, the benchmark and evaluation
  records, and `docs/feature-inventory.json`.
* `backend/app/discovery/`, `backend/app/api/routes.py`, `backend/app/assurance/`,
  `backend/app/retrieval/`, `backend/app/persistence/review.py`, and the provider/contract tests.
* `.github/workflows/ci.yml`; hosted run `43683744000`; PR #75.

Use `git diff 827e487..6b80def` for the close-out integration and inspect the earlier M3 commits as
needed. Do not treat a story acceptance review as milestone acceptance; verify the milestone-level
integration and exit criteria.

## Output format

Return exactly one Markdown document:

* `## Verdict` — `APPROVE`, `REQUEST_CHANGES`, or `NEEDS_INPUT`.
* `## M3 exit criteria` — one row per criterion: PASS / FAIL / NOT VERIFIED, with the evidence.
* `## Findings` — numbered `M3-R<n>` with severity (`critical`/`major`/`minor`), blocking status,
  path/line or artifact, expected/actual, and the smallest correction/recheck. Distinguish observed
  defects from hypotheses.
* `## Check verification` — observed commands/reports and hosted checks; name anything unobserved.

APPROVE requires all M3 exit criteria satisfied at the merged snapshot, all M3 story approvals
intact, the repository invariants preserved, no open major finding, and the hosted checks observed
green. A minor finding may be recorded without blocking the milestone if it is explicitly
nonblocking.
