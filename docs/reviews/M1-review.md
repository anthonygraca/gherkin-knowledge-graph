# M1 milestone exit review — round 1

**Milestone:** M1 — AI-free vertical slice. **Submission 1 of 7** (milestone counter).
**Reviewer:** Codex, `gpt-6.1-sol`, `xhigh`, read-only — session `01a1d374-de65-7192-adca-8efe345d268c`,
2026-11-13T05:50:13Z → 05:55:53Z (339.56 s), exit 0; 154,525 CLI-reported tokens.
**Reviewed tree:** `f1a6ea501aac68886d3372b8db00228d34d815f2`; integrated code snapshot
`29df1050aea4ad8b0b42041fd519636a6b0b7794`.
**Packet:** `docs/reviews/M1-review-prompt.md` (supplied copy sha256
`aad90391854fa8ce983b643cd442557108c9300b13f8064fae878e7b7a6a4104`; the committed copy is being
rebuilt with the corrected single manifest block).
**Verdict:** **NEEDS_INPUT** — all 40 story criteria and the M1 engineering exit PASS; one blocking
evidence gap (**M1-E1**, retained hosted-CI results) and two nonblocking fixes (**M1-N1** OpenAPI
description, **M1-N2** packet digest duplication). Repairs are in
`docs/reports/omp-m1-milestone/IMPLEMENTATION.md`; submission 2 is pending.

The verdict below is copied verbatim from the reviewer's final message (raw file sha256
`29b2a7af22a7eac08e8c069a2b031118b5c7745db8569a452b742aad883a1309` before path sanitization); only
the absolute repository path is substituted with `<task_repo>`.

---

**NEEDS_INPUT**

All 40 story criteria and the M1 engineering exit are supported at `29df1050aea4ad8b0b42041fd519636a6b0b7794`. Approval remains pending verification of the hosted required checks: the packet supplies a success summary, but no retained CI result, and GitHub was inaccessible during review. I requested that evidence from OMP.

The review tree `f1a6ea501aac68886d3372b8db00228d34d815f2` preserves the integrated product, tests, fixtures, workflow, and canonical criteria. No files were changed or work delegated.

| Criterion | Assessment | Evidence |
|---|---|---|
| DT-01 SCN-501 | PASS | REQ-001 fields, status, revision and independently hashed Git blob match. |
| SCN-502 | PASS | SCN-001 tag identity, title and anchored locator match; unannotated files excluded. |
| SCN-503 | PASS | Missing front matter rejects ingestion with the file identified. |
| SCN-504 | PASS | Untagged scenarios produce no artifact. |
| SCN-505 | PASS | Dangling identity tag rejected with its name. |
| SCN-506 | PASS | Duplicate requirement identities rejected. |
| SCN-507 | PASS | Tag/SHA results identical; reads use the resolved commit. |
| SCN-508 | PASS | Doc strings preserve data; opening and unterminated-delimiter cases covered. |
| SCN-509 | PASS | Malformed scenario identity rejected. |
| SCN-510 | PASS | YAML quoting and comments retain their intended meaning. |
| SCN-511 | PASS | Invalid YAML rejected with contextual diagnostics. |
| DT-02 SCN-521 | PASS | CODE-001 has the correct baseline-b identity, path, revision and changed hash. |
| SCN-522 | PASS | Unannotated files and annotation-like string contents excluded. |
| SCN-523 | PASS | TEST-001 identity and committed-blob hash match. |
| SCN-524 | PASS | Late annotations rejected with the file identified. |
| SCN-525 | PASS | Conflicting declarations rejected with both identities. |
| SCN-526 | PASS | Git-object reads establish working-tree independence; retained mapped test passes. |
| SCN-527 | PASS | All ten artifacts match the committed snapshot at both baselines. |
| DT-03 SCN-601 | PASS | Accepted links preserve reviewer and decision-time provenance. |
| SCN-602 | PASS | LNK-007 remains proposed; REQ-002 has no accepted links. |
| SCN-603 | PASS | Invalid relation direction rejected with the expected direction. |
| SCN-604 | PASS | Unknown endpoint rejected with SCN-999 identified. |
| SCN-605 | PASS | Wrong file/member review state rejected with contextual link diagnostics. |
| SCN-606 | PASS | Repeated ingestion preserves link facts without writes. |
| DT-04 SCN-611 | PASS | Required chain and EV-001 returned; tag/SHA responses identical. |
| SCN-612 | PASS | Proposal-only thread has empty accepted links and evidence. |
| SCN-613 | PASS | Six threads served with snapshot/example reads forbidden; schema 0.2.0. |
| SCN-614 | PASS | Unknown root and non-requirement root return the documented 404s. |
| SCN-615 | PASS | Counts match both baselines; run IDs derive from resolved commits. |
| SCN-616 | PASS | Inventory and filtering return the expected artifacts. |
| AS-01 SCN-701 | PASS | REQ-002 produces the expected missing-verification finding. |
| SCN-702 | PASS | Pending proposal does not satisfy coverage. |
| SCN-703 | PASS | REQ-001 produces no missing-verification finding. |
| SCN-704 | PASS | Rule, severity, revisions, baseline and independently calculated fingerprint match. |
| SCN-705 | PASS | Unknown baseline returns 404; unknown policy returns 400. |
| AS-04 SCN-801 | PASS | Baseline-a counts and requirement labels match responses and screenshots. |
| SCN-802 | PASS | Baseline changes reload data and prevent stale attribution. |
| SCN-803 | PASS | Altered responses change categories, coverage labels and numeric counts. |
| SCN-804 | PASS | LNK-007 is visibly proposed and excluded from coverage. |
| SCN-805 | PASS | Baseline-b displays accepted relations, SCN-001’s evidence and baseline. |

