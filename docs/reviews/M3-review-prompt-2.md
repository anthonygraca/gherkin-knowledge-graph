# M3 milestone review — submission 2

## Scope

**Milestone:** M3 — Local semantic discovery (roadmap §7), including the close-out review,
provider-honesty, retrieval-lifecycle, and local-inference stories.
**Canonical roadmap:** `CONTINUOUS_TRACEABILITY_ROADMAP.md` §7 M3.
**Close-out dispositions:** `docs/adr/0012-closeout-scope-decisions.md`.
**Merged snapshot:** `main` at `4e4b3059010652b0b22ba7a6fb8f055273529360` (PR #76 merge).
**Hosted CI on the merge commit:** run `43687159833`. Verify it directly with
`gh run view 43687159833 --json databaseId,conclusion,status,headSha,jobs` and
`gh pr checks 76`. The previous close-out merge is `6b80def`; its CI was green.

This is an **independent milestone re-review**. The prior verdict is
`docs/reviews/M3-review-1.md` (REQUEST_CHANGES; **M3-R1** major). Inspect the actual repository; do
not edit, implement, commit, regenerate fixtures, or delegate. Read-only commands are allowed.
Network access is available for read-only `gh` verification.

## Prior finding and repair

**M3-R1:** `RetrievalLifecycle.bind` used `provider.index_revision`, which resolves the provider's
default baseline, instead of the provider identity for `manifest.baseline`. Valid baseline-a
candidates were falsely rejected, and empty baseline-a batches recorded baseline-b provenance.

**Repair (`757685a`, merged by PR #76):**

- `bind` resolves `provider.binding_for(manifest.baseline)` once for providers that expose it and
  uses that identity for candidate validation and `SnapshotBoundBatch.provider_index_revision`;
  fixture providers without `binding_for` retain `index_revision`.
- A real local-provider integration test covers baseline-a → baseline-b → baseline-a and empty
  baseline-a provenance (the provider's default identity remains baseline-b).
- The same `binding_for` contract is implemented by the CocoIndex adapter.

**Required recheck:** Re-run the M3-R1 probes against both the real local adapter and the real
CocoIndex adapter (recorded transport): binding must succeed for baseline-a, baseline-b, and
baseline-a again; a genuine mixed-context candidate set must still be rejected; an empty baseline-a
batch must preserve baseline-a's provider identity. Verify links, evidence, and findings are
unchanged.

## M3 exit criteria and deliverables

Verify, at minimum:

1. **One provider contract.** Fake, local, and CocoIndex adapters implement `CandidateDiscovery`;
   fake and real providers pass the same contract tests; domain assurance requires no model.
2. **Offline fake mode.** The default suite, CI, and every non-live path work without a model,
   network, vector database, Docker, CocoIndex daemon, or GPU. `fake` remains the default.
3. **Measured real retrieval.** Real retrieval is measured against the labeled benchmark and
   reported as an observation, not ground truth; methodology, limitations, and the negative/positive
   result are stated without a general claim.
4. **M3 deliverables.** Local adapter, normalized formatting, local vector/index integration,
   `POST /api/discovery` proposals, the review workflow, and the evaluation report are present and
   accepted within their stories.
5. **M3 story approvals.** AI-01, AI-04, AI-05, AI-06, AI-07, AI-08, AI-09, AS-06, AS-07, AI-02,
   and AI-03 have independent acceptance approvals with no open major finding. The close-out
   reviews are `AS-06-acceptance-2.md`, `AS-07-acceptance-3.md`, `AI-02-acceptance-3.md`, and
   `AI-03-acceptance-4.md`.
6. **Invariants.** Proposals, accepted links, and verification evidence remain separate; discovery
   never writes an accepted link/evidence; change is not failure; revision-bound provenance;
   untrusted model/repository text cannot change review state or policy.
7. **Close-out integration.** The four close-out stories are merged; the final hosted CI and
   fixture/reproducibility checks are green; the M3 parent features (#13 review, #14 retrieval) have
   all children accepted and are eligible for closure.

## Evidence to inspect

* `docs/reviews/M3-review-1.md`, the prior M3 review.
* `docs/reviews/AS-06-acceptance-2.md`, `AS-07-acceptance-3.md`, `AI-02-acceptance-3.md`,
  `AI-03-acceptance-4.md`; earlier M3 approvals in `docs/reviews/`.
* `backend/app/retrieval/lifecycle.py`; `backend/tests/test_retrieval_lifecycle.py`.
* `backend/app/discovery/local_embedding.py`, `backend/app/discovery/code_index.py`, the provider
  contract tests, and the recorded CocoIndex transport.
* `docs/reports/omp-cocoindex-*`, `docs/reports/omp-closeout/`, the benchmark/evaluation records,
  `docs/feature-inventory.json`.
* `docs/STATUS.md`, `CONTINUOUS_TRACEABILITY_ROADMAP.md` M3, ADR 0012, ADR 0008.
* `.github/workflows/ci.yml`; hosted runs `43683744000`, `43686600314`, `43687159833`; PRs #75/#76.

Use `git diff 827e487..4e4b305` for the full integration and inspect the earlier M3 commits as
needed. Do not treat a story acceptance review as milestone acceptance; verify the milestone-level
integration and exit criteria.

## Output format

Return exactly one Markdown document:

* `## Verdict` — `APPROVE`, `REQUEST_CHANGES`, or `NEEDS_INPUT`.
* `## M3 exit criteria` — one row per criterion: PASS / FAIL / NOT VERIFIED, with the evidence.
* `## Findings` — numbered `M3-R<n>` with severity, blocking status, path/line or artifact,
  expected/actual, and the smallest correction/recheck. Distinguish observed defects from
  hypotheses.
* `## Check verification` — observed commands/reports and hosted checks; name anything unobserved.

APPROVE requires all M3 exit criteria satisfied at the merged snapshot, all M3 story approvals
intact, the repository invariants preserved, no open major finding, and the hosted checks observed
green. A minor finding may be recorded without blocking the milestone if it is explicitly
nonblocking.
