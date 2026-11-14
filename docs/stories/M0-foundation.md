# M0 — stories, acceptance criteria, and exit evidence

Milestone **M0 (Contract + fixture foundation)** is defined in `CONTINUOUS_TRACEABILITY_ROADMAP.md` §7.
This file records what M0 includes, who owns it, and which command proves each exit criterion.

**Acceptance source of truth.** [FT-01.feature](FT-01.feature) and
[FT-02.feature](FT-02.feature) contain the canonical Gherkin criteria, with stable scenario
IDs and the existing AC labels. Their scenario wording was extracted unchanged from this
document. This index retains scope, rationale and the [verification map](#acceptance-verification-map).
The files are specifications verified by the existing pytest checks and, from M2 onward, executed
by the Cucumber suite under `bdd/` (see `docs/feature-inventory.json`). A documentation migration
does not constitute a new independent review or retroactively add scenario IDs to historical
execution records. Follow
[the development lifecycle](../development-lifecycle.md) for new stories.

**Backlog mapping.** M0 reuses the roadmap's own foundation stories — **FT-01** and **FT-02**
(owner: B lead, priority P0). Parts of the milestone that the backlog does not cover
(repository layout, developer setup guide, initial CI workflow) are tracked as platform tasks
**M0-P1…M0-P3** instead of inventing parallel story IDs, so the roadmap remains the single
source of story numbers. Any change to this file is a contract change: A, B, and C all review it.

---

## FT-01 — labeled fixture repository and baseline oracle (owner: B lead) · GitHub [#18](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/18)

> As a developer, I want labeled fixture repos and baseline oracles so I can test without external systems.

### AC-1.1 Deterministic Git history

Canonical scenario: [SCN-101 in FT-01.feature](FT-01.feature), tagged `@AC-1.1`.

### AC-1.2 Healthy chain has no findings

Canonical scenario: [SCN-102 in FT-01.feature](FT-01.feature), tagged `@AC-1.2`.

### AC-1.3 Missing links are reported

Canonical scenario: [SCN-103 in FT-01.feature](FT-01.feature), tagged `@AC-1.3`.

### AC-1.4 Change after verification is reverification, not failure

Canonical scenario: [SCN-104 in FT-01.feature](FT-01.feature), tagged `@AC-1.4`.

### AC-1.5 Confirmed failure stays distinct from staleness

Canonical scenario: [SCN-105 in FT-01.feature](FT-01.feature), tagged `@AC-1.5`.

### AC-1.6 Superseded lifecycle

Canonical scenario: [SCN-106 in FT-01.feature](FT-01.feature), tagged `@AC-1.6`.

### AC-1.7 Unreviewed proposal is never an accepted link

Canonical scenario: [SCN-107 in FT-01.feature](FT-01.feature), tagged `@AC-1.7`.

### AC-1.8 Fixture evidence labels are real

Canonical scenario: [SCN-108 in FT-01.feature](FT-01.feature), tagged `@AC-1.8`.

> AC-1.8 is what makes the labels honest: the "passed" evidence at baseline-a and the
> "failed" evidence at baseline-b are reproducible outcomes of the fixture code, not assertions
> we invented. It also shows that re-running "TEST-001" at baseline-b would fail — which is why
> AC-1.4 must report *reverification*, not failure, when no such run has been recorded.

---

## FT-02 — versioned contracts and mock responses (owner: B lead) · GitHub [#19](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/19)

> As a developer, I want versioned API/domain contracts plus mock responses so I can build independently.

### AC-2.1 Mock API returns schema-valid fixture data

Canonical scenario: [SCN-201 in FT-02.feature](FT-02.feature), tagged `@AC-2.1`.

### AC-2.2 Baseline resolution

Canonical scenario: [SCN-202 in FT-02.feature](FT-02.feature), tagged `@AC-2.2`.

### AC-2.3 Unknown identifiers fail loudly

Canonical scenario: [SCN-203 in FT-02.feature](FT-02.feature), tagged `@AC-2.3`.

### AC-2.4 Discovery proposes, never accepts (contract level of AI-04)

Canonical scenario: [SCN-204 in FT-02.feature](FT-02.feature), tagged `@AC-2.4`.

### AC-2.5 Unimplemented endpoints are honest

Canonical scenario: [SCN-205 in FT-02.feature](FT-02.feature), tagged `@AC-2.5`.

---

## Platform tasks (not stories)

| Task | Deliverable | Location |
| --- | --- | --- |
| M0-P1 | Repository layout and module ownership | `docs/architecture.md`, `AGENTS.md` |
| M0-P2 | Developer setup guide and offline test command | `docs/setup.md`, `README.md` |
| M0-P3 | Initial CI workflow (offline job) | `.github/workflows/ci.yml` |

On the tracker these three platform tasks belong to the **SETUP-01** user story
([#8](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/8), sub-issue of F-01 [#7](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/7)).
They are not separate issues: `M0-Pn` ids exist only in this document.

---

## Independent review gate

This section preserves the first review's findings and repair gate. The subsequent repairs,
oracle attestation and approving re-review are recorded in [STATUS.md](../STATUS.md) and the
linked review records. Those decisions apply to their named snapshots; extracting the criteria
into `.feature` files does not extend the old approval to newly changed documentation.

M0 is not self-certified. The exit criteria above were reviewed independently against the committed
revision, per `docs/reviews/M0-review-prompt.md`.

* Review: `docs/reviews/M0-review.md` · verdict **"M0 not verified"**
* Blocking findings, all mapped to the two foundation stories:
  * **R1 (major, #19)** — `FixtureStore` does not satisfy the declared `ArtifactRepository` port,
    so the M0 "everyone can begin independently" exit criterion is unmet.
  * **R2 (major, #19)** — `ThreadResponse` accepts a non-accepted link inside `accepted_links`.
  * **R3 (major, #18)** — `fixturectl.py verify` reports success for a tampered or deleted
    `expected/baselines.json`.
  * **R4 (minor, #19)**, **R5 (minor, #18)**, **R6 (minor, #19)**, **R7 (minor, #18)** — see the
    review for reproductions.
* Rule: M1 does not start until R1–R3 are repaired, re-tested, and cleared by a re-review. The
  per-finding acceptance conditions are the "Next tasks" table in `docs/STATUS.md`.

Verified by the review and worth keeping: the proposal-versus-accepted separation survived the
attack attempts (discovery never wrote an accepted link or evidence), the fixture history rebuilds
identically in a normal environment, the full offline suite passes, and the fixture's own tests
reproduce the labeled pass/fail evidence.

---

## Acceptance verification map

This is an explicit specification-to-test mapping, not a runner binding, executed result or new
approval. It requires review with the extracted feature files. Test selectors name existing
substantive checks; parameterized checks cover more than one baseline/case. The run's tested
revision/configuration and raw results must be retained separately before making a verification
claim. M0 checks fixture contracts and reviewed sample findings, not a general assurance engine.

| Criterion | Scenario | Existing verification selectors | Scope / limitation |
| --- | --- | --- | --- |
| AC-1.1 | SCN-101 | `backend/tests/test_fixture_repo.py::test_rebuilding_in_another_directory_is_reproducible`; `backend/tests/test_fixture_repo.py::test_generated_history_matches_the_committed_manifest`; `backend/tests/test_fixture_repo.py::test_tags_exist_and_resolve_to_those_commits` | Rebuilt history and manifest/tag identity. |
| AC-1.2 | SCN-102 | `backend/tests/test_fixture_oracle.py::test_healthy_artifacts_have_no_finding`; `backend/tests/test_api_contract.py::test_findings_match_the_oracle_exactly` | Healthy A chain in the oracle and fixture-backed response. |
| AC-1.3 | SCN-103 | `backend/tests/test_fixture_oracle.py::test_case_2_and_3_coverage_gaps_are_labeled`; `backend/tests/test_api_contract.py::test_findings_match_the_oracle_exactly` | Missing-link labels and served samples, not computed discovery. |
| AC-1.4 | SCN-104 | `backend/tests/test_fixture_oracle.py::test_case_4_reverification_identifies_both_baselines_and_the_change`; `backend/tests/test_api_contract.py::test_findings_match_the_oracle_exactly` | Content change, pinned evidence and negative failure expectation. |
| AC-1.5 | SCN-105 | `backend/tests/test_fixture_oracle.py::test_case_5_failure_is_distinct_from_staleness`; `backend/tests/test_api_contract.py::test_findings_match_the_oracle_exactly` | Recorded failure remains distinct from reverification in fixture labels. |
| AC-1.6 | SCN-106 | `backend/tests/test_fixture_oracle.py::test_case_7_superseded_requirement_is_flagged_for_lifecycle_review`; `backend/tests/test_api_contract.py::test_findings_match_the_oracle_exactly` | Superseded metadata and lifecycle-review label. |
| AC-1.7 | SCN-107 | `backend/tests/test_fixture_oracle.py::test_case_6_proposal_is_pending_and_not_accepted`; `backend/tests/test_api_contract.py::test_thread_keeps_proposals_out_of_accepted_links` | Pending proposal label and absence from accepted thread. |
| AC-1.8 | SCN-108 | `backend/tests/test_fixture_repo.py::test_fixture_test_suite_reproduces_the_labeled_evidence` | Executes the nested fixture suite at both tags; expected B failures are fixture observations. |
| AC-2.1 | SCN-201 | `backend/tests/test_api_contract.py::test_health_reports_contract_and_fixture_status`; `backend/tests/test_api_contract.py::test_artifact_is_addressable_by_tag_or_commit`; `backend/tests/test_api_contract.py::test_thread_carries_the_accepted_chain_with_evidence`; `backend/tests/test_api_contract.py::test_findings_match_the_oracle_exactly` | Validated response models and fixture revision; offline environment requires the separately recorded run context. |
| AC-2.2 | SCN-202 | `backend/tests/test_api_contract.py::test_artifact_is_addressable_by_tag_or_commit`; `backend/tests/test_api_contract.py::test_findings_by_sha_and_by_tag_are_identical` | Artifact and findings responses resolve tags/SHAs consistently. |
| AC-2.3 | SCN-203 | `backend/tests/test_api_contract.py::test_unknown_artifact_returns_a_problem_document` | Missing artifact produces the specified 404 problem. |
| AC-2.4 | SCN-204 | `backend/tests/test_api_contract.py::test_discovery_returns_a_proposal_and_never_an_accepted_link`; `backend/tests/test_domain_contracts.py::test_candidate_has_no_acceptance_vocabulary` | Fake provider response/provenance and no candidate acceptance fields. |
| AC-2.5 | SCN-205 | `backend/tests/test_api_contract.py::test_contract_only_endpoints_are_honest` | Parameterized endpoint checks include assurance evaluation's 501 and owning story. |

Run the existing verification implementation with:

```bash
uv run --offline --project backend pytest backend/tests -q
uv run --offline --project backend python tools/fixturectl.py verify
```

These commands do not execute `.feature` files. A green suite supports the mapped observations
at its recorded revision; acceptance of this mapping and any broader claim remains a review task.

## Exit criteria → evidence

| M0 exit criterion (roadmap §7) | Evidence |
| --- | --- |
| Repository layout | `docs/architecture.md`, `AGENTS.md` |
| Setup guide | `docs/setup.md` |
| Fixture generator | `tools/fixturectl.py build` |
| Tagged baselines | `fixtures/banking-demo/expected/baselines.json`, AC-1.1 |
| Labeled expected outputs | `fixtures/banking-demo/expected/baseline-{a,b}.json`, AC-1.2…1.7 |
| Pydantic contracts | `backend/app/domain/`, `docs/domain-contracts.md` |
| OpenAPI stub/examples | `GET /openapi.json`, `fixtures/api-responses/` |
| Fake candidate provider | `backend/app/discovery/fake.py`, AC-2.4 |
| Sample findings response | `fixtures/api-responses/findings.baseline-{a,b}.json` |
| Initial CI workflow | `.github/workflows/ci.yml` |
| Clone → documented command → deterministic offline tests | `uv sync --project backend` then `uv run --project backend pytest backend/tests` |
| Mock APIs return schema-valid fixture data | AC-2.1…2.5, `backend/tests/test_api_contract.py` |
| Everyone can begin independently | A-PR1 / B-PR1 / C-PR1 below |

---

## Follow-on assignments (after M0)

| Assignment | Owner | Stories | Deliverable |
| --- | --- | --- | --- |
| **A-PR1** | Developer A | AI-01 (P0) | `CandidateDiscovery` protocol tests, provider configuration, JSON-fixture provider hardening, retrieval-evaluation dataset notes. No embedding dependency. |
| **B-PR1** | Developer B | DT-01, DT-02, DT-04 (P0) | Requirement + Gherkin parsing into the same `Artifact` contract, SQLite-or-memory persistence, `GET /api/threads/REQ-001` from parsed data replacing the fixture replay. |
| **C-PR1** | Developer C | AS-01, AS-04, AS-05 (P0) | Deterministic `missing_verification_link` / `missing_implementation_link` rules over the fixture store, mock findings API, first React/TypeScript dashboard view of one finding. |

**Integration gate:** all three PRs pass on a clean machine in fake/offline mode. No stream may
depend on another stream's real implementation to merge.

**Owner-of-record per boundary:** B leads schemas and example payloads; C owns UI API
consumption and contract checks; A owns the discovery contract and evaluation methodology.
