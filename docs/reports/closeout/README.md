# Continuous Traceability Assurance — close-out report

**Date:** 2026-11-15
**Final reviewed code:** `main` at `db8e3096a5b4fc1fea2a190f3113de98f706a6f8` (PR #79 merge)
**M4 milestone re-review:** APPROVE at `db8e309` (`docs/reviews/M4-review-2.md`)
**Close-out records:** landed by the close-out PR (#80); final merge/run is recorded on that PR.

## Final state

|Area|State|
|---|---|
|M0 foundation|APPROVE at `bca69cf`; closed|
|M1 vertical slice|APPROVE at `e1497cf`; closed|
|Expanded M2|APPROVE at submission 7/7; closed|
|M3|APPROVE at `4e4b305` (`docs/reviews/M3-review-2.md`); parent features #13/#14 closed|
|M4|APPROVE at `db8e309` (`docs/reviews/M4-review-2.md`); parent feature #16 closed|
|M3 stories|AS-06 #28, AS-07 #29, AI-02 #31, AI-03 #32 accepted and merged (PRs #75/#76); issues closed|
|M4 stories|CI-01 #36, CI-02 #37 accepted and merged (PRs #78/#79); issues closed|
|Default path|Offline, `fake` discovery, no GPU/model/network/vector DB/Docker required|
|Final full suite|**205 scenarios / 1,990 steps passed**; strict gate 205 cases / 1,990 results|
|Backend|**556 passed, 4 skipped** (the four skips are opt-in live checks)|
|Frontend|Build and 14 component tests passed|
|Hosted final runs|M4 merge run `43716166621` and M4 review-repair main run `43725911468` — all six jobs green at their heads|

## Delivered scope

| Story | Issue | Result | Canonical evidence | Acceptance |
|---|---|---|---|---|
| AS-06 review decisions | #28 | Append-only local review journal, proposal capture, server-assigned trusted operator, loopback/origin boundary, workspace projection, review UI/history, restart/durability | `docs/stories/AS-06.feature` (29 IDs / 37 cases), `backend/tests/test_review_workspace.py`, final Cucumber report | `docs/reviews/AS-06-acceptance-2.md` APPROVE |
| AS-07 provider honesty | #29 | Unregistered/registered-failure/empty-success problems, provider catalogue, no fake fallback, proposal provenance everywhere | `docs/stories/AS-07.feature` (7 IDs / 12 cases), `backend/tests/test_provider_availability.py`, frontend tests | `docs/reviews/AS-07-acceptance-3.md` APPROVE |
| AI-03 snapshot lifecycle | #32 | Content-hash planning, corpus cache keys, manifests, staged publication with rollback, canonical read validation, mixed-context rejection, honest counts | `docs/stories/AI-03.feature` (6 IDs), `backend/tests/test_retrieval_lifecycle.py` | `docs/reviews/AI-03-acceptance-4.md` APPROVE |
| AI-02 local inference | #31 | Same-machine Apache-2.0 EmbeddingGemma 2 270M ONNX provider, opt-in live evidence, model manifest, deterministic fake default | `docs/stories/AI-02.feature` (6 IDs / 7 offline + SCN-3205 live), `AI-02-MODEL-MANIFEST.md`, `AI-02-EVIDENCE.md` | `docs/reviews/AI-02-acceptance-3.md` APPROVE |
| CI-01 revision assurance | #36 | Typed report/input manifest, event revision resolver, offline banking evaluation, portable self-assurance, incomplete diagnostics, run-unique hosted publication | `docs/stories/CI-01.feature` (6 IDs / 9 cases), `docs/assurance-report-contract.md`, `tools/assurance.py`, `.github/workflows/ci.yml` | `docs/reviews/CI-01-acceptance-6.md` APPROVE |
| CI-02 finding diff | #37 | Stable fingerprints, 2/4/0 forward, 0/4/2 reverse, 0/4/0 self, payload retention, completeness/identity/revision/version refusals, no classification on refusal | `docs/stories/CI-02.feature` (6 IDs / 19 cases), `backend/app/assurance/reporting.py`, CLI tests | `docs/reviews/CI-02-acceptance-6.md` APPROVE |

Earlier M3/M4 evidence stories (AI-01, AI-04, AI-05, AI-06, AI-07, AI-08, AI-09) retain their
independent APPROVEs; see the review records in `docs/reviews/`.

## Verification and evidence

* Final Cucumber report: `docs/reports/omp-closeout/evidence/final-cucumber.ndjson`
  (sha256 `84271f6f4e32c8ad2217b810df107cf337afac63b54c6c172c90350706cea1c1`),
  summary `final-cucumber.log`; `testRunFinished.success=true`, all 1,990 steps PASSED.
* Final inventory: `docs/feature-inventory.json`
  (sha256 `08c6f9621e550edd2e71045f53eb4336836b5285de226543739a3114a06c6715`), 41 files;
  GT-02 recheck 3/3; `docs/feature-inventory.md`.
* Final report/inventory hashes: `docs/reports/omp-closeout/evidence/final-run-hashes.txt`.
* Backend: `final-backend.log` — 556 passed / 4 skipped; `final-step-resolution.log` — 205 cases /
  1,990 results; fixture verify, Ruff, format, and whitespace clean.
* AI-02 live: pytest 1 passed; SCN-3205 1 scenario / 14 steps under `unshare -rn`; weights digest
  `sha256:b396bde0f7a85398c9c42d08a3c0b68d30952e91dcd408bfa327c727e86457a3`, runtime
  `onnxruntime 1.32.0`, external egress false, namespace retained in
  `AI-02-live-observations.json`.
* Hosted runs: PR #75 docs `43682516693`; M3 binding `43686600314`; main `43683744000` and
  `43687159833`; M4 acceptance `43713557672`; M4 main `43716166621`; M4 review repair
  `43724811108`; final M4 main `43725911468`. All observed six-job (or four-job before M4) successes
  at their exact heads.
* `final-manifest.sha256` pins the reviewed code, contracts, stories, reviews, evidence, report,
  inventory, and hosted-run capture. Regenerate with `sha256sum -c` from the repository root.

## Independent reviews

| Area | Specification | Acceptance |
|---|---|---|
| AS-06 | review 5 | reviews 1–2; APPROVE at submission 2 |
| AS-07 | review 3 | reviews 1–3; APPROVE at submission 3 |
| AI-03 | review 2 | reviews 1–4; APPROVE at submission 4 |
| AI-02 | review 2 | reviews 1–3; APPROVE at submission 3 (minor R5 repaired) |
| CI-01 | review 4 | reviews 1–6; APPROVE at submission 6 |
| CI-02 | review 4 | reviews 1–6; APPROVE at submission 6 |
| M3 | — | review 1 REQUEST_CHANGES; review 2 APPROVE |
| M4 | — | review 1 REQUEST_CHANGES; review 2 APPROVE |

The story acceptance reviews used Codex `gpt-6.1-sol` at high reasoning. The M4 reviews used the
repository's independent `reviewer` agent because the Codex workspace ran out of credits; the exact
error and the alternative are recorded in
`docs/reports/omp-closeout/evidence/codex-credit-blocker.md`. No review record was fabricated, and
all prior verdicts remain in `docs/reviews/`.

## Resource usage

* AI-02 host: Intel Core i5-7500T, 4 logical CPUs, 15 GiB RAM, no GPU. Model: Apache-2.0
  EmbeddingGemma 2 text 270M ONNX, ~346 MiB on disk. Observed runtime load 2.38–3.61 s, corpus build
  5.94–21.81 s, warm query median 0.365–2.225 s, RSS delta ~506–508 MiB. These are one-corpus
  observations, not a retrieval-quality benchmark.
* CocoIndex/benchmark: the M4 research comparison records its methodology, small-corpus limits,
  runtime/latency observations, and the negative CocoIndex result; no general retrieval claim is made.
* Hosted M4 runs: the Cucumber job is the long pole (~10–12 minutes); the assurance jobs add
  seconds to a minute. No GPU or shared model service is used.

## Retrospective

**What worked.** Freezing the report/comparison contract before implementation removed recurring
ambiguities. Independent reviewers repeatedly found real integration defects that the happy-path
scenarios missed: M3's provider identity was bound to the default baseline; the report loader
normalized payloads before digest checking; completeness checks were kind-level rather than
item-level; unreadable historical inputs were skipped; stale output paths could survive; coverage
double-counted outline examples; and a portable report could forge `identity_kind`. Each was repaired
with a failing probe/regression and re-reviewed.

**Process lessons.** (1) A validation contract must be executable and exhaustive; prose alone did not
stop bypasses. (2) Keep identity and payload normalization separate. (3) A report's self-declared
provenance is not trustworthy without cross-checks; scope is a stronger source-locator signal than
the declared kind. (4) Hosted runners cannot be assumed to support `unshare`; an in-process network
guard plus a fresh run path is portable. (5) The final report/inventory bootstrap requires a run,
then regeneration, then a verification run. (6) Feature-branch commits that reference a parent issue
need the map entry at the **commit being judged**; amend the unpushed feature-branch messages rather
than weakening commitlint.

**Residual risk (plainly).**

* AS-06 is a trusted-local-operator design. Any process/person with the local account can act as the
  operator; it is not multi-user authentication. The append-only local journal is not replicated.
* AI-02's live evidence is one CPU model on one host with a synthetic corpus. It is not a
  retrieval-quality claim or a cross-hardware performance guarantee; the default remains `fake`.
* The CocoIndex benchmark was negative on the small corpus (no Recall@1 gain, lower precision, ~1 s
  query). No general retrieval claim is made.
* CI-02 does not implement portable source-locator continuity mapping; every `source_locator` report
  is refused. A future reviewed mapping requires an additive contract/ADR.
* Optional shared model hosting was not deployed; the project does not claim it. The default remains
  offline.
* The M4 milestone re-review's nonblocking note about the post-merge `43725911468` capture is repaired
  by this close-out record: the capture is committed and included in the final manifest, and STATUS
  names the merged snapshot/run.
* Codex workspace credits are exhausted; further model-assisted reviews require a credit refill or
  continued use of the independent reviewer agent. This is a review-tool limitation, not a product
  dependency.

## Evidence index

* `docs/reports/omp-closeout/evidence/` — full suite logs, reports, GT-02 rechecks, manifests, hosted
  run captures, AI-02 live records, and the Codex credit blocker.
* `docs/reviews/` — specification, acceptance, M3/M4 milestone reviews, prompts, and repairs.
* `docs/assurance-report-contract.md` — the normative M4 report/comparison contract.
* `docs/STATUS.md` — the concise final state and verification counts.
