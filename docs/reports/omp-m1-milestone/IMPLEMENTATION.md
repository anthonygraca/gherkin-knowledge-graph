# M1 roadmap run — implementation and exit record

| Field | Value |
| --- | --- |
| Mode / ceiling | roadmap, **M1** — AI-free vertical slice |
| Repository | anthonygraca/gherkin-knowledge-graph |
| Starting revision | `e18cdcfafe058e2f1d99c3c0b4bc2e155e9b16c9` (`main`) |
| Integrated revision | `29df1050aea4ad8b0b42041fd519636a6b0b7794` (`main`, AS-04 merge) |
| Review tree | `e1497cfd91626709195035154e50a6003681f681` (`main`, after round-1 repairs) |
| Run window (observed) | 2026-11-13T00:44Z → 2026-11-13T05:16Z (demo end) |
| OMP model / thinking | `vllm/deepseek-ai/DeepSeek-V4.1-Flash-1017`; `max` |
| Reviewer | Codex `gpt-6.1-sol`, `xhigh`, read-only, fresh session per submission |
| GitHub authority | Through merge, after required CI and independent review |

## Stories

| Story | Issue | Feature | Submissions | Verdict | Merged | Issue |
| --- | --- | --- | --- | --- | --- | --- |
| DT-01 | [#20](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/20) | DT-01.feature | 5 / 7 | APPROVE 2026-11-13T01:57Z | PR [#44](https://github.com/anthonygraca/gherkin-knowledge-graph/pull/44) → `26a25d0` | closed |
| DT-02 | [#21](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/21) | DT-02.feature | 4 / 7 | APPROVE 2026-11-13T02:46Z | PR [#45](https://github.com/anthonygraca/gherkin-knowledge-graph/pull/45) → `590e776` | closed |
| DT-03 | [#22](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/22) | DT-03.feature | 2 / 7 | APPROVE 2026-11-13T03:08Z | PR [#46](https://github.com/anthonygraca/gherkin-knowledge-graph/pull/46) → `0970f7a` | closed |
| DT-04 | [#23](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/23) | DT-04.feature | 2 / 7 | APPROVE 2026-11-13T03:53Z | PR [#47](https://github.com/anthonygraca/gherkin-knowledge-graph/pull/47) → `c43541b` | closed |
| AS-01 | [#2](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/2) | AS-01.feature | 1 / 7 (+AS01-R1) | APPROVE 2026-11-13T04:09Z | PR [#48](https://github.com/anthonygraca/gherkin-knowledge-graph/pull/48) → `d238776` | closed |
| AS-04 | [#26](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/26) | AS-04.feature | 3 / 7 | APPROVE 2026-11-13T05:08Z | PR [#49](https://github.com/anthonygraca/gherkin-knowledge-graph/pull/49) → `29df105` | closed |

Hosted CI on `29df105` (run `43370472013`): Commit references, Offline contract/fixture/API tests,
and Frontend build/component tests all **success**.

## M1 exit criterion

> Demo `REQ-001` digital thread and one intentionally missing link end-to-end; all tests run without
> GPU/embedding dependency.

| Check | Evidence | Result |
| --- | --- | --- |
| REQ-001 thread | `GET /api/threads/REQ-001?baseline=baseline-b` → REQ-001, SCN-001, CODE-001, TEST-001; LNK-001..003; EV-001; tag/SHA bodies identical | PASS |
| Missing link | `POST /api/assurance/evaluate {"baseline":"baseline-a"}` → `FND-8e701f84ea44fa6c` missing_verification_link for REQ-002, pinned to `0f8607b…`; baseline-b the same finding pinned to `156ad72…`; REQ-001 has no such finding | PASS |
| UI demo | baseline-a: REQ-001 Covered, REQ-002 Missing verification; REQ-002 proposals labelled `not accepted`; baseline-b: REQ-001 thread with LNK-001..003 and EV-001; 390×844 summary; 0 console errors | PASS |
| Offline | backend 233 passed and network-denied suite 233 passed (probe: `OSError: [Errno 101] Network is unreachable`); frontend 10 passed from committed JSON; no GPU/embedding/vector store/Docker | PASS |
| Integration | threads assembled from ingested Git data; no served read uses example thread/snapshot files; `fixturectl verify` current | PASS |
| Schema | `SCHEMA_VERSION = 0.2.0` (additive artifact inventory) | PASS |

Demo captures: `docs/reports/omp-m1-milestone/evidence/` (`http-*.json`,
`m1-summary-baseline-a.png`, `m1-thread-req-001-baseline-b.png`, `m1-proposals-req-002.png`,
`m1-summary-mobile.png`).

## Checks at the integrated snapshot

```text
commit=29df1050aea4ad8b0b42041fd519636a6b0b7794
captured_start=2026-11-13T05:13:37Z
pytest backend/tests -q                          exit 0  233 passed
fixturectl.py verify                             exit 0  reproducible/current
ruff check .                                     exit 0
ruff format --check .                            exit 0
git diff --check                                 exit 0
python tools/commitlint.py                       exit 0  (25 commits)
unshare -rn … socket probe                       DENIED (Network is unreachable)
unshare -rn backend/.venv/bin/python -m pytest backend/tests -q  exit 0  233 passed
captured_end=2026-11-13T05:13:53Z
frontend: npm run build                          exit 0
frontend: npm test                               exit 0  10 passed
```

Retained logs: `docs/reports/omp-m1-milestone/evidence/checks.txt`,
`checks-frontend.txt`, `pytest-full.log`, `pytest-network-denied.log`, `network-probe.log`,
`fixturectl.log`, `ruff.log`, `format.log`, `diffcheck.log`, `commitlint.log`,
`npm-build.log`, `npm-test.log`.

## Resources (CLI-reported totals; not a token accounting)

| Task | Submissions | Codex tokens |
| --- | --- | --- |
| Preflight model probe | — | 16,289 |
| DT-01 | 5 | 101,186 + 116,127 + 116,325 + 109,635 + 109,446 |
| DT-02 | 4 | 111,394 + 79,997 + 105,534 + 98,577 |
| DT-03 | 2 | 82,688 + 114,923 |
| DT-04 | 2 | 132,667 + 136,441 |
| AS-01 | 1 | 106,974 |
| AS-04 | 3 | 109,521 + 295,809 + 108,468 |
| Milestone review attempt 1 | 0 consumed (no verdict) | 54,511 (failed: workspace out of credits) |
| Milestone review round 1 | 1 consumed | 154,525 (NEEDS_INPUT) |
| Milestone review round 2 | 1 consumed | 137,915 (APPROVE) |

OMP delegations: none. OMP advisory calls: none. Quota/cost telemetry: not exposed; not claimed.
Wall time is reported from captured UTC boundaries; review calls overlap other work where possible.

## Milestone review — round 1: NEEDS_INPUT (submission 1 of 7)

Reviewer: `gpt-6.1-sol`, `xhigh`, read-only, session `01a1d374-de65-7192-adca-8efe345d268c`;
2026-11-13T05:50:13Z → 05:55:53Z (339.56 s), exit 0; 154,525 tokens. Verdict:
`docs/reviews/M1-review.md`. **All 40
story criteria and the M1 engineering exit PASS** at the integrated code snapshot `29df105`; the
reviewer returned NEEDS_INPUT for retained hosted-CI evidence, plus two nonblocking fixes.

| Finding | Severity | Disposition |
| --- | --- | --- |
| M1-E1 hosted results were summarized, not retained | medium, blocking evidence | Captured `gh run view 43370472013` and the check-runs API for `29df105`: full SHA `29df105…`, completed, success, and all three jobs (Commit references, Offline tests, Frontend tests) success. Evidence: `evidence/hosted-ci-43370472013.json`, `evidence/check-runs-29df105.json`, `evidence/hosted-checks.txt`. |
| M1-N1 findings OpenAPI text still said evaluate was contract-only | low, nonblocking | Updated the description to name the implemented M1 rule subset and the AS-02/AS-03 deferral; backend suite and ruff re-run (`evidence/repair-checks.txt`, 233 passed). |
| M1-N2 the packet retained a stale duplicate report digest | low, nonblocking | Rebuilt the packet with one manifest block and current digests; verified every manifest line against the tree before resubmission. |

Submission 2 is pending at the post-repair snapshot. The M1 gate remains **not satisfied** until a
verdict exists.

## Milestone review — round 2: APPROVE (submission 2 of 7)

Reviewer: `gpt-6.1-sol`, `xhigh`, read-only, session `01a1d385-f9a4-7952-8796-a4387986acda`;
2026-11-13T06:08:54Z → 06:20:10Z (675.73 s), exit 0; 137,915 tokens. Verdict:
`docs/reviews/M1-review-2.md`; packet `docs/reviews/M1-review-prompt-2.md` (sha256 `8586bd34…`).

* All 40 story criteria and the M1 engineering exit PASS at review tree `e1497cf` / code snapshot
  `29df105`; **no open major finding**.
* M1-E1 (hosted evidence), M1-N1 (OpenAPI text), and M1-N2 (packet digest) closed.
* The reviewer independently checked 63 parser/domain tests, 10 frontend tests, both TypeScript
  configurations, an in-memory production build, eight HTTP captures, six threads with example
  reads forbidden, malformed-input probes, lint/format, and commitlint over 31 commits.
* Approval covers the M1 engineering gate only; it does not attest stakeholder validation, human
  labels/link decisions, or release authorization.

## Milestone verdict

**APPROVE — M1 engineering gate SATISFIED** at review tree
`e1497cfd91626709195035154e50a6003681f681` (code snapshot `29df105`), submission 2 of 7
(milestone counter), `gpt-6.1-sol` at `xhigh`. No open major finding. Earlier credit-exhaustion
attempts are recorded in `docs/reviews/M1-review-attempt-1.md` and did not consume submissions.


## Owner / human gates (separate from the engineering exit)

* Stakeholder validation of the M1 demo has not been attested by the owner.
* The draft `project-definition.md` and the M0 feature-extraction/mapping reviews remain owner
  dispositions.
* Issue closure for #18/#19, the required-status-check ruleset, and the README work item remain
  open owner actions.
* M2–M4 work is outside this run's ceiling.
