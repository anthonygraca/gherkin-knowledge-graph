# Canonical acceptance specification for CI-01 (#36), M4.
# Specification APPROVED by docs/reviews/CI-01-spec-review-4.md; ADR 0012 §3 is accepted and the M3
# gate is approved by docs/reviews/M3-review-2.md. Report/comparison contract:
# docs/assurance-report-contract.md.
@CI-01 @issue-36 @M4
Feature: CI-01: Assurance evaluates and reports the triggering revision
  Evaluation is pinned, reproducible, offline, and independent of inference. Tool failure is not a
  finding.

  Rule: Evaluation is pinned, reproducible, and independent of inference

    @SCN-3401
    Scenario: Evaluate a pinned repository revision offline
      Given banking-demo baseline-b resolves to its fixture commit
      And dependencies are provisioned and external network access is denied
      And no model provider is enabled
      When the assurance command ingests and evaluates that commit
      Then it exits 0
      And its completed report follows the report contract and identifies banking-demo at the resolved baseline-b commit
      And the report records the CTA evaluator revision and input content hashes
      And its findings match the hand-labeled baseline-b oracle
      And its report and input manifest are stored outside the evaluated repository

    @SCN-3402
    Scenario: A PR event selects its head revision
      Given a deterministic PR event contains different head and test-merge SHAs
      When the workflow revision resolver processes that event
      Then the selected evaluated revision equals the event head SHA
      And the report records that exact selected revision
      And no test-merge SHA is reported as the head revision
      And a deterministic push event selects its non-zero after SHA
      And the selected commit is used for ingestion and evaluation, not only recorded

    @SCN-3403
    Scenario: Self-ingestion reports supported assurance scope
      Given a pinned CTA checkout and an attributable Cucumber report for that revision
      When portable self-assurance evaluates the checkout with that report
      Then the report identifies scope "gherkin_executability"
      And it records the tested commit and execution report digest
      And parsed feature hashes match the imported report provenance
      And the report's execution sources equal the imported report's feature hashes
      And coverage gaps are counted, not reported as findings
      And it makes no requirement-to-production-code verification claim

  Rule: Findings, unknown evidence, and tool failures remain distinct

    @SCN-3404
    Scenario: Recorded execution failure is an assurance finding
      Given a valid deterministic Cucumber report records a failed scenario
      And its provenance matches the evaluated repository revision
      When portable assurance ingests and evaluates that report
      Then the assurance command exits 0
      And tool_outcome is "completed"
      And an execution_failed finding identifies the failing execution
      And the report does not claim that a requirement is verified or failed

    @SCN-3405
    Scenario Outline: Tool failure cannot publish a complete successful report
      Given the assurance command encounters "<failure>"
      When the command evaluates the selected revision
      Then it exits 2
      And its diagnostic report follows the contract's incomplete envelope
      And when the report destination is unwritable the same JSON is printed on stderr
      And failure_stage and failure_code identify the failure
      And the report is marked incomplete
      And the failure is not converted into an assurance finding

      Examples:
        | failure                               |
        | an unknown repository revision        |
        | malformed execution-report provenance |
        | an unreadable required ingestion input |
        | an unwritable report destination      |

    @SCN-3406
    Scenario: Workflow publication leaves repository branches unchanged
      Given a completed deterministic assurance report contains findings
      When the workflow publishes its artifact and job summary
      Then the artifact contains the report and its input manifest
      And the summary identifies the evaluated revision and finding count
      And no commit, branch update, pull-request comment, or deployment is requested
      And tracked repository content is unchanged
      And on tool failure the workflow uploads the incomplete diagnostic with no finding
      And a valid failed Cucumber run still publishes completed execution_failed findings while the test gate remains failing
