# M4 milestone review — submission 1

## Scope

**Milestone:** M4 — Continuous integration and research comparison (roadmap §7), including
revision-triggered assurance, comparable finding-set diff, and the research/benchmark evidence.
**Roadmap:** `CONTINUOUS_TRACEABILITY_ROADMAP.md` §7 M4.
**Close-out decisions:** ADR 0012 §3; `docs/assurance-report-contract.md`.
**Merged snapshot:** `main` at `1731aedb912d16c5e0bbfdd5c22c460ce2e0d1c2` (PR #78 merge).
**Hosted CI on the merge commit:** run `43716166621`; verify directly with
`gh run view 43716166621 --json databaseId,conclusion,status,headSha,jobs` and `gh pr checks 78`.
**Prior milestone:** M3 APPROVE at `4e4b305` (`docs/reviews/M3-review-2.md`).

This is an **independent milestone review**, not a story acceptance re-review. Inspect the actual
repository; do not edit, implement, commit, regenerate fixtures, or delegate. Read-only commands are
allowed. Network access is available for read-only `gh` verification.

## M4 exit criteria and deliverables

Verify, at minimum:

1. **Revision-triggered assurance.** A pinned, offline workflow evaluates the selected PR-head/
   push-after revision; the typed report carries the evaluated revision, evaluator revision, input
   coverage/hashes, findings, completeness, and publication metadata; exit `0` means completed and
   exit `2` is a tool failure, never a finding. Publication uses artifacts/summaries and does not
   mutate branches.
2. **Comparable finding diff.** Complete, comparable, revision-bound reports are classified by the
   stable fingerprint; banking yields 2 new / 4 unchanged forward, 0/4/2 reverse, 0/4/0 self; payloads
   are retained; absent/differing/incomplete/malformed inputs and source-locator identities are
   refused with `findings-not-comparable` and no classification. Absence never creates a requirement
   verdict or implies remediation.
3. **Reproducible benchmark/report.** The M4 research comparison has a reproducible methodology,
   known limitations, runtime/cost observations, and a measured positive or negative result. The
   explicit-link-only, embedding-assisted, graph, and hybrid arms are represented where the accepted
   scope requires them; no general retrieval claim is inferred from a small corpus.
4. **Optional scope honesty.** Optional shared model hosting is not silently claimed; the default
   path remains offline and model-free, with opt-in live evidence separated from benchmark/quality
   claims.
5. **Story approvals and integration.** CI-01 and CI-02 are independently accepted at the final code
   (`docs/reviews/CI-01-acceptance-6.md`, `CI-02-acceptance-6.md`); the earlier M4 evidence stories
   (AI-05/AI-07/AI-08/AI-09, as applicable) remain approved; the parent feature #16 is eligible for
   closure with no open major finding.
6. **Invariants.** Proposals/accepted links/evidence remain separate; change is not failure;
   provenance is revision-bound; untrusted model/repository text cannot change review state, links,
   or verification.
7. **Evidence.** The final full suite, backend suite, strict gate, fixture reproducibility, Ruff,
   final report/inventory, hosted CI, and final evidence manifest are green and hash-pinned. The
   final close-out report may follow this review; the milestone evidence itself must be present.

## Evidence to inspect

* `docs/assurance-report-contract.md`; `tools/assurance.py`;
  `backend/app/assurance/reporting.py`; `backend/app/domain/assurance_report.py`.
* `.github/workflows/ci.yml` (`banking-assurance`, `self-assurance`, run-unique artifacts).
* `docs/stories/CI-01.*`, `docs/stories/CI-02.*`;
  `docs/reviews/CI-01-acceptance-6.md`, `CI-02-acceptance-6.md`, and the repair records.
* `docs/reports/omp-closeout/evidence/final-cucumber.ndjson`, `final-cucumber.log`,
  `final-backend.log`, `final-step-resolution.log`, `final-run-hashes.txt`,
  `final-manifest.sha256`, `hosted-ci-m4-main-run.json`.
* The M4 benchmark/research records in `docs/reports/omp-cocoindex-*`, `docs/reports/omp-closeout/`,
  and the accepted AI-05/AI-07/AI-08/AI-09 review records in `docs/reviews/`.
* `docs/STATUS.md`, `CONTINUOUS_TRACEABILITY_ROADMAP.md`, ADR 0012, ADR 0008.

Use `git diff b6e6931..1731aed` for the M4 integration and inspect the earlier M4 commits as needed.
Do not treat a story acceptance review as milestone acceptance; verify the milestone-level
integration and exit criteria.

## Output format

* `## Verdict` — `APPROVE`, `REQUEST_CHANGES`, or `NEEDS_INPUT`.
* `## M4 exit criteria` — one row per criterion: PASS / FAIL / NOT VERIFIED, with the evidence.
* `## Findings` — numbered `M4-R<n>` with severity, blocking status, path/artifact,
  expected/actual, and the smallest correction/recheck. Distinguish observed defects from
  hypotheses.
* `## Check verification` — observed commands/reports/hosted checks; name anything unobserved.

APPROVE requires all M4 exit criteria satisfied at the merged snapshot, the M4 story approvals
intact, the invariants preserved, no open major finding, and the hosted checks observed green. A
minor finding may be recorded without blocking the milestone if it is explicitly nonblocking.
