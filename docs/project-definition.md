# CTA project definition and initial system obligations

**Status: Draft for owner and team review.** This is the first lifecycle artifact for the project's own engineering intent. It records a reviewable starting point based on the research objective and the owner's request to practice full-lifecycle traceability with Gherkin acceptance criteria. No new requirement approval, release acceptance, or completed implementation is asserted here.

Existing work predates this draft. Associations below are proposed retrospective allocations to existing stories; they do not imply these requirements were baselined before M0 development. The roadmap remains the delivery plan, [STATUS.md](STATUS.md) records actual milestone state, and [the research report](continuous-traceability-research-report.md) contains hypotheses and a proposed comparison rather than experimental results.

## Purpose and intended use

CTA helps an engineer inspect the relationships among approved obligations, Gherkin behavioral specifications, source/test artifacts and execution evidence at a selected baseline. It reports identifiable gaps, known failures and required reassessment while preserving the difference between those states.

The research asks whether this produces useful information beyond ordinary Gherkin CI, and whether graph representation adds practical value over an equally informed simpler implementation. The intended outcome is a small, documented, reproducible open-source research MVP achievable by 3–4 students over five weeks.

The tool supports engineering decisions. It does not approve requirements automatically, establish complete semantic coverage, replace hazard analysis, or make certification claims.

## Stakeholders and needs

| Stakeholder | Need / decision the product should support | Validation activity |
| --- | --- | --- |
| Requirements/verification engineer | Identify which behavioral specifications and evidence are connected to the selected obligation, with enough context to assess applicability. | Inspect a known thread and explain what its evidence supports and what remains unknown. |
| Developer/maintainer | See which reviewed relationships or verification activities need attention after a relevant change. | Apply a controlled change and decide what must be reviewed or rerun from the report. |
| Engineering reviewer | Distinguish source facts, proposals, approvals, passing/failing observations and unresolved judgments. | Review an ambiguous/missing-data case without mistaking it for a confirmed defect. |
| Research evaluator/instructor | Reproduce a fair CI/simple-storage/graph comparison and assess the evidence for the hypotheses. | Reproduce the experiment from the published inputs, labels, versions and invocations. |
| Contributor/operator | Install and run the demonstration on an ordinary development machine, then retain or export a reviewable report. | Follow setup/demo instructions with no network or optional model service during execution. |
| Repository owner/release approver | Know which increment is accepted, what was tested and what limitations remain. | Review a release packet against its stated milestone criteria and unresolved findings. |

## System boundary and concept of operation

The research system includes local artifact/report adapters, explicit association and review records, storage/query components, deterministic assurance policies and report/API consumers. Human approval and upstream authoring remain external activities. Git and one test runner supply source/execution context. Optional models supply proposals only.

Typical operation:

1. An engineer identifies the approved requirement baseline, repository revision and target configuration.
2. CTA imports scoped inventories, explicit associations and actual execution reports with available provenance.
3. Deterministic checks identify valid paths, broken references, missing policy-required relationships, unavailable information and changed review/evidence bases.
4. The report names its inputs, policy, evidence and limits. A passing scenario and a required upstream review can coexist.
5. A human records a disposition or changes the specification/implementation; new executions supply new observations.
6. A release or decision record cites the evaluated baseline and retained evidence.

For the initial product demo, retain the existing banking fixture and M0 contract. The proposed warning-requirement revision example is a later controlled evaluation case after its stories/contracts are agreed. CTA's own development uses the same discipline through files/issues/reviews before the unfinished product can ingest itself.

## Candidate system obligations

The following `REQ-101`–`REQ-108` labels reserve discussion identities for CTA's own proposed obligations. They are distinct from `REQ-001`–`REQ-003` in the synthetic banking repository. These records are not yet individual artifact files in the ingestion contract and are not an accepted graph inventory. Before approval, review their wording, allocation, verification methods and scope; create the appropriate supported artifact records in the owning story rather than silently changing the parser contract.

