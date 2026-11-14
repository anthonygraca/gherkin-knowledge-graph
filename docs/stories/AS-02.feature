# Canonical acceptance specification for AS-02 (#3), M2.
# Source criteria: the GitHub story intake at
# https://github.com/anthonygraca/gherkin-knowledge-graph/issues/3 (verified 2026-11-13T13:05Z)
# and its task children #5/#6. Executed by the Cucumber suite (bdd/) from M2 onward.
@AS-02 @issue-3 @M2
Feature: AS-02: Potential stale-evidence findings after relevant changes
  A passing run whose relevant content changed afterwards requests reverification. It is never a
  verification failure: no recorded execution failed.

  @SCN-2021
  Scenario: Implementation changed since verification
    Given "SCN-001" verifies "REQ-001"
    And a test for "SCN-001" passed at baseline "baseline-a" with evidence "EV-001"
    And a relevant linked implementation changed at baseline "baseline-b"
    And no later matching verification evidence exists
    When assurance evaluates baseline "baseline-b"
    Then a "reverification_required" finding is produced for "REQ-001"
    And the finding identifies both baselines and the changed artifact "CODE-001"
    And "REQ-001" is not marked "verification_failed"

  @SCN-2022
  Scenario: Unchanged content needs no reverification
    Given a test for "SCN-001" passed at baseline "baseline-a" with evidence "EV-001"
    And no relevant artifact changed at baseline "baseline-a"
    When assurance evaluates baseline "baseline-a"
    Then no "reverification_required" finding names "REQ-001"

  @SCN-2023
  Scenario: A later run replaces the freshness decision, not the history
    Given "TEST-002" passed at "baseline-a" and failed at "baseline-b"
    When assurance evaluates baseline "baseline-b"
    Then the failing evidence "EV-003" produces a "verification_failed" finding
    And the earlier passing evidence "EV-002" is still recorded
