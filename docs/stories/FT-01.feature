# Canonical M0 acceptance specification; migrated from M0-foundation.md.
# Verification uses the existing pytest checks mapped in that document.
# These scenarios are not currently bound to or executed by a Gherkin runner.
@FT-01 @issue-18 @M0
Feature: FT-01: Labeled fixture repository and baseline oracle
  As a developer, I want labeled fixture repos and baseline oracles so I can test without external systems.

  @SCN-101 @AC-1.1
  Scenario: Fixture history is reproducible
    Given the fixture generator builds "banking-demo" twice in different directories
    When each generated repository is asked for the tags "baseline-a" and "baseline-b"
    Then both repositories report the same commit SHA for each tag
    And those SHAs match the committed manifest "fixtures/banking-demo/expected/baselines.json"

  @SCN-102 @AC-1.2
  Scenario: Requirement with a complete accepted chain
    Given "REQ-001" has accepted links to "SCN-001", "CODE-001", and "TEST-001"
    And evidence "EV-001" recorded a passing run for "TEST-001" at baseline "baseline-a"
    When findings for baseline "baseline-a" are inspected
    Then no finding references "REQ-001"

  @SCN-103 @AC-1.3
  Scenario: Coverage gaps at baseline "baseline-a"
    Given "REQ-002" has no accepted verification scenario
    And "SCN-002" has no accepted implementation
    When findings for baseline "baseline-a" are inspected
    Then a "missing_verification_link" finding references "REQ-002"
    And a "missing_implementation_link" finding references "SCN-002"

  @SCN-104 @AC-1.4
  Scenario: Implementation changed since verification
    Given "SCN-001" verification passed at baseline "baseline-a" (evidence "EV-001")
    And the file backing "CODE-001" changed between baseline "baseline-a" and "baseline-b"
    And no later evidence exists for "SCN-001"
    When findings for baseline "baseline-b" are inspected
    Then a "reverification_required" finding references "REQ-001", "SCN-001", and "CODE-001"
    And that finding references evidence "EV-001"
    And no "verification_failed" finding references "REQ-001"

  @SCN-105 @AC-1.5
  Scenario: Failing test at the evaluated baseline
    Given evidence "EV-003" recorded a failing run for "TEST-002" at baseline "baseline-b"
    When findings for baseline "baseline-b" are inspected
    Then a "verification_failed" finding references "REQ-003", "SCN-003", and "TEST-002"
    And that finding references evidence "EV-003"
    And no "reverification_required" finding references "SCN-003"

  @SCN-106 @AC-1.6
  Scenario: Superseded requirement with live relationships
    Given "REQ-003" is marked "superseded" in its requirement front matter
    And "REQ-003" still has accepted links
    When findings for baseline "baseline-a" or "baseline-b" are inspected
    Then a "lifecycle_review_required" finding references "REQ-003"

  @SCN-107 @AC-1.7
  Scenario: Semantically plausible proposal stays pending
    Given the fixture records "LNK-007" as a proposed link from "REQ-002" to "SCN-002"
    When findings for baseline "baseline-a" are inspected
    Then a "candidate_pending_review" finding references "REQ-002" and "SCN-002"
    And "LNK-007" has review state "proposed"
    And no accepted link exists between "REQ-002" and "SCN-002"

  @SCN-108 @AC-1.8
  Scenario: The fixture test suite reproduces the labeled evidence
    Given a checkout of tag "baseline-a"
    When the fixture test suite runs
    Then it passes
    Given a checkout of tag "baseline-b"
    When the fixture test suite runs
    Then it fails exactly in "tests/test_accounts.py::test_withdraw_allows_fractional_amounts"
    And it fails exactly in "tests/test_transfers.py::test_transfer_exactly_at_limit_is_permitted"
