## Verdict

**REVISE**

AS06-SPEC-R3, R7, and R9 remain open. Three additional specification inconsistencies block freeze.

This was read-only specification inspection. No files were changed, tests run, implementation performed, commits created, or work delegated. PASS below means specification readiness, not execution evidence.

Locations refer to `docs/stories/AS-06.feature` and `docs/stories/AS-06.md` unless stated otherwise.

## Round-1 dispositions

| Finding | Disposition | Revised location | Justification |
| --- | --- | --- | --- |
| AS06-SPEC-R1 | repaired | `AS-06.md:27–40`; SCN-3018, SCN-3019 | Explicit mutation baselines, omission errors, retained resolved commits, hash-based applicability, and evidence-only revision coverage resolve the original baseline-binding gap. |
| AS06-SPEC-R2 | repaired | `AS-06.md:55–59`; SCN-3002, SCN-3003 | LNK-007 receives a durable snapshot with its first decision using stored provenance and authoritative endpoint hashes, without separate capture or fixture changes. |
| AS06-SPEC-R3 | open | `AS-06.md:44–59, 127–134` | Surfaces, audit fields, and digest inputs are defined, but the pending-queue response requires `{link, snapshot}` without defining the representation of legacy LNK-007 before its first-decision snapshot exists. |
| AS06-SPEC-R4 | repaired | `AS-06.md:61–86`; SCN-3012, SCN-3013, SCN-3021 | Endpoint, direction, and hash validation now have typed failures, while identical, conflicting, and terminal recaptures have explicit outcomes. |
| AS06-SPEC-R5 | repaired | `AS-06.md:97–107`; SCN-3005, SCN-3006, SCN-3008 | Absent, null, empty, and whitespace-only rejection reasons are distinguished, and SCN-3008 now supplies a valid reason. |
| AS06-SPEC-R6 | repaired | `AS-06.md:109–112`; SCN-3016 | Concurrent terminal decisions now require exactly one success, one conflict, and one durable terminal event with matching workspace state. |
| AS06-SPEC-R7 | open | `AS-06.md:114–125`; SCN-3014, SCN-3015 | Successful acceptance recovery and preservation during another successful decision are covered, but restart examples for an undecided captured proposal and a rejection remain absent. |
| AS06-SPEC-R8 | repaired | `AS-06.md:63, 90, 139–146`; SCN-3017, SCN-3022 | Both mutation surfaces have explicit loopback and browser-origin restrictions, including absent-Origin allowance and typed refusal outcomes. |
| AS06-SPEC-R9 | open | `AS-06.md:148–161`; SCN-3020 | The browser example covers acceptance and requiring a rejection reason, but does not exercise successful rejection with retained details or a refused write visibly reported without success. |

## New findings

1. **AS06-SPEC2-R1 — blocking — Pending-proposal applicability makes decision error precedence ambiguous.**

   **Location:** `AS-06.md:37–40, 97–107`; SCN-3009 and SCN-3018.

   Decision step 4 returns `404 proposal-not-found` when a proposal is not “applicable at the selected baseline,” but applicability for pending proposals is undefined. Using the documented hash-based applicability rule rejects changed content at step 4, before step 7 can produce SCN-3009’s required `409 proposal-stale`. Restricting applicability to the capture baseline instead prevents SCN-3018’s evidence-only revision acceptance.

   **Smallest repair:** Define proposal lookup separately from freshness: an existing captured proposal remains addressable at another resolved baseline, with endpoint-hash mismatch handled by step 7. Specify pending-queue visibility separately from whether a review request can address that proposal.

