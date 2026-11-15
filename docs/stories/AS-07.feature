# Canonical acceptance specification for AS-07 (#29), M3.
# Derived from the owner's issue and the Codex advisory. Provider failure remains distinct from
# findings, empty success, and accepted coverage. Provenance presentation and problem-extension
# contracts are normative in docs/stories/AS-07.md and docs/domain-contracts.md.
@AS-07 @issue-29 @M3
Feature: AS-07: Honest provider availability and proposal provenance
  Provider failure remains distinct from findings, empty success, and accepted coverage. The
  dashboard never substitutes one provider's output for another's, and every proposal
  presentation identifies the provider, model version, and index identity it actually has.

  Rule: Provider failure remains distinct from findings and empty success

    @SCN-3101 @browser
    Scenario: An unregistered provider fails while baseline data remains usable
      Given the effective discovery registry contains only "fake"
      And the dashboard displays REQ-001 at baseline-a
      When discovery is requested with provider "missing-provider"
      Then the API returns a 400 problem with code "provider-not-registered"
      And failed_provider is "missing-provider"
      And registered_providers is ["fake"]
      And the candidate panel displays the selected provider as unavailable and names "missing-provider"
      And the candidate panel lists the registered providers and keeps "fake" selectable
      And the accepted thread and EV-001 remain accessible
      And no assurance finding is created

    @SCN-3102 @browser
    Scenario: A registered provider fails after an earlier successful request
      Given the configured provider "cocoindex" previously returned candidates for baseline-a
      And that provider now times out through its deterministic recorded transport
      When discovery is requested for baseline-b
      Then the API returns a 503 problem with code "provider-unavailable"
      And failed_provider is "cocoindex"
      And the panel displays the provider failure and names "cocoindex"
      And no baseline-a candidate appears as a current baseline-b result
      And no successful empty-result state is displayed
      And the application does not silently request fake discovery
      And the accepted thread and EV-001 remain accessible
      And accepted links, evidence, and findings are unchanged

    @SCN-3103 @browser
    Scenario: A valid empty result is not an unavailable provider
      Given the configured discovery provider is "fake"
      When candidates are requested for REQ-003 at baseline-a
      Then the API returns 200 with an empty candidates array
      And the response retains provider, model_version, and index_revision
      And the panel displays zero candidates without an unavailable-provider state

  Rule: Proposal provenance and acceptance state are visible separately

    @SCN-3104 @browser
    Scenario: A fixture proposal retains its provenance through review
      Given LNK-007 is displayed in the proposal panel at baseline-a
      And a rejection decision for LNK-007 is recorded with reason "Not this scenario"
      When its details and review history are opened
      Then every proposal presentation displays provider "fake"
      And every proposal presentation displays model_version "fake-fixture-v1"
      And every proposal presentation displays its recorded index_revision
      And it is labelled as fixture-generated
      And the review history retains that provenance with the rejection
      And it is absent from accepted_links

    @SCN-3105 @browser
    Scenario: A model-backed adapter is distinguishable without a live model test
      Given the CocoIndex provider adapter uses a deterministic recorded search transport
      And the real discovery route and problem mapping are exercised
      When its mapped proposal is displayed
      Then the panel identifies the provider as "cocoindex"
      And it displays the recorded model identity
      And it labels the snapshot value as a CTA snapshot binding
      And it does not label the proposal as fixture-generated or accepted
      And this check establishes adapter/API/UI behaviour, not live inference or retrieval quality

    @SCN-3106 @browser
    Scenario Outline: Historical missing provenance is shown as unknown
      Given a historical proposed link whose <field> is <value>
      When the proposal is displayed
      Then <field> is shown as "not recorded"
      And no current <field> is substituted
      And the proposal remains outside accepted_links

      Examples:
        | field          | value  |
        | provider       | absent |
        | provider       | null   |
        | model_version  | absent |
        | model_version  | null   |
        | index_revision | absent |
        | index_revision | null   |

    @SCN-3107 @browser
    Scenario: A historical model-backed proposal remains labelled when its provider is disabled
      Given a recorded proposal whose provider is "cocoindex" and whose model and index identity are recorded
      And the effective discovery registry contains only "fake"
      When the proposal is displayed in history
      Then the panel identifies the provider as "cocoindex"
      And it displays the recorded model identity
      And it labels the recorded index value as a CTA snapshot binding
      And it does not label the proposal as fixture-generated
      And it reports the provider as currently unavailable without hiding the recorded provenance
