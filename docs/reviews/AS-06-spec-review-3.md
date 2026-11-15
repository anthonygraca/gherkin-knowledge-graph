## Verdict

**REVISE**

AS06-SPEC2-R2 remains open: failure during commit-marker fsync can still expose a refused decision after restart. AS06-SPEC-R9 is partially repaired, but the new browser refusal scenario does not establish a usable pending control before the competing decision.

Read-only specification inspection only; no edits, tests, implementation, commits, or delegation. PASS below means specification readiness, not execution evidence.

Locations refer to `docs/stories/AS-06.feature` and `docs/stories/AS-06.md`.

## Round-2 dispositions

| Finding | Disposition | Exact revised location | Basis |
| --- | --- | --- | --- |
| AS06-SPEC-R3 | repaired | `AS-06.md:63–86, 178–183` | Pending legacy proposals now have an explicit nullable snapshot, binding discriminator, stored provenance, and defined workspace response shape. |
| AS06-SPEC-R7 | repaired | `AS-06.feature:172–210` — SCN-3014, SCN-3023, SCN-3024, SCN-3015 | Acceptance, undecided capture, and rejection recovery now preserve observable state and journal bytes, while another successful decision preserves earlier records. |
| AS06-SPEC-R9 | open | `AS-06.feature:250–287`; `AS-06.md:199–211` | Successful rejection and retained history are covered, but SCN-3026 opens the workspace after the proposal has already been accepted, leaving its refusal path unestablished (AS06-SPEC3-R1). |
| AS06-SPEC2-R1 | repaired | `AS-06.md:45–59, 129–136`; SCN-3009 and SCN-3018 | Addressability, freshness, and pending visibility are separate, allowing stale proposals to produce `409` and equal-content revisions to remain reviewable. |
| AS06-SPEC2-R2 | open | `AS-06.md:151–170`; `AS-06.feature:157–164, 289–296` | Tail refusal is specified, but a complete commit marker followed by a failing fsync satisfies replay’s committed-pair rule despite the required `503` and no-acceptance restart guarantee. |
| AS06-SPEC2-R3 | repaired | `AS-06.feature:177–180` — SCN-3014 | Restart excludes the accepted proposal from pending while explicitly retaining unrelated LNK-007. |

For **AS06-SPEC2-R2**, the remaining counterexample is precise: payload fsync succeeds, the complete matching commit line is written, and commit-line fsync fails. Lines 163–164 require refusal without publication, while lines 153–155 classify the surviving pair as committed and replay it. SCN-3010 forbids that acceptance after restart. Adding a commit marker moves the uncertainty to the marker’s final write/fsync; it does not resolve it.

## New findings

1. **AS06-SPEC3-R1 — blocking — SCN-3026 does not establish the browser state needed to submit the conflicting decision.**

   **Location:** `AS-06.feature:281–286`; `AS-06.md:55–59, 199–208`.

   The API acceptance occurs before the reviewer opens the workspace. At that point, the proposal is already accepted and excluded from pending. A conforming UI therefore need not offer an acceptance control, so the scenario cannot reliably reach its required conflict display.

   **Smallest repair:** Open the workspace and display the pending proposal first; then accept through the API; then submit through the already displayed browser control without an intervening refresh. Retain the conflict, no-new-success, refresh, and single-terminal-decision assertions. This also completes the remaining AS06-SPEC-R9 coverage.

## Scenario assessment

Assessments concern each example together with its normative companion contract.

| Scenario ID | Assessment | Basis |
| --- | --- | --- |
| SCN-3001 | PASS | Capture identity, provenance, hashes, and nonmutation outcomes are defined. |
| SCN-3002 | PASS | Legacy binding, acceptance audit, and workspace projection are defined. |
| SCN-3003 | PASS | Rejection retains its reason and has explicit projection outcomes. |
| SCN-3004 | PASS | Identity mismatch has a typed refusal and no-decision outcome. |
| SCN-3005 | PASS | Absent and null rejection reasons have explicit outcomes. |
| SCN-3006 | PASS | Empty and nonempty whitespace-only reasons are covered. |
| SCN-3007 | PASS | Unconfigured identity has a typed unavailable outcome. |
| SCN-3008 | PASS | Valid rejection input isolates terminal-decision conflict. |
| SCN-3009 | PASS | Cross-baseline lookup reaches the defined stale-hash refusal. |
| SCN-3010 | FAIL | Final commit-marker fsync failure contradicts restart nonpublication: SPEC2-R2. |
| SCN-3011 | PASS | Missing proposal has a typed not-found and no-write outcome. |
| SCN-3012 | PASS | Endpoint, direction, and both hash-validation failures are covered. |
| SCN-3013 | PASS | Identical pending capture is explicitly idempotent. |
| SCN-3014 | PASS | Successful recovery preserves acceptance and unrelated pending LNK-007. |
| SCN-3015 | PASS | A later successful decision preserves earlier decision bytes and state. |
| SCN-3016 | PASS | Concurrent decisions have a single-winner durability invariant. |
| SCN-3017 | PASS | Peer and browser-origin violations have typed refusals. |
| SCN-3018 | PASS | Equal endpoint hashes permit acceptance across an evidence-only revision. |
| SCN-3019 | PASS | Decision projection requires compatible endpoint content. |
| SCN-3020 | PASS | Browser acceptance, provenance, pending removal, and history are specified. |
| SCN-3021 | PASS | Conflicting and terminal recaptures have explicit outcomes. |
| SCN-3022 | PASS | Loopback requests without Origin are explicitly permitted. |
| SCN-3023 | PASS | Pending capture recovery preserves snapshot, provenance, history, and bytes. |
| SCN-3024 | PASS | Rejection recovery preserves reason, operator, exclusion, and bytes. |
| SCN-3025 | PASS | Browser rejection retains visible reason, operator, and timestamp. |
| SCN-3026 | FAIL | Opening after API acceptance does not establish a pending submission control: SPEC3-R1. |
| SCN-3027 | PASS | A complete payload without its marker is excluded from replay and blocks subsequent writes. |

## Freeze conditions

- Resolve **AS06-SPEC2-R2** by defining a consistent observable outcome for final commit-marker write/fsync failure, including restart behavior; distinguish an indeterminate commit outcome if needed, and align SCN-3010 with an explicit example of that boundary.
- Repair SCN-3026’s browser ordering as described in **AS06-SPEC3-R1**, completing **AS06-SPEC-R9**.
- Re-review the revised specification; implementation and test execution are not prerequisites for this freeze decision.