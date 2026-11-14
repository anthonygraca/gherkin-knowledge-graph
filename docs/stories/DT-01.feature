# Canonical acceptance specification for DT-01 (#20), M1.
# Source criteria: the GitHub story intake at
# https://github.com/anthonygraca/gherkin-knowledge-graph/issues/20 (verified 2026-11-13T00:52:26Z)
# and roadmap §6 F-02. Failure and boundary scenarios were added during refinement; the two
# intake scenarios keep their original wording.
# Verified by the pytest selectors mapped in DT-01.md and executed by the Cucumber suite (bdd/)
# from M2 onward.
@DT-01 @issue-20 @M1
Feature: DT-01: Requirements and Gherkin scenarios parsed into stable artifacts
  A requirement document declares its identity in YAML front matter. A Gherkin scenario
  declares its identity with an @SCN-nnn tag. Ingestion reads the repository at a pinned
  revision, never the working tree, and rejects malformed declarations instead of skipping
  them silently.

  @SCN-501
  Scenario: Requirement document parsed into an artifact
    Given the fixture repository checked out at "baseline-a"
    When the requirements are ingested
    Then an artifact "REQ-001" of type "requirement" exists with title "Instant withdrawal availability"
    And its locator is "requirements/REQ-001.md"
    And its content_hash is the sha256 of the file bytes at that revision
    And its metadata records status "active"

  @SCN-502
  Scenario: Scenario identity comes from the Gherkin tag
    Given "features/withdrawals.feature" contains the tag "@SCN-001"
    When the scenarios are ingested
    Then an artifact "SCN-001" of type "scenario" exists with locator "features/withdrawals.feature#SCN-001"
    And its title is the scenario name from the feature file
    And unannotated files produce no artifacts

  @SCN-503
  Scenario: A requirement without front matter is rejected
    Given a repository revision where "requirements/BROKEN.md" has no front matter block
    When the revision is ingested
    Then ingestion fails with an error naming "requirements/BROKEN.md"
    And no partial artifact set is returned

  @SCN-504
  Scenario: An untagged scenario creates no artifact
    Given a feature file containing a scenario without an "@SCN-nnn" tag
    When the scenarios are ingested
    Then no artifact is created for that scenario

  @SCN-505
  Scenario: A dangling scenario tag is rejected
    Given a feature file where "@SCN-999" is not followed by a "Scenario:" line
    When the scenarios are ingested
    Then ingestion fails with an error naming "@SCN-999"

  @SCN-506
  Scenario: Duplicate artifact identities are rejected
    Given two requirement documents declare the same id "REQ-900"
    When the revision is ingested
    Then ingestion fails with an error naming "REQ-900"

  @SCN-507
  Scenario: A symbolic revision is resolved once for the whole scan
    Given the fixture repository has tag "baseline-a" at a full commit SHA
    When the revision is ingested by tag name
    Then every artifact revision is that full commit SHA
    And ingesting the same revision by its SHA returns identical artifacts

  @SCN-508
  Scenario: Scenario-like text inside a doc string is data
    Given a tagged scenario whose step contains a doc string with "@SCN-999" and "Scenario: not real"
    When the scenarios are ingested
    Then only the real tagged scenario becomes an artifact
    And an opening delimiter line never also closes the same doc string
    And an unterminated doc string is an error

  @SCN-509
  Scenario: A malformed scenario identity token is rejected
    Given a scenario tagged "@SCN-99"
    When the scenarios are ingested
    Then ingestion fails with an error naming "@SCN-99"

  @SCN-510
  Scenario: Quoted front matter values keep their meaning
    Given a requirement whose id and status are quoted YAML strings with a trailing comment
    When the requirement is ingested
    Then the id is "REQ-900" without quotation marks
    And the status is "superseded" without the comment
    And a quoted title is stored without quotation marks

  @SCN-511
  Scenario: Invalid YAML front matter is rejected
    Given a requirement whose front matter has an unterminated quoted title
    When the revision is ingested
    Then ingestion fails with an error naming the file and the YAML problem