2. **AS06-SPEC2-R2 — blocking — Failed-write recovery rules do not support the promised restart outcome.**

   **Location:** `AS-06.md:107, 114–125`; SCN-3010.

   A complete decision line can be appended before fsync fails. The decision then returns `503`, but replay’s rule to validate complete lines would expose that decision after restart, contradicting SCN-3010. Separately, ignoring a trailing partial line while preserving all bytes leaves subsequent appends unspecified: appending another JSON object can turn the ignored tail into a malformed interior record.

   **Smallest repair:** Define which records replay treats as committed after an unsuccessful write, consistent with SCN-3010’s refusal guarantee. Define subsequent mutation behavior after a partial tail; explicitly refusing further writes with `503 review-storage-unavailable` is one bounded option. Add examples for complete-write/fsync failure and partial-tail restart followed by another mutation.

3. **AS06-SPEC2-R3 — blocking — Restart scenario incorrectly requires an empty global pending queue.**

   **Location:** `AS-06.feature:15–18, 172–181`; `AS-06.md:132`; `fixtures/banking-demo/tree/evidence/proposed-links.json:7–11`.

   SCN-3014 accepts a newly captured SCN-002 → CODE-001 proposal, then requires the workspace pending queue to be empty. Baseline-a also contains pending LNK-007, which this scenario never decides. The documented queue is baseline-wide, so LNK-007 must remain pending.

   **Smallest repair:** Replace the empty-queue assertion with exclusion of the accepted proposal and preservation of unrelated pending LNK-007.

## Scenario assessment

Each assessment concerns the individual example together with its referenced normative contract. Missing alternative examples are recorded separately above.

| Scenario ID | Assessment | Basis |
| --- | --- | --- |
| SCN-3001 | PASS | Capture, snapshot identity, provenance, and nonmutation outcomes are defined. |
| SCN-3002 | PASS | Legacy binding and acceptance audit/projection outcomes are specified. |
| SCN-3003 | PASS | Rejection reason, retained history, and projection outcomes are specified. |
| SCN-3004 | PASS | Identity mismatch has a typed refusal and no-decision outcome. |
| SCN-3005 | PASS | Absent and null rejection reasons have explicit outcomes. |
| SCN-3006 | PASS | Empty and nonempty whitespace-only reasons are distinguished. |
| SCN-3007 | PASS | Unconfigured identity has a typed unavailable outcome. |
| SCN-3008 | PASS | Valid rejection input isolates the terminal-decision conflict. |
| SCN-3009 | FAIL | Applicability checking can preempt the required stale response: SPEC2-R1. |
| SCN-3010 | FAIL | Complete-write/fsync failure can replay a refused acceptance: SPEC2-R2. |
| SCN-3011 | PASS | Missing proposal has a typed not-found and no-write outcome. |
| SCN-3012 | PASS | Invalid endpoints, direction, and both hash mismatches are covered. |
| SCN-3013 | PASS | Identical pending capture is explicitly idempotent. |
| SCN-3014 | FAIL | Empty queue contradicts retained LNK-007; recovery also depends on SPEC2-R2. |
| SCN-3015 | PASS | Another successful decision must preserve prior decision bytes and state. |
| SCN-3016 | PASS | Concurrent decisions have a deterministic single-winner invariant. |
| SCN-3017 | PASS | Non-loopback and forbidden-Origin writes have typed refusals. |
| SCN-3018 | FAIL | Cross-revision pending-proposal applicability remains undefined: SPEC2-R1. |
| SCN-3019 | PASS | Accepted-decision projection depends on compatible endpoint content. |
| SCN-3020 | PASS | The acceptance browser path is specified; rejection and refusal coverage remain missing under R9. |
| SCN-3021 | PASS | Provenance conflicts and terminal recapture have typed outcomes. |
| SCN-3022 | PASS | A local request without Origin is explicitly allowed. |

## Freeze conditions

- Define the pending-read representation of legacy proposals without snapshots.
- Add restart examples for a captured proposal still pending and for a successful rejection, preserving their audit details and projected state.
- Add browser examples for successful rejection with retained reason/history and a refused write visibly reported without success.
- Separate pending-proposal lookup from freshness and workspace visibility.
- Resolve failed-write replay and partial-tail subsequent-write behavior.
- Correct SCN-3014’s pending-queue assertion.

These repairs require specification changes and re-review; implementation or test execution is not required for this freeze decision.