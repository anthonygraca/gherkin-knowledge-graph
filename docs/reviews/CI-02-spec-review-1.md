## Verdict

**REQUEST_CHANGES**

The finding identity, fixture counts, and classification meaning are sound. Implementation still requires decisions about report structure, comparison eligibility, input validation, payload retention, and the portable-mapping exception.

GitHub #37 could not be retrieved. Issue alignment was assessed against its captured body in `docs/reports/omp-closeout/advice/request.md:221`, rather than a verified current issue body.

## Criterion assessment

| Scenario | Assessment | Exact text or contract needing change |
|---|---|---|
| SCN-3501 | AMBIGUOUS | “complete comparable assurance reports” lacks a normative eligibility contract. “the report includes both resolved revisions and both report digests” lacks field definitions, digest construction, and a report schema. The counts and finding types are correct. |
| SCN-3502 | CLEAR | The reverse counts and “resolved means absent from the current comparable finding set” are precise and consistent with the oracle. No semantic correction required; its serialized result depends on the missing shared report contract. |
| SCN-3503 | CLEAR | Self-comparison of the complete banking baseline-a report correctly yields 0 new / 4 unchanged / 0 resolved. No scenario-specific correction required. |
| SCN-3504 | AMBIGUOUS | “before and after payloads are both retained” and “neither payload is rewritten” must identify the complete retained payload, its representation, and whether preservation means field-value equality or original bytes. |
| SCN-3505 | AMBIGUOUS | “two report inputs differ by” does not establish otherwise-valid inputs. “the current evaluation is incomplete” omits the previous evaluation. Repository identity, rule scope, policy version, and contradictory baseline require exact comparison rules. |
| SCN-3506 | AMBIGUOUS | “no reviewed continuity mapping accompanies them” leaves behavior with a mapping undefined. “does not classify displaced findings as resolved and new” is weaker than refusing every new/unchanged/resolved classification. |

## Findings

1. **CI02-SPEC-R1 — major; blocking: yes — The comparison report format is missing.**

   SCN-3501 requires revisions and report digests; SCN-3504 requires retained payloads. Neither the feature nor companion defines the typed comparison envelope. The captured issue additionally requires documentation in M4’s benchmark report format.

   CI-01 specifies report contents behaviorally, but does not supply a concrete shared schema. Existing findings responses do not establish the proposed completeness, policy-version, identity-strategy, or evaluator-provenance fields.

   **Smallest correction:** freeze one shared CI-01/CI-02 contract and reference it from the canonical criteria. Define:

   - Schema version, comparison direction, repository identity, both evaluated revisions, and both source-report digests.
   - Classification entries and counts, including full current payloads for new findings, full previous payloads for resolved findings, and full before/after pairs for unchanged findings.
   - Required retained provenance, deterministic ordering, digest algorithm and hashed representation.
   - Successful exit behavior and the typed diagnostic representation for refusal.
   - How classification fields are absent or unavailable on refusal, so empty successful sets cannot be confused with “no classification.”

   Clarify that retained payloads preserve field values, including original baselines, evidence references, severity, status, explanations, and artifact revisions—or explicitly require byte preservation if that is intended. Document the envelope’s relationship to the benchmark format.

2. **CI02-SPEC-R2 — major; blocking: yes — “Comparable” has no complete operational definition.**

   SCN-3505 names repository, evaluated rule scope, and policy-version mismatches without defining their representation or equality. The current evaluator exposes policy name `default`; it does not establish a policy-version contract.

   CI-01 also records evaluator revision. The specification does not decide whether different evaluator revisions are compatible when declared scope and policy match. Silent acceptance and unconditional rejection would produce different supported behavior.

   **Smallest correction:** define a comparison-eligibility predicate covering supported report schemas, repository identity, assurance scope, evaluated rule set, policy identity/version, identity strategy, and completed evaluation state. State which provenance fields must match and which may differ. In particular, evaluated revisions must be allowed to differ; evaluator-revision compatibility needs an explicit rule.

   Define “a finding baseline contradicts its report” as disagreement between that finding’s `evaluated_baseline` and its containing report’s resolved **evaluated** revision. Legitimately older evidence `tested_commit` values must remain permitted.

