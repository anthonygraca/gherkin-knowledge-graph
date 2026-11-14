# Canonical acceptance specification for PG-01 (#63), M2.
# Source criteria: the expanded-M2 intake recorded in issue #63 and session prompt §8A/§21.
# The fixture repositories under fixtures/external-*/ are ordinary projects that never adopted
# CTA conventions; their expected inventories are hand-counted.
@PG-01 @issue-63 @M2
Feature: PG-01: Portable read-only Gherkin ingestion and repository-scoped queries
  CTA indexes an existing Git repository at a pinned commit without modifying it or executing its
  code. Missing requirement metadata and missing runtime matching metadata are reported as absent,
  never as defects.

  Rule: Indexing is read-only and annotation-free

    @SCN-2201
    Scenario: Untagged scenarios are queryable without requirements metadata
      Given an independent Git repository contains valid untagged Gherkin scenarios
      And it has no CTA-specific source annotations or requirements inventory
      When CTA indexes a pinned commit in read-only mode
      Then the scenarios and their steps are available through repository-scoped queries
      And their exact source locations and revision are returned
      And the repository's tracked files remain byte-identical
      And missing requirement links are not reported as an implementation failure

    @SCN-2206
    Scenario: Indexing executes nothing from the repository
      Given an independent repository whose test hooks would write a sentinel file
      When CTA indexes it
      Then no hook or step definition from it was executed
      And the index reports zero modified files

  Rule: Missing metadata is unknown, not defective

    @SCN-2202
    Scenario: Step-definition resolution is unknown without framework evidence
      Given an external repository contains Gherkin steps
      And no supported framework matching report is available
      When CTA queries step-to-definition resolution
      Then the result is UNKNOWN or NOT_AVAILABLE
      And no undefined-step defect is asserted from missing metadata alone

  Rule: Supplied framework evidence is attributed

    @SCN-2203
    Scenario: Existing runtime metadata establishes executable relationships
      Given an external repository has a trusted Cucumber execution report
      When CTA ingests the report against the corresponding Git revision
      Then reported Gherkin step matches and outcomes are linked to their definitions
      And each relationship identifies its report provenance and tested commit
      And no unobserved production-code execution is inferred

  Rule: Imported runs keep their provenance

    @SCN-2207
    Scenario: A report without provenance cannot be attributed
      Given an external repository indexed at a pinned commit
      And a Cucumber report whose provenance sidecar is missing
      When CTA imports the report
      Then the import is refused with "report-not-applicable"
      And no execution records are stored

  Rule: Identity is repository-scoped

    @SCN-2204
    Scenario: Same scenario identifiers never collide across repositories
      Given two independent repositories use the same scenario tag and relative path
      When CTA indexes each at its own pinned revision
      Then each scenario has a distinct repository-scoped identity
      And querying one repository does not include the other's records

  Rule: The official Gherkin AST is preserved

    @SCN-2205
    Scenario: Rules, outlines, data tables, and doc strings are preserved
      Given an external repository contains a Rule and a Scenario Outline with Examples
      When its features are parsed at a pinned commit
      Then the rule and both example instances are queryable
      And the data table and doc string are kept as step arguments
