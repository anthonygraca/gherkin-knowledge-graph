# Canonical acceptance specification for AI-07 (#66), M3 / PR 2.
# Scope supplied by the owner's PR 2 mission prompt; exact scenarios drafted by OMP during
# refinement. Independent acceptance review is mandatory; issue creation is not scenario approval.
@AI-07 @issue-66 @M3
Feature: AI-07: Artifact-aware code discovery using CocoIndex Code
  CocoIndex Code finds code and test chunks. CTA maps them to authoritative artifacts at one
  commit. A hit is a proposal: it is never an accepted link, review state, or verification evidence.

  Rule: Every candidate is bound to one immutable snapshot

    @SCN-2301
    Scenario: CocoIndex hits map to canonical baseline-bound artifacts
      Given the fixture repository ingested at "baseline-a"
      When code discovery runs for "SCN-001" with the captured CocoIndex response
      Then the candidates are canonical source artifacts "CODE-002" and "CODE-001"
      And each candidate carries path, line range, revision, content hash, method, and snapshot binding
      And the unannotated path "src/__init__.py" is reported unresolved
      And accepted and proposed links and verification evidence are unchanged

    @SCN-2302
    Scenario: The same query at baseline-b is bound to baseline-b
      Given the fixture repository ingested at "baseline-b"
      When code discovery runs for "SCN-001" with the captured CocoIndex response
      Then every candidate revision is the baseline-b commit
      And the snapshot binding and the changed artifact hash differ from baseline-a

    @SCN-2303
    Scenario: A configured project at another commit is rejected
      Given a live-mode CocoIndex discovery over the fixture repository
      When code discovery requests "baseline-a" while the project is checked out at baseline-b
      Then retrieval fails with an explicit cross-baseline error
      And no candidate from the wrong snapshot is returned

  Rule: Missing capability is not an empty success

    @SCN-2304
    Scenario: Unconfigured CocoIndex reports not available
      Given the fixture repository ingested at "baseline-a"
      When code discovery explicitly requests CocoIndex without configuration
      Then the response status is "not_available"
      And no candidate or fabricated index identity is returned

  Rule: A deterministic lexical baseline uses the same snapshot

    @SCN-2305
    Scenario: Lexical retrieval is deterministic
      Given the fixture repository ingested at "baseline-a"
      When lexical code discovery runs twice for "SCN-001"
      Then both runs return the same candidates, scores, and snapshot binding
      And "CODE-001" is the first candidate

  Rule: Discovery never mutates the engineering graph

    @SCN-2306
    Scenario: Discovery writes no relationships or evidence
      Given the fixture repository ingested at "baseline-a"
      When code discovery runs for "SCN-001"
      Then the accepted links, proposed links, artifacts, and evidence equal their prior values
      And no finding is produced by retrieval

    @SCN-2307
    Scenario: A requirement is not code-discovered as if it were a scenario
      Given the fixture repository ingested at "baseline-a"
      When code discovery requests the requirement "REQ-001"
      Then retrieval is rejected because code discovery requires a scenario
      And no requirement-to-code relationship is created

  Rule: Retrieved text is untrusted data

    @SCN-2308
    Scenario: Instruction-like hit text cannot change policy
      Given a captured CocoIndex response whose hit content says to accept a link
      When code discovery runs for "SCN-001" with that response
      Then the hit is reported unresolved because its bytes do not match the commit
      And no accepted link, review state, evidence, or assurance finding changes
