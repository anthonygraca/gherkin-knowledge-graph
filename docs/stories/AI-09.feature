# Canonical acceptance specification for AI-09 (#70), PR 4 benchmark (M4-style evidence).
# Scope supplied by the owner's PR 4 mission prompt; scenarios drafted by OMP.
@AI-09 @issue-70 @M4
Feature: AI-09: Evidence-grounded retrieval benchmark
  The benchmark compares lexical code retrieval (A), CocoIndex code retrieval (B), accepted-graph
  answers (C), and hybrid graph+semantic answers (D). It measures; it does not claim M4 completion.

  Rule: A and B use identical inputs

    @SCN-2501
    Scenario: Code retrieval baselines share snapshot, queries, and labels
      Given the code-retrieval evaluation capture
      When the benchmark report is generated
      Then the report names the same labels hash for A and B
      And both method sections use the hand-labeled code cases
      And no metric is fabricated for a method that did not run

  Rule: Graph answers are scored against hand-labeled expectations

    @SCN-2502
    Scenario: Accepted-graph answers match the labeled cases
      Given the evidence-answer labels
      When the benchmark evaluates accepted-graph answers
      Then status, accepted links, evidence, findings, and graph paths match every labeled case
      And citation accuracy is one
      And unsupported assertions are zero

    @SCN-2503
    Scenario: Hybrid answers keep semantic candidates outside the graph
      Given the evidence-answer labels
      When the benchmark evaluates hybrid answers
      Then the authoritative fields match the accepted-graph method
      And semantic candidates are reported separately
      And every graph path remains accepted-only

  Rule: The report is reproducible and bounded

    @SCN-2504
    Scenario: The report records its inputs and limits
      Given the benchmark report
      Then it records the labels, code-evaluation capture, and answer-label hashes
      And it states that C and D receive additional graph information
      And it does not claim M4 or M3 completion
