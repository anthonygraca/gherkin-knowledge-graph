# Canonical acceptance specification for AS-07 (#29), M3 — REFINEMENT DRAFT.
# Derived from the owner's issue and the Codex advisory. Implementation waits for review and the
# removal of @refinement-draft.
@AS-07 @issue-29 @M3 @refinement-draft
Feature: AS-07: Honest provider availability and proposal provenance
  Provider failure remains distinct from findings, empty success, and accepted coverage.

  Rule: Provider failure remains distinct from findings and empty success

    @SCN-3101
    Scenario: An unregistered provider fails while baseline data remains usable
      Given the effective discovery registry contains only "fake"
      And the dashboard displays REQ-001 at baseline-a
      When discovery is requested with provider "missing-provider"
      Then the API returns a 400 problem with code "provider-not-registered"
      And failed_provider is "missing-provider"
      And registered_providers is ["fake"]
      And the candidate panel displays the selected provider as unavailable
      And the accepted thread and EV-001 remain accessible
      And no assurance finding is created

    @SCN-3102
    Scenario: A registered provider fails after an earlier successful request
      Given a configured provider previously returned candidates for baseline-a
      And that provider now times out through the deterministic failure transport
      When discovery is requested for baseline-b
      Then the API returns a typed 503 problem
      And the panel displays the provider failure
      And no baseline-a candidate appears as a current baseline-b result
      And the application does not silently request fake discovery

    @SCN-3103
    Scenario: A valid empty result is not an unavailable provider
      Given the configured discovery provider is "fake"
      When candidates are requested for REQ-003
      Then the API returns 200 with an empty candidates array
      And the response retains provider, model_version, and index_revision
      And the panel displays zero candidates without an unavailable-provider state

  Rule: Proposal provenance and acceptance state are visible separately

    @SCN-3104
    Scenario: A fixture proposal retains its provenance through review
      Given LNK-007 is displayed in the proposal panel
      When its details and review history are opened
      Then every proposal presentation displays provider "fake"
      And every proposal presentation displays model_version "fake-fixture-v1"
      And every proposal presentation displays its recorded index_revision
      And it is labelled as fixture-generated
      And it is absent from accepted_links until an acceptance decision exists

    @SCN-3105
    Scenario: A model-backed adapter is distinguishable without a live model test
      Given the CocoIndex adapter uses a deterministic recorded search transport
      When its mapped proposal is displayed
      Then the panel identifies the provider as "cocoindex"
      And it displays the recorded model identity
      And it labels the snapshot value as a CTA snapshot binding
      And it does not label the proposal as fixture-generated or accepted

    @SCN-3106
    Scenario: Historical missing provenance is shown as unknown
      Given a historical proposed link has no recorded model_version
      When the proposal is displayed
      Then its model version is shown as not recorded
      And no current model version is substituted
      And the proposal remains outside accepted_links
