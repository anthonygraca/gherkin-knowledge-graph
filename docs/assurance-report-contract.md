# Assurance report and comparison contract (M4, report version 1.0)

**Status:** normative for CI-01 (#36) and CI-02 (#37). Versioned independently of the API
`SCHEMA_VERSION`; these are workflow/tool artifacts, not API bodies.

## 1. Report envelope

A report is one JSON object:

|Field|Type|Rule|
|---|---|---|
|`report_version`|string|Exactly `"1.0"`.|
|`run_id`|string|Caller-supplied or generated UUID for this invocation; retained for publication provenance.|
|`generated_at`|UTC ISO-8601|Timezone-aware timestamp.|
|`scope`|enum|`requirement_assurance` or `gherkin_executability`.|
|`repository`|string|Repository identity (`banking-demo` or the CTA repository id).|
|`identity_strategy`|string|`fixture` for the banking repository; `explicit` for the CTA checkout.|
|`baseline`|string or null|Canonical baseline for requirement assurance; null for self-assurance.|
|`evaluated_revision`|string or null|Resolved immutable commit of the **evaluated repository**. Required for a completed report; null only in an incomplete diagnostic where resolution failed.|
|`evaluator_revision`|string|CTA package version plus evaluated CTA checkout commit, e.g. `cta@0.8.0+<sha>`.|
|`policy`|string|`default`.|
|`policy_version`|string|`1`.|
|`identity_kind`|enum|`stable_fingerprint` for requirement findings; `source_locator` for portable/self-assurance findings.|
|`rule_scope`|sorted unique rule ids|The complete evaluated rule set, independent of which rules emitted findings.|
|`inputs`|list of input entries|Every required ingestion input, as defined below.|
|`coverage`|object or null|Availability/coverage counts; required for `gherkin_executability`, optional/null for requirement assurance.|
|`findings`|list of finding payloads|Empty in an incomplete diagnostic.|
|`tool_outcome`|enum|`completed` or `incomplete`.|
|`incomplete_reason`|string or null|Required non-empty when incomplete; null when completed.|
|`failure_stage`|string or null|Incomplete only: `resolution`, `input`, `report_parse`, `evaluation`, `write`, or `publication`.|
|`failure_code`|string or null|Incomplete only: a stable machine-readable code such as `revision-unknown`, `input-unreadable`, `report-malformed`, `report-unwritable`.|
|`report_digest`|string|`sha256:` over canonical JSON of this object excluding `report_digest`.|
|`execution_report`|object or null|`gherkin_executability` completed reports only; null for requirement assurance and for incomplete diagnostics.|

Canonical JSON: UTF-8, `ensure_ascii=false`, keys sorted, separators `("," ":" )`, no trailing
whitespace; digest `sha256:` of those bytes. The report digest self-reference is avoided by excluding
the `report_digest` field.

`execution_report` = `{report_digest, tested_commit, adapter, sources: [{path, digest}],
metadata_digest}`. The report consumes the existing portable importer provenance (report digest,
metadata sidecar, tested commit, source hashes); it does not trust report prose. Every imported source
digest must equal the indexed feature bytes at `tested_commit`; coverage is compared separately.

### 1.1 Input entries and input manifest

An input entry is
`{kind, id, path, revision, digest, available, required}`:

* `kind`: `artifact`, `historical_artifact`, `accepted_link_set`, `proposed_link_set`, `evidence_set`,
  `execution_report`, `provenance_sidecar`, `feature`, `fixture_manifest`, or `policy`.
* `id`/`path` identify the item; `revision` is the commit whose content was read; `digest` is
  `sha256:` over the canonical bytes, or null when unavailable; `available` is bool; `required`
  is bool.

Requirement assurance covers, with `required: true`: every evaluated artifact at
`evaluated_revision`; the accepted-link, proposed-link and evidence sets used by the rule engine
(canonical sorted JSON digests); every historical artifact content consulted for freshness
(`tested_commit` content); the fixture baselines/history input; and the policy/rule scope. Historical
inputs are revision-qualified; they are not relabelled as evaluated content.

Self-assurance covers, with `required: true`: the execution report and metadata provenance sidecar;
every indexed feature at `tested_commit`; the policy/rule scope. Optional parser diagnostics are
recorded in `coverage.diagnostics`; an unreadable **required** input is an incomplete diagnostic.

The separately published input manifest is:

`{manifest_version: "1.0", report_digest, scope, repository, baseline, evaluated_revision, entries,
diagnostics}`.

It is the report's `inputs` plus its diagnostics, and is written next to the report (outside the
evaluated repository).