| Candidate | Draft obligation | Origin/rationale | Proposed allocation and verification |
| --- | --- | --- | --- |
| REQ-101 | For a selected known baseline and obligation, CTA shall expose the associated declared artifacts, accepted relationships and available execution evidence with source identifiers. | Engineer's need to inspect a digital thread. | DT-01/03/04 (#20/#22/#23); demonstrate a complete and an incomplete thread. M0 supplies a fixture-specific contract example only. |
| REQ-102 | CTA shall distinguish proposed associations from accepted associations in reports and shall preserve the fact that neither alone establishes verified behavior. | Reviewer need; AGENTS.md invariant 1. | FT-02 (#19), AI-01/04 (#30/#34), later AS-06 (#28); check separation and that discovery creates no accepted relationship or execution. |
| REQ-103 | CTA shall identify the source revision and relevant content fingerprints used in a verification conclusion, and shall determine content freshness from those fingerprints. | Configuration applicability; AGENTS.md invariant 3. | DT-05/06 (#24/#25), AS-02 (#3); evidence-only commit control and changed-content case. |
| REQ-104 | CTA shall distinguish a relevant change requiring reassessment or reverification from a failing execution recorded for the evaluated baseline. | Conservative engineering conclusions; AGENTS.md invariant 4. | AS-02/03 (#3/#4); positive, failure and no-change controls. M0 labels demonstrate the intended distinction, not a general implementation. |
| REQ-105 | Each assurance finding shall identify its policy/rule, implicated artifacts, available evidence and evaluated baseline, including previous/current versions when relevant. | Reviewer explainability; AGENTS.md invariant 5. | FT-02 (#19), AS-01/02/03/05 (#2/#3/#4/#27); inspect every frozen benchmark finding and its resolvable inputs. |
| REQ-106 | Following explicit dependency installation, required tests and the core demonstration shall run without network access, a GPU, optional model services, a vector server or Docker. | Contributor reproducibility; AGENTS.md invariant 2. | SETUP-01/FT-01 (#8/#18); clean setup and offline execution demonstration with the environment recorded. |
| REQ-107 | Capability unavailable in the selected increment shall be reported explicitly rather than returning a fabricated successful result. | Trustworthy interpretation of system state; AGENTS.md invariant 7. | FT-02 (#19), later implementing stories; contract-only endpoint checks and invalid-input cases. |
| REQ-108 | The research release shall provide reproducible inputs and evidence for comparing conventional CI, enhanced CI and a graph representation under equivalent authoritative inputs. | Research objective and RQ1–RQ4. | Proposed amendment to the research-comparison scope of CI-01/02 (#36/#37), not a claim that those issues already specify this entire obligation; frozen benchmark and independent report review. |

Gherkin rules and examples will refine behavioral obligations at the software level. These high-level obligations are not a request to duplicate the same normative software behavior in multiple stores. Preserve a single authoritative behavioral wording and link the story/approval metadata to it. Additional system, quality or process obligations remain independently documented when scenarios cannot adequately express them.

## Initial risk and control review

These are product-development risks for this prototype, not an aircraft or medical-device hazard analysis.

| Risk | Planned control | Review owner of record |
| --- | --- | --- |
| An unreviewed mapping looks approved or verified. | Separate candidates, accepted associations and evidence; review version-pinned decisions. | B for contracts; A/C review affected boundaries. |
| A content change is reported as a confirmed software failure. | Separate change/reverification and recorded failure policies with explicit negative controls. | C; B reviews provenance inputs. |
| Missing ingestion/configuration data produces a reassuring clean report. | Declare input scope/completeness and expose unavailable information; fail invalid imports explicitly. | B/C. |
| Self-evaluation hides defects or creates circular expected results. | Independent human-reviewed oracle and independent milestone review; preserve raw source/run records. | B leads oracle; a different reviewer checks exits. |
| Graph/AI/UI scope prevents a complete experiment and usable release. | Protect deterministic vertical slice, simpler comparison baseline and release time; optional providers remain optional. | Technical lead and all workstreams. |

## Initial validation and release objectives

Demonstrate that a reviewer can distinguish the supported claim “scenario passed at X under Y” from “the revised obligation still needs allocation review.” Compare that workflow with the ordinary runner and deterministic simpler baseline before attributing any advantage to the graph.

Verification asks whether CTA meets its specified behavior. Validation asks whether the report helps the intended engineer make the required decision accurately and with reasonable effort. Track both separately. The owner accepts the bounded project/release scope; milestone review must still be independent of authorship under repository conventions.

## Decisions to resolve at the first lifecycle review

| Decision | Draft starting point / disposition needed |
| --- | --- |
| Primary release user and interface | Engineer/reviewer working locally; choose the required CLI/API/UI path within the agreed five-week scope. Current roadmap includes a dashboard; the research proposal permits a CLI fallback. |
| Core acceptance demonstration | Keep existing M0 banking contract; decide the owning stories for the requirement-revision review example before extending implementation. |
| Behavioral specification authority | Store reviewed story acceptance criteria in `.feature` files and link issue records to the reviewed revision. M0 migration is retrospective. |
| Direct Gherkin execution | Existing pytest checks remain the verification implementation. Select a future binding/runner through an explicit story/ADR; store no invented Gherkin pass results. |
| Research/backend priorities | Resolve the research report's SQL/RDF comparison and deterministic-first emphasis against existing UI/semantic-discovery priorities in a reviewed roadmap change. |
| Ownership and acceptance | Identify the human product owner/release approver and the people reviewing each requirement allocation. No signature or approval is inferred from document creation. |

The next lifecycle activity is to review this definition and baseline the accepted intent, with disputed or deferred decisions visible. M0 landing prerequisites remain in force. Implementation then proceeds in eligible increments through [the lifecycle workflow](development-lifecycle.md), with Gherkin criteria refined before each new story is coded.