| Milestone gate | Assessment | Basis |
|---|---|---|
| REQ-001 digital-thread demonstration | PASS | Fresh responses reproduce the captures; screenshots show the chain and evidence. |
| Intentionally missing link end-to-end | PASS | Evaluator reports REQ-002; dashboard displays missing verification and its proposal. |
| Tests require no GPU/embedding service | PASS | Dependency/source inspection, frontend replay, and retained network-denied backend execution. |
| Required backend/fixture checks | PASS | Hash-matched logs record 233 passes normally and under network denial, plus successful fixture verification. |
| Frontend build and tests | PASS | Independent 10-test replay, both TypeScript configurations and in-memory production build pass. |
| Lint, formatting and commit references | PASS | Independently passed; commitlint checked the 29-commit review history. |
| Hosted required checks at integrated SHA | NOT VERIFIED | Only the submitted success summary was available; see M1-E1. |

The seven repository invariants hold within the reviewed M1 scope. Proposal/acceptance partition attacks were rejected; discovery has no acceptance/evidence writer; evidence retains tested revisions and artifact hashes are reproducible from Git. M1 introduces no freshness/failure classification, findings identify their inputs, oracle-label substance remains unchanged from the recorded human-attestation revision, and link review returns 501 naming AS-06. AS01-R1’s revision assertion is repaired.

Three findings remain:

- **M1-E1 — medium, blocking evidence gap.** [IMPLEMENTATION.md:25](<task_repo>/docs/reports/omp-m1-milestone/IMPLEMENTATION.md:25>). Expected: attributable hosted results for all three required checks at the exact integrated SHA. Actual: the report states success without retaining the run metadata; neither GitHub browsing nor `gh` could retrieve it here. **Smallest recheck:** OMP supplies raw `gh run view 43370472013 --repo anthonygraca/gherkin-knowledge-graph --json headSha,status,conclusion,jobs,url` output. Confirm the full SHA and successful completion of all three jobs. No CI failure was observed.

- **M1-N1 — low, nonblocking documentation defect.** [routes.py:149](<task_repo>/backend/app/api/routes.py:149>). Expected: OpenAPI describes the implemented M1 evaluator. Actual: the findings endpoint’s description says evaluation is contract-only and returns 501; independent dispatch returns 200. **Correction/recheck:** update that description to identify the implemented M1 rule and remaining deferred rules, then inspect `/openapi.json`. No prose-pinning test is needed.

- **M1-N2 — low, nonblocking packet inconsistency.** [M1-review-prompt.md:106](<task_repo>/docs/reviews/M1-review-prompt.md:106>) and line 145 retain stale STATUS/report digests. The submitted message corrects them but also includes the stale duplicate report digest. Current hashes are STATUS `20dafd11…4150b` and report `c4f91100…420bf`. **Correction/recheck:** retain one current digest per record and recompute those two hashes. Product, criteria and runtime-evidence hashes matched.

Independent verification included **63 parser/domain tests**, **10 frontend tests**, **34 API/assurance cases**, all eight HTTP-capture comparisons, Git-blob checks, malformed-input probes and example-read denial. API replay used inline synchronous dependency dispatch in memory. Full backend, fixture-rebuild and network-denied results were assessed from retained logs; browser console cleanliness was not independently verified.

This review does not attest stakeholder validation, human labels or link decisions, or release authorization.