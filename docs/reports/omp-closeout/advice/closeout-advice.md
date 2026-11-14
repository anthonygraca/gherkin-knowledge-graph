# Advisory refinement of the six remaining CTA stories

**Disposition: draft specifications for owner discussion, not implementation or acceptance review.** This advice is based on repository revision `140e98c`, the supplied issue bodies, and read-only inspection. No files were changed, dependencies installed, tests run, or work delegated.

The Gherkin below is proposed content for the six canonical `.feature` files. Adoption requires a reviewed specification revision and companion record. None of these scenarios has execution evidence from this advisory. The proposed scenario ranges do not collide with the existing development specifications.

## Readiness and shared conventions

| Story | Readiness verdict | Reason |
|---|---|---|
| AS-06 #28 | **needs-design-decision** | Reviewer identity enforcement, proposal capture, and the relationship between immutable baselines and review decisions need explicit disposition. |
| AS-07 #29 | **ready-after-spec** | Existing provider errors and provenance supply most of the contract; UI states and structured provider details need specification. |
| AI-02 #31 | **blocked** | An actual same-machine model/runtime configuration, licence acceptance, hardware suitability, and local execution evidence remain outstanding. |
| AI-03 #32 | **needs-design-decision** | The original CTA-owned embedding-refresh obligation conflicts with ADR 0008. Recommend explicit re-scope, described below. |
| CI-01 #36 | **blocked** | Its specification can be refined now, but implementation must wait for the M3 exit gate. The supported self-assurance scope also needs owner disposition. |
| CI-02 #37 | **blocked** | Implementation follows M3 and CI-01’s report contract. Stable artifact fingerprints support the banking fixture; portable locator identities need an explicit comparison limitation. |

For every companion `docs/stories/<ID>.md`, record:

- Source: owning GitHub issue, roadmap sections, applicable invariants and ADRs.
- Rationale, owner, parent feature, milestone, scope, non-goals and dependencies.
- Canonical feature revision and hash.
- Scenario-to-check mapping, distinguishing planned bindings from existing checks.
- Independent expected results and their human review disposition.
- Actual execution records separately: tested commit, relevant content hashes, configuration, command, report digest and outcomes.
- Review disposition: **draft; owner decisions and independent acceptance review outstanding**.

Use the existing Cucumber harness and strict resolution gate for adopted behavioral criteria. Deterministic adapters may replace external inference and storage failures; they must exercise the application’s actual validation, projection and reporting logic. An opt-in local-model scenario that did not run remains `not_executed`.

All new request, response and persisted report shapes belong in typed domain models. The first additive contract change after `0.5.0` requires a MINOR bump to `0.6.0`; subsequent independently landed contract changes follow the same policy. Update domain contracts and regenerate affected fixtures together. Preserve existing field meanings and fingerprint algorithms.

## AS-06 — Accept or reject proposed links with audit details

