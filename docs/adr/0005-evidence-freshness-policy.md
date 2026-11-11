# ADR 0005 — Initial evidence-freshness policy

**Status:** Accepted (rule implemented in M2) · 2026-11-10

## Context

Roadmap §4 states the semantics that matter most for credibility: an implementation change after
recorded verification is a reason for impact assessment or reverification, **not** proof of failure;
and an unchanged code file does not itself prove verification is current if dependencies or
environments changed. Roadmap §11 asks for an evidence-freshness policy, and roadmap §9 requires
rules to declare and test their simplifying assumptions.

## Decision

Findings distinguish three situations, with no overlap:

| Situation | Finding | Precondition |
| --- | --- | --- |
| A run failed at the evaluated baseline | `verification_failed` | evidence with `result=failed` whose `tested_commit` content matches the evaluated baseline |
| Content changed since the last pass, nothing has re-run | `reverification_required` | passing evidence exists; some artifact in the scenario's accepted chain has a different `content_hash` at the evaluated baseline than at the evidence's `tested_commit`; no later run exists |
| No scenario is accepted for a requirement | `missing_verification_link` | no accepted `verified_by` link |

Algorithm (M2 target), stated in `docs/domain-contracts.md` in full: for each scenario with an
accepted chain, take the most recent evidence by `executed_at`, then compare content hashes of the
scenario's file, its implementation files, and its test files between the evaluated baseline and the
evidence's `tested_commit`.

**Declared assumptions (all falsifiable, all to be stated in any UI that shows the finding):**

1. File-level granularity; sub-file changes are detected as whole-file changes.
2. Path-stable identity: a rename is a new artifact and therefore a change.
3. Dependencies are exactly the accepted links; there is no call graph, no requirements-to-requirements
   graph, no transitive dependency analysis.
4. Environment, toolchain, and dependency-version changes are **not** modelled.
5. Only the most recent run per scenario is considered.
6. A run's outcome applies to the content hashes present at its `tested_commit`.

Assumption 4 is the reason a reverification finding says "reverify", never "verified": absence of a
detected change is not positive evidence of correctness, and the UI must not present it as one.

## Consequences

* `verification_failed` can only be produced by a recorded failure, so a stale-evidence situation can
  never be reported as a regression.
* The fixture proves the distinction with real, reproducible runs: `TEST-001` is unchanged while
  `CODE-001` changed, producing reverification for `REQ-001`; `TEST-002` failed at the evaluated
  baseline, producing failure for `REQ-003`. A test also shows that re-running `TEST-001` at
  `baseline-b` would fail — reverification is the correct, useful signal.
* Over-reporting change is accepted as the safe direction at this granularity.

## Alternatives considered

* Treat any change in the repository since evidence as staleness. Rejected: it floods the report and
  destroys the signal the demo depends on.
* Treat an unchanged file as "verified current". Rejected: it would claim something the system cannot
  know; see assumption 4.
* Compare commit SHAs instead of content hashes. Rejected in ADR-0003.
* Model environments now. Rejected for M2: it needs a fingerprint the fixture does not yet record;
  recorded as assumption 4 with a revisit trigger.

## Revisit when

Environment or dependency changes must be attributed (add an environment fingerprint to
`VerificationEvidence` and compare it), or when sub-file granularity becomes necessary.
