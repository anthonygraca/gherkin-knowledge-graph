## Verdict

**REVISE**

All three round-3 findings are repaired. One blocking contradiction remains between capture’s unconditional failure guarantee and the revised indeterminate journal outcome.

Read-only inspection only; no edits, tests, implementation, commits, or delegation. PASS below means specification readiness, not execution evidence.

## Round-3 dispositions

| Finding | Disposition | Exact revised location | Basis |
|---|---|---|---|
| AS06-SPEC2-R2 | repaired | `docs/stories/AS-06.md:137–140, 166–177`; `docs/stories/AS-06.feature:157–177` | Confirmed rollback guarantees nonpublication after restart, while an unconfirmed rollback explicitly permits an indeterminate outcome and recovery of one complete decision. |
| AS06-SPEC-R9 | repaired | `docs/stories/AS-06.feature:263–301`; `docs/stories/AS-06.md:216–220` | Browser acceptance, rejection with retained audit details, and a reachable refusal path now have observable outcomes. |
| AS06-SPEC3-R1 | repaired | `docs/stories/AS-06.feature:294–301` | The browser displays the pending acceptance control before the competing API acceptance, then submits without refreshing. |

## New findings

1. **AS06-SPEC4-R1 — blocking — Capture’s failure guarantee contradicts indeterminate journal recovery.**

   **Location:** [AS-06.md:102–113](/home/anthonygraca/CSU%20Fullerton%20Dropbox/Anthony%20Graca/cpsc-583-knowledge-representation/project/gherkin-knowledge-graph/docs/stories/AS-06.md:102), [AS-06.md:154–177](/home/anthonygraca/CSU%20Fullerton%20Dropbox/Anthony%20Graca/cpsc-583-knowledge-representation/project/gherkin-knowledge-graph/docs/stories/AS-06.md:154).

   Capture states, “No failure appends an event or publishes a proposal.” The journal includes `proposal_captured` events and now permits an indeterminate failure whose complete committed pair survives restart. For a capture whose complete pair is written, final fsync fails, and rollback cannot be confirmed, replaying that pair publishes a proposal despite the capture guarantee. Suppressing it conflicts with committed-pair replay. SCN-3010 and SCN-3028 specify decision failures only.

   **Smallest repair:** Limit capture’s no-event/no-publication guarantee to validation/conflict refusals and confirmed rollback; explicitly apply the indeterminate response and recovery rules to capture events. Add a capture failure example defining the response, live projection, and permitted restart outcomes.

## Scenario assessment

PASS assesses each stated example with its companion contract. The missing capture-storage-failure boundary is reported above; it does not make the existing successful-capture examples ambiguous.

| Scenario ID | Assessment | Basis |
|---|---|---|
| SCN-3001 | PASS | Successful capture defines identity, provenance, hashes, and nonmutation. |
| SCN-3002 | PASS | Legacy acceptance defines audit and workspace outcomes. |
| SCN-3003 | PASS | Rejection retains its reason and excludes the proposal appropriately. |
| SCN-3004 | PASS | Identity mismatch has a typed refusal without mutation. |
| SCN-3005 | PASS | Absent and null rejection reasons have explicit outcomes. |
| SCN-3006 | PASS | Empty and whitespace-only reasons are covered. |
| SCN-3007 | PASS | Missing operator configuration has a typed refusal. |
| SCN-3008 | PASS | A second terminal decision preserves the original decision. |
| SCN-3009 | PASS | Changed endpoint content produces stale-proposal refusal. |
| SCN-3010 | PASS | Confirmed rollback establishes restart nonpublication. |
| SCN-3011 | PASS | Missing proposal produces a typed not-found response. |
| SCN-3012 | PASS | Endpoint, direction, and both hash defects have explicit refusals. |
| SCN-3013 | PASS | Identical pending capture is idempotent. |
| SCN-3014 | PASS | Acceptance recovery preserves history, bytes, and unrelated pending work. |
| SCN-3015 | PASS | A later decision preserves earlier decision bytes and state. |
| SCN-3016 | PASS | Concurrent valid decisions have one successful terminal outcome. |
| SCN-3017 | PASS | Peer and browser-origin violations have typed refusals. |
| SCN-3018 | PASS | Equal endpoint hashes permit review across an evidence-only revision. |
| SCN-3019 | PASS | Acceptance projection requires compatible endpoint content. |
| SCN-3020 | PASS | Browser acceptance includes provenance, pending removal, and audit history. |
| SCN-3021 | PASS | Conflicting and terminal recaptures have distinct refusals. |
| SCN-3022 | PASS | Local requests without Origin are explicitly permitted. |
| SCN-3023 | PASS | A committed pending capture survives restart unchanged. |
| SCN-3024 | PASS | Rejection recovery preserves reason, operator, exclusion, and bytes. |
| SCN-3025 | PASS | Browser rejection displays retained audit details. |
| SCN-3026 | PASS | The stale browser control now reaches the required conflict outcome. |
| SCN-3027 | PASS | An uncommitted tail is excluded from replay and blocks further writes. |
| SCN-3028 | PASS | Indeterminate decision persistence has bounded restart outcomes and blocks further mutations. |

## Freeze conditions

- Resolve **AS06-SPEC4-R1** by aligning capture’s failure guarantee with indeterminate journal recovery and adding the capture failure boundary criterion.