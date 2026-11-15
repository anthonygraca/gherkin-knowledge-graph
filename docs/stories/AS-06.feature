# Canonical acceptance specification for AS-06 (#28), M3.
# Derived from the owner's issue and the Codex advisory in
# docs/reports/omp-closeout/advice/closeout-advice.md. Owner dispositions are accepted in
# docs/adr/0012-closeout-scope-decisions.md §1 (trusted-local-operator identity, append-only
# journal outside the fixture/evaluated repository, workspace projection over immutable baselines).
# Contract notes (baseline selection, snapshot identity, journal events, workspace response shapes)
# are normative in docs/stories/AS-06.md and docs/domain-contracts.md.
@AS-06 @issue-28 @M3
Feature: AS-06: Human decisions on version-bound proposals
  Discovery proposals become accepted relationships only through an explicit capture action and a
  human decision. Decisions are durable audit events, and acceptance never changes evidence or
  assurance findings. A review decision names the baseline it was evaluated against explicitly;
  an omitted baseline is a request-validation error, never a silent "latest" choice.

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
      And its snapshot digest is the canonical hash of the snapshot identity fields
      And no accepted link, verification evidence, or assurance finding is created
      And every file in the fixture repository retains its original content hash

    @SCN-3012
    Scenario Outline: Refuse an invalid capture without publishing a proposal
      Given the review journal is empty
      When the operator submits a capture with "<defect>"
      Then the response is a <status> problem with code "<code>"
      And no proposal or decision is appended

      Examples:
        | defect                             | status | code             |
        | an unknown target artifact SCN-999 | 422    | proposal-invalid |
        | a relation direction that contradicts the endpoint artifact types | 422 | proposal-invalid |
        | a source content hash that disagrees | 409 | proposal-stale |
        | a target content hash that disagrees | 409 | proposal-stale |

    @SCN-3013
    Scenario: Repeating an identical capture returns the existing proposal
      Given a captured proposal for SCN-002 implemented_by CODE-001 at baseline-a
      When the operator submits the identical snapshot again
      Then the response is 200 with the existing link and snapshot
      And the journal still contains exactly one capture event for that proposal

    @SCN-3021
    Scenario Outline: Capture conflicts are typed and publish nothing
      Given a captured proposal for SCN-002 implemented_by CODE-001 at baseline-a
      When the operator submits "<submission>"
      Then the response is a 409 problem with code "<code>"
      And the journal still contains exactly one capture event for that proposal

      Examples:
        | submission                                            | code              |
        | the same endpoints with a different provider identity | proposal-conflict |
        | the same endpoints after a terminal decision          | review-conflict   |

    @SCN-3018
    Scenario: An evidence-only revision change remains reviewable
      Given a captured proposal for SCN-002 implemented_by CODE-001 at baseline-a
      And an evidence-only revision exists whose endpoint content hashes equal baseline-a
      When the operator accepts that proposal against that evidence-only revision
      Then the response contains the proposal with review_state "accepted"
      And the decision identifies the selected commit and the unchanged endpoint hashes
      And no source change or verification failure is inferred from the different commit

    @SCN-3029
    Scenario Outline: Capture persistence failure is bounded
      Given a valid capture for SCN-002 implemented_by CODE-001 at baseline-a
      And the journal <failure>
      When the operator submits that capture
      Then the response is a 503 problem with code "review-storage-unavailable"
      And its durability is "<durability>"
      And the live workspace <live>
      And restarting <restart>

      Examples:
        | failure                                                                 | durability    | live                                            | restart                                    |
        | fails and rolls back to its prior committed length                      | not_committed | does not list the proposal or an accepted link   | exposes no captured proposal               |
        | writes a complete pair but cannot confirm durability or roll it back    | indeterminate | does not list the proposal optimistically       | exposes either no proposal or one complete pending captured proposal, never an accepted link |

  Rule: Decisions are durable audit events and do not perform verification

    @SCN-3002
    Scenario: Accept the existing pending proposal
      Given LNK-007 is proposed at baseline-a
      And baseline findings and evidence have been recorded for comparison
      When "rv-ana" posts decision "accept" for LNK-007 at baseline-a
      Then the response contains LNK-007 with review_state "accepted"
      And the journal contains one decision identifying "rv-ana" and a server UTC timestamp
      And that decision identifies the proposal snapshot and baseline-a endpoint hashes
      And the workspace thread contains LNK-007 only in accepted_links
      And the workspace pending queue excludes LNK-007
      And workspace history returns that acceptance
      And baseline findings and evidence equal the recorded values
      And default baseline thread reads equal their values before the decision

    @SCN-3003
    Scenario: Reject a proposal with a retained reason
      Given LNK-007 is proposed at baseline-a
      When "rv-ana" rejects LNK-007 at baseline-a with reason "The scenario does not cover the requirement"
      Then the journal contains one rejection with that reason
      And the workspace history returns that rejection
      And LNK-007 is absent from the workspace accepted links and pending queue
      And LNK-007 is labelled as rejected for that baseline
      And baseline findings, evidence, and fixture file hashes are unchanged

    @SCN-3004
    Scenario: Refuse a decision supplied under another reviewer identity
      Given LNK-007 is proposed at baseline-a
      When "rv-mallory" posts decision "accept" for LNK-007 at baseline-a
      Then the response is a 403 problem with code "review-identity-mismatch"
      And no decision is appended
      And the workspace still shows LNK-007 as proposed

    @SCN-3005
    Scenario Outline: Refuse a rejection whose reason field is absent or null
      Given LNK-007 is proposed at baseline-a
      When "rv-ana" rejects LNK-007 at baseline-a with <input>
      Then the response is a 422 problem with code "request-validation"
      And no decision is appended

      Examples:
        | input           |
        | no reason field |
        | a null reason   |

    @SCN-3006
    Scenario Outline: Refuse a rejection whose reason is blank
      Given LNK-007 is proposed at baseline-a
      When "rv-ana" rejects LNK-007 at baseline-a with <input>
      Then the response is a 422 problem with code "review-reason-required"
      And no decision is appended

      Examples:
        | input                              |
        | an empty reason                    |
        | a reason of three space characters |

    @SCN-3007
    Scenario: Refuse review when no operator identity is configured
      Given the application has no configured operator identity
      When "rv-ana" posts decision "accept" for LNK-007 at baseline-a
      Then the response is a 503 problem with code "review-identity-unavailable"
      And no decision is appended

    @SCN-3008
    Scenario: Refuse a second terminal decision
      Given a durable acceptance decision already exists for LNK-007 at baseline-a
      When "rv-ana" posts decision "reject" for LNK-007 at baseline-a with reason "Changed my mind"
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
    Scenario: Failed persistence with a successful rollback does not publish an acceptance
      Given LNK-007 is proposed at baseline-a
      And the journal cannot durably append a record and can roll back to its prior committed length
      When "rv-ana" posts decision "accept" for LNK-007 at baseline-a
      Then the response is a 503 problem with code "review-storage-unavailable"
      And its durability is "not_committed"
      And the workspace still shows LNK-007 as proposed
      And restarting with the same journal does not expose an accepted decision

    @SCN-3028
    Scenario: An unconfirmed commit is reported as indeterminate
      Given LNK-007 is proposed at baseline-a
      And the journal writes a complete commit pair but cannot confirm its durability or roll it back
      When "rv-ana" posts decision "accept" for LNK-007 at baseline-a
      Then the response is a 503 problem with code "review-storage-unavailable"
      And its durability is "indeterminate"
      And the application does not report the decision as successful
      And further journal mutations are refused with "review-storage-unavailable"
      And restarting exposes either no decision or exactly one complete committed decision
      And no partial or malformed record is replayed

    @SCN-3011
    Scenario: Refuse a missing proposal
      When "rv-ana" posts decision "accept" for LNK-999 at baseline-a
      Then the response is a 404 problem with code "proposal-not-found"
      And no decision is appended

    @SCN-3014
    Scenario: Captures and decisions survive restart
      Given a captured proposal for SCN-002 implemented_by CODE-001 at baseline-a
      And "rv-ana" accepts that proposal at baseline-a
      When the application restarts with the same journal
      Then the workspace thread contains that proposal only in accepted_links
      And the workspace pending queue excludes that proposal
      And the workspace pending queue still lists the unrelated pending proposal LNK-007
      And the workspace history returns the capture and the acceptance
      And the decision identifies the same snapshot and operator
      And the journal bytes are identical to their bytes before restart

    @SCN-3023
    Scenario: A pending capture survives restart without a decision
      Given a captured proposal for SCN-002 implemented_by CODE-001 at baseline-a
      When the application restarts with the same journal
      Then the workspace pending queue lists that proposal with its snapshot and provenance
      And the workspace history returns its capture event
      And no accepted link or decision exists for it
      And the journal bytes are identical to their bytes before restart

    @SCN-3024
    Scenario: A rejection survives restart with its reason
      Given a captured proposal for SCN-002 implemented_by CODE-001 at baseline-a
      And "rv-ana" rejects that proposal at baseline-a with reason "The candidate is not the implementation"
      When the application restarts with the same journal
      Then the workspace history returns the rejection with its reason and operator
      And the proposal is absent from accepted links and the pending queue
      And the journal bytes are identical to their bytes before restart

    @SCN-3015
    Scenario: A later decision preserves earlier decision bytes
      Given a captured proposal for SCN-002 implemented_by CODE-001 at baseline-a
      And a captured proposal for SCN-002 exercised_by TEST-002 at baseline-a
      And the first proposal is rejected with reason "Not the right implementation"
      When "rv-ana" accepts the second proposal at baseline-a
      Then the first decision's journal bytes are unchanged
      And the workspace history returns both decisions
      And the first proposal remains absent from accepted links and pending

    @SCN-3016
    Scenario: Concurrent terminal decisions serialize
      Given LNK-007 is proposed at baseline-a
      When "rv-ana" submits an acceptance and a rejection for LNK-007 at baseline-a concurrently
      Then exactly one request returns a successful decision
      And the other request returns a 409 problem with code "review-conflict"
      And exactly one terminal decision event is appended
      And the workspace thread and pending queue agree with that decision

    @SCN-3017
    Scenario Outline: Refuse a review write outside the trusted local boundary
      Given LNK-007 is proposed at baseline-a
      When a decision request arrives with <condition>
      Then the response is a <status> problem with code "<code>"
      And no decision is appended

      Examples:
        | condition                                   | status | code                     |
        | a non-loopback client address               | 403    | review-loopback-required |
        | a browser Origin of https://example.invalid | 403    | review-origin-forbidden  |

    @SCN-3022
    Scenario: A loopback request without a browser Origin is allowed
      Given LNK-007 is proposed at baseline-a
      When "rv-ana" posts decision "accept" for LNK-007 at baseline-a without an Origin header
      Then the response is 200 with LNK-007 accepted
      And the journal contains one decision

    @SCN-3019
    Scenario: Decisions apply only under compatible endpoint content
      Given a captured proposal for SCN-002 implemented_by CODE-001 at baseline-a
      And the proposal is accepted at baseline-a
      When the workspace is read at baseline-a and at baseline-b
      Then baseline-a shows the proposal as accepted
      And baseline-b shows the same acceptance only if both endpoint hashes are unchanged
      And neither workspace shows an acceptance whose endpoint content differs from the snapshot
      And default baseline reads remain unchanged

    @SCN-3020 @browser
    Scenario: Review workspace shows provenance, decisions, and history
      Given banking-demo baseline-a is loaded
      And trusted-local-operator mode identifies the operator as "rv-ana"
      And the review journal is empty
      When the reviewer captures the fake candidate for SCN-002 implemented_by CODE-001 at baseline-a
      And the reviewer opens the review workspace for REQ-002
      Then the proposal shows provider "fake", model version "fake-fixture-v1", and its index revision
      And the proposal is labelled as fixture-generated
      And the review controls require a reason for rejection
      When the reviewer accepts the proposal
      Then the workspace shows the proposal as accepted and excludes it from the pending queue
      And the history shows one acceptance by "rv-ana" with a server timestamp

    @SCN-3025 @browser
    Scenario: Rejection is visible with its retained reason and history
      Given banking-demo baseline-a is loaded
      And trusted-local-operator mode identifies the operator as "rv-ana"
      And the review journal is empty
      When the reviewer captures the fake candidate for SCN-002 implemented_by CODE-001 at baseline-a
      And the reviewer opens the review workspace for REQ-002
      And the reviewer rejects the proposal with reason "Not the right implementation"
      Then the workspace excludes the proposal from accepted links and the pending queue
      And the history shows one rejection by "rv-ana" with that reason and a server timestamp
      And the proposal remains absent from default baseline accepted links

    @SCN-3026 @browser
    Scenario: A refused review write is reported without a success state
      Given banking-demo baseline-a is loaded
      And trusted-local-operator mode identifies the operator as "rv-ana"
      And the review journal is empty
      When the reviewer captures the fake candidate for SCN-002 implemented_by CODE-001 at baseline-a
      And the reviewer opens the review workspace for REQ-002 and displays the pending acceptance control
      And the proposal is accepted through the API in another local request
      And the reviewer submits the already displayed acceptance control without refreshing
      Then the dashboard displays the typed review conflict
      And it does not display the proposal as newly accepted
      And refreshing the workspace shows the proposal as accepted by the earlier decision
      And the journal contains exactly one terminal decision

    @SCN-3027
    Scenario: An uncommitted journal tail blocks further mutations
      Given a captured proposal for SCN-002 implemented_by CODE-001 at baseline-a
      And the journal ends with a complete payload record lacking a commit marker
      When the application restarts with the same journal
      Then the uncommitted record is not replayed
      And a new review mutation is refused with a 503 problem and code "review-storage-unavailable"
      And no new journal record is appended
