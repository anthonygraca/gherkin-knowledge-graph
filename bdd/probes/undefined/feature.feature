Feature: Harness probe
  Scenario: An undefined step is detected
    Given the probe receives the value 6
    Then no definition exists for this probe step
