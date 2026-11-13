# AS-04 — independent review, round 1

**Task:** AS-04 (#26), M1, owner C. **Submission 1 of 7.**
**Reviewer:** Codex, `gpt-6.1-sol`, `xhigh`, read-only — session `01a1d326-1f96-7e80-a251-ed613c6485d1`,
2026-11-13T04:24:12Z → 04:31:11Z (418.81 s), exit 0; 109,521 CLI-reported tokens.
**Reviewed snapshot:** branch `feat/26-as-04-summary-ui`, base
`d238776bf0b53e6963f8e81721ce9a106f848adb`, captured 2026-11-13T04:22Z; 28/28 hashes matched
before and after.
**Packet:** `docs/reviews/AS-04-review-prompt.md`, sha256
`42253195ead218481771136b405be228d88a613e356d2f0d4a5aae7a28f68b30` (46,424 bytes).
**Verdict:** REQUEST_CHANGES — **R1** (stale summary under a new baseline), **R2** (stale thread under
a new selection), both blocking; **N1** (numeric-count coverage) nonblocking. All repaired for
submission 2 (`docs/reviews/AS-04-review-2.md`).

The verdict below is copied verbatim from the reviewer's final message (raw file sha256
`d7b028c803cc892af4571743c3b17fb7fb7fe1eeb78319710837e1ac7acd4031` before path sanitization);
only the absolute repository path is substituted with `<task_repo>`.

---

**REQUEST_CHANGES — AS-04, submission 1 of 7.**

Reviewed `feat/26-as-04-summary-ui`, base `d238776bf0b53e6963f8e81721ce9a106f848adb`, snapshot captured `2026-11-13T04:22Z`. All **28 supplied hashes matched before and after review**. No files changed.

| Criterion | Assessment | Evidence |
|---|---|---|
| SCN-801 | PASS | Loaded baseline-a shows all four counts, REQ-001 Covered and REQ-002 Missing verification. |
| SCN-802 | FAIL | Baseline changes can display the previous baseline’s counts and coverage under the new baseline. AS04-R1. |
| SCN-803 | PASS | Counts follow response contents; an independent probe with two findings of one type rendered `2`. |
| SCN-804 | FAIL | Settled proposal labeling works, but selecting REQ-002 temporarily displays REQ-001’s accepted chain and evidence. AS04-R2. |
| SCN-805 | FAIL | Settled baseline-b content is correct; during selection changes, the thread heading can identify a different requirement/baseline from its contents. AS04-R2. |

**Blocking findings**

- **AS04-R1 — major, blocking; SCN-802 and baseline/error honesty.** At [App.tsx:126](<task_repo>/frontend/src/App.tsx:126), changing the baseline retains existing findings and artifacts while the displayed baseline changes immediately. Reproduced: hold baseline-b’s findings request after loading baseline-a; the summary says baseline-b while showing baseline-a’s four counts and REQ-001 as Covered. Rejecting the request leaves that mismatch after loading ends. An initial request failure also displays “No findings at this baseline.”

  **Expected:** numbers and coverage identify their actual loaded baseline; unavailable data remains distinguishable from a successful empty result. **Smallest correction/recheck:** retain the loaded baseline with summary data and render only a matching snapshot, with explicit loading/error/empty states. Add deferred-response and rejected-request regression checks.

- **AS04-R2 — major, blocking; SCN-804/805 and thread attribution.** At [App.tsx:156](<task_repo>/frontend/src/App.tsx:156), starting a new thread request retains the previous thread while its heading uses the new selection. Reproduced: select REQ-002 after loading REQ-001 and delay its response. “Thread for REQ-002” displays LNK-001 and EV-001; LNK-007 is absent until completion. Baseline changes have the same exposure.

  **Expected:** displayed relationships and evidence belong to the identified requirement and baseline. **Smallest correction/recheck:** guard rendering against both `thread.root_id` and `thread.baseline`, and show a pending state for unmatched data. Check delayed requirement changes, baseline changes and failures.

**Nonblocking test improvement**

**AS04-N1 — low, nonblocking; SCN-803.** [App.test.tsx:115](<task_repo>/frontend/src/App.test.tsx:115) checks category disappearance without checking a changed numeric count. Add a response containing two findings of one type and assert `2`. The implementation passed that independent probe.

**Verification and limits**

Independent checks passed: both TypeScript configurations, production bundling entirely in memory, Ruff, formatting, whitespace, proposed commit-message validation, five submitted test bodies through an adapted React harness, and seven assurance cases through adapted ASGI dispatch. AS01-R1 is repaired: both revision fields are checked against the committed manifest tag.

Real API probes matched the fixture inventories, findings and six threads, accounting for inventory sorting. Accepted links, proposals and evidence remain separate; AS-06 review returns 501. Backend product code and generated fixtures are unchanged. No new freshness computation or model dependency was introduced.

**NOT VERIFIED:** the official Vitest run stopped before collection because temporary-directory creation was denied. Full pytest, fixture verification and network-denied execution were not rerun; retained raw outputs were requested but remain unavailable. Four screenshots were inspected; they cannot establish the claimed zero console errors.

This review does not attest human labeling, human link decisions, refinement sign-off or stakeholder acceptance.