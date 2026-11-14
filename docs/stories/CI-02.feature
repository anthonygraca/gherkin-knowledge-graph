# Canonical acceptance specification for CI-02 (#37), M4 — REFINEMENT DRAFT / GATED.
# Implementation follows CI-01 and the M3 gate. Portable-locator comparison requires an owner
# disposition on comparison identity. See docs/adr/0012-closeout-scope-decisions.md.
@CI-02 @issue-37 @M4 @refinement-draft
Feature: CI-02: Comparable finding sets are classified by stable identity
  Finding identity is the existing stable fingerprint. Comparison requires complete, comparable,
  revision-bound reports; absence does not imply remediation.

  Rule: Identity determines new, unchanged, and resolved categories

    @SCN-3501
    Scenario: Compare the hand-labeled banking baselines
      Given complete comparable assurance reports for banking-demo baseline-a and baseline-b
      When the findings diff command compares baseline-a to baseline-b
      Then it reports 2 new findings
      And it reports 4 unchanged findings
      And it reports 0 resolved findings
      And the new finding types are reverification_required and verification_failed
      And the report includes both resolved revisions and both report digests

    @SCN-3502
    Scenario: Reverse comparison exposes the resolved category
      Given complete comparable assurance reports for banking-demo baseline-a and baseline-b
      When the findings diff command compares baseline-b to baseline-a
      Then it reports 0 new findings
      And it reports 4 unchanged findings
      And it reports 2 resolved findings
      And resolved means absent from the current comparable finding set
      And no verification evidence or requirement verdict is created

    @SCN-3503
    Scenario: Comparing a baseline with itself changes nothing
      Given a complete assurance report for banking-demo baseline-a
      When that report is compared with itself
      Then it reports 0 new findings
      And it reports 4 unchanged findings
      And it reports 0 resolved findings

    @SCN-3504
    Scenario: Payload changes do not replace an unchanged finding identity
      Given two comparable finding reports contain the same rule, finding type, and artifact IDs
      And those findings have different explanations and evidence references
      When the reports are compared
      Then the finding is classified as unchanged
      And its before and after payloads are both retained
      And neither payload is rewritten

  Rule: Unknown or incompatible inputs cannot imply resolution

    @SCN-3505
    Scenario Outline: Refuse an invalid comparison
      Given two report inputs differ by "<condition>"
      When the findings diff command compares them
      Then it exits 2 with code "findings-not-comparable"
      And it identifies the invalid input and reason
      And it returns no new, unchanged, or resolved classification

      Examples:
        | condition                                |
        | the previous resolved revision is absent |
        | the current resolved revision is absent  |
        | the current evaluation is incomplete     |
        | repository identities differ             |
        | evaluated rule scopes differ             |
        | policy versions differ                   |
        | a finding baseline contradicts its report|

    @SCN-3506
    Scenario: Source locators alone do not establish cross-revision continuity
      Given two portable finding reports use source-locator identities
      And no reviewed continuity mapping accompanies them
      When the findings diff command compares those reports
      Then it exits 2 with code "findings-not-comparable"
      And it reports that stable cross-revision identity is unavailable
      And it does not classify displaced findings as resolved and new
