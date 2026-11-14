# Canonical acceptance specification for AS-05 (#27), M2.
# Source criteria: the GitHub story intake at
# https://github.com/anthonygraca/gherkin-knowledge-graph/issues/27 (verified 2026-11-13T13:05Z)
# and roadmap §7 (M2). Dashboard behaviour is verified by Vitest component tests and executed
# through the Cucumber browser suite under bdd/ from M2 onward.
@AS-05 @browser @issue-27 @M2
# Executable-status note: Findings drill-down rendering is verified by Vitest component tests and a recorded browser demonstration; browser-level Cucumber bindings are pending under GT-02.
Feature: AS-05: Drill-down into findings and their evidence
  The dashboard must let a reviewer judge whether a finding is justified: which rule fired, at which
  baseline, on which artifacts, with which evidence and tested commit. Reverification and confirmed
  failure must remain differentiable by wording, not only by colour.

  @SCN-2041
  Scenario: Drill into a reverification finding
    Given the "reverification_required" finding for "REQ-001" at "baseline-b"
    When the finding is opened in the dashboard
    Then it names the rule, the evaluated baseline, and the changed artifact
    And it shows the evidence "EV-001" with the revision it was executed at
    And it does not present the requirement as failed

  @SCN-2042
  Scenario: A confirmed failure is presented differently
    Given the "verification_failed" finding for "REQ-003" at "baseline-b"
    When the finding is opened
    Then the failing evidence "EV-003" and its revision are shown
    And the wording states a failed verification, not a reverification request
