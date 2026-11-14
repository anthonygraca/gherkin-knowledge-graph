# Canonical acceptance specification for DT-06 (#25), M2.
# Source criteria: the GitHub story intake at
# https://github.com/anthonygraca/gherkin-knowledge-graph/issues/25 (verified 2026-11-13T13:05Z)
# and roadmap §7 (M2). Executed by the Cucumber suite (bdd/) from M2 onward.
@DT-06 @issue-25 @M2
Feature: DT-06: Changed artifacts and impacted accepted links between baselines
  Change detection is content-hash based, not commit-SHA based, and belongs to the repository port.
  The assurance rules consume the change set; they do not re-implement the diff.

  @SCN-2011
  Scenario: Change set between baseline-a and baseline-b
    Given the fixture repository with both baselines ingested
    When the change set between them is requested
    Then the changed artifacts are exactly "CODE-001" and "TEST-002"
    And "TEST-001" is reported unchanged
    And an evidence-only commit does not mark artifacts as changed

  @SCN-2012
  Scenario: Impacted accepted links
    Given "CODE-001" changed between the two baselines
    When impacted links are requested
    Then the accepted links reaching "CODE-001" are reported
    And links to unchanged artifacts are not

  @SCN-2013
  Scenario: The change set identifies artifacts added at the later baseline
    Given an artifact exists at "baseline-b" but not at "baseline-a"
    When the change set between them is requested
    Then the added artifact is reported as changed