3. **CI02-SPEC-R3 — major; blocking: yes — Incomplete previous evaluations are not explicitly covered.**

   The feature introduction and ADR require complete reports, but SCN-3505 only exercises an incomplete current evaluation. An incomplete previous evaluation can invent new findings just as an incomplete current evaluation can invent resolutions.

   **Smallest correction:** require completeness independently for both inputs and add the previous-incomplete example. Make the outline’s setup “otherwise valid, comparable inputs except for the named condition.” Identify the affected side for finding-baseline contradictions, and apply that validation to both sides.

   Preserve exit `2`, code `findings-not-comparable`, an attributable reason, and no classification for every refusal. Evaluation failure or unavailable evidence must never be converted into an empty successful finding set.

4. **CI02-SPEC-R4 — major; blocking: yes — Imported finding identity inconsistencies and duplicates have no disposition.**

   The identity algorithm itself is fixed correctly: `finding_fingerprint` hashes rule ID, finding type, and sorted unique artifact IDs. Baseline, prose, evidence, severity, and status are excluded.

   However, `AssuranceFinding` validates the `finding_id` pattern without checking that it matches those inputs. The draft does not say whether comparison trusts supplied IDs, recomputes them, or rejects disagreement. Multiple payloads with one identity also make the required before/after pair ambiguous.

   **Smallest correction:** require each supplied ID to match the existing fingerprint without rewriting the supplied payload. Specify duplicate handling, including conflicting payloads sharing an identity. Rejecting duplicate identities and inconsistent IDs with the standard refusal diagnostic would resolve this without introducing a selection rule.

5. **CI02-SPEC-R5 — major; blocking: yes — Portable comparison has an undefined positive branch.**

   ADR 0012 establishes that source-locator findings are not comparable without an independently reviewed continuity mapping. It does not define a mapping format or comparison algorithm.

   SCN-3506 leaves implementers to decide whether an accompanying mapping enables comparison, what constitutes independent review, and whether same-revision or mixed-strategy inputs qualify. Its final assertion also permits partial classifications other than the specifically prohibited resolved/new pair.

   **Smallest correction:** explicitly defer mapping consumption for this slice and refuse all source-locator comparisons until a separately reviewed additive mapping contract exists. Alternatively, specify that contract before implementation. In either case, require the same complete refusal semantics as SCN-3505: exit `2`, `findings-not-comparable`, and **no** new, unchanged, or resolved classification.

6. **CI02-SPEC-R6 — minor; blocking: no — Useful boundary examples are absent.**

   After the contracts above are frozen, add examples for complete empty reports, artifact-ID reordering/deduplication, and changes to each identity component. A severity-only payload change would also demonstrate that “unchanged” describes identity rather than identical content.

   **Smallest correction:** extend the verification plan with independent expected sets for these cases. These examples need not block implementation once their governing rules are explicit.

## Implementation readiness

The following behavior is determined without guessing:

- Preserve the existing fingerprint algorithm.
- Classify identities using `new = current − previous`, `unchanged = current ∩ previous`, and `resolved = previous − current`.
- Keep payload-only changes within the unchanged category.
- Treat classification as an observation about finding-set membership, without creating verification evidence, requirement verdicts, or automatic closure.

An independent read-only calculation over the hand-labeled oracles confirmed:

| Comparison | New | Unchanged | Resolved |
|---|---:|---:|---:|
| baseline-a → baseline-b | 2 | 4 | 0 |
| baseline-b → baseline-a | 0 | 4 | 2 |
| baseline-a → itself | 0 | 4 | 0 |

The four persistent identities are the missing verification link, missing implementation link, pending candidate review, and lifecycle review. Baseline-b adds reverification for `CODE-001/REQ-001/SCN-001` and recorded verification failure for `REQ-003/SCN-003/TEST-002`.

These semantics respect “change is not failure” and “absence does not imply remediation.” No direct semantic conflict with CI-01 was found; the blocking problem is its unfinished shared report contract.

Freeze R1–R5 before implementation. The recorded M3 gate is approved, but CI-01’s producer contract remains a dependency. This review establishes neither specification approval nor execution evidence.
