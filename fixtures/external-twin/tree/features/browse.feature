Feature: Twin repository browsing

  @SCN-001
  Scenario: A twin scenario that reuses an identifier
    Given the twin catalog has an entry
    Then the twin query sees only this repository
