# Canonical acceptance specification for FT-03 (lifecycle adoption); see FT-03.md for the
# verification map, the analysis procedures and the recorded author checks.
# These scenarios are verified by inspection/analysis, not by a Gherkin runner.
@FT-03 @issue-39 @M0
Feature: FT-03: Establish lifecycle traceability and Gherkin acceptance specifications
  As a project contributor, I want requirements, story acceptance criteria, implementation
  and verification evidence connected through a documented lifecycle, so that each change
  has a reviewable engineering basis.

  Rule: Each refined story keeps one authoritative acceptance specification

    @SCN-401
    Scenario: A refined story points to its canonical criteria
      Given the refined stories "FT-01" and "FT-02" have canonical criteria files under "docs/stories/"
      When a contributor needs the current acceptance criteria of "FT-01" or "FT-02"
      Then "docs/stories/FT-01.feature" and "docs/stories/FT-02.feature" carry the normative scenario wording
      And the M0 index cites each criterion as a link to its canonical scenario rather than restating the steps
      And the user-story issue form asks for the canonical acceptance specification before implementation

    @SCN-402
    Scenario: Migrated criteria keep their wording and their labels
      Given the M0 acceptance criteria recorded in "docs/stories/M0-foundation.md" at revision "efa824b5"
      When each migrated scenario in "FT-01.feature" and "FT-02.feature" is compared with that record
      Then every scenario title and step matches its source after leading indentation is removed
      And each scenario retains its original "AC-1.x" or "AC-2.x" label as a tag
      And the migrated scenarios number eight for "FT-01" and five for "FT-02"

  Rule: Every canonical scenario names how it will be verified

    @SCN-403
    Scenario: Each M0 scenario maps to a check that exists
      Given the canonical M0 scenarios "SCN-101" through "SCN-108" and "SCN-201" through "SCN-205"
      When the M0 acceptance verification map is inspected
      Then every scenario appears in exactly one mapping row
      And every pytest selector in the map resolves to a test function that exists under "backend/tests/"
      And the map states that a mapping row is not an executed result or an approval

    @SCN-404
    Scenario: A missing or unresolvable mapping is reported
      Given a copy of the M0 verification map with one scenario row removed and one selector renamed to a nonexistent test
      When the documented mapping-resolution procedure is applied to that copy
      Then it reports the unmapped scenario and the unresolvable selector
      And no scenario affected by those defects is reported as mapped

  Rule: Specification, execution and approval stay separate records

    @SCN-405
    Scenario: Status records claim neither execution nor approval
      Given "FT-01.feature", "FT-02.feature" and "FT-03.feature" have no Gherkin runner bindings
      When the migrated criteria are described in "STATUS.md", the M0 index, the issue map and the migration review record
      Then each record describes their verification as the mapped pytest checks
      And none claims that the scenarios were executed as Gherkin
      And none records an independent approval of the migration

  Rule: Scenario identity stays unique and traceable

    @SCN-406
    Scenario: Scenario and file identities are unique and traceable
      Given the canonical feature files under "docs/stories/"
      When their tags are collected
      Then every "@SCN-nnn" identifier is unique across those files
      And every canonical scenario carries exactly one "@SCN-nnn" tag
      And every canonical feature file names its story ID and its GitHub issue tag
