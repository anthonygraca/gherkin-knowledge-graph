# Follow-up acceptance slice for SETUP-01 (#8): commit-reference enforcement.
# Verified by pytest selectors in SETUP-01.md and executed by the Cucumber suite (bdd/) from M2
# onward; the pytest checks remain independent regression evidence.
@SETUP-01 @issue-8 @M0
# Executable-status note: Commit-history lint behaviour is verified by the 28 mapped pytest checks in backend/tests/test_commitlint.py; Cucumber bindings are pending under GT-02.
Feature: SETUP-01: Enforce traceability for new commits
  As a contributor, I want every new commit to name a registered work item
  so reviewers can trace repository changes to their intended purpose.

  Rule: New commit subjects identify their primary story or task

    @SCN-301
    Scenario: A contributor uses the new subject format
      Given issue 8 is registered as a story in the issue map
      When a commit message is "ci(traceability): [issue #8] enforce commit references"
      Then commit lint succeeds
      And the same message without the optional scope also succeeds

    @SCN-302
    Scenario: A body-only reference cannot replace the subject reference
      Given a commit subject is "ci: enforce commit references"
      And its body contains "Refs #8"
      When commit lint checks the message
      Then it fails and describes the required subject format

    @SCN-303
    Scenario: A reference must identify a registered story or task
      Given issue 999 is absent from the story and task tables
      When issue 999 appears in the required subject reference or a body reference line
      Then commit lint fails
      And feature rows and duplicate numbers mentioned only in prose are not valid work items

  Rule: Adoption preserves historical commits and checks every new contribution

    @SCN-304
    Scenario: A correct final commit does not hide an earlier invalid commit
      Given a legacy commit without an issue reference is the fixed adoption baseline
      And an invalid new commit follows it
      And a valid new commit follows the invalid commit
      When commit lint checks the new history
      Then it reports the invalid new commit
      And it does not report the legacy commit

    @SCN-305
    Scenario: Pull request history is selected from the actual branch
      Given a topic branch and its target both contain the adoption baseline
      And both branches contain independent later commits
      When commit lint checks the topic head excluding the target history
      Then it checks every topic commit absent from the target
      And it excludes commits already reachable from the target

    @SCN-306
    Scenario: Real merge commits and their side branches retain traceability
      Given a new merge commit integrates a topic branch
      When either the merge message or a topic commit lacks the required issue reference
      Then commit lint fails
      And a conforming merge with conforming topic commits succeeds

  Rule: Validation uses attributable local inputs and fails on missing history

    @SCN-307
    Scenario: A later map edit cannot repair an invalid historical reference
      Given a new commit references an issue absent from its own issue map
      And the working tree later adds that issue
      When commit lint checks the commit
      Then it fails using the map at that commit

    @SCN-308
    Scenario: Missing Git history is not a passing check
      Given a selected revision is unavailable or the repository is shallow
      When commit lint checks the history
      Then it fails with an operational error
      And it does not claim the selected commits passed
