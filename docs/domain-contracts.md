# Domain contracts

Everything here is versioned by `SCHEMA_VERSION` in `backend/app/version.py`.
**MINOR** = additive (new optional field, enum member, error type, endpoint). **MAJOR** =
removed or renamed field, changed meaning, changed relation direction, changed fingerprint
inputs. Fixture and response files declare the version they implement; loaders reject mismatches.

## Artifact identity

| Concept | Rule |
| --- | --- |
| `artifact_id` | `REQ-nnn` \| `SCN-nnn` \| `CODE-nnn` \| `TEST-nnn`. Stable across revisions. |
| Declaration | requirement: YAML front matter `id:` in `requirements/*.md`; scenario: Gherkin tag `@SCN-nnn`; source/test: first-line annotation `# cta:artifact CODE-nnn` / `TEST-nnn`. Unannotated files are not artifacts. |
| `artifact_type` | `requirement` \| `scenario` \| `source` \| `test` |
| `locator` | `"<path>"`, or `"<path>#<anchor>"` when one file holds several artifacts (scenarios inside a feature file). |
| `source_uri` | Absolute URI of the authoritative source; fixtures use `fixture://<repository>/<path>`. |
| `revision` | Immutable revision the artifact was read at (fixture: git commit SHA). Provenance, not a freshness key. |
| `content_hash` | `sha256:<hex>` of the artifact bytes at `revision`. **Freshness is decided on this.** |
| `metadata` | Free-form scalars. `metadata.status = active \| superseded` on requirements drives the lifecycle rule. |

Rationale for hashes over revisions: each fixture baseline is two commits (source, then the CI
evidence commit). Comparing revisions would make the evidence-only commit look like a source
change; comparing `content_hash` does not. The same reasoning applies to any repository where
CI commits metadata after a verified revision.

## Baselines and revisions

* A **baseline** is a revision expression: a fixture tag (`baseline-a`) or a commit SHA.
* Requests accept either. Responses report the canonical baseline name when the revision resolves
  to a known baseline, otherwise the SHA, so tag and SHA calls return identical bodies.
* Version-pinning fields (`Artifact.revision`, `Finding.evaluated_baseline`) always carry the
  resolved commit SHA.
* Multiple baseline snapshots coexist in the fixture snapshot; later workstreams add the
  ingestion and query paths that populate them.
* Every loader of contract-bearing fixture data checks `schema_version` and refuses to serve a file
  written against another version (`fixture-data-invalid`, 500). Serving mixed contract versions is
  a defect, not a compatibility mode.
* `ArtifactRepository` is the consumer-facing read contract: `baselines`, `resolve_baseline`,
  `commit_of`, `get_artifact`, `list_artifacts`, `list_links`, `list_evidence`,
  `changed_artifacts`. `resolve_baseline` is the display identity (tag when known); `commit_of`
  returns the resolved SHA that evidence and findings are pinned to. The M0 mock satisfied the
  port; the M1 store implements it over ingested Git data and passes the same contract tests.

## Relations

Direction is `source --relation_type--> target`:

| Relation | Direction | Meaning |
| --- | --- | --- |
| `verified_by` | requirement → scenario | The scenario supplies verification for the requirement. |
| `implemented_by` | scenario → source | The source artifact implements the scenario. |
| `exercised_by` | scenario → test | The test exercises the scenario. |

Adding a relation type is an additive contract change: enum, docs, oracle, and tests in one
change. Direction ambiguity is a bug — discovery is anchored on `source_id`.

Ingestion validates every declared link: the file's `schema_version` must match, its
`review_state` must match the file name, ids must be unique within and across the accepted and
proposed files, both endpoints must exist at the revision, and the source/target artifact types
must equal `RELATION_DIRECTION[relation_type]`. A violation fails ingestion; links are never
silently dropped. The table in `app/domain/enums.py` is the executable form of this section.

## Review states

`proposed` → `accepted` | `rejected`. Only humans (or the fixture) set these. Consequences:

* `TraceCandidate` (a proposal from discovery) carries **no** link id and **no** review state.
* Response shapes keep `accepted_links` and `proposed_links` in separate arrays.
* Accepting a link never changes verification status; a link is a claim about intent, evidence is a
  recorded execution.

## Verification evidence

`VerificationEvidence` = `evidence_id` (`EV-nnn`), `test_id`, optional `scenario_id`, `result`
(`passed` | `failed` | `skipped`), `tested_commit`, `executed_at` (UTC), `run_uri`.

