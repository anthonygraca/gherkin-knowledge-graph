# AS-04 — independent review, round 2

**Task:** AS-04 (#26), M1, owner C. **Submission 2 of 7.**
**Reviewer:** Codex, `gpt-6.1-sol`, `xhigh`, read-only — session `01a1d33b-a290-70b2-b8a6-4deeccb0d957`,
2026-11-13T04:47:42Z → 04:55:20Z (457.66 s), exit 0; 295,809 CLI-reported tokens.
**Reviewed snapshot:** branch `feat/26-as-04-summary-ui`, base
`d238776bf0b53e6963f8e81721ce9a106f848adb`, captured 2026-11-13T04:44Z; 30/30 hashes matched
before and after.
**Packet:** `docs/reviews/AS-04-review-prompt-2.md`, sha256
`0c6c76e7156bd82710a504b9a4f92c4bbec1d3c2ea3b3d6cbbe5f4a8ccc6336d` (35,424 bytes).
**Verdict:** **NEEDS_INPUT** — SCN-801…805 all PASS; R1/R2/N1 closed. **E1** (blocking evidence gap:
raw check logs missing; network invocation abbreviated) and **N2** (nonblocking: stale thread error
after a successful selection) were addressed for submission 3 (`docs/reviews/AS-04-review-3.md`).
The verdict attests no human labeling, link decisions, refinement sign-off, stakeholder acceptance,
or milestone completion.

The verdict below is copied verbatim from the reviewer's final message (raw file sha256
`3d932ab9b3f7fe24184ebb545f64c57ecaf70eb23affaa9dd69bf5af7938296d`; it contained no local absolute
paths, so no sanitization was needed).

---

**NEEDS_INPUT — AS-04, submission 2 of 7.**

Reviewed `feat/26-as-04-summary-ui`, base `d238776bf0b53e6963f8e81721ce9a106f848adb`, snapshot captured `2026-11-13T04:44Z`. All **30 supplied hashes matched before and after review**. No repository files edited.

| Criterion | Assessment | Observed behavior |
|---|---|---|
| SCN-801 | PASS | Baseline-a shows response-derived counts, REQ-001 Covered, and REQ-002 Missing verification. |
| SCN-802 | PASS | Baseline changes hide unmatched summary data; delayed responses and failures preserve correct attribution. |
| SCN-803 | PASS | Altered responses change displayed categories and numeric counts, including `2`. |
| SCN-804 | PASS | LNK-007 appears under proposals with “not accepted”; REQ-002 remains uncovered. |
| SCN-805 | PASS | Baseline-b shows LNK-001–003, relation types, SCN-001’s evidence, and the baseline. Thread transitions hide unmatched contents. |

**Prior dispositions:** AS04-R1, AS04-R2, and AS04-N1 are repaired. The AS01-R1 test now independently binds both revision fields to the manifest tag and passes.

**AS04-E1 — major, blocking verification gap; story DoD §4 and lifecycle execution evidence.**  
[AS-04.md:97](docs/stories/AS-04.md:97) requires the backend suite, fixture verification, and network-denied suite. [IMPLEMENTATION.md:98](docs/reports/omp-as-04-summary/IMPLEMENTATION.md:98) provides summarized outcomes; retained raw execution records are unavailable, and the network-denied invocation contains an ellipsis.

Expected: attributable execution evidence identifying exact invocations, configuration, snapshot, outputs, and exits. Actual: these required checks remain **NOT VERIFIED** independently; repeating them requires filesystem writes. This is an evidence gap, not an observed implementation failure.

Smallest correction/recheck: OMP should supply the retained full-suite, fixture-verification, and network-denied logs tied to this unchanged manifest. These were requested during review.

**AS04-N2 — low, nonblocking; error attribution/recovery.**  
At [App.tsx:178](frontend/src/App.tsx:178), a successful thread selection does not clear the previous thread’s global error. Reproduced: fail REQ-002, then select REQ-001; its correct chain and EV-001 load while the REQ-002 failure alert remains.

Expected: alerts describe the active request. Smallest correction/recheck: key or separately reset thread errors without clearing unrelated errors; check failure followed by successful selection.

Independent verification passed:

- Official Vitest: **10 passed**, using threads, disabled caching, and the runner config loader.
- Both TypeScript configurations and production bundling in memory.
- **19 domain tests** and **seven submitted assurance cases** through adapted ASGI dispatch.
- Real API inventories, findings, and six threads against committed fixtures; unknown-baseline errors and AS-06’s 501.
- Ruff, formatting, whitespace, and proposed commit-message validation.

Accepted links, proposals, and evidence remain separate. Backend product code and generated fixtures are unchanged; no new freshness computation or model dependency was introduced. Four screenshots support the demonstrated views; the claimed clean browser console remains unverified.

This review does not attest human labeling, human link decisions, refinement sign-off, stakeholder acceptance, or milestone completion.