# Canonical acceptance specification for AS-03 (#4), M2.
# Source criteria: the GitHub story intake at
# https://github.com/anthonygraca/gherkin-knowledge-graph/issues/4 (verified 2026-11-13T13:05Z)
# and roadmap §4/§7. Executed by the Cucumber suite (bdd/) from M2 onward.
@AS-03 @issue-4 @M2
Feature: AS-03: Keep failed, missing, and potentially stale evidence distinct
  One evaluation can contain all three situations. Their meanings are different and their
  precedence is declared: a confirmed failure at the evaluated baseline wins for its scenario;
  a stale pass is a request for reverification; a missing accepted link is a coverage gap.

  Rule: The distinctions are visible in one evaluation

    @SCN-2031
    Scenario: Distinguish missing, failed, and stale evidence in one evaluation
      Given "REQ-001" has passing verification evidence at baseline "baseline-a"
      And "REQ-002" has no accepted verification scenario
      And "REQ-003" has a failing test at baseline "baseline-b"
      And a relevant linked implementation of "REQ-001" changed at baseline "baseline-b"
      When assurance evaluates baseline "baseline-b"
      Then "REQ-002" yields a "missing_verification_link" finding
      And "REQ-003" yields a "verification_failed" finding
      And "REQ-001" yields a "reverification_required" finding
      And no finding downgrades "reverification_required" to "verification_failed"

  Rule: Applicability is decided by content, not commit identity

    @SCN-2032
    Scenario: Evidence recorded at a source commit applies to its evidence commit
      Given evidence "EV-001" was recorded at the source commit of "baseline-a"
      And the evidence commit stores the report without changing artifact content
      When assurance evaluates baseline "baseline-a"
      Then the evidence is treated as applicable
      And "REQ-001" has no "verification_failed" finding
