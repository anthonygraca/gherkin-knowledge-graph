# Canonical acceptance specification for AI-05 (#35), M3.
# Criteria extracted from the issue body and roadmap §6; independent review required.
@AI-05 @issue-35 @M3
Feature: AI-05: Labeled precision/recall and recall@k evaluation of retrieval
  Retrieval quality is measured against hand-labeled fixture candidates, never treated as
  expected values inside rule tests.

  Rule: Metrics come from labeled pairs

    @SCN-2601
    Scenario: A provider is measured against the labeled candidate index
      Given the labeled candidate index with positive and negative labels
      When the evaluation harness runs for the fake provider
      Then it reports recall@1, recall@5, recall@10, precision@k, MRR, and the false-candidate rate
      And the report records the provider, model version, and index revision
      And the report records the dataset hash and per-source results

    @SCN-2602
    Scenario: Reports retain the dataset revision they used
      Given a completed evaluation report
      When the labeled dataset changes
      Then the previous report remains with its recorded dataset hash
      And a new report names the new hash

    @SCN-2603
    Scenario: The harness runs offline with the fake provider
      Given no network, model, or vector service
      When the evaluation harness runs
      Then it completes using only the fixture candidate index
