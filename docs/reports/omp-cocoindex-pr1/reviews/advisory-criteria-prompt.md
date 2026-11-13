# AI-06 criteria advisory (not an implementation acceptance review)

You are advising on a proposed canonical Gherkin acceptance specification before implementation.
This is an advisory call, not an acceptance verdict, and it does not count against the mission's
seven implementation-review submissions. Do not edit files, commit, or delegate. Read-only.

## Context

- Repository: CTA (Continuous Traceability Assurance), `anthonygraca/gherkin-knowledge-graph`.
- Story: AI-06 (#56), a new implementation-approach story under F-08, slice M3. It adopts
  CocoIndex Code (`cocoindex-io/cocoindex-code`, installed 0.2.43, Apache-2.0) for semantic *code*
  search behind an optional typed adapter.
- Mission slice: "PR 1 — CocoIndex Code compatibility, integration contract, and live smoke."
  PR 1 must not register a real `CandidateDiscovery`, map hits to `TraceCandidate`s, change
  `POST /api/discovery`, touch assurance policy, or claim AI-02/AI-03/AI-05.
- Repository invariants: offline by default; proposals/accepted links/evidence separate; no LLM
  authority over deterministic assurance; evidence is revision/content-hash aware; honest
  contracts; indexed repository text is untrusted; no fabricated provenance.
- Observed MCP contract (version 0.2.43): initialize serverInfo `{name:"cocoindex-code",
  version:"0.2.43"}`; one tool `search(query, limit 1..100, offset>=0, refresh_index, languages,
  paths)`; tool result is `content[0].text` containing JSON
  `{success, results:[{file_path, language, content, start_line, end_line, score}],
  total_returned, offset, message}`. It exposes no index revision, chunk hash, or project identity.
- Planned implementation: `backend/app/discovery/cocoindex.py` (models/errors/fake
  transport/client), `backend/app/discovery/cocoindex_mcp.py` (stdio MCP transport spawning
  `ccc mcp` in a configured project root with an allow-listed env and hard deadline),
  `backend/app/settings.py` (`CTA_CCC_EXECUTABLE`, `CTA_CCC_PROJECT_ROOT`,
  `CTA_CCC_LIVE_OPT_IN`, `CTA_CCC_LIVE_TESTS`), `tools/probe_cocoindex.py`, offline contract tests,
  an opt-in live test, ADR 0008, and an integration guide. No API/schema change.
- Live smoke uses an isolated worktree of the synthetic `fixtures/banking-demo` at `baseline-a`,
  an isolated `COCOINDEX_CODE_DIR`/`COCOINDEX_CODE_RUNTIME_DIR`, localhost Ollama
  `embeddinggemma-2:270m-q8_0-text`, and a synthetic query.

## Proposed canonical specification (docs/stories/AI-06.feature)

```gherkin
@AI-06 @issue-56 @M3
Feature: AI-06: CocoIndex Code semantic code-search capability and integration contract
  As a developer, I want an optional, bounded CocoIndex Code adapter that returns attributable
  source-code hits from one pinned project snapshot, so that semantic code retrieval can be
  integrated later without weakening CTA's offline default or its separation of proposals,
  accepted relationships, and verification evidence.

  Rule: CocoIndex is optional and never required by default paths.

    @SCN-1001
    Scenario: Offline default is unchanged
      Given no CocoIndex executable, project root, daemon, or embedding endpoint is configured
      When the default configuration is loaded and a discovery request runs
      Then discovery uses the deterministic "fake" provider
      And no CocoIndex process is started
      And no index is read and no network request is made
      And "cocoindex" is not a registered discovery provider in this slice

  Rule: Search results are non-authoritative, bounded observations.

    @SCN-1002
    Scenario: A structured search returns normalized hits
      Given a configured project snapshot and a deterministic structured transport
      When the client searches for "withdraw whole dollar amounts"
      Then it returns the hits in the transport's reported order
      And every hit reports its project-relative path, language, 1-based line range, content, and score as reported
      And every hit identifies the provider and the configured project root
      And the index identity is either observed and reported or explicitly unavailable
      And no hit exposes a link id, review state, evidence id, or assurance conclusion

    @SCN-1003
    Scenario: Invalid hit data is rejected, never repaired
      Given a transport result containing an absolute path, a parent-directory escape, an empty path, or an invalid line range
      When the client normalizes the result
      Then it raises "cocoindex-protocol-error"
      And no invalid hit is dropped, clamped, or rewritten
      And no artifact identity is invented

    @SCN-1004
    Scenario: Unavailable, timed-out, and failed searches fail honestly
      Given a missing executable, a project root without CocoIndex settings, a server that does not answer, or a search reporting success false
      When a search is attempted
      Then the client raises the matching typed error
      And a spawned server is terminated within the configured timeout
      And the caller receives no fabricated hits

  Rule: The adapter touches only the configured snapshot.

    @SCN-1005
    Scenario: Search is confined to the configured snapshot
      Given a project root containing CocoIndex settings and a list of path filters
      When the client searches
      Then the server runs with that project root as its working directory
      And absolute, parent-escaping, or non-glob path filters are rejected before execution
      And the client passes only an allow-listed subprocess environment

  Rule: Indexed repository text is untrusted data, not instruction.

    @SCN-1006
    Scenario: Instruction-like text stays data
      Given an indexed source file whose comments contain instruction-like text
      When the search returns a hit for that file
      Then the text is carried as data in the hit
      And it creates no link, review decision, evidence record, policy change, or citation

  Rule: Live integration evidence is explicit, attributable, and optional.

    @SCN-1007
    Scenario: A live synthetic smoke is attributable
      Given explicit live opt-in, an installed CocoIndex release, a reachable embedding runtime, and a pinned synthetic fixture snapshot
      When that snapshot is indexed and the capability probe searches it for a source-code concept
      Then at least one returned path and line range exists at the recorded snapshot revision
      And the report records the CocoIndex version, embedding model, snapshot revision, index snapshot identity, latency, and observed result fields
      And without live opt-in the report says "NOT RUN" and does not claim a live pass
```

## Questions for the advisory

1. Is this the right *story boundary* for PR 1, given the repository's story/traceability rules and
   the explicit non-goals (no `CandidateDiscovery` registration, no `TraceCandidate` mapping, no
   API change, no claim on AI-02/AI-03/AI-05)?
2. Are the seven scenarios observable and testable without relying on implementation internals or
   invented CocoIndex fields? Identify any step that cannot be verified as written.
3. Which failure or boundary cases are missing for a bounded external-process adapter (for example
   malformed MCP envelopes, stderr handling, server version mismatch, path-filter semantics,
   content size, duplicate chunks, non-success with partial results)?
4. Is the "index identity is either observed or explicitly unavailable" wording honest and
   implementable given the observed MCP contract? Suggest precise wording if not.
5. Does any scenario accidentally imply that CocoIndex search verifies requirements, supplies
   evidence, or covers `.feature` scenarios? Flag wording that a reviewer could read as an
   overclaim.
6. Are the live/NOT RUN semantics clear enough that a missing executable or endpoint cannot be
   reported as a pass?

Return a concise advisory: criteria readiness (READY / REVISE), numbered findings with severity
(major/minor) and a concrete suggested change, and any wording you would change. Do not review the
eventual implementation; it does not exist yet.
