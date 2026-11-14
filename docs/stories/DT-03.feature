# Canonical acceptance specification for DT-03 (#22), M1.
# Source criteria: the GitHub story intake at
# https://github.com/anthonygraca/gherkin-knowledge-graph/issues/22 (verified 2026-11-13T02:50:26Z)
# and roadmap §6 F-03. Failure scenarios were added during refinement; the two intake scenarios
# keep their wording.
# Verified by the pytest selectors mapped in DT-03.md and executed by the Cucumber suite (bdd/)
# from M2 onward.
@DT-03 @issue-22 @M1
Feature: DT-03: Typed, provenance-aware traceability links with review state
  Links are directional claims: requirement --verified_by--> scenario,
  scenario --implemented_by--> source, scenario --exercised_by--> test. Accepted links and
  proposals live in separate declared files and are never merged into one collection. Ingestion
  validates direction, endpoints, and declared review state; it does not mutate links.

  @SCN-601
  Scenario: Accepted relationship recorded with provenance
    Given an accepted link between "REQ-001" and "SCN-001" of type "verified_by"
    When the link is read back
    Then its review_state is "accepted"
    And its provenance records the reviewer and the decision time

  @SCN-602
  Scenario: Proposals never appear as accepted relationships
    Given "LNK-007" proposes "REQ-002" verified_by "SCN-002"
    When the links for "REQ-002" are listed
    Then "LNK-007" appears only in the proposed collection
    And the accepted collection is empty

  @SCN-603
  Scenario: A link that contradicts its relation direction is rejected
    Given a link from "CODE-001" to "SCN-001" of type "verified_by"
    When the revision is ingested
    Then ingestion fails with an error naming the link and the expected direction

  @SCN-604
  Scenario: A link to an unknown artifact is rejected
    Given a link whose target "SCN-999" does not exist at the revision
    When the revision is ingested
    Then ingestion fails with an error naming "SCN-999"

  @SCN-605
  Scenario: A link file declaring the wrong review state is rejected
    Given "evidence/accepted-links.json" contains a link with review_state "proposed"
    When the revision is ingested
    Then ingestion fails with an error naming the file and the link

  @SCN-606
  Scenario: Repeated ingestion returns identical link facts
    Given a revision with accepted and proposed links
    When the revision is ingested twice
    Then the link ids, review states, provenance, and timestamps are identical
    And no decision history is rewritten
