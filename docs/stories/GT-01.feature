# Canonical acceptance specification for GT-01 (#60), M2.
# Source criteria: the expanded-M2 intake recorded in issue #60 and session prompt §9/§16.
# The probe suites under bdd/probes/ are deliberately separate from this suite so harness
# behaviour is exercised without recursion.
@GT-01 @issue-60 @M2
Feature: GT-01: Cucumber runtime integration and executable acceptance harness
  CTA's own acceptance specifications run through a real Cucumber runtime. The harness must make
  failure visible: undefined and ambiguous steps fail a strict validation gate, and a failing
  assertion fails the scenario.

  Rule: The harness executes real assertions

    @SCN-2101
    Scenario: A CTA acceptance scenario executes against the application
      Given a probe acceptance suite whose step performs a real assertion
      When the probe suite runs through the selected Cucumber runtime
      Then the scenario executes and passes
      And the structured report records the scenario and each step outcome

  Rule: Unresolved steps are not silent

    @SCN-2102
    Scenario: Undefined steps fail strict validation
      Given a probe acceptance suite with an undefined step
      When strict step-resolution validation runs
      Then validation fails
      And the unresolved step and its source location are reported

    @SCN-2103
    Scenario: Ambiguous steps fail strict validation
      Given a probe acceptance suite with an ambiguous step
      When strict step-resolution validation runs
      Then validation fails
      And the ambiguity names the competing definitions

    @SCN-2105
    Scenario: A dry run does not satisfy strict validation
      Given a probe acceptance suite run without executing steps
      When strict step-resolution validation runs
      Then validation fails
      And the report shows steps that were not executed

    @SCN-2104
    Scenario: A failing assertion fails the scenario
      Given a probe acceptance suite with a deliberately failing assertion
      When the probe suite runs through the selected Cucumber runtime
      Then the scenario is reported failed
      And the report preserves the failing step
