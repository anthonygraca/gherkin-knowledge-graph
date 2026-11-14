# Canonical M0 acceptance specification; migrated from M0-foundation.md.
# From M2 onward executed by the Cucumber suite (bdd/). SCN-205 asserted the M0 501 contract for
# POST /api/assurance/evaluate; AS-01 implemented that endpoint in M1, which superseded the
# contract-only state. The scenario keeps its approved wording and is tagged @superseded-by-AS-01
# so the executable suite does not assert the obsolete 501; the supersession is recorded in
# STATUS.md and the M2 feature inventory.
@FT-02 @issue-19 @M0
Feature: FT-02: Versioned contracts and mock responses
  As a developer, I want versioned API/domain contracts plus mock responses so I can build independently.

  @SCN-201 @AC-2.1
  Scenario: Fixture-backed read endpoints
    Given the backend runs with no network and no embedding or LLM service
    When "GET /api/artifacts/REQ-001?baseline=baseline-a" is called
    Then the response validates against the "Artifact" contract
    And its "revision" equals the commit SHA tagged "baseline-a"
    And "GET /api/threads/REQ-001?baseline=baseline-b" returns the accepted chain plus evidence
    And "GET /api/findings?baseline=baseline-b" validates against the "FindingsResponse" contract

  @SCN-202 @AC-2.2
  Scenario: Baselines are addressed by tag or commit
    Given "baseline-a" resolves to a commit SHA in the fixture manifest
    When the same endpoint is called with the tag and with that SHA
    Then both responses are identical

  @SCN-203 @AC-2.3
  Scenario: Unknown artifact
    When "GET /api/artifacts/REQ-999" is called
    Then the status is 404
    And the body is an RFC 9457 problem document with a "urn:cta:error:artifact-not-found" type

  @SCN-204 @AC-2.4
  Scenario: Discover likely implementation from a scenario
    Given the candidate-discovery provider is "fake"
    When candidates are requested for "SCN-001"
    Then "CODE-001" is returned as a proposed "implemented_by" candidate at rank 1
    And the response includes the provider name, model version, and index revision
    And the candidate carries no link identifier or review state
    And no accepted link is created or modified

  @SCN-205 @AC-2.5 @superseded-by-AS-01
  Scenario: Contract-only endpoints in M0
    When "POST /api/assurance/evaluate" is called
    Then the status is 501
    And the problem document names the owning story and milestone
