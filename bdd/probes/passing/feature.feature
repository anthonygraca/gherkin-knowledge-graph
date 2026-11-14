Feature: Harness probe
  Scenario: A real assertion runs
    Given the probe receives the value 6
    Then the probe assertion passes
