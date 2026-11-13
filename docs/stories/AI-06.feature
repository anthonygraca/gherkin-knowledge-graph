# Canonical acceptance specification for AI-06 (#56), M3.
# Source criteria: the RAG mission's PR 1 slice ("CocoIndex Code compatibility, integration
# contract, and live smoke") and the adoption decision recorded in docs/adr/0008.
# This is an implementation-approach story under F-08. It does not amend or close AI-01 (#30),
# AI-02 (#31), AI-03 (#32), AI-04 (#34), or AI-05 (#35). CocoIndex Code supplies semantic
# code-search observations; CTA keeps artifact identity, accepted links, evidence, and policy.
# These scenarios are mapped to pytest checks; no Gherkin runner executes them.
@AI-06 @issue-56 @M3
Feature: AI-06: CocoIndex Code semantic code-search capability and integration contract
  As a developer, I want an optional, bounded CocoIndex Code adapter that returns attributable
  source-code hits from one configured project snapshot, so that semantic code retrieval can be
  integrated later without weakening CTA's offline default or its separation of proposals,
  accepted relationships, and verification evidence.

  Rule: CocoIndex is optional and never required by default paths.

    @SCN-1001
    Scenario: Offline default is unchanged
      Given no CocoIndex executable, project root, daemon, or embedding endpoint is configured
      When the default configuration is loaded and a discovery request runs
      Then discovery uses the deterministic "fake" provider
      And no CocoIndex process is started
      And no CocoIndex index is accessed and no network request is made
      And "cocoindex" is not a registered discovery provider in this slice

  Rule: Requests and results are bounded observations.

    @SCN-1002
    Scenario: Search requests are bounded before execution
      Given a CocoIndex client with configured request bounds
      When a search requests a limit of 1 or 100, a non-negative offset, and a non-empty query
      Then the request is accepted
      And a limit of 0 or 101, a negative offset, an empty or over-2000-character query, or more than 10 path or language filters is rejected with "cocoindex-request-error" before any process starts
      And a path filter that is absolute, carries a drive or UNC prefix, contains a parent-directory component, or does not use relative POSIX path syntax is rejected with "cocoindex-request-error"
      And response bytes, per-hit content, and captured stderr have configurable limits

    @SCN-1003
    Scenario: A structured search returns normalized hits
      Given a captured structured result and a configured project root
      When the client normalizes the result
      Then it preserves the reported order and any duplicate chunks
      And every hit reports its project-relative path, language, 1-based line range, content, and score as reported
      And the configured project root is recorded as caller-supplied context, not as observed index identity
      And the server name and version are recorded when the server reports them
      And the index identity is reported as unavailable because the MCP contract does not expose it
      And a valid empty result is a success with no hits
      And no hit exposes a link id, review state, evidence id, verification claim, or assurance conclusion

    @SCN-1004
    Scenario: Malformed results are rejected whole, never repaired
      Given a result with an absolute path, a parent-directory escape, an empty path, an invalid line range, a non-finite score, a wrong field type, missing or non-text content, a mismatched response id, an MCP error flag, inconsistent counts, or a response beyond the configured bound
      When the client normalizes the result
      Then it raises "cocoindex-protocol-error"
      And the entire response is rejected, including any otherwise-valid hits, instead of returning a partial list
      And no invalid hit is dropped, clamped, or rewritten
      And no artifact identity is invented

    @SCN-1005
    Scenario Outline: Failures are typed and owned processes are reaped
      Given <condition>
      When a search is attempted
      Then it raises "<error>"
      And a process the adapter started is terminated and reaped within the configured cleanup interval, without stopping an unrelated shared daemon
      And the caller receives no hit list

      Examples:
        | condition                                            | error                         |
        | the executable is missing                            | cocoindex-configuration-error |
        | the project root has no CocoIndex settings marker    | cocoindex-configuration-error |
        | the server name, version, or search schema is incompatible | cocoindex-capability-error |
        | the server exits before initialize                   | cocoindex-unavailable         |
        | the server closes its output pipe                    | cocoindex-unavailable         |
        | the server exits non-zero                            | cocoindex-unavailable         |
        | the server does not answer before the deadline       | cocoindex-timeout             |
        | the server ignores termination after the deadline    | cocoindex-timeout             |
        | the search reports success false, even with partial results | cocoindex-query-error   |

  Rule: The adapter selects one configured project and validates what it returns.

    @SCN-1006
    Scenario: Only the configured project is selected and returned paths are validated
      Given a configured project root containing CocoIndex settings
      When the client searches
      Then the server runs with that project root as its working directory
      And the adapter refuses to use the default shared CocoIndex state directory
      And the adapter never falls back to an ancestor CocoIndex project
      And only allow-listed subprocess environment variables are passed
      And when hits are verified against the snapshot, a missing file, a symlink resolving outside the root, a line range beyond end of file, or content that differs from the declared comparison rule is rejected

  Rule: Indexed repository text is untrusted data, not instruction.

    @SCN-1007
    Scenario: Instruction-like text stays data
      Given an indexed source file whose comments contain instruction-like text
      When the search returns a hit for that file
      Then the text is carried as data in the hit
      And it creates no link, review decision, evidence record, policy change, verification claim, or coverage claim

  Rule: Live integration evidence is explicit, attributable, and optional.

    @SCN-1008
    Scenario: Without live opt-in the probe reports NOT RUN
      Given live opt-in is not enabled
      When the capability probe runs
      Then it reports "NOT RUN" with the reason
      And it starts no CocoIndex process, accesses no CocoIndex index, and contacts no embedding endpoint
      And an offline suite that skips the live test does not satisfy a live acceptance criterion

    @SCN-1009
    Scenario: Opted-in prerequisites are unavailable
      Given live opt-in is enabled but the executable, project marker, daemon, or embedding runtime is unavailable
      When the capability probe runs
      Then it reports an explicit unavailable or failed outcome with the reason
      And it does not report a pass or substitute fake hits

    @SCN-1010
    Scenario: Opted-in execution fails
      Given live opt-in is enabled and a probe step fails
      When the capability probe runs
      Then the failure is reported with its typed error and step
      And the outcome is not reported as a pass, a skip, or a successful offline result

    @SCN-1011
    Scenario: An opted-in synthetic smoke is attributable
      Given explicit live opt-in, an installed CocoIndex release, a reachable embedding runtime, and a pinned synthetic fixture snapshot
      When that snapshot is indexed and the capability probe searches it for a hand-selected source-code target
      Then at least one returned path and line range exists at the recorded snapshot revision
      And the returned content equals that snapshot's lines for the range after removing a single trailing newline
      And the report records the CocoIndex version, embedding model, adapter revision, snapshot revision and content hashes, index isolation configuration, indexing outcome, server-reported index identity or explicit unavailability, latency, observed result fields, invocation, and raw report digest
      And the report claims a bounded integration observation only, not retrieval quality or requirement verification
