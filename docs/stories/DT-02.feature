# Canonical acceptance specification for DT-02 (#21), M1.
# Source criteria: the GitHub story intake at
# https://github.com/anthonygraca/gherkin-knowledge-graph/issues/21 (verified 2026-11-13T02:01:06Z)
# and roadmap §6 F-02. Failure and boundary scenarios were added during refinement; the two intake
# scenarios keep their intent.
# Verified by the pytest selectors mapped in DT-02.md. These scenarios are not currently bound
# to or executed by a Gherkin runner.
@DT-02 @issue-21 @M1
Feature: DT-02: Source and test artifacts tied to path and Git revision
  A Python file declares itself as a source or test artifact with a first-line
  `# cta:artifact CODE-nnn` / `TEST-nnn` annotation. Ingestion reads the committed blob at the
  requested revision, so revisions and content hashes describe what Git holds, not what the
  working tree happens to contain.

  @SCN-521
  Scenario: Source artifact declared by in-file annotation
    Given "src/accounts.py" begins with the annotation "# cta:artifact CODE-001"
    When the repository is ingested at "baseline-b"
    Then artifact "CODE-001" has type "source" and locator "src/accounts.py"
    And its revision is the commit tagged "baseline-b"
    And its content_hash differs from the same artifact at "baseline-a"

  @SCN-522
  Scenario: Files without an annotation are not artifacts
    Given "src/__init__.py" has no cta:artifact annotation
    When the repository is ingested
    Then no artifact references "src/__init__.py"

  @SCN-523
  Scenario: Test artifact declared by in-file annotation
    Given "tests/test_accounts.py" begins with "# cta:artifact TEST-001"
    When the repository is ingested at "baseline-a"
    Then artifact "TEST-001" has type "test" and locator "tests/test_accounts.py"
    And its content_hash is the sha256 of the committed blob

  @SCN-524
  Scenario: An annotation that is not on the first line is rejected
    Given a Python file whose annotation appears after its first line
    When the repository is ingested
    Then ingestion fails with an error naming that file

  @SCN-525
  Scenario: A file cannot declare two artifact identities
    Given a Python file containing two different cta:artifact annotations
    When the repository is ingested
    Then ingestion fails with an error naming the conflicting identities

  @SCN-526
  Scenario: Content hashes come from the committed revision
    Given an ingested revision with a clean working tree
    When a file is modified in the working tree without committing
    Then re-ingesting the same revision returns the committed content_hash
    And the artifact revision is unchanged

  @SCN-527
  Scenario: Every declared artifact matches the committed snapshot at both baselines
    Given the fixture repository built from its declarative history
    When each tagged baseline is ingested
    Then the artifact ids, types, titles, locators, revisions, and content hashes equal
      "fixtures/api-responses/snapshot.json" for that baseline
