# Canonical acceptance specification for AI-02 (#31), M3 — REFINEMENT DRAFT / BLOCKED.
# Blocked on owner acceptance of an actual local model, runtime, licence, and hardware configuration.
# The external Ollama endpoint does not satisfy this specification.
@AI-02 @issue-31 @M3 @refinement-draft
Feature: AI-02: Optional inference executes on the same machine
  Local inference is optional. Remote endpoints, implicit downloads, and remote execution do not
  satisfy it.

  Rule: Local inference is optional and remote execution is refused

    @SCN-3201
    Scenario: Default discovery needs no model runtime
      Given no local model runtime is installed
      And no local inference opt-in is configured
      When fake discovery is requested for SCN-001
      Then discovery succeeds through "fake"
      And no model process is started
      And no model weights are downloaded
      And no network connection is attempted

    @SCN-3202
    Scenario: A remote endpoint cannot satisfy local inference mode
      Given local inference mode is configured with endpoint "http://192.0.2.10:11434"
      When that provider is requested for SCN-001
      Then the API returns a 400 problem with code "invalid-request"
      And no connection to that endpoint is attempted
      And no candidates are returned

    @SCN-3203
    Scenario: Missing local weights produce an unavailable result
      Given local inference mode is explicitly enabled
      And its configured weights digest is absent from local storage
      When that provider is requested for SCN-001
      Then the API returns a 503 problem with code "retrieval-unavailable"
      And no automatic download or remote fallback occurs
      And accepted links, evidence, and findings are unchanged

  Rule: Contract behavior is independent of model quality

    @SCN-3204
    Scenario: The adapter passes the shared discovery contract offline
      Given the local provider adapter uses deterministic embedding and search transports
      When the shared CandidateDiscovery contract cases execute against it
      Then returned source IDs equal the requested source IDs
      And candidate counts obey top_k and relation filters
      And ranks are contiguous from one
      And every candidate carries provider, model_version, and index_revision
      And no candidate carries a link ID or review state
      And accepted links, evidence, and findings are unchanged

    @SCN-3205
    Scenario: Real indexing and discovery work with external egress denied
      Given the owner-accepted local model manifest identifies installed weights and runtime
      And non-loopback egress is denied for the inference process tree
      And an isolated banking-demo index has not yet been built
      When that runtime indexes baseline-a and executes the shared discovery contract cases
      Then the contract cases complete without external network access
      And the execution record names the weights digest and runtime version
      And it records the query and document formatting versions
      And every returned candidate identifies that model and its snapshot binding

    @SCN-3206
    Scenario: Malformed local inference output is not an empty success
      Given the local adapter receives a non-finite embedding through its deterministic transport
      When discovery is requested for SCN-001
      Then a typed retrieval-unavailable problem is returned
      And no partial candidate list is returned
      And no accepted link, evidence, or finding is written
