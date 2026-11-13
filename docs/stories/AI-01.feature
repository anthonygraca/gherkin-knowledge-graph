# Canonical acceptance specification for AI-01, extracted unchanged from issue #30.
# AI-01 was closed with the fake-provider slice; the real CandidateDiscovery adapter remains
# a later story. PR 1 serves the provider boundary and does not claim these scenarios.
# They are verified by the mapped pytest checks in AI-01.md; no Gherkin runner is configured.
@AI-01 @issue-30 @M0
Feature: AI-01: Fake and real CandidateDiscovery implementations behind one interface
  As a developer, I want fake and real CandidateDiscovery implementations behind one
  interface, so that domain work never depends on a model being available.

  @SCN-901
  Scenario: One contract, interchangeable adapters
    Given the "fake" provider and any future local provider
    When the shared contract tests run against a provider
    Then it returns ranked candidates whose source_id is the requested artifact
    And it reports the provider name, model version, and index revision
    And it exposes no way to accept, store, or verify a link

  @SCN-902
  Scenario: Provider configuration is explicit
    Given an unknown provider name
    When candidates are requested
    Then the request fails with "provider-not-registered"
    And the response lists the registered providers