### 1.2 Finding payload

Every `findings` entry has: `finding_id`, `rule_id`, `finding_type`, `severity`, `status`,
`artifact_ids`, `artifact_keys`, `artifact_revisions`, `evaluated_baseline`, `evidence_ids`,
`execution_keys`, `explanation`. Requirement findings fill `artifact_ids`, `artifact_revisions`,
`status`; portable findings fill `artifact_keys`, `execution_keys`, `status`. Empty lists are
permitted for the fields a scope does not use.

`finding_id` is the existing fingerprint over `(rule_id, finding_type, sorted artifact ids or
artifact keys)`. `status`, baseline, evidence, execution keys, prose, severity, and artifact revisions
are excluded, so an unchanged problem keeps identity across revisions and explanation edits. The full
payload is the retained before/after value in CI-02; retention is exact field-value equality of this
serialized payload, not source-byte preservation, and neither payload is rewritten.

“Findings match the oracle” means the requirement finding payloads equal the hand-labeled expected
fields the oracle declares: rule id, finding type, severity, status, sorted artifact ids, evaluated
baseline, evidence ids, artifact revisions, and finding id. Prose may differ only if the oracle marks
prose as unasserted; the fixture oracle tests compare the canonical fields.

### 1.3 Coverage and completeness

`coverage` = `{available, features_indexed, features_covered_by_report, scenarios_total,
scenarios_executed, scenarios_skipped, scenarios_unknown, diagnostics: [string]}`.

A report is `completed` iff: the evaluated revision resolved; every required input was readable and
digested; the evaluator ran; the report and manifest were written. Findings may be non-empty; exit
`0`. A valid report may cover a subset of indexed features; the missing count is recorded, not
converted into a finding or an undefined-step defect.

|Situation|Outcome|
|---|---|
|No execution report / report unreadable / metadata missing for self-assurance|`incomplete`, exit `2`, `failure_stage="input"`, no findings|
|Malformed report or provenance mismatch|`incomplete`, exit `2`, `failure_stage="report_parse"`, no findings|
|Unknown evaluated revision|`incomplete`, exit `2`, `failure_stage="resolution"`, `evaluated_revision=null`|
|Unreadable required ingestion input|`incomplete`, exit `2`, `failure_stage="input"`, that input `available=false`/`digest=null`|
|Valid report with partial coverage|`completed`, exit `0`; coverage counts; findings only for observed facts|
|Skipped/unknown executions|`completed`, exit `0`; coverage counts; no execution failure finding|
|Non-required feature diagnostic|`completed`, exit `0`; diagnostic in `coverage`; no finding|
|Report destination unwritable|`incomplete`, exit `2`, `failure_stage="write"`; JSON on stderr; no completed report at the destination|

Absent evidence creates neither execution evidence nor an undefined-step defect. Banking freshness
remains content-based; the report does not change that rule.

### 1.4 Incomplete diagnostic

An incomplete diagnostic uses the same envelope with `tool_outcome="incomplete"`,
`incomplete_reason`, `failure_stage`, `failure_code`, `findings=[]`, and `execution_report=null`.
`evaluated_revision` and `baseline` are null only when resolution failed; otherwise they are the
resolved values. `inputs` include the entries known at failure, with `available=false`/`digest=null`
where unreadable. It is never converted into a finding. If it can be written, it is written atomically
(temp file in the destination directory, then replace); if the destination is unwritable, exactly one
JSON object is printed on stderr.

## 2. Revision resolution and workflow matrix

`resolve_evaluated_revision(event)`:

* `pull_request` → `pull_request.head.sha`; never `merge_commit_sha`/the synthetic test merge.
* `push` → the non-zero `after` commit, else the workflow `github.sha`.
* dispatch/input → the supplied full commit, else `github.sha`.

The workflow has two jobs with distinct repositories:

|Job|Evaluated repository|Evaluated revision|Scope|Evaluator revision|
|---|---|---|---|---|
|`banking-assurance`|`banking-demo`|pinned canonical `baseline-b` commit|`requirement_assurance`|the CTA event head/after selected for this run|
|`self-assurance`|CTA checkout|the CTA event head/after|`gherkin_executability`|the same CTA event head/after|

The event-selected SHA is not a commit in the generated banking repository; it is the evaluator
revision there. The self-assurance job evaluates the CTA checkout at the event SHA. The workflow
publishes both reports/manifests and a job summary naming each evaluated/evaluator revision and
finding count. Supported triggers are `pull_request` (opened/synchronize/reopened/edited), `push` to
main, and `workflow_dispatch`; hosted event/run/report evidence is required.

