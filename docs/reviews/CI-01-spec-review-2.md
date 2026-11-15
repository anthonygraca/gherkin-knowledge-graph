## Verdict

**REQUEST_CHANGES**

The revision resolves several subpoints, but completeness, diagnostic construction, workflow scope, and failed-test publication still require design decisions. The companion misidentifies prior findings R3, R5, and R6; its disposition table does not establish their closure.

Specification inspection only. No files changed, tests executed, commits created, or work delegated.

## Criterion assessment

| Scenario | Assessment | Remaining issue |
|---|---|---|
| SCN-3401 | AMBIGUOUS | Input-manifest coverage and finding-payload mapping remain insufficiently defined. |
| SCN-3402 | AMBIGUOUS | Selected-commit execution is now explicit, but workflow revision attribution across the CTA and generated banking repositories conflicts. |
| SCN-3403 | AMBIGUOUS | Provenance validation is clearer; partial coverage, unavailable execution, and retained provenance remain underspecified. |
| SCN-3404 | CLEAR | A valid recorded failure produces `execution_failed`, while assurance completes with exit `0` and makes no requirement verdict. |
| SCN-3405 | AMBIGUOUS | Stderr fallback is defined, but the incomplete envelope cannot represent every listed failure without additional choices. |
| SCN-3406 | AMBIGUOUS | Tool-failure upload is added; failed-test publication, gate preservation, and fallback artifact delivery remain unresolved. |

## Findings

1. **CI01-SPEC-R1 — major; blocking: yes — Report and manifest contract only partially frozen.**

   **Location:** report contract §1, especially `inputs`; §2; SCN-3401.

   “Every required ingestion input” does not enumerate coverage of accepted/proposed links, evidence, historical artifact content used for freshness, or execution metadata. The separately published “input manifest” has no defined document shape or path/revision context.

   The finding payload also omits existing `AssuranceFinding.status` and `artifact_revisions` without defining whether this is a deliberate projection. Consequently, “findings match the … oracle” does not establish which fields must match.

   **Smallest correction:** Define manifest coverage and serialization, including revision-qualified historical inputs and provenance sidecars. Define the scope-specific finding types or explicit projections, preserving required revision attribution, and specify oracle comparison fields.

2. **CI01-SPEC-R2 — major; blocking: yes — Workflow revision attribution conflicts across repositories.**

   **Location:** contract §§3 and 6; SCN-3402.

   Section 3 requires the event-selected commit to drive ingestion and evaluation. Section 6 says the workflow builds the banking fixture and “evaluates the selected revision.” A triggering CTA commit is not a commit in the generated banking repository.

   The specification does not assign each workflow evaluation to its repository and revision. An implementer must choose whether the workflow evaluates CTA, banking, or both, and how each report relates to the event.

   **Smallest correction:** Define the workflow’s scope/repository/revision matrix. Distinguish CTA head/push-after self-assurance from banking baseline evaluation, identify evaluator attribution, and require hosted event-to-report evidence for the supported triggers.

3. **CI01-SPEC-R3 — major; blocking: yes — Completeness remains distinct from neither coverage nor availability.**

   **Location:** contract §1; SCN-3403 and the Rule preceding SCN-3404.

   `tool_outcome=completed` labels completeness but does not define its predicate. There is still no disposition for absent reports, valid partial reports, skipped/unknown executions, or recoverable ingestion diagnostics.

   The source-equality language also needs to distinguish “every imported source matches” from “the report covers every indexed feature.” These produce different outcomes for filtered executions. Existing portable behavior explicitly supports unavailable evidence and unknown outcomes.

   **Smallest correction:** Add a completeness/availability decision table and boundary examples. Specify required execution inputs, permitted coverage gaps, diagnostic handling, and resulting exit/outcome values. Define the intended source-set equality and how coverage limitations remain observable.

4. **CI01-SPEC-R4 — major; blocking: yes — The incomplete envelope and fallback publication remain inconsistent.**

   **Location:** contract §1 and §6; SCN-3405–3406.

   Stderr delivery resolves the original missing fallback channel. However, `execution_report` remains required for portable scope even when provenance is malformed or resolution fails. Required input digests cannot be supplied for unreadable inputs, and no incomplete representation is defined.

   For an unwritable destination, the diagnostic exists only on stderr, while §6 unconditionally requires its artifact upload. No capture/staging rule connects those requirements or prevents publication of an older destination file.

   **Smallest correction:** Define diagnostic-specific nullability and unavailable-input representation, plus identifiable failure stage/code. Specify fallback capture for artifact publication and prohibit stale completed output from being published as this run’s result.

5. **CI01-SPEC-R5 — major; blocking: yes — Failed-execution publication and test-gate preservation remain unspecified.**

   **Location:** SCN-3404 and SCN-3406; contract §6.

   The added failure publication covers evaluator exit `2`. Prior R5 concerns a different path: Cucumber fails, its valid report yields assurance exit `0`, and workflow sequencing must still run assurance and publication while preserving the failing test gate.

   `if: always()` on artifact upload alone does not require assurance or summary generation after the failed test step. Publisher-failure behavior also remains undefined.

   **Smallest correction:** Add an integration example requiring a valid failed Cucumber run to produce and publish completed assurance findings while the original test gate remains failing. Define how artifact/summary failures affect workflow status without rewriting evaluator outcome.

6. **CI01-SPEC-R6 — minor; blocking: no — Gate wording remains stale.**

   **Location:** CI-01.feature:1–3; CI-01.md:6–7 and disposition row R6.

   These still describe owner acceptance and M3 exit as pending. ADR 0012 §3 records acceptance, and `docs/reviews/M3-review-2.md` records M3 approval. Prior R6 concerned this wording, not hosted-versus-YAML evidence.

   **Smallest correction:** Reference the completed dispositions while retaining draft status pending specification approval. Correct the disposition table’s R3/R5/R6 mappings.

## Implementation readiness

Frozen: the two assurance scopes, offline execution, PR-head/push-after selection, end-to-end selected-commit intent, report-only exit semantics, basic digest construction, portable provenance validation, and prohibition on branch writes.

Remaining: manifest and payload coverage, completeness/availability semantics, workflow scope-to-revision attribution, constructible diagnostics with reliable publication, and failed-test gate preservation.

M3 eligibility is established. CI-01 implementation readiness is **not yet established**.
