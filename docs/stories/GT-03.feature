# Canonical acceptance specification for GT-03 (#62), M2.
# Source criteria: the expanded-M2 intake recorded in issue #62 and session prompt §12–§14.
@GT-03 @issue-62 @M2
Feature: GT-03: Ingest step definitions, matches, and executions into the graph
  Executable relationships are ingested additively. A registered or matched definition is not an
  execution, and neither is evidence that production code ran.

  @SCN-2121
  Scenario: Matched and observed relationships stay distinct
    Given an external repository indexed at a pinned commit with an imported report
    When the executable relations are queried
    Then matched relationships name definitions with source locators
    And observed relationships name an execution key
    And no relation claims production-code execution

  @SCN-2122
  Scenario: Unobserved scenarios do not claim execution
    Given an indexed repository without an imported report
    When executions are queried
    Then coverage reports every scenario as unexecuted
    And no execution evidence is fabricated