## 3. Comparison eligibility

CI-02 compares only two **completed, comparable** reports. Both must have:

* `tool_outcome=completed` and a non-null `evaluated_revision`;
* the same `scope`, `repository`, `policy`, `policy_version`, `evaluator_revision`, and exact
  `rule_scope`;
* every finding's `evaluated_baseline` equal to its **containing report's** `evaluated_revision`;
  older evidence `tested_commit` values may differ and are not compared;
* `identity_kind=stable_fingerprint`;
* each report's `report_digest` must equal the canonical digest recomputed over that report excluding
  the `report_digest` field; a missing/malformed/mismatched digest is a refusal naming that side;
* unique finding identities; each supplied `finding_id` must equal the fingerprint recomputed from
  rule id, finding type, and sorted artifact ids/keys. A mismatch or duplicate (including identical
  duplicates) is a refusal; payloads are never rewritten.

Evaluated revisions may differ (that is the point of the diff); evaluator revisions must match
exactly. A change of evaluator code requires a regenerated compatible report pair or a future
versioned compatibility rule.

`source_locator` identities have no stable cross-revision identity. This slice implements no
continuity mapping; any source-locator report is refused, and a claimed mapping is not trusted. A
future reviewed mapping needs its own additive ADR/contract.

A non-comparable pair exits `2` with:
`{diff_version: "1.0", tool_outcome: "incomplete", code: "findings-not-comparable",
invalid_input: "previous" | "current" | "both", reason: <non-empty>, classifications: null}`.
No new/unchanged/resolved keys or lists are produced. `invalid_input` identifies the offending side;
`"both"` when both fail. Conditions: missing previous/current resolved revision, previous/current
incomplete, repository identity differs, evaluated rule scopes differ, policy versions differ,
evaluator revisions differ, a finding baseline contradicts its report, duplicate/inconsistent
identity, a report digest mismatch, or source-locator identity. Finding-baseline and report-digest
validation run on both sides.

## 4. Comparison output and ordering

A successful diff exits `0` and writes:
`diff_version`, `previous_revision`, `current_revision`, `previous_report_digest`,
`current_report_digest`, `repository`, `scope`, `policy`, `policy_version`, `evaluator_revision`,
`rule_scope`, `new` (finding payloads), `unchanged` (`{finding_id, before, after}`), `resolved`
(finding payloads), and `counts`. All lists are sorted by `finding_id`; the unchanged pairs retain
the full before and after payloads without rewriting either.

Classification is by `finding_id`: current-only → new; previous-only → resolved; both → unchanged.
Absence from the current comparable set is the only meaning of resolved; no verification evidence,
accepted link, or requirement verdict is created. Payload-only changes stay unchanged. Comparing a
report with itself is 0 new / 0 resolved / all unchanged. Empty completed reports compare as
0/0/0. Artifact-id reordering/deduplication keeps the fingerprint; changing a fingerprint component
yields a new current finding and a resolved previous finding.

The banking fixture must produce exactly: baseline-a → baseline-b = **2 new / 4 unchanged /
0 resolved** (`reverification_required`, `verification_failed`); reverse = **0 new / 4 unchanged /
2 resolved**; self = **0 new / 4 unchanged / 0 resolved**.

This envelope is the M4 benchmark comparison format; benchmark reports cite or embed this diff with
`diff_version=1.0`.

## 5. Workflow publication

The assurance workflow runs with `permissions: contents: read`, installs frozen dependencies, and
never commits, pushes, updates a branch, comments on a pull request, or deploys. It writes the report
and input manifest to run-unique paths under `$RUNNER_TEMP`, appends a job summary naming each
evaluated/evaluator revision and finding count, and uploads the report, manifest, and captured stderr
diagnostic (`if: always()`). The CLI writes reports atomically and removes/avoids a stale completed
destination: a failed run's diagnostic is on stderr and must not be published as a completed report
from an earlier run.

A failing Cucumber acceptance gate does **not** suppress assurance/publication: the self-assurance
job uses `needs: [bdd]` with `if: always()`, downloads the valid failing report artifact, produces
completed findings (including `execution_failed`), exits `0`, and publishes. The original BDD job
remains failed; the assurance job does not mask or rewrite it. If artifact/summary publication
fails, the assurance job is marked failed, but the evaluator's `tool_outcome` in the report is not
rewritten; publisher failure is not an evaluator failure.
