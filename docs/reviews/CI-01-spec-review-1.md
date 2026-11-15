## Verdict

**REQUEST_CHANGES**

The draft agrees with ADR 0012’s two scopes and outcome semantics, but implementation still requires choices about report comparability, completeness, diagnostic delivery, and workflow execution.

Reviewed checkout `0456d199e243490ac1571588b0441d11e7ddef3d`; CI-01 feature SHA-256 `ec53d9f057849517641d69c18c59b2161309522713d1d8d3f8b9d1dd93bbaa3c`. Live GitHub access failed; issue consistency was assessed against the captured #36 body in `docs/reports/omp-closeout/advice/request.md:195`. No files were changed, tests executed, or work delegated.

## Criterion assessment

| Scenario | Assessment | Exact text or contract needing change |
|---|---|---|
| SCN-3401 | AMBIGUOUS | “its complete report” and “input content hashes” lack a normative envelope, manifest definition, completeness predicate, and digest rules. Reference a frozen report contract. The offline conditions and baseline-b oracle are otherwise observable. |
| SCN-3402 | AMBIGUOUS | “the selected evaluated revision equals the event head SHA” clearly defines selection, but does not establish that ingestion and execution actually use that commit. Add end-to-end attribution and a push-after case. |
| SCN-3403 | AMBIGUOUS | “an attributable Cucumber report” and “parsed feature hashes match” need an explicit reference to existing importer provenance requirements and retained provenance fields. The `gherkin_executability` scope and prohibition on production-code verification claims are clear. |
| SCN-3404 | CLEAR | “exits 0,” `tool_outcome="completed"`, and an `execution_failed` finding distinguish observed execution failure from tool failure. No correction is needed to this scenario’s core rule. |
| SCN-3405 | AMBIGUOUS | “its diagnostic report” is undefined when “an unwritable report destination” occurs. “marked incomplete” also lacks defined semantics for unavailable evidence and recoverable ingestion diagnostics. Specify diagnostic transport and outcome/completeness rules. |
| SCN-3406 | AMBIGUOUS | “Given a completed deterministic assurance report” bypasses revision-triggered production of that report. Publication contents and prohibited writes are observable, but failure-path publication and interaction with existing test gates are unspecified. Hosted execution is explicitly required by the companion. |

## Findings

1. **CI01-SPEC-R1 — major; blocking: yes — The typed report contract is not frozen.**

   **Location:** CI-01.feature:18–20, 35–37, 48, 57–58, 72; CI-01.md:11–13; ADR 0012 §3.

   “Typed” describes an implementation property without defining the data CI-02 will consume. Existing `AssuranceFinding`, `ExecutableFinding`, and `ReportProvenance` provide reusable components, but none supplies the proposed envelope. CI-02 already requires repository, scope, policy, completeness, baseline consistency, and report digests.

   **Smallest correction:** Add a normative report-contract table, referenced by both stories, defining:

   - Schema version, run identity, UTC timestamp, repository identity and identity strategy.
   - Distinct evaluated and evaluator revisions, including permitted absent values in diagnostics.
   - Scope discriminator, evaluated rule set, policy identity/version, and finding payload type for each scope.
   - Input-manifest entries and coverage: evaluated content, links, evidence, relevant historical inputs, execution report and provenance sidecar.
   - Completeness, tool outcome, diagnostics, and their permitted combinations.
   - Manifest/report/evidence digest algorithms and byte or canonicalization rules, including how any report digest avoids self-reference.
   - Finding-baseline consistency and preservation of the existing fingerprint. Portable locator identities must retain ADR 0012’s comparison restriction.

   The schema implementation can follow this agreement; prose approval of an unspecified envelope is insufficient.

2. **CI01-SPEC-R2 — major; blocking: yes — Revision selection is specified more strongly than revision execution.**

   **Location:** SCN-3402; SCN-3406; captured issue #36 acceptance criterion.

   The issue requires ingestion, evaluation, and storage **for the triggering revision**. A resolver test plus publication of a pre-existing report does not demonstrate that behavior. Push-after selection appears only in companion prose.

   This matters because the existing BDD job uses default PR checkout behavior, while the commit-reference job explicitly selects PR head. Its Cucumber output cannot simply be labeled as head evidence.

   **Smallest correction:** Require an observable path from supported PR/push event through ingestion/evaluation to the published report. Assert that evaluated content comes from PR head or push-after, and that imported execution provenance belongs to that selected revision. A separate head execution is acceptable; existing test gates may retain their own baseline. Define supported triggers and retain hosted event/run/report evidence.

