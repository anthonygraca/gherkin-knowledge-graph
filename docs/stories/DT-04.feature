# Canonical acceptance specification for DT-04 (#23), M1.
# Source criteria: the GitHub story intake at
# https://github.com/anthonygraca/gherkin-knowledge-graph/issues/23 (verified 2026-11-13T03:12:49Z)
# and roadmap §6 F-03. Failure, boundary, and cutover scenarios were added during refinement; the
# two intake scenarios keep their wording.
# Verified by the pytest selectors mapped in DT-04.md and executed by the Cucumber suite (bdd/)
# from M2 onward.
@DT-04 @issue-23 @M1
Feature: DT-04: Retrieve the thread associated with a requirement
  A thread is assembled from the ingested revision: the requirement, the accepted links reachable
  from it, the artifacts those links reach, and the evidence for the scenarios and tests in the
  thread. Proposals remain a separate array. The response is independent of tag-vs-SHA wording and
  of any precomputed example file.

  @SCN-611
  Scenario: Thread for a fully linked requirement
    Given the fixture repository is ingested at "baseline-b"
    When the thread for "REQ-001" is requested
    Then the response contains "REQ-001", "SCN-001", "CODE-001", and "TEST-001"
    And the accepted links "LNK-001", "LNK-002", and "LNK-003"
    And the evidence recorded for "SCN-001"
    And the response is identical whether the baseline is given as the tag or the commit SHA

  @SCN-612
  Scenario: Thread for a requirement with only a proposal
    Given "REQ-002" has no accepted links
    When the thread for "REQ-002" is requested
    Then "accepted_links" is empty
    And "LNK-007" appears only in "proposed_links"

  @SCN-613
  Scenario: The thread is assembled from the ingested revision
    Given the committed thread example files are unavailable
    When the thread for "REQ-001" is requested
    Then the same thread is served from parsed repository data
    And its schema_version matches the running contract

  @SCN-614
  Scenario: Unknown and non-requirement roots are documented 404s
    Given "REQ-999" does not exist
    When its thread is requested
    Then the response is 404 "artifact-not-found"
    And a thread for an existing source artifact "CODE-001" is 404 "thread-not-found"

  @SCN-615
  Scenario: Re-ingesting a revision reports what it found
    Given the fixture repository at "baseline-a"
    When an ingestion run is requested
    Then it reports the artifact, accepted-link, proposed-link, and evidence counts
    And its run id is deterministically derived from the resolved commit

  @SCN-616
  Scenario: Artifact inventory for a baseline
    Given the fixture repository is ingested at "baseline-a"
    When artifacts are listed for that baseline
    Then every requirement, scenario, source, and test artifact is returned
    And filtering by artifact type returns only that type
