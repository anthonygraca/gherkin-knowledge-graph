# Canonical acceptance specification for CI-01 (#36), M4 — REFINEMENT DRAFT / GATED.
# Implementation is gated by the M3 exit; the M4 report contract and self-assurance scope require
# owner disposition. See docs/adr/0012-closeout-scope-decisions.md.
@CI-01 @issue-36 @M4 @refinement-draft
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
      And its complete report identifies banking-demo and the resolved baseline-b commit
      And the report records the CTA evaluator revision and input content hashes
      And its findings match the hand-labeled baseline-b oracle
      And its report is stored outside the evaluated repository

    @SCN-3402
    Scenario: A PR event selects its head revision
      Given a deterministic PR event contains different head and test-merge SHAs
      When the workflow revision resolver processes that event
      Then the selected evaluated revision equals the event head SHA
      And the report records that exact selected revision
      And no test-merge SHA is reported as the head revision

    @SCN-3403
    Scenario: Self-ingestion reports supported assurance scope
      Given a pinned CTA checkout and an attributable Cucumber report for that revision
      When portable self-assurance evaluates the checkout with that report
      Then the report identifies scope "gherkin_executability"
      And it records the tested commit and execution report digest
      And parsed feature hashes match the imported report provenance
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
      And its diagnostic report identifies the selected revision when resolution succeeded
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