3. **CI01-SPEC-R3 — major; blocking: yes — Unknown evidence and incomplete evaluation lack separate semantics.**

   **Location:** SCN-3403; SCN-3405; the Rule “Findings, unknown evidence, and tool failures remain distinct.”

   The rule promises an unknown-evidence distinction, but every example supplies either attributable evidence or a hard failure. Existing portable contracts support no report, skipped execution, unknown outcomes, partial coverage, and ingestion diagnostics. An empty finding set can therefore mean unavailable evidence rather than a clean suite.

   Without a completeness definition, implementations could disagree about whether these reports qualify for CI-02 comparison.

   **Smallest correction:** Define evaluation completeness separately from execution availability/coverage. Add boundary examples for absent evidence, valid but partial/skipped/unknown execution, and ingestion diagnostics. State when execution evidence is required, which diagnostics prevent complete evaluation, and the resulting exit/completeness values. Preserve existing rules: absence creates neither execution evidence nor undefined-step defects; feature attribution uses hashes; banking freshness remains content-based.

4. **CI01-SPEC-R4 — major; blocking: yes — The storage-failure diagnostic has no delivery contract.**

   **Location:** SCN-3405, especially the unwritable-destination example.

   The scenario requires a diagnostic report even when its destination cannot be written. It does not identify a fallback channel, diagnostic shape, or representation of an unresolved revision. Two implementations could satisfy the exit-code assertion while producing incompatible or unavailable diagnostics.

   **Smallest correction:** Specify a guaranteed observable fallback, such as a typed diagnostic on stderr, carrying tool-failure outcome, incomplete status, failure code/stage, requested revision and resolved revision when available. State that no complete report from this failed run may be published, including an older file accidentally reused at the destination. Keep genuine partial findings distinguishable from the tool error itself.

5. **CI01-SPEC-R5 — major; blocking: yes — Failed-test publication and gate preservation need an integration criterion.**

   **Location:** SCN-3404; SCN-3406; CI-01.md non-goal “replacing existing test gates.”

   A valid failed Cucumber run makes assurance complete successfully, while the project’s acceptance gate must still fail. Current workflow sequencing stops ordinary subsequent steps after the failed suite; only the existing report upload explicitly runs unconditionally.

   The draft does not require assurance and summary publication to occur in that situation. An implementation could lose precisely the findings SCN-3404 introduces, or mask the original gate failure to obtain publication.

   **Smallest correction:** Add a workflow failure-path example: a valid attributable failed run still produces and publishes assurance findings, the assurance command returns `0`, and the original test gate remains failing. Separately define observable behavior when artifact or summary publication fails, distinguishing publisher failure from evaluator outcome.

6. **CI01-SPEC-R6 — minor; blocking: no — Gate wording is stale.**

   **Location:** CI-01.feature:1–3; CI-01.md:6–7.

   These still describe owner disposition as pending. ADR 0012 accepts the two-scope framing, and `docs/reviews/M3-review-2.md` records M3 approval.

   **Smallest correction:** Reference those completed decisions while retaining the specification’s draft status until this review is resolved. Refresh related inventory wording when adopting the specification.

## Implementation readiness

The existing behavior can be reused without redesign: deterministic banking rules and hand-labeled oracles; content-based freshness; stable finding fingerprints; portable provenance validation; executability findings; read-only ingestion; and the distinction between findings and tool failure. The production-code assurance prohibition, report-only command semantics, prohibited branch writes, and requirement for hosted evidence are clear.

Before CI-01 implementation begins, freeze the shared report/manifest contract, completeness and evidence-availability semantics, diagnostic fallback, supported event-to-revision execution path, and failed-gate publication behavior. These are observable contract decisions that CI-02 and acceptance tests must not inherit accidentally from implementation.

Reuse substantive existing M2 and portable checks for their established contracts. New verification should exercise the command and hosted workflow boundaries. Historical green CI and YAML inspection do not establish execution of CI-01.
