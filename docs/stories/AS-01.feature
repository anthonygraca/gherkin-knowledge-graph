# Canonical acceptance specification for AS-01 (#2), M1.
# Source criteria: the GitHub story intake at
# https://github.com/anthonygraca/gherkin-knowledge-graph/issues/2 (verified 2026-11-13T03:56:41Z)
# and roadmap §6 F-05. Boundary and failure scenarios were added during refinement; the intake
# scenario keeps its wording.
# Verified by the pytest selectors mapped in AS-01.md. These scenarios are not currently bound
# to or executed by a Gherkin runner.
@AS-01 @issue-2 @M1
Feature: AS-01: Missing coverage/link findings
  A requirement is missing verification when it has no accepted `verified_by` link to an existing
  scenario at the evaluated baseline. A proposal is not acceptance. The rule is deterministic,
  offline, and explains its inputs and simplifying assumptions.

  @SCN-701
  Scenario: Requirement has no accepted verification scenario
    Given requirement "REQ-002" exists
    And no accepted verification scenario is linked to "REQ-002"
    When assurance evaluates baseline "baseline-a"
    Then a "missing_verification_link" finding is produced for "REQ-002"

  @SCN-702
  Scenario: A pending proposal does not satisfy the rule
    Given "LNK-007" proposes "REQ-002" verified_by "SCN-002" and is not accepted
    When assurance evaluates baseline "baseline-a"
    Then "REQ-002" still produces a "missing_verification_link" finding
    And the proposal is not counted as an accepted link

  @SCN-703
  Scenario: A requirement with accepted verification has no such finding
    Given "REQ-001" has accepted link "LNK-001" verified_by "SCN-001"
    When assurance evaluates baseline "baseline-a"
    Then no "missing_verification_link" finding names "REQ-001"

  @SCN-704
  Scenario: Findings identify their rule, inputs, and evaluated baseline
    Given assurance evaluated baseline "baseline-b"
    Then each finding names the rule id, severity, artifact revisions, and resolved commit
    And the finding fingerprint follows the canonical rule-and-artifact inputs

  @SCN-705
  Scenario: Unusable evaluation requests are rejected honestly
    When assurance is asked for baseline "baseline-z"
    Then the response is 404 "baseline-not-found"
    When assurance is asked for an unknown policy
    Then the response is 400 "invalid-request"
