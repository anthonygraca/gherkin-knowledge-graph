# Canonical acceptance specification for AS-06 (#28), M3 — REFINEMENT DRAFT.
# Derived from the owner's issue and the Codex advisory in
# docs/reports/omp-closeout/advice/closeout-advice.md. Owner disposition on the trusted-local-operator
# identity and append-only journal design is outstanding; implementation must not start until the
# draft is reviewed and the draft tag is removed.
@AS-06 @issue-28 @M3 @refinement-draft
Feature: AS-06: Human decisions on version-bound proposals
  Discovery proposals become accepted relationships only through an explicit capture action and a
  human decision. Decisions are durable audit events, and acceptance never changes evidence or
  assurance findings.

  Background:
    Given banking-demo baseline-a is loaded
    And the review journal is empty and outside the fixture repository
    And trusted-local-operator mode identifies the operator as "rv-ana"

  Rule: Discovery candidates become reviewable proposals only through explicit capture

    @SCN-3001
    Scenario: Capture a candidate without accepting it
      Given fake discovery returned SCN-002 implemented_by CODE-001
      When the operator submits that candidate and its baseline-a endpoint hashes to POST "/api/link-proposals"
      Then a new link is returned with review_state "proposed"
      And its snapshot retains the submitted provider, model version, and index revision
      And its snapshot identifies baseline-a and both endpoint content hashes
      And no accepted link, verification evidence, or assurance finding is created
      And every file in the fixture repository retains its original content hash

  Rule: Decisions are durable audit events and do not perform verification

    @SCN-3002
    Scenario: Accept the existing pending proposal
      Given LNK-007 is proposed at baseline-a
      And baseline findings and evidence have been recorded for comparison
      When "rv-ana" posts decision "accept" for LNK-007
      Then the response contains LNK-007 with review_state "accepted"
      And the journal contains one decision identifying "rv-ana" and a server UTC timestamp
      And that decision identifies the proposal snapshot and baseline-a endpoint hashes
      And the workspace thread contains LNK-007 only in accepted_links
      And the workspace pending queue excludes LNK-007
      And baseline findings and evidence equal the recorded values
      And default baseline thread reads equal their values before the decision

    @SCN-3003
    Scenario: Reject a proposal with a retained reason
      Given LNK-007 is proposed at baseline-a
      When "rv-ana" rejects LNK-007 with reason "The scenario does not cover the requirement"
      Then the journal contains one rejection with that reason
      And the workspace history returns that rejection
      And LNK-007 is absent from the workspace accepted links and pending queue
      And baseline findings, evidence, and fixture file hashes are unchanged

    @SCN-3004
    Scenario: Refuse a decision supplied under another reviewer identity
      Given LNK-007 is proposed at baseline-a
      When "rv-mallory" posts decision "accept" for LNK-007
      Then the response is a 403 problem with code "review-identity-mismatch"
      And no decision is appended
      And the workspace still shows LNK-007 as proposed

    @SCN-3005
    Scenario: Refuse a rejection without a reason
      Given LNK-007 is proposed at baseline-a
      When "rv-ana" posts decision "reject" for LNK-007 with no reason
      Then the response is a 422 problem with code "request-validation"
      And no decision is appended

    @SCN-3006
    Scenario: Refuse a rejection whose reason is whitespace only
      Given LNK-007 is proposed at baseline-a
      When "rv-ana" rejects LNK-007 with reason
        """
        """
      Then the response is a 422 problem with code "review-reason-required"
      And no decision is appended

    @SCN-3007
    Scenario: Refuse review when no operator identity is configured
      Given the application has no configured operator identity
      When "rv-ana" posts decision "accept" for LNK-007
      Then the response is a 503 problem with code "review-identity-unavailable"
      And no decision is appended

    @SCN-3008
    Scenario: Refuse a second terminal decision
      Given a durable acceptance decision already exists for LNK-007
      When "rv-ana" posts decision "reject" for LNK-007
      Then the response is a 409 problem with code "review-conflict"
      And the original decision bytes are unchanged
      And no second decision is appended

    @SCN-3009
    Scenario: Refuse acceptance against changed endpoint content
      Given a captured proposal connects SCN-002 to CODE-001 at baseline-a
      And CODE-001 has different content at baseline-b
      When the operator accepts that proposal against baseline-b
      Then the response is a 409 problem with code "proposal-stale"
      And no decision is appended
      And no verification failure is recorded

    @SCN-3010
    Scenario: Failed persistence does not publish an acceptance
      Given LNK-007 is proposed at baseline-a
      And the decision journal cannot durably append a record
      When "rv-ana" posts decision "accept" for LNK-007
      Then the response is a 503 problem with code "review-storage-unavailable"
      And the workspace still shows LNK-007 as proposed
      And restarting with the same journal does not expose an accepted decision

    @SCN-3011
    Scenario: Refuse a missing proposal
      When "rv-ana" posts decision "accept" for LNK-999
      Then the response is a 404 problem with code "proposal-not-found"
      And no decision is appended
