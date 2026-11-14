# Canonical acceptance specification for GT-02 (#61), M2.
# Source criteria: the expanded-M2 intake recorded in issue #61 and session prompt §10/§16.
@GT-02 @issue-61 @M2
Feature: GT-02: Migrate historical CTA acceptance specifications to executable Cucumber
  Every tracked feature file is classified. Migration is recorded from an actual Cucumber report;
  a pytest mapping or a parse is never described as executed Gherkin.

  Rule: Every tracked feature file is accounted for

    @SCN-2111
    Scenario: Every tracked feature is classified
      Given the repository feature inventory artifact
      Then every tracked feature file appears exactly once
      And every non-executed feature carries an explicit reason

    @SCN-2112
    Scenario: Scenario identifiers stay unique
      Given the canonical acceptance feature files
      When their scenario identifiers are collected
      Then every identifier appears exactly once

    @SCN-2113
    Scenario: Executed status comes from a Cucumber report
      Given the latest Cucumber acceptance report
      When the inventory's executed entries are compared with the report
      Then every executed entry names a scenario present in that report
      And a pytest mapping is not counted as execution
