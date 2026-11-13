# Canonical acceptance specification for AS-04 (#26), M1.
# Source criteria: the GitHub story intake at
# https://github.com/anthonygraca/gherkin-knowledge-graph/issues/26 (verified 2026-11-13T04:13:19Z)
# and roadmap §6 F-06. Boundary scenarios were added during refinement; the two intake scenarios
# keep their wording. Verified by frontend component tests plus a recorded browser demonstration;
# the scenarios are not executed by a Gherkin runner.
@AS-04 @issue-26 @M1
Feature: AS-04: Summary of findings and coverage counts
  The dashboard shows, for the selected baseline, how many findings of each type exist and which
  requirements are covered. Counts come from the findings response. Proposals are displayed as
  proposals and never counted as coverage.

  @SCN-801
  Scenario: Coverage summary for a baseline
    Given the fixture data at "baseline-a"
    When the dashboard loads the summary
    Then it shows the finding counts by type for that baseline
    And it shows "REQ-001" as fully covered
    And it shows "REQ-002" as missing a verification scenario

  @SCN-802
  Scenario: The baseline is always visible
    Given findings for "baseline-a" and "baseline-b" differ
    When the baseline selector changes
    Then the summary reloads for the selected baseline
    And the selected baseline is displayed with the numbers

  @SCN-803
  Scenario: Counts are derived from the response, not hard-coded
    Given a findings response containing a different set of findings
    When the dashboard renders it
    Then the displayed counts change accordingly

  @SCN-804
  Scenario: Proposals are labelled and excluded from coverage
    Given "REQ-002" has proposed link "LNK-007" and no accepted verification link
    When its thread is displayed
    Then "LNK-007" is labelled as a proposal
    And "REQ-002" is not shown as covered

  @SCN-805
  Scenario: The thread view shows the accepted chain and its evidence
    Given the fixture data at "baseline-b"
    When the thread for "REQ-001" is displayed
    Then the accepted links and their relation types are shown
    And the evidence for "SCN-001" is shown
    And the baseline is shown with the thread
