# AS-04 implementation record — findings and coverage summary UI

| Field | Value |
| --- | --- |
| Story | AS-04 — [#26](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/26), verified OPEN 2026-11-13T04:13:19Z (`gh issue view`, milestone "M1 — AI-free vertical slice") |
| Canonical criteria | [AS-04.feature](../../stories/AS-04.feature), sha256 `44f0ce7d64cdd2f80fa093a0adcdd5964821c5fa4102abbccf503dc7484d6f6e` |
| Brief / verification map | [AS-04.md](../../stories/AS-04.md) |
| Branch / base | `feat/26-as-04-summary-ui` from `d238776bf0b53e6963f8e81721ce9a106f848adb` (AS-01 merge) |
| Contract version | `SCHEMA_VERSION = 0.2.0`, `PACKAGE_VERSION = 0.1.0` (no backend shape change) |
| Submission | **3 of 7** — rounds 1–2: REQUEST_CHANGES, NEEDS_INPUT; round 3 **APPROVE** (2026-11-13T05:08Z) |
| Snapshot captured | 2026-11-13T04:58Z (approved snapshot) |

## What changed

| Path | sha256 | Purpose |
| --- | --- | --- |
| `frontend/package.json` | `7d82d45f0d7bd214b9a014d89ed696ca0c32550bd4b81c3cbfaccc1866908315` | React 19 + Vite 6 + Vitest 3 scripts |
| `frontend/package-lock.json` | `5fd857b362d57ef48f0ff8862d474770ad5dc98d33c944bc64734dacd1591bac` | Locked dependency tree |
| `frontend/vite.config.ts` | `bde007f1fd26fa27cc068f64d8c02ee388ee08d22c7d4a15b211c0cd5870d7d1` | Dev proxy for `/health` and `/api`; jsdom tests |
| `frontend/tsconfig*.json` | `770b4140…`, `3bee9baf0672e6e0de5fe433bc6ec75ef31eb87f3b319b1111afaac0864d0e28`, `3ced5d22…` | Strict TypeScript configs (ES2024 lib for `Promise.withResolvers`) |
| `frontend/index.html` | `4e00b5c1e7c64dfbeb8aa8fca0d0acc71be382a17960305e256c1b76a3f765f2` | Shell |
| `frontend/src/main.tsx` | `704cd9cb2b4b80f3c9d53ffb1a11273c6a4ea59bcd2c64df0920b3659561adfd` | Entry point |
| `frontend/src/App.tsx` | `0ed430a622b6dc3acce7e5f5666ee0a7258034fe8c338a4a01d91d9b4c1de446` | Baseline selector, keyed state, per-request error attribution |
| `frontend/src/api.ts` | `edfa55c6421cacbb2f1e1408e84a7b85b946ed3588670d494e0cd9a9326c86b5` | Typed API client with injected base URL |
| `frontend/src/types.ts` | `6169bbac5bb00fde197aefd3fbedede17dc33403042059d7de1d3cc3b26f08df` | API response types |
| `frontend/src/styles.css` | `22d7c55129eee011cdff3123a98e69adf86b3b534ec97371d8e2cb16c3b1a772` | Readable light/dark layout |
| `frontend/src/App.test.tsx` | `7317566625f28486211673a0e0b42f7bcc5600b9103c775fa541710a46148fc2` | Ten component tests, including transition/failure/recovery/numeric regressions |
| `frontend/src/test-setup.ts` | `9b328c4843431fa76d8de00008fc159e95f99a840211085ff3b8f25e53d14409` | jest-dom matchers |
| `.github/workflows/ci.yml` | `3a1b1a4fb55653d5162719932b8fc084e11476f8145b0fe59a3ed7727a15b4c1` | Frontend CI job (install, build, test) |
| `docs/setup.md` | `66547bba1717b2338557e503d9700aa3606d995c98f13b2bd1bc89adae2fdca0` | Node prerequisite and frontend commands |
| `docs/architecture.md` | `d81c78a672a65843ff9d7133b1cf55037d6a2bbb3b12859c33feb10a5a6153e9` | Frontend implemented |
| `docs/STATUS.md` | `5b3c32843c8ddb72ee016635e22075c0ed2a7ef3e5e38e24ed2c3c039fc00f2a` | AS-01 landed; AS-04 active |
| `backend/tests/test_assurance_rules.py` | `784361e690a18ebcbeebb3b47f403825a5fefd371068e1067b6fda907f613067` | AS01-R1: revisions bound to `committed_manifest.tags[baseline]` |
| `docs/stories/AS-04.feature` | `44f0ce7d64cdd2f80fa093a0adcdd5964821c5fa4102abbccf503dc7484d6f6e` | Canonical criteria (SCN-801…805) |
| `docs/stories/AS-04.md` | `a90650fc994157f39bece4d6e5a57864b46806264084f15445e44b30dcad3ea1` | Brief, assumptions, map |

The backend response shapes, fixtures, and generated files are unchanged.

## Review round 1 — REQUEST_CHANGES (submission 1 of 7)

Reviewer: Codex `gpt-6.1-sol`, `xhigh`, read-only; session `01a1d326-1f96-7e80-a251-ed613c6485d1`;
2026-11-13T04:24:12Z → 04:31:11Z (418.81 s), exit 0; 28/28 hashes matched.
Verdict: `docs/reviews/AS-04-review.md`.

| Finding | Severity | Repair | Recheck |
| --- | --- | --- | --- |
| AS04-R1 a baseline change could show the previous baseline's counts/coverage under the new baseline | blocking | Findings and artifacts are stored with the baseline they were fetched for; the summary renders only when both keys equal the selected baseline, otherwise a loading note. The old data cannot render under the new heading, even before effects run. | `App.test.tsx` "never shows the previous baseline's summary under the new baseline (AS04-R1)" |
| AS04-R2 selecting a requirement could show the previous requirement's chain, or a heading with another requirement's contents | blocking | Thread data is keyed by baseline and root; the body renders only when both match the current selection, otherwise "Loading thread…" (or an explicit unavailable message after a failure). | `App.test.tsx` "never pairs a thread heading with another requirement's chain (AS04-R2)", "shows an explicit error instead of another thread's contents (AS04-R2)" |
| AS04-N1 the count test checked disappearance, not a changed numeric count | low, nonblocking | Added a response with two findings of one type and asserted the rendered count `2`. | `App.test.tsx` "renders a numeric count of two for two findings of one type (AS04-N1)" |

Failed summary requests now show "Findings are unavailable for this baseline." rather than a
loading or empty-success message; failed thread requests show "Thread unavailable for this
requirement." Both keep the old data hidden by key.

The transition tests use deferred promises and rejected promises to hold or fail the new response
and assert the old content is absent. The browser demonstration was repeated at the fixed snapshot;
screenshots were refreshed and the console remained clean.

### AS01-R1 follow-up (nonblocking from the AS-01 approval)

The AS-01 reviewer noted that `evaluated_baseline` and `artifact_revisions["REQ-002"]` were compared
to each other; both could carry the same wrong SHA. The parameterized test now binds both to
`committed_manifest.tags[baseline]`. This is a test-strength repair, verified by the AS-01 suite and
covered by this review and the M1 exit review.

## Review round 2 — NEEDS_INPUT (submission 2 of 7)

Reviewer: same model/effort and read-only sandbox; session `01a1d33b-a290-70b2-b8a6-4deeccb0d957`;
2026-11-13T04:47:42Z → 04:55:20Z (457.66 s), exit 0; 30/30 hashes
matched. Verdict: `docs/reviews/AS-04-review-2.md`. All five criteria PASS; R1/R2/N1 confirmed
closed.

| Finding | Severity | Disposition |
| --- | --- | --- |
| AS04-E1 the packet summarized the backend/fixture/network checks without retained full logs; the network invocation contained an ellipsis | major, blocking evidence | Re-ran the checks at this unchanged snapshot and committed the exact `checks.txt`, pytest, fixture-verify, ruff, socket-probe, and network-denied logs under `evidence/`; the exact invocation is `unshare -rn backend/.venv/bin/python -m pytest backend/tests -q`. The probe log shows `OSError: [Errno 101] Network is unreachable`. |
| AS04-N2 a failed thread request's global error remained after a successful selection | low, nonblocking | Errors are attributed per request (`healthError`, `summaryError`, `threadError`); a successful request clears only its own error. The failure→recovery test asserts the alert disappears when REQ-001 loads. |

Retained evidence logs (`docs/reports/omp-as-04-summary/evidence/`): `checks.txt`,
`pytest-full.log`, `fixturectl-verify.log`, `ruff-check.log`, `ruff-format.log`,
`network-probe.log`, `pytest-network-denied.log`, `npm-build.log`, `npm-test.log`.

## Review round 3 — APPROVE (submission 3 of 7)

Reviewer: same model/effort and read-only sandbox; session `01a1d34a-25a7-7490-87ce-c4eecf7c72ab`;
2026-11-13T05:03:34Z → 05:08:19Z (285.11 s), exit 0; 41/41 hashes matched.
Verdict: `docs/reviews/AS-04-review-3.md`.

* SCN-801…805 PASS; E1 (retained logs) and N2 (error attribution/recovery) closed.
* Nonblocking AS04-N3 (record said "Submission 2 pending") corrected in this record.
* The reviewer assessed the full backend/fixture/network checks from the retained logs, not by
  rerunning them in the read-only sandbox.

Approval attests implementation against the supplied criteria. It does not attest human labeling,
link decisions, refinement sign-off, stakeholder acceptance, or milestone completion.

## Acceptance results

| Criterion | Check | Result |
| --- | --- | --- |
| SCN-801 coverage summary | `frontend/src/App.test.tsx` "shows counts by type and coverage for baseline-a" | PASS |
| SCN-802 baseline visible/selector | "reloads when the baseline selector changes"; "never shows the previous baseline's summary under the new baseline (AS04-R1)" | PASS |
| SCN-803 counts from response | "derives counts from the response" | PASS |
| SCN-804 proposals labelled | "labels proposals and keeps them out of coverage" | PASS |
| SCN-805 thread chain/evidence | "shows the accepted chain and its evidence"; "never pairs a thread heading with another requirement's chain (AS04-R2)"; "shows an explicit error instead of another thread's contents (AS04-R2)" (includes recovery) | PASS |
| Browser demonstration | real backend + Vite app, two baselines, proposal thread, mobile viewport | PASS |

## Browser demonstration (observed)

Backend on `127.0.0.1:8000`, Vite on `127.0.0.1:5173`, managed browser, zero console errors:

* baseline-a: counts `candidate_pending_review 1`, `lifecycle_review_required 1`,
  `missing_implementation_link 1`, `missing_verification_link 1`; REQ-001 **Covered**, REQ-002
  **Missing verification**; thread for REQ-001 shows LNK-001..003 and EV-001.
* REQ-002: proposals section labels LNK-007 `not accepted`; coverage stays Missing verification.
* baseline-b: adds `reverification_required 1` and `verification_failed 1`; REQ-001 becomes
  `Needs review: reverification_required`; its thread still shows LNK-001..003 and EV-001.
* 390×844 viewport renders the same summary without loss of the baseline or counts.

Screenshots: `docs/reports/omp-as-04-summary/evidence/summary-baseline-a.png`,
`thread-req-002-proposals.png`, `thread-req-001-baseline-b.png`, `summary-mobile-390.png`.
Both servers were stopped after the demonstration (ports free). The fixed snapshot was re-demonstrated
with zero console errors; the screenshots above are from that run.

## Commands and outcomes (as captured)

```text
snapshot_captured=2026-11-13T04:57:45Z
uv run --project backend pytest backend/tests -q                    exit 0  233 passed
uv run --project backend python tools/fixturectl.py verify          exit 0  reproducible/current
uv run --project backend ruff check .                               exit 0
uv run --project backend ruff format --check .                      exit 0
git diff --check                                                    exit 0
unshare -rn backend/.venv/bin/python -m pytest backend/tests -q     exit 0  233 passed
unshare -rn backend/.venv/bin/python -   (inline socket probe)      DENIED (Network is unreachable)
done_captured=2026-11-13T04:58:01Z

frontend: npm run build                                             exit 0
frontend: npm test                                                  exit 0  10 passed
```

## Self-review

* **Counts from the response:** the component tests mutate the findings response and assert the
  rendered counts/coverage change; no identity or count is hard-coded.
* **Proposal honesty:** proposals render only from `proposed_links`, carry a `not accepted` badge,
  and never affect coverage; REQ-002 remains missing verification.
* **Baseline visibility:** the selector and the resolved commit are always visible; switching
  reloads findings/artifacts/thread.
* **Offline:** tests inject committed JSON; no network. `npm ci` is the only network step (documented).
* **Backend untouched:** no response shape or fixture change; the AS01-R1 change is test-only.
* **Accessibility:** labelled selector, table headers, buttons, and a labelled summary list.

Known limits: the UI consumes the reviewed sample findings in M1; it does not call the evaluator.
Links cannot be reviewed from the UI (AS-06). No authentication or deployment.

## Independent review

**APPROVE** — submission 3 of 7, snapshot captured 2026-11-13T04:58Z, reviewer `gpt-6.1-sol` at
`xhigh`, 41/41 hashes confirmed. Verdict: `docs/reviews/AS-04-review-3.md`. Nonblocking AS04-N3
(record consistency) is fixed here. Commit, PR, CI, and merge state are recorded separately after
landing; this approval does not close #26 by itself.