Evidence is recorded per execution and never overwritten: several runs of the same test at
different revisions coexist, and rules select the most recent relevant one. In the fixture, CI
evidence is committed to the fixture repository for reproducibility; conceptually it arrives from
a CI system identified by `run_uri`, and the record shape is identical.

## Candidates

`TraceCandidate` = `source_id`, `target_id`, `proposed_relation_type`, `rank` (1-based within the
response), `score` (0..1), `discovery_provider`, `model_version`, `index_revision`, optional
`rationale`.

* Ranking is the provider's; `rank` is recomputed after `top_k` trimming and relation filtering.
* `index_revision` is the content fingerprint of the index that produced the candidate
  (convention `sha256:<hex>`). Candidates from different index revisions must never be mixed.
* Evaluation labels (`positive` / `negative`) live only in the fixture index file, are never
  returned by the API, and never filter results: a plausible-but-wrong suggestion must reach the
  reviewer so it can be rejected.

## Findings

`AssuranceFinding` = `finding_id`, `finding_type`, `status`, `severity`, `artifact_ids`,
`evaluated_baseline`, `evidence_ids`, `explanation`, `rule_id`, `artifact_revisions`.

| Rule id | Finding type | Severity | Inputs |
| --- | --- | --- | --- |
| `RULE-MISSING-VERIFICATION-LINK` | `missing_verification_link` | high | requirement without an accepted `verified_by` link |
| `RULE-MISSING-IMPLEMENTATION-LINK` | `missing_implementation_link` | medium | scenario without an accepted `implemented_by` link |
| `RULE-REVERIFICATION-REQUIRED` | `reverification_required` | medium | accepted chain + passing evidence + changed content since that evidence + no later evidence |
| `RULE-VERIFICATION-FAILED` | `verification_failed` | high | recorded failing execution at the evaluated baseline |
| `RULE-CANDIDATE-PENDING-REVIEW` | `candidate_pending_review` | low | stored link with `review_state=proposed` |
| `RULE-LIFECYCLE-SUPERSEDED` | `lifecycle_review_required` | medium | requirement with `metadata.status=superseded` that still has accepted links |

Severity and type come from the policy tables in `app/domain/policy.py`; the oracle is asserted
against those tables, so changing the policy is a deliberate, reviewed edit.

M2 implements all six rules. `GET /api/findings` and `POST /api/assurance/evaluate` evaluate the
same rule set over the ingested revision; neither replays a recorded sample. The evaluator is
compared field-by-field with the hand-labeled oracle (`backend/tests/test_m2_assurance.py`),
including explanation text, severity policy, artifact revisions, and fingerprints.

**Fingerprint.** `finding_id = "FND-" + sha256(rule_id | finding_type | sorted artifact_ids)[:16]`
with `sha256` truncated to 16 hex characters. It deliberately excludes the baseline, the evidence
set, and all prose, so the same underlying problem keeps one identity across baselines — which is
what makes new/unchanged/resolved diffing (M4) possible — and so editing an explanation does not
manufacture a new finding.

**`artifact_revisions`** pins each referenced artifact to the revision it had at
`evaluated_baseline`, giving drill-down a version-aware anchor without inventing a second
baseline field: the evaluated baseline is the finding's, the previously verified revision is the
referenced evidence's `tested_commit`.

### Evidence state model and precedence (M2, implemented)

Inputs: the evaluated baseline and its resolved commit; accepted links at that baseline; evidence
records with `result`, `tested_commit`, `executed_at`, and `run_uri`; and artifact content hashes at
both the evaluated baseline and each evidence record's `tested_commit`.

| State | Meaning | Finding |
| --- | --- | --- |
| No accepted verification link | The requirement has no accepted scenario | `missing_verification_link` |
| No execution evidence | Nothing has run for the scenario | none; coverage absence is visible in counts, not a defect |
| Confirmed failure | A run that applies to the evaluated content failed (latest run for the scenario) | `verification_failed` |
| Reverification required | The latest run passed, relevant content changed since `tested_commit`, no later run | `reverification_required` |
| Current / applicable evidence | Latest run passed and relevant content hashes match | none |
| Unknown applicability | The tested commit cannot be read, or the graph is incomplete | none; never converted into a failure |

Precedence: for one scenario, an applicable failing latest run wins and suppresses
`reverification_required`. A stale pass is never reported as a failure, and a missing link is
independent of evidence. Applicability is decided by **content hashes**, not SHA equality: a run
recorded at a source commit applies to the later evidence-only commit because the artifact bytes are
identical. `label_of(commit)` maps a source commit to its baseline name by content equality so prose
says "passed at baseline-a", not a bare SHA.

### Freshness rule as implemented (assumptions declared)

