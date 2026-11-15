## Verdict

REVISE

This is a specification-readiness verdict only. Inspection was read-only; no tests were run.

## Findings

1. **AS07-SPEC-R1 — blocking — SCN-3101, SCN-3102; companion “Contract impact”.**

   SCN-3101 requires structured problem fields, but the companion calls them optional and leaves public contract impact conditional. SCN-3102 specifies only a “typed 503”; it selects neither a stable code nor the failed-provider field. Existing contracts distinguish `retrieval-unavailable` from CocoIndex-specific errors.

   **Smallest repair:** State that `failed_provider` and `registered_providers` are optional across problem documents but required for `provider-not-registered`; the list comes from the effective registry. Name the registered provider in SCN-3102 and fix its timeout status/code—for example, `503 cocoindex-timeout` for CocoIndex—with `failed_provider: "cocoindex"`. Make the additive public contract update and MINOR schema bump definite.

2. **AS07-SPEC-R2 — blocking — SCN-3102, SCN-3105; companion “Verification plan”.**

   The recorded transport is honestly distinguished from real inference. However, the specification does not explicitly require the displayed result to pass through the real discovery route and problem mapping. Separate API and component checks could satisfy the current wording while supplying fabricated responses to the UI.

   **Smallest repair:** Add a normative verification statement: “The timeout and recorded-response cases replace only the provider’s external transport. The real provider adapter, `POST /api/discovery`, response/problem mapping, and dashboard consumption are exercised. API responses are not stubbed. These checks establish adapter/API/UI behavior, not live inference or retrieval quality.”

3. **AS07-SPEC-R3 — blocking — SCN-3101, SCN-3102.**

   SCN-3101 exposes the failed name and registered list in the API, but requires only a generic unavailable state in the panel. SCN-3102’s “displays the provider failure” also permits a generic message. Its accepted-thread/evidence usability is unspecified after the registered-provider failure.

   **Smallest repair:** Require the panel to display the failed provider’s name and, for the registration error, the returned registered-provider list. Explicitly distinguish selected-provider unavailability from availability of `"fake"`. Extend SCN-3102 to retain usable accepted-thread/evidence reads and unchanged accepted links, evidence, and findings, with no successful empty-result state or automatic provider switch.

4. **AS07-SPEC-R4 — blocking — SCN-3104–SCN-3106; companion “Scope”.**

   “Every proposal presentation” lacks an explicit surface boundary. SCN-3104 opens history without establishing any historical record, so its history assertion can be vacuous. SCN-3105 covers only the panel, while AS-06 permits absent provider, model, and index provenance; SCN-3106 specifies the missing-value behavior only for `model_version`.

   **Smallest repair:** Define the covered surfaces as transient discovery candidates, persisted proposals, proposal details, review history, and hybrid-answer candidates wherever present. Apply the three provenance fields and fixture/CTA-binding labels consistently across them. Give SCN-3104 a recorded review event whose original provenance remains visible. Extend SCN-3106 with examples for absent/null provider, model version, and index revision: each displays “not recorded” without substituting current configuration. Preserve the existing scenario IDs.

5. **AS07-SPEC-R5 — nonblocking — companion “Scope” and “Verification plan”.**

   Documenting fake mode is in scope, but the issue’s requirement that it remain the **default** development path has no explicit inspection criterion.

   **Smallest repair:** Add: “Documentation identifies fake discovery as the default and gives a reproducible offline development invocation requiring no model or network; verify this deliverable by inspection.”

## Scenario assessment

PASS denotes specification readiness, not executed behavior.

| Scenario ID | Assessment | Basis |
|---|---|---|
| SCN-3101 | FAIL | Required problem extensions and visible provider/list behavior need clarification: R1, R3. |
| SCN-3102 | FAIL | Timeout code, transport boundary, and complete failure-state behavior remain underspecified: R1–R3. |
| SCN-3103 | PASS | Clearly separates successful zero candidates, retained provenance, and provider unavailability. |
| SCN-3104 | FAIL | Presentation scope and nonempty history coverage need definition: R4. |
| SCN-3105 | FAIL | Recorded-adapter intent is honest; integrated exercise and presentation scope need clarification: R2, R4. |
| SCN-3106 | FAIL | Model-version case is coherent, but other nullable provenance fields lack defined examples: R4. |

SCN-3101–SCN-3106 are unchanged from the committed draft, unique among development feature tags, and within the assigned AS-07 range.

## Freeze conditions

- Resolve blocking findings AS07-SPEC-R1–R4 in the canonical specification and explicitly normative companion notes.
- Preserve existing scenario identities.
- Obtain specification re-review; implementation or passing execution evidence is not required for this freeze decision.