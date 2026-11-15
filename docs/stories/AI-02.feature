# Canonical acceptance specification for AI-02 (#31), M3.
# The owner-accepted manifest is docs/reports/omp-closeout/AI-02-MODEL-MANIFEST.md: Apache-2.0
# EmbeddingGemma 2 text 270M ONNX weights, onnxruntime CPU, this workstation only.
# SCN-3205 is @live-local: excluded from the default offline suite and executed under unshare -rn
# with the real local weights. The external Ollama endpoint does not satisfy this specification.
@AI-02 @issue-31 @M3
Feature: AI-02: Optional inference executes on the same machine
  Local inference is optional. Remote endpoints, implicit downloads, and remote execution do not
  satisfy it.

  Rule: Local inference is optional and remote execution is refused

    @SCN-3201
    Scenario: Default discovery needs no model runtime
      Given no local model runtime is installed
      And no local inference opt-in is configured
      When discovery is requested with no provider override
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
    Scenario Outline: Missing local weights or runtime produce an unavailable result
      Given local inference mode is explicitly enabled
      And <condition>
      When that provider is requested for SCN-001
      Then the API returns a 503 problem with code "retrieval-unavailable"
      And no automatic download or remote fallback occurs
      And accepted links, evidence, and findings are unchanged

      Examples:
        | condition                                                       |
        | its configured weights digest is absent from local storage      |
        | its installed weights do not match the configured digest        |
        | its weights are installed but the runtime package is unavailable |

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
      And a known artifact with no eligible targets returns an empty list with retained provenance
      And a runtime that cannot report its model identity fails explicitly without candidates
      And accepted links, evidence, and findings are unchanged

    @SCN-3205 @live-local
    Scenario: Real indexing and discovery work with external egress denied
      Given the owner-accepted local model manifest identifies installed weights and runtime
      And non-loopback egress is denied for the inference process tree
      And an isolated banking-demo index has not yet been built
      When that runtime indexes baseline-a and executes the shared discovery contract cases
      Then the contract cases complete without external network access
      And the execution record names the weights digest and runtime version
      And it records the query and document formatting versions
      And the live record retains the egress-denial observation
      And the observed weights, runtime, and formatting match the identified manifest
      And every returned candidate identifies that model and its snapshot binding

    @SCN-3206
    Scenario: Malformed local inference output is not an empty success
      Given the local adapter receives a non-finite embedding through its deterministic transport
      When discovery is requested for SCN-001
      Then a typed retrieval-unavailable problem is returned
      And no partial candidate list is returned
      And no accepted link, evidence, or finding is written