```text
for each scenario S with an accepted chain:
    runs = evidence whose scenario_id == S, ordered by executed_at desc
    latest = runs[0] if any
    if latest.result == failed and latest covers the evaluated content:
        emit verification_failed          (a confirmed failure)
    if latest.result == passed and any of {S's file, its implementation files, its test files}
       has a different content_hash at the evaluated baseline than at latest.tested_commit
       and no later run exists:
        emit reverification_required      (impact assessment, NOT failure)
```

Simplifying assumptions, all testable and to be revisited: file-level granularity; identity is
path-stable (a rename is a new artifact); only accepted links define dependencies (no call graph,
no requirements-to-requirements dependencies); environment, dependency, and toolchain changes are
not modelled; only the latest run per scenario is considered; a run's outcome is assumed to apply
to the content hashes at its `tested_commit`. Findings must state when one of these is load-bearing.
One counterexample is worth recording here: an unchanged source file does **not** prove
verification is current if a dependency or environment changed, which is why this is a
reverification signal and never a pass.

## Errors

All errors are RFC 9457 problem documents: `type` (`urn:cta:error:<code>`), `title`, `status`,
`detail`, `instance`, plus `code`; 501 responses also carry `story` and `milestone`.

| Code | Status | Meaning |
| --- | --- | --- |
| `artifact-not-found` | 404 | Unknown artifact id at the requested baseline |
| `baseline-not-found` | 404 | Revision expression resolves to no known baseline |
| `thread-not-found` | 404 | Artifact known, no thread materialized for it (M0: requirement roots only) |
| `provider-not-registered` | 400 | Unknown discovery provider; detail lists registered providers |
| `invalid-request` | 400 | Request is valid JSON but semantically unusable |
| `request-validation` | 422 | Body/path/query failed schema validation |
| `not-implemented` | 501 | Contract frozen, implementation belongs to a later milestone (names `story`, `milestone`) |
| `fixture-data-missing` / `fixture-data-invalid` | 500 | Server-side fixture problem; message says how to regenerate |
| `repository-not-indexed` | 404 | Portable query named a repository or revision that is not indexed |
| `scenario-not-found` | 404 | Portable scenario key absent at the pinned revision |
| `report-not-applicable` | 400 | Report's parsed feature content does not match the indexed revision |
| `internal-error` | 500 | Unhandled error; logged with traceback |

## Fixture file schemas

| File | Model | Provenance |
| --- | --- | --- |
| `fixtures/banking-demo/history.json` | `FixtureHistory` | hand-written |
| `fixtures/banking-demo/expected/baselines.json` | `BaselinesManifest` | generated |
| `fixtures/banking-demo/expected/baseline-<x>.json` | `ExpectedFindingsFile` | hand-labeled |
| `fixtures/banking-demo/expected/candidate-links.json` | `CandidateIndexFile` | hand-labeled |
| `<fixture repo>/evidence/verification-runs.json` | `FixtureEvidenceFile` | hand-written (inside the fixture repo) |
| `<fixture repo>/evidence/accepted-links.json`, `proposed-links.json` | `FixtureLinkFile` | hand-written; one review state per file, enforced by the model |
| `fixtures/api-responses/snapshot.json` | `FixtureSnapshot` | generated |
| `fixtures/api-responses/findings.<baseline>.json` | `MaterializedFindings` | generated from the oracle |
| `fixtures/api-responses/threads/<id>.<baseline>.json` | `ThreadResponse` | generated |
| `fixtures/api-responses/discovery.<id>.json` | `DiscoveryResponse` | generated from the index via the real provider code |

Template tokens inside fixture overlays: `{{COMMIT:<commit-id>}}`,
`{{DISCOVERY_PROVIDER}}`, `{{DISCOVERY_MODEL_VERSION}}`, `{{DISCOVERY_INDEX_REVISION}}`.
Unknown tokens fail the build rather than rendering literally.

## Portable repository contracts (schema 0.4.0, additive)

These models live in `app/domain/portable.py` and are deliberately separate from CTA's strict
fixture artifacts. An external repository needs no `@SCN-nnn` tag, no `# cta:artifact` annotation,
no YAML front matter, and no accepted links to be indexed.

