## Verdict

REVISE

The accepted ADR resolves the operator and journal architecture choices. Blocking gaps remain in baseline binding, snapshot identity, observable contracts, and coverage of concurrency and recovery.

This is a specification assessment only. No files were changed, tests run, or work delegated.

## Findings

1. **AS06-SPEC-R1 — blocking — SCN-3002, SCN-3009: Review baseline and projection applicability are undefined.**

   SCN-3009 accepts “against baseline-b,” but the existing `ReviewRequest` has no baseline field and the scenario names no other selection mechanism. Other scenarios implicitly select baseline-a. The specification also does not say whether a decision appears in workspaces for other baselines.

   **Smallest repair:** Define the review request’s baseline parameter, its omission rule, and the resolved revision retained in the decision. Specify when that decision applies to a workspace at another baseline. Require freshness comparison of both endpoint content hashes, and add an equal-hashes/different-revision example that remains reviewable, including an evidence-only revision change.

2. **AS06-SPEC-R2 — blocking — SCN-3002, SCN-3003: Existing LNK-007 has no defined proposal snapshot.**

   The fixture proposal contains discovery provenance but no capture baseline, endpoint hashes, or snapshot identifier. SCN-3002 nevertheless requires its decision to identify those inputs. Neither the draft nor ADR §1 defines how this legacy proposal acquires them.

   **Smallest repair:** Define a legacy binding rule. For example: “For an imported proposal without a capture snapshot, construct the snapshot from its stored link/provenance and server-read endpoint hashes at the explicitly selected resolved baseline; durably retain that binding with the first decision without changing the fixture.” State whether any further explicit capture action is required, and illustrate the chosen behavior for LNK-007.

3. **AS06-SPEC-R3 — blocking — SCN-3001–SCN-3003; companion Contract impact: Snapshot and read surfaces lack an observable contract.**

   “Its snapshot,” “workspace thread,” “pending queue,” and “workspace history” have no defined API selector or response shape. Existing `TraceLink` has no typed snapshot or decision fields. A reviewer cannot determine where operator, decision time, baseline, hashes, and provenance must be observable.

   **Smallest repair:** Document the capture request/response and workspace/history read contracts, including success statuses and selectors. Define the immutable snapshot’s contents and identifier, and the decision fields identifying its link, snapshot, operator, server UTC time, reason, and evaluated revision. Preserve the existing review POST’s `TraceLink` response unless an explicitly versioned change is intended. Specify snapshot digest inputs if a digest identifies it. This requires contract documentation before freeze, not implementation.

4. **AS06-SPEC-R4 — blocking — SCN-3001: Capture has no defined invalid-input or duplicate behavior.**

   The only capture example succeeds. It does not require checking submitted hashes against authoritative baseline artifacts or rejecting missing endpoints and invalid relation directions. Repeating the same capture could create another pending proposal, return the original, or conflict; all currently fit the wording.

   **Smallest repair:** State the endpoint, direction, and authoritative-hash validation rules with typed failure outcomes and no published proposal on failure. Define capture identity and duplicate behavior, including capture after a terminal decision. Add examples for invalid capture and repeated capture, distinguishing an identical snapshot from changed content or provenance.

5. **AS06-SPEC-R5 — blocking — SCN-3006, SCN-3008: Rejection inputs do not isolate their intended outcomes.**

   SCN-3006 supplies an empty DocString, so it does not demonstrate a nonempty whitespace-only reason. SCN-3008 submits a rejection without a reason while expecting `409 review-conflict`; SCN-3005 expects a reasonless rejection to return `422`. Validation precedence is unspecified.

   **Smallest repair:** Supply an explicit nonempty whitespace value in SCN-3006, using an escaped request value or a step such as “reason consisting of three U+0020 spaces.” In SCN-3008, supply a valid nonblank rejection reason so that only the terminal-state conflict is under examination. State the outcomes for omitted, null, empty, and whitespace-only rejection reasons.

6. **AS06-SPEC-R6 — blocking — Decision rule; SCN-3008: Sequential conflict coverage leaves concurrency unspecified.**

   An already durable decision followed by another request does not establish what happens when two valid requests both encounter a pending proposal. The companion mentions conflicting writes but gives no expected result.

   **Smallest repair:** Add: “When concurrent valid accept and reject requests target the same proposal snapshot, exactly one succeeds, the other returns `409 review-conflict`, exactly one terminal decision is durable, and workspace state agrees with that decision.” Either request may win; the invariant must be deterministic.

