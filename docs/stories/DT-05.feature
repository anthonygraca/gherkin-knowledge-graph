# Canonical acceptance specification for DT-05 (#24), M2.
# Source criteria: the GitHub story intake at
# https://github.com/anthonygraca/gherkin-knowledge-graph/issues/24 (verified 2026-11-13T13:05Z)
# and roadmap §7 (M2). Failure and boundary scenarios were added during refinement; the two intake
# scenarios keep their intent. Executed by the Cucumber suite (bdd/) from M2 onward.
@DT-05 @issue-24 @M2
Feature: DT-05: Test outcomes associated with exact tested commits
  Verification evidence is append-only. Each run names the commit that was executed; the commit that
  merely stores the report is never substituted for it. Freshness decisions compare content hashes,
  so an evidence-only commit cannot look like a source change.

  @SCN-2001
  Scenario: Evidence records the revision that was executed
    Given a test run for "TEST-002" executed at the "baseline-b-change" revision
    When the evidence is read
    Then it carries the commit SHA that was executed, not the commit that stored the record
    And it records the result, the execution time, and the run URI

  @SCN-2002
  Scenario: Several runs of one test are kept
    Given "TEST-002" passed at "baseline-a" and failed at "baseline-b"
    Then both records exist with distinct evidence ids
    And the later run does not overwrite the earlier one

  @SCN-2003
  Scenario: An evidence-only commit changes no artifact content hash
    Given the fixture baselines "baseline-a" and "baseline-b"
    When the artifact content hashes are compared across the evidence-only commit
    Then no artifact is reported as changed
    And the evidence still identifies the source commit it tested

  @SCN-2004
  Scenario: Evidence naming an unknown test is rejected
    Given a repository revision whose evidence references unknown test artifact "TEST-999"
    When the revision is ingested
    Then ingestion fails with an error naming "TEST-999"
