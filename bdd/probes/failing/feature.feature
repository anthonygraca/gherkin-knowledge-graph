Feature: Harness probe
  Scenario: A failing assertion fails the scenario
    Given the probe receives the value 6
    Then the probe assertion is deliberately wrong