7. **AS06-SPEC-R7 — blocking — Decision durability rule; SCN-3001–SCN-3003, SCN-3010: Successful recovery and append-only preservation lack examples.**

   SCN-3010 covers restart after failed persistence. Nothing demonstrates that successful captures and decisions survive restart. SCN-3008 preserves an earlier record during a refused operation, but does not establish preservation when another decision succeeds.

   **Smallest repair:** Add recovery examples showing that a captured pending proposal and successful acceptance/rejection retain their snapshot, audit fields, history, and projected state after restart. Add a successful decision on a different proposal and require previously recorded decisions and snapshots to remain unchanged. Leave journal format and synchronization mechanisms to design.

8. **AS06-SPEC-R8 — blocking — Identity rule and ADR 0012 §1: The accepted write boundary is insufficiently specified for verification.**

   The scenarios cover configured identity and identity mismatch, but not the accepted loopback and browser-origin restrictions. “Browser-origin restrictions” does not identify allowed origins or the treatment of an absent `Origin` header.

   **Smallest repair:** Define the allowed-origin policy, including absent-origin requests, and identify every capture/review mutation surface governed by it. Add observable rejection/no-write criteria for a disallowed browser origin and an inspection or integration criterion establishing loopback-only write access. No authentication service is needed.

9. **AS06-SPEC-R9 — blocking — Companion Scope and Verification plan: The promised review UI has no canonical acceptance criteria.**

   The companion includes “minimal review UI/history” and browser checks for accept/reject/history. The canonical scenarios exercise API and persistence behavior without specifying the corresponding user actions or visible results. AS-07’s provenance presentation does not define these actions.

   **Smallest repair:** Add browser criteria for accepting a proposal, rejecting with a required reason, viewing retained decision details, and showing a refused write without presenting success. Require the pending queue and accepted-link presentation to reflect the workspace result while findings and evidence remain unchanged. Alternatively, explicitly delegate this UI scope to a named story and align both companions.

10. **AS06-SPEC-R10 — nonblocking — Feature header; companion Status, Design defaults, Contract impact: Review-state metadata is stale.**

    The documents still describe operator/journal decisions as outstanding or proposed, although ADR 0012 §1 is accepted. The companion also requires an “independent acceptance review” before implementation, conflating that later review with this specification freeze review.

    **Smallest repair:** Reference the accepted ADR disposition and identify independent specification approval as the remaining pre-implementation gate. Keep implementation verification and acceptance review as later gates.

## Scenario assessment

PASS concerns the individual example’s specification readiness, not execution evidence. Cross-cutting blocking findings still prevent freezing the story.

| Scenario ID | Assessment | Basis |
| --- | --- | --- |
| SCN-3001 | FAIL | Snapshot/read contract and capture validation/duplicate outcomes are undefined: R3–R4. |
| SCN-3002 | FAIL | Review baseline, legacy snapshot binding, and audit/read contracts are unresolved: R1–R3. |
| SCN-3003 | FAIL | Legacy snapshot binding and history/read contracts are unresolved: R2–R3. |
| SCN-3004 | PASS | Configured identity mismatch has a specific status, code, and no-write outcome. |
| SCN-3005 | PASS | Rejection without a reason has a specific validation and no-write outcome. |
| SCN-3006 | FAIL | Empty DocString does not exercise the stated whitespace-only boundary: R5. |
| SCN-3007 | PASS | Missing configured identity has a specific unavailable/no-write outcome. |
| SCN-3008 | FAIL | Missing rejection reason confounds the intended conflict outcome: R5. |
| SCN-3009 | FAIL | “Against baseline-b” has no defined request mechanism or complete freshness contract: R1. |
| SCN-3010 | PASS | Failed persistence has coherent publication and restart expectations; successful recovery remains uncovered. |
| SCN-3011 | PASS | A well-formed missing proposal ID has a specific not-found/no-write outcome. |

SCN-3001–SCN-3011 are unchanged from their committed draft, unique among the development feature tags, and within the allocated AS-06 range. Preserve those identities when revising examples.

## Freeze conditions

- Resolve blocking findings AS06-SPEC-R1 through AS06-SPEC-R9 in the canonical criteria and explicitly referenced contract notes.
- Add independently specified examples for duplicate/invalid capture, equal-hash revision changes, concurrent decisions, successful restart recovery, append-only preservation, write restrictions, and the retained UI scope.
- Align current status text with accepted ADR 0012 and record independent specification approval against the revised feature revision/hash before removing `@refinement-draft`. Implementation test results are not a prerequisite for this specification approval.