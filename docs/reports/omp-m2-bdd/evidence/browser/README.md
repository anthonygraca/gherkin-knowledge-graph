# Browser demonstration — findings drill-down (AS-05)

Captured 2026-11-13 against a real `uvicorn` backend on `127.0.0.1:8000` and the Vite dashboard on
`127.0.0.1:5173`, in a headless browser tab opened by the harness (not Vitest/jsdom).

Observed in the live DOM:

* baseline selector `baseline-b`, resolved commit shown in the header;
* six findings rendered from `GET /api/findings?baseline=baseline-b`, matching the evaluated rule
  set (two of them were added by M2: `reverification_required`, `verification_failed`);
* `reverification_required` drill-down: rule `RULE-REVERIFICATION-REQUIRED`, evaluated baseline
  `893c3b54ab035be491aaa737b9b13ba3677c5044`, artifacts `CODE-001`/`REQ-001`/`SCN-001`, evidence
  `EV-001 passed` at tested commit `d29bafc3d37b4f467a434f02231223862696a1ee`, wording
  "not a verification failure";
* `verification_failed` drill-down: rule `RULE-VERIFICATION-FAILED`, evidence `EV-003 failed` at
  tested commit `5bf2ee1e0f71728eaad72c0139695147b8a85b5c`, wording "Verification failed";
* re-verified after the review repair: with the thread selector still on REQ-001, opening the
  REQ-003 failure finding loads EV-003 and its tested commit `5bf2ee1e…`; the thread heading stays
  `Thread for REQ-001 baseline-b`;
* browser console errors: none.

The selected baseline commit differs from the earlier fixture SHAs because the schema-0.3.0
regeneration rebuilt the deterministic history; the oracle expectations are unchanged.

`baseline-b-drilldown.png` is the full-page screenshot taken after both drill-downs were opened.
HTTP captures (health, findings for both baselines, thread, evaluate) are in `../http/`.
