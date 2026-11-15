## Verdict

**REQUEST_CHANGES**

Reviewed the uncommitted snapshot based on `827e487`. All AS-07 cases are recorded passing, but implementation and verification gaps remain. No files were changed or work delegated.

## Criterion assessment

| Scenario | Assessment | Basis |
|---|---|---|
| SCN-3101 | PASS | Unknown-provider problem includes both extensions; fake remains selectable; thread/evidence remain accessible. |
| SCN-3102 | FAIL | Provider construction failures escape the required mapping; timeout evidence bypasses the real adapter. |
| SCN-3103 | PASS | Empty success retains provider/model/index and displays zero candidates distinctly. |
| SCN-3104 | FAIL | Review history preserves provenance, but the thread’s proposal table omits it. |
| SCN-3105 | PASS | Recorded transport exercises the real CocoIndex adapter and displays model identity and CTA snapshot binding. |
| SCN-3106 | FAIL | All six examples pass for proposal cards; the thread presentation renders blank provenance instead of “not recorded.” |
| SCN-3107 | PASS | Disabled CocoIndex history retains its model classification, recorded provenance, and separate availability notice. |

## Findings

1. **AS07-ACC-R1 — Major; blocking: yes — Provider construction escapes the availability boundary.**  
   **Location:** `backend/app/api/routes.py:178`, `backend/app/api/routes.py:186`.  
   **Expected:** A registered discovery provider that cannot execute returns `503 provider-unavailable` with `failed_provider`.  
   **Actual:** `providers.get()` runs before the `try`. A read-only probe through the real route and exception handler, with CocoIndex registered and its executable missing, returned `503 cocoindex-configuration-error` without `failed_provider`. The blanket `DomainError` rethrow also leaves availability errors unmapped.  
   **Smallest correction/recheck:** Include provider construction and availability failures within the discovery boundary, preserving unknown-provider and request-validation semantics. Recheck missing executable and transport timeout, including unchanged accepted data and absence of fallback.

2. **AS07-ACC-R2 — Major; blocking: yes — The thread proposal presentation drops provenance.**  
   **Location:** `frontend/src/App.tsx:38`, `frontend/src/App.tsx:579`, `frontend/src/App.tsx:1091`; incomplete assertions at `bdd/step_definitions/providers.steps.js:324`.  
   **Expected:** Every proposal presentation displays provider/model/index, fixture classification, and explicit missing-value labels.  
   **Actual:** `LinksTable` displays only reviewer identity/time through `provenanceText`. Rendering its actual implementation with recorded LNK-007 produced an empty provenance cell despite complete fixture provenance. Missing historical fields likewise receive no “not recorded” labels there. The “every proposal presentation” steps inspect only history.  
   **Smallest correction/recheck:** Apply the provenance presentation to thread proposal rows. Check pending LNK-007 and all six absent/null cases across both thread rows and proposal cards, then verify rejection history.

3. **AS07-ACC-R3 — Major; blocking: yes — Timeout acceptance evidence replaces the adapter.**  
   **Location:** `bdd/support/provider_ui_app.py:25`, `bdd/support/provider_ui_app.py:81`; `bdd/step_definitions/providers.steps.js:162`.  
   **Expected:** The timeout case replaces only external transport beneath the real CocoIndex adapter.  
   **Actual:** Timeout mode installs `TimeoutDiscovery`, which constructs candidates itself and subsequently raises `TimeoutError`. It never executes `CocoIndexCandidateDiscovery` or `CodeDiscovery`, contradicting the normative verification boundary.  
   **Smallest correction/recheck:** Inject a recorded-success/timeout transport beneath the real adapter and rerun SCN-3102 through the real route and dashboard. Observe discovery requests when asserting no silent fake fallback.

4. **AS07-ACC-R4 — Minor; blocking: no — Presentation ignores catalogue kind metadata.**  
   **Location:** `frontend/src/App.tsx:167`, `frontend/src/App.tsx:217`; `backend/app/discovery/registry.py:23`.  
   **Expected:** Current catalogue metadata determines provider classification; historical classification survives disabling providers.  
   **Actual:** Presentation uses a separate two-entry table. The registered `local-embeddinggemma` provider is classified as `model` by the backend but renders “provider kind not recorded.” A read-only presentation probe confirmed this.  
   **Smallest correction/recheck:** Consume catalogue kinds and maintain the historical fallback consistently. Check local-provider candidates and disabled-provider history.

5. **AS07-ACC-R5 — Minor; blocking: no — The promised lifecycle documentation is missing.**  
   **Location:** `docs/stories/AS-07.md:124`; `docs/development-lifecycle.md:87`.  
   **Expected:** Both README and development lifecycle documentation identify fake discovery as the default offline path.  
   **Actual:** README does; the lifecycle document does not mention fake discovery or its invocation.  
   **Smallest correction/recheck:** Add the default offline invocation or an explicit linked instruction, then inspect both documents.

## Check verification

- Inspected `git diff 827e487`, implementation files, canonical criteria, companion contract, specification approval, and owner dispositions.
- Verified all **54 manifest hashes** match current files.
- Parsed `final-cucumber.ndjson`: **177 cases, 1,704 passing step results**, successful completion. All seven AS-07 IDs occur; SCN-3106 has six passing examples—**12 concrete AS-07 cases total**. Embedded AS-07 source matches the current feature file.
- Independently ran the strict report gate: **PASS**.
- Independently ran Ruff without cache, format checking, and `git diff --check 827e487`: **PASS**.
- Observed retained backend evidence: **535 passed, 4 skipped**; retained fixture verification: **PASS**.
- Read-only route/handler and rendering probes reproduced R1, R2, and R4.
- No inspected failure path converts provider failure into accepted links, evidence, findings, or empty success.
- Full suites were not rerun because their harnesses write files. Current frontend build/component-test results, commit-reference results, and hosted required checks were **not observed** for this uncommitted snapshot.