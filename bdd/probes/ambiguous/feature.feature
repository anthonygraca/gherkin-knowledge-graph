Feature: Harness probe
  Scenario: An ambiguous step is detected
    Given a step that matches twice
    Then the probe assertion passes