**Owner:** C, with B reviewing persistence/domain contracts and A reviewing discovery provenance.  
**Issue:** [#28](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/28) · **Parent:** F-07 #13 · **Milestone:** M3  
**Verdict:** **needs-design-decision**.

### Decisions and recommended defaults

**1. Enforce a trusted local operator identity without introducing an authentication service. Owner decision required.**

Recommended exact criterion wording:

> In trusted-local-operator mode, review writes are enabled only for an explicitly configured operator identity supplied by application startup configuration outside the ingested repository. The server assigns that identity to each decision and rejects a supplied `reviewer_id` that differs. The review service is accessible only on loopback, with browser-origin restrictions for review writes. An unset operator identity disables review writes.

This revisits ADR 0006 explicitly. Comparing a caller-controlled name to another caller-controlled name would not satisfy identity enforcement.

The smallest assumption is that the person controlling this local process is the configured operator. Residual risk: another process or person with access to that local account can act as that operator or alter local storage. This does not authenticate a distinct human or support multiple reviewers. **Only the owner can accept this limitation or require stronger identity verification.** Until that disposition, do not claim the original “authorized reviewer” criterion is fulfilled.

**2. Capture candidates through an explicit action outside the discovery provider.**

`TraceCandidate` must retain no link ID or review state. Recommend an additive `POST /api/link-proposals` accepting a typed candidate snapshot, repository, baseline and endpoint content hashes. The application validates endpoint existence and relation direction, then allocates a proposed `TraceLink` and stores its immutable snapshot.

Treat submitted discovery provenance as reported provenance, not authenticated model output. Record who submitted it. Capture does not accept the link. Discovery itself performs neither operation.

This supplies the missing path from a transient candidate to the existing review endpoint.

**3. Separate baseline facts from a review workspace.**

Keep baseline reads unchanged by default. Recommend an explicit workspace read, such as:

`GET /api/threads/{artifact_id}?baseline=...&review_view=workspace`

It projects decisions over the baseline and returns an additive `review_revision` identifying the decision-log position. Accepted and proposed links remain separate arrays.

Baseline findings continue to describe baseline facts. The workspace pending queue describes the review projection. A review write must not run assurance, rewrite findings, change evidence or assign a verification verdict.

**4. Use durable, append-only decisions.**

Recommend a local application-owned journal outside fixtures and the evaluated repository. Record:

- Decision ID, repository, link ID and proposal snapshot digest.
- Evaluated baseline SHA and both endpoint content hashes.
- Decision, server-assigned operator, UTC time and reason.
- Original provider, model and index provenance.
- Previous review revision and resulting review revision.

Publish the projection only after durable append succeeds. Serialize conflicting decisions. For this slice, permit only `proposed → accepted` or `proposed → rejected`; repeat or reversal requests return `409`. Reopening and revocation need separately reviewed behavior.

The precise journal implementation needs B’s design review; append-only application behavior does not imply tamper-resistant storage.

### Proposed `AS-06.feature`

```gherkin
@AS-06 @issue-28 @M3
Feature: AS-06: Human decisions on version-bound proposals

  Background:
    Given banking-demo baseline-a is loaded
    And the review journal is empty and outside the fixture repository
    And trusted-local-operator mode identifies the operator as "rv-ana"

  Rule: Discovery candidates become reviewable proposals only through explicit capture

    @SCN-3001
    Scenario: Capture a candidate without accepting it
      Given fake discovery returned SCN-002 implemented_by CODE-001
      When the operator submits that candidate and its baseline-a endpoint hashes to POST "/api/link-proposals"
      Then a new link is returned with review_state "proposed"
      And its snapshot retains the submitted provider, model version, and index revision
      And its snapshot identifies baseline-a and both endpoint content hashes
      And no accepted link, verification evidence, or assurance finding is created
      And every file in the fixture repository retains its original content hash

  Rule: Decisions are durable audit events and do not perform verification

    @SCN-3002
    Scenario: Accept the existing pending proposal
      Given LNK-007 is proposed at baseline-a
      And baseline findings and evidence have been recorded for comparison
      When "rv-ana" posts decision "accept" for LNK-007
      Then the response contains LNK-007 with review_state "accepted"
      And the journal contains one decision identifying "rv-ana" and a server UTC timestamp
      And that decision identifies the proposal snapshot and baseline-a endpoint hashes
      And the workspace thread contains LNK-007 only in accepted_links
      And the workspace pending queue excludes LNK-007
      And baseline findings and evidence equal the recorded values
      And default baseline thread reads equal their values before the decision

    @SCN-3003
    Scenario: Reject a proposal with a retained reason
      Given LNK-007 is proposed at baseline-a
      When "rv-ana" rejects LNK-007 with reason "The scenario does not cover the requirement"
      Then the journal contains one rejection with that reason
      And the workspace history returns that rejection
      And LNK-007 is absent from the workspace accepted links and pending queue
      And baseline findings, evidence, and fixture file hashes are unchanged

    @SCN-3004
    Scenario Outline: Refuse an invalid review without appending a decision
      Given LNK-007 is proposed at baseline-a
      When a review request is made with reviewer "<reviewer>" and decision "<decision>" and reason "<reason>"
      Then the response is a problem document with status <status>
      And no decision is appended
      And the workspace still shows LNK-007 as proposed

      Examples:
        | reviewer   | decision | reason | status |
        | rv-mallory | accept   |        | 403    |
        | rv-ana     | reject   |        | 422    |
        | rv-ana     | reject   |        | 422    |

    @SCN-3005
    Scenario: Refuse review when no operator identity is configured
      Given the application has no configured operator identity
      When "rv-ana" posts decision "accept" for LNK-007
      Then the response is a 503 problem with code "review-identity-unavailable"
      And no decision is appended

    @SCN-3006
    Scenario: Refuse a second terminal decision
      Given a durable acceptance decision already exists for LNK-007
      When "rv-ana" posts decision "reject" for LNK-007
      Then the response is a 409 problem with code "review-conflict"
      And the original decision bytes are unchanged
      And no second decision is appended

    @SCN-3007
    Scenario: Refuse acceptance against changed endpoint content
      Given a captured proposal connects SCN-002 to CODE-001 at baseline-a
      And CODE-001 has different content at baseline-b
      When the operator accepts that proposal against baseline-b
      Then the response is a 409 problem with code "proposal-stale"
      And no decision is appended
      And no verification failure is recorded

    @SCN-3008
    Scenario: Failed persistence does not publish an acceptance
      Given LNK-007 is proposed at baseline-a
      And the decision journal cannot durably append a record
      When "rv-ana" posts decision "accept" for LNK-007
      Then the response is a 503 problem with code "review-storage-unavailable"
      And the workspace still shows LNK-007 as proposed
      And restarting with the same journal does not expose an accepted decision

    @SCN-3009
    Scenario: Refuse a missing proposal
      When "rv-ana" posts decision "accept" for LNK-999
      Then the response is a 404 problem with code "proposal-not-found"
      And no decision is appended
```

Before adoption, replace the duplicate final row of SCN-3004 with an explicitly whitespace-only reason supplied through a DocString or a dedicated binding. The intended requirement is that both empty and whitespace-only rejection reasons fail; they must not become indistinguishable examples in the canonical file.

### Companion notes

**Scope:** explicit capture, version-bound accept/reject, history retrieval, workspace projection and a minimal review UI. Keep the existing review POST’s `TraceLink` response; add typed history and capture surfaces.

**Non-goals:** multi-user authentication, automatic acceptance, reversal/revocation, Git writes, evidence production or automatic assurance evaluation.

**Dependencies:** existing discovery/ingestion contracts; AS-07 can supply the shared provenance presentation.

**Verification:** API and persistence integration checks against temporary journals; restart recovery, conflicting writes, invalid relation direction and stale snapshots; browser checks for accept/reject/history. Snapshot evidence, findings and fixture bytes independently before writes. Check evidence-only revision changes using equal endpoint hashes.

**ADR/schema:** revisit ADR 0006 identity and storage decisions. New endpoints, errors and optional workspace metadata require a MINOR schema bump. Do not change `TraceCandidate` or existing baseline response semantics.

## AS-07 — Useful unavailable-provider behavior and clear provenance

**Owner:** C, with A reviewing provider semantics and B reviewing problem shapes.  
**Issue:** [#29](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/29) · **Parent:** F-07 #13 · **Milestone:** M3  
**Verdict:** **ready-after-spec**.

### Decisions and recommended defaults

**Distinguish registration, availability and empty results.**

- Unknown provider: existing `400 provider-not-registered`.
- Registered provider that cannot execute: typed `503` problem.
- Successful discovery with zero candidates: successful empty result with provenance.
- Existing code retrieval’s explicit `not_available` response remains meaningful; the UI must handle it without relabeling it as successful discovery.

Add optional structured `failed_provider` and `registered_providers` problem extensions. Generate the list from the effective registry, including enabled optional providers.

**Do not silently switch providers.** If the selected provider fails, offer an explicit switch to `fake`. The selected provider may be unavailable while fake mode remains available.

**Show provenance at every proposal presentation.** Cover transient candidates, persisted proposals, review history and hybrid-answer candidates. Display provider, model version, and index identity with its actual meaning. In particular, a CocoIndex `snapshot:...` value is a **CTA snapshot binding**, not a server-reported index revision.

Label fixture and model-backed paths using registered provider metadata, not a guess based on a name. Missing historical provenance must display “not recorded”; it must never be fabricated.

No material product-policy decision is needed unless the owner wants automatic fallback.

### Proposed `AS-07.feature`

```gherkin
@AS-07 @issue-29 @M3
Feature: AS-07: Honest provider availability and proposal provenance

  Rule: Provider failure remains distinct from findings and empty success

    @SCN-3101
    Scenario: An unregistered provider fails while baseline data remains usable
      Given the effective discovery registry contains only "fake"
      And the dashboard displays REQ-001 at baseline-a
      When discovery is requested with provider "missing-provider"
      Then the API returns a 400 problem with code "provider-not-registered"
      And failed_provider is "missing-provider"
      And registered_providers is ["fake"]
      And the candidate panel displays the selected provider as unavailable
      And the accepted thread and EV-001 remain accessible
      And no assurance finding is created

    @SCN-3102
    Scenario: A registered provider fails after an earlier successful request
      Given a configured provider previously returned candidates for baseline-a
      And that provider now times out through the deterministic failure transport
      When discovery is requested for baseline-b
      Then the API returns a typed 503 problem
      And the panel displays the provider failure
      And no baseline-a candidate appears as a current baseline-b result
      And the application does not silently request fake discovery

    @SCN-3103
    Scenario: A valid empty result is not an unavailable provider
      Given the configured discovery provider is "fake"
      When candidates are requested for REQ-003
      Then the API returns 200 with an empty candidates array
      And the response retains provider, model_version, and index_revision
      And the panel displays zero candidates without an unavailable-provider state

  Rule: Proposal provenance and acceptance state are visible separately

    @SCN-3104
    Scenario: A fixture proposal retains its provenance through review
      Given LNK-007 is displayed in the proposal panel
      When its details and review history are opened
      Then every proposal presentation displays provider "fake"
      And every proposal presentation displays model_version "fake-fixture-v1"
      And every proposal presentation displays its recorded index_revision
      And it is labelled as fixture-generated
      And it is absent from accepted_links until an acceptance decision exists

    @SCN-3105
    Scenario: A model-backed adapter is distinguishable without a live model test
      Given the CocoIndex adapter uses a deterministic recorded search transport
      When its mapped proposal is displayed
      Then the panel identifies the provider as "cocoindex"
      And it displays the recorded model identity
      And it labels the snapshot value as a CTA snapshot binding
      And it does not label the proposal as fixture-generated or accepted

    @SCN-3106
    Scenario: Historical missing provenance is shown as unknown
      Given a historical proposed link has no recorded model_version
      When the proposal is displayed
      Then its model version is shown as not recorded
      And no current model version is substituted
      And the proposal remains outside accepted_links
```

### Companion notes

**Scope:** discovery controls, typed provider errors, empty/unavailable UI states, provenance components and default fake-mode documentation.

**Non-goals:** automatic fallback, model installation, provider-health assurance findings or acceptance decisions.

**Dependencies:** current registry and retrieval contracts. Integrate review-history presentation with AS-06 when available; do not require AI-02 for deterministic UI verification.

**Verification:** real API error handling plus browser/component tests using deterministic provider transports. SCN-3105 verifies presentation of an adapter path; it is not evidence that real inference executed.

**ADR/schema:** preserve ADR 0008’s distinction between snapshot binding and server index identity. Structured problem extensions require a MINOR bump; UI-only changes would not.

## AI-02 — Same-machine local inference

**Owner:** A, with B reviewing domain boundaries and C reviewing unavailable states.  
**Issue:** [#31](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/31) · **Parent:** F-08 #14 · **Milestone:** M3  
**Verdict:** **blocked** pending a concrete local configuration and owner acceptance.

### Decisions and recommended defaults

**Actual model and hardware acceptance are owner decisions.** Record the exact model identifier, immutable weights digest, quantization, licence terms, runtime/version, formatting instructions, supported platform and measured memory/storage needs. The model name observed in ADR 0008 is a candidate for investigation, not approval or proof of laptop compatibility.

If the selected model differs from the issue title, amend the title and specification explicitly.

**Reuse the existing CocoIndex integration where feasible.** Configure its embedding runtime on the same machine rather than adding another source-code embedding pipeline. Keep the existing `CandidateDiscovery` contract and optional provider activation.

**Local means local execution, not merely a local-looking URL.** For an Ollama-based implementation:

- Use an explicitly selected same-machine runtime with local weights and local compute.
- Reject remote endpoints and remote/cloud execution modes.
- Disable redirects, proxy routing and automatic model downloads in the inference path.
- Verify both indexing and query execution with non-loopback egress denied for the runtime and its child processes.
- Provision weights separately through an explicit setup step.

Loopback configuration alone cannot establish that the runtime does not forward requests. The live evidence must identify the runtime process/configuration that actually performed inference.

The smallest honest assumption is one documented, owner-accepted laptop configuration. A pass applies to that configuration only.

### Proposed `AI-02.feature`

```gherkin
@AI-02 @issue-31 @M3
Feature: AI-02: Optional inference executes on the same machine

  Rule: Local inference is optional and remote execution is refused

    @SCN-3201
    Scenario: Default discovery needs no model runtime
      Given no local model runtime is installed
      And no local inference opt-in is configured
      When fake discovery is requested for SCN-001
      Then discovery succeeds through "fake"
      And no model process is started
      And no model weights are downloaded
      And no network connection is attempted

    @SCN-3202
    Scenario: A remote endpoint cannot satisfy local inference mode
      Given local inference mode is configured with endpoint "http://192.0.2.10:11434"
      When that provider is requested for SCN-001
      Then the API returns a 400 problem with code "invalid-request"
      And no connection to that endpoint is attempted
      And no candidates are returned

    @SCN-3203
    Scenario: Missing local weights produce an unavailable result
      Given local inference mode is explicitly enabled
      And its configured weights digest is absent from local storage
      When that provider is requested for SCN-001
      Then the API returns a 503 problem with code "retrieval-unavailable"
      And no automatic download or remote fallback occurs
      And accepted links, evidence, and findings are unchanged

  Rule: Contract behavior is independent of model quality

    @SCN-3204
    Scenario: The adapter passes the shared discovery contract offline
      Given the local provider adapter uses deterministic embedding and search transports
      When the shared CandidateDiscovery contract cases execute against it
      Then returned source IDs equal the requested source IDs
      And candidate counts obey top_k and relation filters
      And ranks are contiguous from one
      And every candidate carries provider, model_version, and index_revision
      And no candidate carries a link ID or review state
      And accepted links, evidence, and findings are unchanged

    @SCN-3205 @local-model @opt-in
    Scenario: Real indexing and discovery work with external egress denied
      Given the owner-accepted local model manifest identifies installed weights and runtime
      And non-loopback egress is denied for the inference process tree
      And an isolated banking-demo index has not yet been built
      When that runtime indexes baseline-a and executes the shared discovery contract cases
      Then the contract cases complete without external network access
      And the execution record names the weights digest and runtime version
      And it records the query and document formatting versions
      And every returned candidate identifies that model and its snapshot binding

    @SCN-3206
    Scenario: Malformed local inference output is not an empty success
      Given the local adapter receives a non-finite embedding through its deterministic transport
      When discovery is requested for SCN-001
      Then a typed retrieval-unavailable problem is returned
      And no partial candidate list is returned
      And no accepted link, evidence, or finding is written
```

### Companion notes

**Scope:** optional same-machine inference configuration, validation, provenance, invocation guide and attributable local execution.

**Non-goals:** shared DGX services, remote Ollama, cloud fallback, automatic downloads, universal hardware support or a retrieval-quality guarantee.

**Dependencies:** AI-06/07 integration and AI-03’s scope disposition. A fresh isolated index can verify AI-02 without waiting for incremental lifecycle implementation.

**Verification:** default adapter/error cases use deterministic transports. The same substantive contract cases also run opt-in against the selected local installation. Retain the egress-denial procedure, effective configuration, model/runtime identities, hardware measurements and raw reports. A skipped live check does not close AI-02.

**ADR/schema:** revisit ADR 0006’s model decision and document the local configuration alongside ADR 0008. Reusing existing provider fields and error types needs no schema bump by itself. Any added public provenance model or error type requires a MINOR bump.

## AI-03 — Explicit re-scope to snapshot and cache lifecycle

**Owner:** A, with B reviewing manifests and C reviewing provenance.  
**Issue:** [#32](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/32) · **Parent:** F-08 #14 · **Milestone:** M3  
**Verdict:** **needs-design-decision**.

### Recommended disposition

**Explicitly re-scope AI-03 to “Revision-aware retrieval snapshot and cache lifecycle.” Owner approval is required.**

ADR 0008 assigns source-code chunking, embeddings, incremental indexing and vector storage to CocoIndex. CTA should own:

- Content-hash change planning over its eligible artifact corpus.
- Repository/revision and model/configuration manifests.
- Isolated snapshot/index lifecycle and publication.
- Candidate provenance, compatibility checks and refresh observations.

This replaces the original requirement that CTA prove only changed artifacts were re-embedded and unchanged vectors were retained. **The current MCP contract cannot substantiate those claims.** Record their supersession in the issue, roadmap and ADR; do not close the original obligation by relabeling snapshot hashes as embedding statistics.

If the owner retains the original obligation, AI-03 remains blocked until an observable backend capability or a separately approved candidate-index design can verify it.

### Defaults under the proposed re-scope

Use two distinct identities:

1. **Corpus cache key:** content-derived from repository identity, sorted eligible artifact IDs/paths/hashes, model/weights identity, formatting configuration and relevant adapter settings. Exclude commit SHA so evidence-only commits permit content reuse.
2. **Snapshot binding:** retains the existing revision-bound meaning, including the evaluated commit. It is not a CocoIndex server index revision.

Changing the model or embedding configuration invalidates compatibility even when artifact bytes are unchanged.

Create new snapshots in staging; publish only after validation succeeds. Retain previous manifests and results. Because `ccc mcp` can update its index at startup, each session needs an isolated disposable index; do not assert immutability of an index file that an active session can change.

Measure CTA-observable wall time and artifact changes. Report actual embedding counts as `not_available` unless the backend exposes attributable measurements.

### Proposed `AI-03.feature`

These criteria apply **only after the owner adopts the re-scope**.

```gherkin
@AI-03 @issue-32 @M3
Feature: AI-03: Revision-aware retrieval snapshot and cache lifecycle

  Rule: Refresh planning uses artifact content and explicit configuration

    @SCN-3301
    Scenario: Plan the banking fixture content changes
      Given a retrieval manifest for banking-demo baseline-a
      And the eligible corpus contains source and test artifacts
      When the refresh planner compares baseline-a with baseline-b
      Then changed artifacts are exactly CODE-001 and TEST-002
      And unchanged artifacts are exactly CODE-002 and TEST-001
      And the manifest records both resolved revisions and their artifact content hashes
      And the plan does not claim that CocoIndex embedded exactly two items

    @SCN-3302
    Scenario: An evidence-only commit permits content reuse
      Given two commits have identical eligible artifact IDs, paths, and content hashes
      And their model and retrieval configuration are identical
      When refresh manifests are built for both commits
      Then both manifests have the same corpus cache key
      And their snapshot bindings identify their respective commits
      And the content-change plan is empty
      And no source change or verification failure is inferred from the different commits

    @SCN-3303
    Scenario: A model change invalidates compatibility
      Given an existing manifest and unchanged artifact content
      When a manifest is requested with a different weights digest
      Then the corpus cache key differs
      And the old cache is not declared compatible with the new model
      And the old manifest remains unchanged

  Rule: Snapshot publication and result combination preserve one provenance context

    @SCN-3304
    Scenario: Failed refresh leaves the previous snapshot usable
      Given baseline-a has a published retrieval manifest
      And the deterministic index adapter fails while building baseline-b
      When refresh is requested for baseline-b
      Then refresh reports a typed failure
      And no baseline-b snapshot is published
      And requests explicitly naming baseline-a still use its original manifest
      And requests naming baseline-b do not receive baseline-a results as a substitute

    @SCN-3305
    Scenario: Mixed snapshot candidates cannot form one ranked list
      Given one candidate batch is bound to baseline-a
      And another candidate batch is bound to baseline-b
      When the batches are submitted to the candidate-combination service
      Then combination fails with code "mixed-index-context"
      And no combined ranked list is returned

    @SCN-3306
    Scenario: Refresh cost distinguishes measurements from unavailable backend data
      Given the deterministic search transport exposes no embedding counter
      When a baseline-b refresh completes
      Then its report contains measured non-negative elapsed time
      And it contains added, changed, removed, and unchanged artifact counts
      And items_embedded is null with availability "not_available"
      And the report identifies the published snapshot binding and configuration digest
```

### Companion notes

**Scope:** manifests, content-change plans, isolation, publication, compatibility and honest refresh reporting.

**Non-goals:** a CTA source-code chunker/vector store, claims about unobserved CocoIndex vector reuse, semantic indexing of requirements/scenarios or changing freshness policy.

**Dependencies:** existing AI-07 snapshots; AI-02 supplies the accepted real local configuration. Most lifecycle behavior is verifiable beforehand using deterministic adapters.

**Verification:** hand-labeled baseline change sets; evidence-only commits; model/configuration changes; additions/deletions; failed publication; same-request snapshot pinning during refresh. Tests must verify actual manifest and combination behavior rather than manufacture successful responses.

**ADR/schema:** explicitly amend ADR 0008 and the AI-03 roadmap wording. Typed manifests, reports and errors require a MINOR schema bump. Preserve `index_revision` and `index_binding` meanings; add separately named fields where needed.

## CI-01 — Revision-triggered assurance

**Owner:** shared; name one implementation lead before adoption.  
**Issue:** [#36](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/36) · **Parent:** F-10 #16 · **Milestone:** M4  
**Verdict:** **blocked** for implementation by the M3 gate.

### Decisions and recommended defaults

**1. State which repository and rules are evaluated. Owner disposition required.**

Recommend two explicitly separate scopes:

- **CTA repository:** portable Gherkin ingestion and supported executability assurance using attributable Cucumber reports.
- **Banking fixture:** M2 requirement/link/evidence assurance against its own nested Git revisions.

Do not claim the fixture run assures CTA’s production code. Conversely, portable self-ingestion does not automatically provide requirement-to-code coverage assurance for this repository.

**2. Pin event revisions explicitly.**

For a PR, evaluate the event’s head SHA; for a push, evaluate its after SHA. Record any deliberately evaluated merge revision separately. Never let checkout defaults silently choose the reported baseline.

Each report must identify the **evaluator revision** and **evaluated repository revision**, even when equal.

**3. Keep tool outcome separate from findings.**

Recommended report-only policy:

- Exit `0`: ingestion and evaluation completed and the report was stored, including when findings exist.
- Exit `2`: configuration, ingestion, report-validation, evaluation or storage failure.
- An observed failing scenario can produce an assurance finding without constituting an assurance-tool failure.

Existing project test gates can still fail independently. Missing execution evidence is unavailable information, not a passing verification result.

**4. Store reports outside Git.**

Publish workflow artifacts and a job summary. Do not commit findings or modify branches. Use read permissions and no deployment credentials.

The evaluator must run offline with dependencies already provisioned. GitHub scheduling, dependency provisioning and artifact upload are networked workflow operations; describe that boundary honestly.

### Proposed report envelope

Use a typed envelope containing schema version, run identity, UTC time, evaluator revision, repository identity, evaluated revision, source/content manifest digest, rule/policy identity, supported scope, report/evidence digests, completeness, tool outcome and findings.

For workspace-derived inputs, also identify their immutable review snapshot. The default CI input is the committed repository baseline.

### Proposed `CI-01.feature`

```gherkin
@CI-01 @issue-36 @M4
Feature: CI-01: Assurance evaluates and reports the triggering revision

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
        | failure                                  |
        | an unknown repository revision           |
        | malformed execution-report provenance    |
        | an unreadable required ingestion input   |
        | an unwritable report destination         |

    @SCN-3406
    Scenario: Workflow publication leaves repository branches unchanged
      Given a completed deterministic assurance report contains findings
      When the workflow publishes its artifact and job summary
      Then the artifact contains the report and its input manifest
      And the summary identifies the evaluated revision and finding count
      And no commit, branch update, pull-request comment, or deployment is requested
      And tracked repository content is unchanged
```

### Companion notes

**Scope:** a reproducible assurance command and revision-triggered workflow; typed report storage and summary; the explicitly approved self/fixture scopes.

**Non-goals:** generalized repository connectors, deployment, model inference, automatic remediation, generated-finding commits or replacing existing project test gates.

**Dependencies:** M3 closure, existing portable ingestion/execution-report support and deterministic M2 rules. Define the report envelope with CI-02 before implementation.

**Verification:** deterministic event inputs exercise the actual revision resolver; real ingestion/evaluation runs offline against temporary repositories; corrupt reports and I/O failures exercise real error boundaries. Retain a hosted workflow run separately to establish trigger and artifact behavior. YAML inspection alone does not prove hosted execution.

**ADR/schema:** revisit ADR 0006’s CI deferral. Add typed reporting contracts and errors with a MINOR schema bump. Preserve configuration-specific execution provenance.

## CI-02 — New, unchanged and resolved findings

**Owner:** shared; name one implementation lead before adoption.  
**Issue:** [#37](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/37) · **Parent:** F-10 #16 · **Milestone:** M4  
**Verdict:** **blocked** by M3 and the CI-01 report contract.

### Decisions and recommended defaults

**Use the existing fingerprint without changing its inputs.** For supported stable-artifact findings, compare `finding_id`, based on rule, finding type and sorted artifact IDs. Do not compare baseline, explanation or evidence text as identity.

Return unchanged entries as **before/after pairs**. An unchanged identity can have changed severity, evidence or explanation.

**Require comparable, complete inputs.** Both inputs must identify resolved revisions, repository, supported scope, rule/policy identity, identity strategy and report/input hashes. Reject incomplete evaluations and incompatible scopes or policies. Do not infer resolution from a failed or narrower run.

**Limit the initial identity guarantee explicitly. Owner decision required.**

The banking fixture has stable declared artifact IDs. Portable findings use source-locator keys, which can change or be reused after edits and line movement. Excluding the baseline from the hash does not establish logical continuity.

Recommend:

> Initial new/unchanged/resolved classification supports finding sets with the existing stable declared-artifact identity strategy. Portable source-locator findings are reported as not comparable unless an independently reviewed continuity mapping exists.

This is an honest boundary, but it means automated self-assurance diffs are not generally solved by this slice. If the owner requires them for F-10 closure, approve a separate additive comparison-identity design first. Do not silently change existing `finding_id` semantics.

“Resolved” means absent from the comparable current evaluation. It does not by itself establish requirement satisfaction or prove a remediation caused the change.

### Proposed `CI-02.feature`

```gherkin
@CI-02 @issue-37 @M4
Feature: CI-02: Comparable finding sets are classified by stable identity

  Rule: Identity determines new, unchanged, and resolved categories

    @SCN-3501
    Scenario: Compare the hand-labeled banking baselines
      Given complete comparable assurance reports for banking-demo baseline-a and baseline-b
      When the findings diff command compares baseline-a to baseline-b
      Then it reports 2 new findings
      And it reports 4 unchanged findings
      And it reports 0 resolved findings
      And the new finding types are reverification_required and verification_failed
      And the report includes both resolved revisions and both report digests

    @SCN-3502
    Scenario: Reverse comparison exposes the resolved category
      Given complete comparable assurance reports for banking-demo baseline-a and baseline-b
      When the findings diff command compares baseline-b to baseline-a
      Then it reports 0 new findings
      And it reports 4 unchanged findings
      And it reports 2 resolved findings
      And resolved means absent from the current comparable finding set
      And no verification evidence or requirement verdict is created

    @SCN-3503
    Scenario: Comparing a baseline with itself changes nothing
      Given a complete assurance report for banking-demo baseline-a
      When that report is compared with itself
      Then it reports 0 new findings
      And it reports 4 unchanged findings
      And it reports 0 resolved findings

    @SCN-3504
    Scenario: Payload changes do not replace an unchanged finding identity
      Given two comparable finding reports contain the same rule, finding type, and artifact IDs
      And those findings have different explanations and evidence references
      When the reports are compared
      Then the finding is classified as unchanged
      And its before and after payloads are both retained
      And neither payload is rewritten

  Rule: Unknown or incompatible inputs cannot imply resolution

    @SCN-3505
    Scenario Outline: Refuse an invalid comparison
      Given two report inputs differ by "<condition>"
      When the findings diff command compares them
      Then it exits 2 with code "findings-not-comparable"
      And it identifies the invalid input and reason
      And it returns no new, unchanged, or resolved classification

      Examples:
        | condition                                |
        | the previous resolved revision is absent |
        | the current resolved revision is absent  |
        | the current evaluation is incomplete     |
        | repository identities differ             |
        | evaluated rule scopes differ             |
        | policy versions differ                   |
        | a finding baseline contradicts its report|

    @SCN-3506
    Scenario: Source locators alone do not establish cross-revision continuity
      Given two portable finding reports use source-locator identities
      And no reviewed continuity mapping accompanies them
      When the findings diff command compares those reports
      Then it exits 2 with code "findings-not-comparable"
      And it reports that stable cross-revision identity is unavailable
      And it does not classify displaced findings as resolved and new
```

### Companion notes

**Scope:** deterministic diff service/command, comparison validation, typed report and integration with CI artifacts and the M4 benchmark format.

**Non-goals:** requirement verdicts, automatic finding closure, policy migration, inferred rename continuity or retroactive rewriting of findings.

**Dependencies:** CI-01’s complete, revision-bound reports; existing fingerprint semantics. Broader portable support depends on an owner-approved identity design.

**Verification:** hand-labeled banking counts, reverse and identical comparisons, independent fingerprint vectors, payload changes, duplicate/conflicting IDs, missing revisions, incomplete reports and incompatible scopes. Classifications must come from the application’s actual diff service.

**ADR/schema:** document comparison eligibility and the portable limitation. A new typed diff envelope/error requires a MINOR bump. Do not alter the current fingerprint algorithm; a future comparison identity should use an explicitly named, versioned additive field.

## Dependency order and closure conditions

### Recommended order

1. **Owner dispositions first:** AS-06’s trusted-local-operator criterion; AI-02’s model/licence/hardware selection; AI-03’s re-scope; CI scope and comparison limitations.
2. **AS-07** can proceed after its specification is reviewed. It needs no live model.
3. **AS-06** can proceed alongside the retrieval work after identity and journal design are settled.
4. **AI-02 and AI-03** share model/configuration and snapshot contracts. Their deterministic work can proceed independently; real AI-02 execution requires the accepted local installation.
5. **M3 exit demonstration and independent milestone review.**
6. **CI-01**, followed by **CI-02**, under the reviewed M4 report contract.
7. **M4 integration, benchmark/report completion and independent milestone review.**

M4 specifications may be refined now. M4 implementation remains gated by M3.

### Parent features and milestones

| Parent or milestone | Earliest honest closure condition |
|---|---|
| **F-07 #13 — Review** | AS-06 and AS-07 accepted, including the identity-policy disposition, durable history, provenance and usable unavailable-provider behavior. |
| **F-08 #14 — Retrieval** | AI-02 accepted on an actual local configuration; AI-03 completed under an explicitly approved re-scope or its original obligation fulfilled; other child slices, including AI-06/07, receive owner closure dispositions. |
| **F-10 #16 — Automation** | CI-01 and CI-02 accepted within an explicitly approved scope, with any required portable-comparison gap resolved; feature-level research planning such as #40 is dispositioned. |
| **M3** | Local fake/real contract evidence, measured real retrieval, offline default, review workflow, remaining story dispositions and independent milestone review with no open major finding. Create or omit a GitHub milestone object only by owner choice; its absence changes no engineering gate. |
| **M4** | Revision-triggered assurance and comparable findings reports integrated with the required reproducible research comparison, limitations and runtime/cost observations; owner disposition and independent milestone review complete. Existing PR 4 benchmark evidence contributes but does not close M4. |

The principal unresolved product choices are the acceptable local identity boundary, AI-03’s replacement obligation, and whether M4 must compare portable self-assurance findings across edits. Record those decisions before implementation turns the proposed defaults into accidental requirements.