| Model | Required information |
| --- | --- |
| `PortableSnapshot` | repository id, identity strategy, resolved commit, tree digest, parser identity, features, diagnostics, `annotation_dependency=false` |
| `PortableFeature` | repository-scoped feature key, path, line, language, tags, background steps, scenarios, file content hash |
| `PortableScenario` | scenario key (`<repo>:<path>#SCN-L<line>`), keyword, kind (`scenario`/`scenario_outline`), tags, rule name, steps, example instances |
| `PortableStep` | step key (`<repo>:<path>#STEP-L<line>`), keyword, text, location, `from_background`, doc string, data table |
| `PortableScenarioInstance` | outline instance key (`.../EX-<n>`), example values, interpolated steps |
| `StepDefinitionRecord` | definition key, framework id, pattern, pattern type, source path/line, runtime |
| `StepResolutionRecord` | scenario/instance/step keys, status (`matched`, `undefined`, `ambiguous`, `unknown`, `not_available`), definition keys |
| `ScenarioExecutionRecord` | execution key, scenario/instance keys, outcome, tested commit, executed time, runtime, report URI/digest, per-step executions |
| `ExecutionImportRequest` | report path, provenance sidecar path, tested commit, adapter |
| `ReportProvenance` | report URI/digest, metadata URI/digest, adapter, runtime, protocol version, tested commit, import time |

Identity rules: `repository_id` is explicit, derived from a normalized remote URL, or derived from
the root commit; the strategy is returned. Scenario identity is the pinned commit plus the source
locator, and it is not claimed to survive edits, moves, or renames. Runtime-generated Cucumber
message ids are provenance only. Equal paths and tags in two repositories never collide because
every key is repository-prefixed.

**Honesty rules.** No report imported → `availability=not_available` and an explicit reason;
`UNDEFINED`/`AMBIGUOUS` require the framework's own `stepDefinitionIds`; an import requires a
provenance sidecar naming the tested commit (and optionally the repository), and the request's
commit must equal it. A report is attributed only when every `source` envelope hash matches the
indexed feature content, and the same report bytes cannot be rebound to another revision. A missing
report never yields an undefined-step finding or a fabricated execution. Scenario outcomes include
hook results; a missing step result is `UNKNOWN`, never a pass.

## Executable relations (schema 0.4.0, additive)

`ExecutableRelation(relation, origin, source_key, target_key, provenance)` with origins
`extracted` (Gherkin AST), `matched` (framework resolution), and `observed` (a trusted report).
Relations: `HAS_STEP`, `EXPANDS_TO`, `MATCHES_DEFINITION`, `HAS_STEP_EXECUTION`,
`EXECUTED_DEFINITION`. `HAS_STEP_EXECUTION` and `EXECUTED_DEFINITION` are emitted only for invoked
steps (`PASSED`/`FAILED`); `SKIPPED`, `PENDING`, `UNDEFINED`, and `AMBIGUOUS` are recorded but are
not observed execution. Coverage counts follow the same rule. `INVOKES`/`CALLS`/`EXERCISED_IN` are **not** emitted: M2 has no validated
production-call extraction, and a matched step definition is not production-code coverage.
Executability findings (`undefined_step`, `ambiguous_step`, `execution_failed`) are separate from
requirement findings and carry portable artifact keys, not `REQ-/SCN-/CODE-/TEST-` ids.


## Code retrieval contracts (schema 0.4.0, additive; AI-07)

`CodeRetrievalRequest` = `artifact_id`, optional `baseline`, `top_k` (1..50), optional `method`
(`lexical`/`cocoindex`; null selects CocoIndex when configured, else lexical), optional
`relation_types`, `include_unresolved`.

`CodeRetrievalResponse` = `schema_version`, `artifact_id`, `baseline`, `revision`, `status`
(`ok`/`not_available`), `method`, `provider`, `model_version`, `index_binding`, `hits`,
`unresolved`, `latency_ms`, `limitations`.

`RetrievalHit` = rank, clamped `score`, `raw_score`, canonical `artifact_id`, `relation_type`,
`path`, `start_line`, `end_line`, authoritative `revision` and `content_hash`, `method`.
`UnresolvedHit` = path, line range, raw score, reason.

Rules:

* Hits are proposals. No field carries a link id, review state, evidence id, or finding.
* A hit resolves only when the path is a source/test artifact at the requested commit and the
  committed blob hash equals the artifact hash. Otherwise it is unresolved.
* `index_binding` is `snapshot:sha256:<digest>` over repository, commit, eligible paths, and their
  authoritative hashes. It is **not** a CocoIndex-reported index revision (0.2.43 exposes none).
* `score` is the reported value clamped to 0..1 for the existing candidate contract; `raw_score` is
  the reported value. Neither is a calibrated probability.
* A configured live CocoIndex project must be checked out at the requested commit; otherwise the
  request fails explicitly rather than returning cross-baseline hits.
* The lexical method is a deterministic comparator over the same snapshot; it is not a research
  claim about semantic retrieval quality.
