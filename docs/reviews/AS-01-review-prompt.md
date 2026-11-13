# Independent implementation review — AS-01, submission 1 of 7

## 1. Story and authorization

**Task:** AS-01 — Missing coverage/link findings.
**Roadmap/feature:** F-05 Assurance, roadmap §6 AS-01; milestone **M1 — AI-free vertical slice**.
**GitHub story:** anthonygraca/gherkin-knowledge-graph issue **#2**, verified OPEN at
2026-11-13T03:56:41Z (`gh issue view`), milestone "M1 — AI-free vertical slice".
**Owner:** C; **Implementer/integrator:** OMP (shared API integration).
**Repository:** `<task_repo>` (read-only sandbox).
**Base:** `c43541b29d62186a4aa7fee32fed98720fc5f921` (`main`, DT-04 merge).
**Branch:** `feat/2-as-01-missing-verification`. **Submission:** 1 of 7.

### User outcome

A systems engineer can run assurance for a baseline and see which requirements lack accepted
verification, with a finding that names the rule, the requirement, and the evaluated commit.

### Scope

`DeterministicAssuranceEvaluator` over the repository port implementing only
`RULE-MISSING-VERIFICATION-LINK`; implement `POST /api/assurance/evaluate`; keep
`GET /api/findings` on the reviewed replay until the rule set is complete. Non-goals: M2 rules
(staleness/failure/missing implementation/pending review/lifecycle), model calls, changing the
findings replay.

### Proposed commit reference

`feat(assurance): [issue #2] report missing verification links deterministically`, body `Refs #2`.

## 2. Acceptance criteria (canonical snapshot)

File `docs/stories/AS-01.feature`, sha256
`835b6d313960624402eccdcf4b51ca5c87ee790ec0249df7a7e72a0ec95a8c85`.

```gherkin
# Canonical acceptance specification for AS-01 (#2), M1.
# Source criteria: the GitHub story intake at
# https://github.com/anthonygraca/gherkin-knowledge-graph/issues/2 (verified 2026-11-13T03:56:41Z)
# and roadmap §6 F-05. Boundary and failure scenarios were added during refinement; the intake
# scenario keeps its wording.
# Verified by the pytest selectors mapped in AS-01.md. These scenarios are not currently bound
# to or executed by a Gherkin runner.
@AS-01 @issue-2 @M1
Feature: AS-01: Missing coverage/link findings
  A requirement is missing verification when it has no accepted `verified_by` link to an existing
  scenario at the evaluated baseline. A proposal is not acceptance. The rule is deterministic,
  offline, and explains its inputs and simplifying assumptions.

  @SCN-701
  Scenario: Requirement has no accepted verification scenario
    Given requirement "REQ-002" exists
    And no accepted verification scenario is linked to "REQ-002"
    When assurance evaluates baseline "baseline-a"
    Then a "missing_verification_link" finding is produced for "REQ-002"

  @SCN-702
  Scenario: A pending proposal does not satisfy the rule
    Given "LNK-007" proposes "REQ-002" verified_by "SCN-002" and is not accepted
    When assurance evaluates baseline "baseline-a"
    Then "REQ-002" still produces a "missing_verification_link" finding
    And the proposal is not counted as an accepted link

  @SCN-703
  Scenario: A requirement with accepted verification has no such finding
    Given "REQ-001" has accepted link "LNK-001" verified_by "SCN-001"
    When assurance evaluates baseline "baseline-a"
    Then no "missing_verification_link" finding names "REQ-001"

  @SCN-704
  Scenario: Findings identify their rule, inputs, and evaluated baseline
    Given assurance evaluated baseline "baseline-b"
    Then each finding names the rule id, severity, artifact revisions, and resolved commit
    And the finding fingerprint follows the canonical rule-and-artifact inputs

  @SCN-705
  Scenario: Unusable evaluation requests are rejected honestly
    When assurance is asked for baseline "baseline-z"
    Then the response is 404 "baseline-not-found"
    When assurance is asked for an unknown policy
    Then the response is 400 "invalid-request"
```

Refinement disposition: owner-authored issue intake + roadmap §6; boundary/failure scenarios were
added without weakening the intake. No separate human refinement sign-off is recorded.

Repository constraints (AGENTS.md): deterministic/offline rules; proposals ≠ accepted links ≠
verification; findings name policy, artifacts, evidence, and baseline; oracle labels are the
independent expectation; no model calls in rules.

## 3. Snapshot and manifest

Snapshot captured 2026-11-13T04:02Z. Manifest (sha256 of every task file):

```text
adf0fd7707f95343f4cd75ce9f476598cf368fb53e0dc88988a953df18f4d008  backend/app/assurance/rules.py
fb9b493481e405cb86d964744378bb04c4a2436ae4ddfcf91b0bbaa7dc9f45a9  backend/app/api/deps.py
04300928d42b6afb3cf192bd26c709242bf6c7d3a67e4c679ef813e93f8a29db  backend/app/api/routes.py
7ebd1e5f9a943fd027167ec8e23c0e236efd12f09e34ab9c598a29643ce0bd7e  backend/app/main.py
d8c528bb854ae9bb7b7125b12276073590bac77846a6f7819265729c0f52d764  backend/tests/test_assurance_rules.py
67f903e59a723ef0991ba671cdd7d7041677b16463478984c5c1cb8e47626ebf  backend/tests/test_api_contract.py
835b6d313960624402eccdcf4b51ca5c87ee790ec0249df7a7e72a0ec95a8c85  docs/stories/AS-01.feature
dbfb4dee6da40c3ae5059a02adaed584d0a05b89e4960d08513c14e0d7cf26ba  docs/stories/AS-01.md
8134ad961dbbd6ee2031977b2893efad82ba7c21e35febe6563b27eda9be27a0  docs/api-contracts.md
9a33f65da79f96148b36ee03ebc4f8dbe05cfa8e039297e36d922a073e94c165  docs/domain-contracts.md
386e5241c5d91a39dc8e9a83d1e1906ab1eda9c6cc9184d4ca518803a8161e89  docs/architecture.md
137dd46fc3ad31634b1bb41095349523be0908eacac53b9ec2531752f0399b0b  docs/STATUS.md
e700547d315e35ab9f63640a4213ec4028118c988daef1ee374073e7c5e90f44  docs/reports/omp-as-01-missing-link/IMPLEMENTATION.md
33951a329dbbc54a44e22f8d75b471567d1ce261470e602408ac0b3bdac1f15f  docs/reports/omp-as-01-missing-link/METRICS.md
532d1910a44c4857bdb05a19b777913bff5b6f40f384069ce3e36fe6a297ffdb  docs/reports/omp-as-01-missing-link/PROMPT_LOG.md
```

`SCHEMA_VERSION = 0.2.0`, `PACKAGE_VERSION = 0.1.0`; no dependency or shape change.

## 4. Implementation

### New evaluator (complete)

`backend/app/assurance/rules.py`:
```python
"""Deterministic assurance rules over an ingested repository (M1 subset).

Only ``RULE-MISSING-VERIFICATION-LINK`` is implemented in M1. The evaluator is pure with respect
to the repository: it reads artifacts and accepted links, emits findings, and mutates nothing.
Proposals never satisfy verification. The remaining rules arrive with AS-02/AS-03 (M2).
"""

from __future__ import annotations

from app.domain.enums import ArtifactType, RelationType, ReviewState, RuleId
from app.domain.errors import InvalidRequest
from app.domain.models import AssuranceFinding, make_finding
from app.domain.policy import RULE_DEFAULT_SEVERITY, RULE_FINDING_TYPE
from app.domain.ports import ArtifactRepository

DEFAULT_POLICY = "default"


class DeterministicAssuranceEvaluator:
    """Evaluate the M1 rule set at one baseline."""

    def __init__(self, repository: ArtifactRepository) -> None:
        self._repository = repository

    def evaluate(self, baseline: str, *, policy: str | None = None) -> list[AssuranceFinding]:
        if policy not in (None, DEFAULT_POLICY):
            raise InvalidRequest(
                f"Unknown policy {policy!r}; the registered policy is {DEFAULT_POLICY!r}."
            )
        canonical = self._repository.resolve_baseline(baseline)
        commit = self._repository.commit_of(canonical)
        artifacts = self._repository.list_artifacts(canonical)
        accepted = self._repository.list_links(canonical, review_state=ReviewState.ACCEPTED)

        scenarios = {
            artifact.artifact_id
            for artifact in artifacts
            if artifact.artifact_type is ArtifactType.SCENARIO
        }
        verified_requirements = {
            link.source_id
            for link in accepted
            if link.relation_type is RelationType.VERIFIED_BY and link.target_id in scenarios
        }

        findings: list[AssuranceFinding] = []
        for artifact in sorted(artifacts, key=lambda item: item.artifact_id):
            if artifact.artifact_type is not ArtifactType.REQUIREMENT:
                continue
            if artifact.artifact_id in verified_requirements:
                continue
            findings.append(
                make_finding(
                    rule_id=RuleId.MISSING_VERIFICATION_LINK,
                    finding_type=RULE_FINDING_TYPE[RuleId.MISSING_VERIFICATION_LINK],
                    severity=RULE_DEFAULT_SEVERITY[RuleId.MISSING_VERIFICATION_LINK],
                    artifact_ids=[artifact.artifact_id],
                    evaluated_baseline=commit,
                    explanation=(
                        f"{artifact.artifact_id} has no accepted verification scenario at "
                        f"{canonical}."
                    ),
                    artifact_revisions={artifact.artifact_id: artifact.revision},
                )
            )
        return sorted(findings, key=lambda finding: finding.finding_id)
```

### Wiring and route diffs

```diff
diff --git a/backend/app/api/deps.py b/backend/app/api/deps.py
index e5613a7..a2209c6 100644
--- a/backend/app/api/deps.py
+++ b/backend/app/api/deps.py
@@ -10,6 +10,7 @@ from typing import Annotated
 
 from fastapi import Depends, Request
 
+from app.assurance.rules import DeterministicAssuranceEvaluator
 from app.assurance.sample_findings import SampleFindingsSource
 from app.discovery.registry import ProviderRegistry
 from app.domain.ports import ArtifactRepository
@@ -35,6 +36,10 @@ def provide_findings_source(request: Request) -> SampleFindingsSource:
     return request.app.state.findings_source
 
 
+def provide_evaluator(request: Request) -> DeterministicAssuranceEvaluator:
+    return request.app.state.evaluator
+
+
 def provide_providers(request: Request) -> ProviderRegistry:
     return request.app.state.providers
 
@@ -43,4 +48,5 @@ SettingsDep = Annotated[Settings, Depends(provide_settings)]
 RepositoryDep = Annotated[ArtifactRepository, Depends(provide_repository)]
 StoreDep = Annotated[IngestedStore, Depends(provide_store)]
 FindingsDep = Annotated[SampleFindingsSource, Depends(provide_findings_source)]
+EvaluatorDep = Annotated[DeterministicAssuranceEvaluator, Depends(provide_evaluator)]
 ProvidersDep = Annotated[ProviderRegistry, Depends(provide_providers)]
diff --git a/backend/app/api/routes.py b/backend/app/api/routes.py
index 94b95f8..73fa04f 100644
--- a/backend/app/api/routes.py
+++ b/backend/app/api/routes.py
@@ -4,6 +4,7 @@ Endpoints are grouped by intent, which is also the honesty axis of the system:
 
 * **reads** — real implementations over the ingested fixture repository.
 * **ingestion** — parses the configured repository at a revision.
+* **assurance** — deterministic rules over ingested facts; no model calls.
 * **discovery** — real implementation, fixture provider; returns proposals only.
 * **contract-only** — the shape is frozen and documented, the implementation belongs to a
   later milestone; the response is 501 with the owning story, never fake success.
@@ -15,7 +16,14 @@ from typing import Annotated
 
 from fastapi import APIRouter, Path, Query
 
-from app.api.deps import FindingsDep, ProvidersDep, RepositoryDep, SettingsDep, StoreDep
+from app.api.deps import (
+    EvaluatorDep,
+    FindingsDep,
+    ProvidersDep,
+    RepositoryDep,
+    SettingsDep,
+    StoreDep,
+)
 from app.domain.api import (
     ArtifactListResponse,
     DiscoveryRequest,
@@ -225,16 +233,17 @@ def post_link_review(
 @router.post(
     "/api/assurance/evaluate",
     response_model=FindingsResponse,
-    tags=["contract-only"],
-    responses={501: _PROBLEM_501, 404: _PROBLEM_404, 422: {"model": ProblemDetails}},
-    summary="Run deterministic assurance rules (contract only in M0)",
+    tags=["assurance"],
+    responses={400: _PROBLEM_400, 404: _PROBLEM_404, 422: {"model": ProblemDetails}},
+    summary="Run the implemented deterministic assurance rules",
 )
-def post_assurance_evaluate(payload: EvaluateRequest) -> FindingsResponse:
-    raise FeatureNotImplemented(
-        story="AS-01, AS-02, AS-03 (C-PR1)",
-        milestone="M1/M2",
-        detail=(
-            "Deterministic rule evaluation is implemented with AS-01…AS-03 against the fixture "
-            "oracle. GET /api/findings currently returns the reviewed sample findings."
-        ),
+def post_assurance_evaluate(
+    payload: EvaluateRequest, repository: RepositoryDep, evaluator: EvaluatorDep
+) -> FindingsResponse:
+    canonical = repository.resolve_baseline(payload.baseline)
+    findings = evaluator.evaluate(canonical, policy=payload.policy)
+    return FindingsResponse(
+        schema_version=SCHEMA_VERSION,
+        baseline=canonical,
+        findings=findings,
     )
diff --git a/backend/app/main.py b/backend/app/main.py
index 3b7daa8..12b56ef 100644
--- a/backend/app/main.py
+++ b/backend/app/main.py
@@ -11,6 +11,7 @@ from fastapi import FastAPI
 
 from app.api.errors import register_exception_handlers
 from app.api.routes import router
+from app.assurance.rules import DeterministicAssuranceEvaluator
 from app.assurance.sample_findings import SampleFindingsSource
 from app.discovery.registry import ProviderRegistry
 from app.persistence.ingested import IngestedStore
@@ -49,6 +50,10 @@ def create_app(settings: Settings | None = None) -> FastAPI:
         openapi_tags=[
             {"name": "reads", "description": "Implemented over the ingested fixture repository."},
             {"name": "ingestion", "description": "Parses the configured repository at a revision."},
+            {
+                "name": "assurance",
+                "description": "Deterministic rules; no model calls, no network.",
+            },
             {"name": "discovery", "description": "Candidate proposals only; never writes links."},
             {
                 "name": "contract-only",
@@ -59,6 +64,7 @@ def create_app(settings: Settings | None = None) -> FastAPI:
     app.state.settings = resolved
     app.state.store = IngestedStore.from_settings(resolved)
     app.state.findings_source = SampleFindingsSource.from_settings(resolved)
+    app.state.evaluator = DeterministicAssuranceEvaluator(app.state.store)
     app.state.providers = ProviderRegistry(resolved)
     register_exception_handlers(app)
     app.include_router(router)
diff --git a/backend/tests/test_api_contract.py b/backend/tests/test_api_contract.py
index 0e61565..d80e42c 100644
--- a/backend/tests/test_api_contract.py
+++ b/backend/tests/test_api_contract.py
@@ -415,7 +415,6 @@ def test_thread_matches_the_committed_example(
     ("path", "payload", "story"),
     [
         ("/api/links/LNK-007/review", {"decision": "accept", "reviewer_id": "rv-ana"}, "AS-06"),
-        ("/api/assurance/evaluate", {"baseline": "baseline-a"}, "AS-01"),
     ],
 )
 def test_contract_only_endpoints_are_honest(
```

### Tests (complete)

`backend/tests/test_assurance_rules.py`:
```python
"""AS-01 acceptance: the missing-verification finding matches the hand-labeled oracle."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.domain.api import FindingsResponse
from app.domain.enums import FindingType
from app.domain.models import finding_fingerprint
from app.domain.oracle import ExpectedFindingsFile
from app.persistence.fixtures import load_model
from app.settings import Settings

BASELINES = ("baseline-a", "baseline-b")


def oracle(fixture_settings: Settings, baseline: str) -> ExpectedFindingsFile:
    return load_model(fixture_settings.expected_dir / f"{baseline}.json", ExpectedFindingsFile)


def evaluate(client: TestClient, baseline: str) -> FindingsResponse:
    response = client.post("/api/assurance/evaluate", json={"baseline": baseline})
    assert response.status_code == 200
    return FindingsResponse.model_validate(response.json())


@pytest.mark.parametrize("baseline", BASELINES)
def test_evaluate_matches_the_oracle_missing_verification_finding(
    client: TestClient, fixture_settings: Settings, baseline: str
) -> None:
    body = evaluate(client, baseline)
    expected = [
        item
        for item in oracle(fixture_settings, baseline).findings
        if item.finding_type is FindingType.MISSING_VERIFICATION_LINK
    ]
    assert len(expected) == 1
    assert body.baseline == baseline
    assert len(body.findings) == 1

    finding = body.findings[0]
    item = expected[0]
    assert finding.rule_id == item.rule_id
    assert finding.finding_type == item.finding_type
    assert finding.severity == item.severity
    assert finding.status == item.status
    assert finding.artifact_ids == item.artifact_ids
    assert finding.evidence_ids == []
    assert finding.explanation == item.explanation
    assert finding.finding_id == finding_fingerprint(
        item.rule_id, item.finding_type, item.artifact_ids
    )
    assert finding.evaluated_baseline == finding.artifact_revisions["REQ-002"]


def test_evaluate_does_not_count_proposals(client: TestClient) -> None:
    body = evaluate(client, "baseline-a")
    assert [finding.artifact_ids for finding in body.findings] == [["REQ-002"]]
    assert not [finding for finding in body.findings if "REQ-001" in finding.artifact_ids]
    assert not [finding for finding in body.findings if "REQ-003" in finding.artifact_ids]


def test_evaluate_leaves_a_covered_requirement_alone(client: TestClient) -> None:
    body = evaluate(client, "baseline-a")
    assert not [finding for finding in body.findings if "REQ-001" in finding.artifact_ids]


def test_evaluate_by_tag_and_sha_identical(client: TestClient, committed_manifest) -> None:
    by_tag = evaluate(client, "baseline-b")
    response = client.post(
        "/api/assurance/evaluate",
        json={"baseline": committed_manifest.tags["baseline-b"]},
    )
    assert response.status_code == 200
    assert FindingsResponse.model_validate(response.json()) == by_tag


def test_unknown_baseline_is_404(client: TestClient) -> None:
    response = client.post("/api/assurance/evaluate", json={"baseline": "baseline-z"})
    assert response.status_code == 404
    assert response.json()["code"] == "baseline-not-found"


def test_unknown_policy_is_400(client: TestClient) -> None:
    response = client.post(
        "/api/assurance/evaluate",
        json={"baseline": "baseline-a", "policy": "invented"},
    )
    assert response.status_code == 400
    assert response.json()["code"] == "invalid-request"
```

### Documentation

`docs/stories/AS-01.md`:
```markdown
# AS-01 — Missing coverage/link findings

**Milestone:** M1 — AI-free vertical slice · **Owner:** C · **Implementer:** OMP (shared API
integration) · **Status:** refined; implementation in progress.

| Record | Value |
| --- | --- |
| Roadmap / feature | F-05 Assurance · roadmap §6 AS-01 |
| GitHub story | [#2](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/2) — verified OPEN 2026-11-13T03:56:41Z (`gh issue view`), milestone "M1 — AI-free vertical slice" |
| Parent feature issue | [#1](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/1) |
| Canonical criteria | [AS-01.feature](AS-01.feature), sha256 `835b6d313960624402eccdcf4b51ca5c87ee790ec0249df7a7e72a0ec95a8c85` |
| Dependencies | DT-04 (#23) merged at `c43541b29d62186a4aa7fee32fed98720fc5f921`; DT-03 links; policy tables |
| Upstream obligation | Roadmap §4 finding contract, §6 F-05; ADR 0005; project-definition REQ-105 (draft) |

## User outcome

A systems engineer can run assurance for a baseline and see which requirements lack accepted
verification, with a finding that names the rule, the requirement, and the evaluated commit — not a
count that hides its inputs.

## Scope

* `DeterministicAssuranceEvaluator` over `ArtifactRepository`, implementing only
  `RULE-MISSING-VERIFICATION-LINK` in M1.
* A requirement is missing verification when it has no accepted `verified_by` link to an existing
  scenario at the evaluated baseline. Proposals do not count.
* Findings use `make_finding` (canonical fingerprint), severity/type from `policy.py`, the resolved
  commit SHA in `evaluated_baseline`, and `artifact_revisions` for the requirement.
* `POST /api/assurance/evaluate` becomes implemented; `GET /api/findings` keeps returning the
  reviewed sample responses until the rule set is complete (M2), so M2 findings are not silently
  dropped.

## Non-goals

`missing_implementation_link`, `reverification_required`, `verification_failed`,
`candidate_pending_review`, and lifecycle rules (AS-02/AS-03 and later); changing the findings
replay; model calls; policy authoring beyond the default policy.

## Preservation boundaries

Response shapes and the finding fingerprint are unchanged. The oracle's missing-verification
finding for `REQ-002` is the independent expectation: the evaluator's explanation template matches
the hand-labeled wording, and the finding equals the oracle entry (rule, type, severity, artifact
ids, evidence ids, fingerprint). `GET /api/findings` behavior is unchanged.

## Design impact

* `app/assurance/rules.py`: `DeterministicAssuranceEvaluator`.
* `app/api/deps.py`: evaluator dependency.
* `app/api/routes.py`: replace the 501 for `/api/assurance/evaluate`; add the `assurance` tag.
* `app/main.py`: construct the evaluator with the store.
* `tests/test_assurance_rules.py`: oracle comparisons for both baselines, proposal non-counting,
  healthy requirement, pinning/fingerprint, and error cases.
* Docs: `docs/api-contracts.md`, `docs/domain-contracts.md` (M1 rule subset statement).

Assumptions (load-bearing):

1. Only accepted `verified_by` links whose target is an existing scenario satisfy verification.
2. A superseded requirement is still evaluated by this rule; lifecycle review is a separate
   finding (the fixture's REQ-003 has an accepted link, so no missing-verification finding).
3. Findings are sorted by fingerprint for deterministic responses.
4. Policy `null`/`"default"` selects the declared tables; any other name is 400 `invalid-request`.

## Refinement disposition

Derived from the owner-authored issue intake and roadmap §6; boundary/failure scenarios were added
without weakening the intake. No separate human refinement sign-off is recorded, and the draft
project definition is not treated as an approved requirements baseline.

## Verification mapping

| Scenario | Observable check | Pytest selector |
| --- | --- | --- |
| SCN-701 missing verification | baseline-a finding equals the oracle entry (rule, severity, ids, evidence, fingerprint, explanation) | `backend/tests/test_assurance_rules.py::test_evaluate_matches_the_oracle_missing_verification_finding` |
| SCN-702 proposal does not count | only REQ-002 is reported; LNK-007 is not accepted | `::test_evaluate_does_not_count_proposals` |
| SCN-703 healthy requirement | REQ-001 never appears | `::test_evaluate_leaves_a_covered_requirement_alone` |
| SCN-704 explainability/pinning | baseline-b finding pins the resolved SHA and the canonical fingerprint; tag and SHA requests are identical | `::test_evaluate_matches_the_oracle_missing_verification_finding` (baseline-b), `::test_evaluate_by_tag_and_sha_identical` |
| SCN-705 error cases | unknown baseline 404, unknown policy 400 | `::test_unknown_baseline_is_404`, `::test_unknown_policy_is_400` |

A mapping row is not an execution result; the run record carries the actual invocation and result.

## Verification plan

Focused assurance tests, full offline suite, HTTP probe of the evaluate endpoint, fixture drift,
ruff, and the network-denied suite.
```

```diff
diff --git a/docs/STATUS.md b/docs/STATUS.md
index 5de0322..accc9cb 100644
--- a/docs/STATUS.md
+++ b/docs/STATUS.md
@@ -2,10 +2,10 @@
 
 ```text
 Date:                2026-11-13
-Current branch:      feat/23-dt-04-thread (from main 0970f7a)
+Current branch:      feat/2-as-01-missing-verification (from main c43541b)
 Milestone:           M0 — exit gate SATISFIED by re-review round 2 (historical record below)
                      M1 — IN PROGRESS; gate NOT yet satisfied
-Active task:         DT-04 (#23) requirement thread, evidence, and the store/API cutover
+Active task:         AS-01 (#2) missing coverage/link findings
 Independent review:  docs/reviews/M0-review.md — first review: "M0 not verified"
                      docs/reviews/M0-rereview-1.md — re-review round 1 (GPT-6.1 Sol, xhigh):
                      NEEDS_INPUT; R1–R7 all repaired; AC-1.1…AC-1.8 and AC-2.1…AC-2.5 all PASS;
@@ -20,7 +20,9 @@ Historical (SETUP-01, 2026-11-12): the commit-reference slice landed via PR #42;
                      had 107 passed; the SETUP-01 tree then had 135 passed (also under an
                      OS-level network denial). Outstanding owner actions: #18/#19 closure, the
                      FT-03/project-definition reviews, the required-check ruleset, README work item.
-Tests executed:      DT-04 (in progress): cutover suite recorded in docs/reports/omp-dt-04-thread/.
+Tests executed:      AS-01 (in progress): focused assurance suite in docs/reports/omp-as-01-missing-link/.
+                     DT-04 approved snapshot: 227 passed; PR #47 merged as c43541b with both
+                     hosted checks passing; issue #23 closed.
                      DT-03 approved snapshot: 219 passed; PR #46 merged as 0970f7a with both
                      hosted checks passing; issue #22 closed.
                      DT-02 approved snapshot: 208 passed; PR #45 merged as 590e776 with both
@@ -50,8 +52,8 @@ not claim that draft as an approved baseline.
 | DT-01 requirements + scenarios parsed | [#20](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/20) | B | [DT-01.feature](stories/DT-01.feature) | **merged** PR [#44](https://github.com/anthonygraca/gherkin-knowledge-graph/pull/44) → `26a25d0`; APPROVE at submission 5; issue closed |
 | DT-02 source/test artifacts | [#21](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/21) | B | [DT-02.feature](stories/DT-02.feature) | **merged** PR [#45](https://github.com/anthonygraca/gherkin-knowledge-graph/pull/45) → `590e776`; APPROVE at submission 4; issue closed |
 | DT-03 typed links + review state | [#22](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/22) | B | [DT-03.feature](stories/DT-03.feature) | **merged** PR [#46](https://github.com/anthonygraca/gherkin-knowledge-graph/pull/46) → `0970f7a`; APPROVE at submission 2; issue closed |
-| DT-04 requirement thread | [#23](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/23) | B | [DT-04.feature](stories/DT-04.feature) | refined; implementation in review |
-| AS-01 missing-link finding | [#2](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/2) | C | not yet written | eligible after DT-04 |
+| DT-04 requirement thread | [#23](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/23) | B | [DT-04.feature](stories/DT-04.feature) | **merged** PR [#47](https://github.com/anthonygraca/gherkin-knowledge-graph/pull/47) → `c43541b`; APPROVE at submission 2; issue closed |
+| AS-01 missing-link finding | [#2](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/2) | C | [AS-01.feature](stories/AS-01.feature) | refined; implementation in review |
 | AS-04 findings/coverage summary | [#26](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/26) | C | not yet written | eligible after AS-01 |
 
 Per-task reports live under `docs/reports/omp-<task-slug>/`; each carries the AC-to-check table,
diff --git a/docs/api-contracts.md b/docs/api-contracts.md
index fa75efc..620ffbe 100644
--- a/docs/api-contracts.md
+++ b/docs/api-contracts.md
@@ -122,9 +122,9 @@ not a requirement root (M1 assembles requirement threads; other roots are a docu
 ### `GET /api/findings?baseline=…`
 
 Findings for one baseline, ordered as in the oracle. **M1 replays reviewed sample findings**
-generated from `fixtures/banking-demo/expected/baseline-*.json`; `POST /api/assurance/evaluate` is
-contract-only in this snapshot (501; AS-01…AS-03). The replay remains until the rule set is
-implemented, so M2 findings are not silently dropped from this response.
+generated from `fixtures/banking-demo/expected/baseline-*.json`; `POST /api/assurance/evaluate`
+runs the implemented M1 rule subset. The replay remains until the rule set is implemented, so M2
+findings are not silently dropped from this response.
 
 ```json
 {
@@ -184,6 +184,50 @@ revision → 404 `baseline-not-found`; malformed repository content → 500 `fix
 missing built repository → 500 `fixture-data-missing` with the build instruction. A revision that is
 not a named baseline is ingestable; `baseline` then reports the SHA.
 
+## Assurance
+
+### `POST /api/assurance/evaluate`
+
+Runs the implemented deterministic rules for one baseline. M1 implements only
+`RULE-MISSING-VERIFICATION-LINK`: a requirement with no accepted `verified_by` link to an existing
+scenario. Proposals never satisfy it. `GET /api/findings` continues to replay the reviewed sample
+responses until AS-02/AS-03 complete the rule set.
+
+Request:
+
+```json
+{ "baseline": "baseline-a", "policy": null }
+```
+
+Response:
+
+```json
+{
+  "schema_version": "0.2.0",
+  "baseline": "baseline-a",
+  "findings": [
+    {
+      "finding_id": "FND-8e701f84ea44fa6c",
+      "finding_type": "missing_verification_link",
+      "status": "open",
+      "severity": "high",
+      "artifact_ids": ["REQ-002"],
+      "evaluated_baseline": "0f8607b29d1ccb423062d856835f5310c9f54aa3",
+      "evidence_ids": [],
+      "explanation": "REQ-002 has no accepted verification scenario at baseline-a.",
+      "rule_id": "RULE-MISSING-VERIFICATION-LINK",
+      "artifact_revisions": {
+        "REQ-002": "0f8607b29d1ccb423062d856835f5310c9f54aa3"
+      }
+    }
+  ]
+}
+```
+
+Errors: unknown baseline → 404 `baseline-not-found`; unknown policy → 400 `invalid-request`; invalid
+body → 422. Findings are deterministic and offline; `evaluated_baseline` and `artifact_revisions`
+always carry the resolved commit SHA.
+
 ## Discovery
 
 ### `POST /api/discovery`
@@ -235,17 +279,16 @@ first, so the contract is real even though the behaviour is not implemented:
 | Endpoint | Body | Owning work |
 | --- | --- | --- |
 | `POST /api/links/{link_id}/review` | `{ "decision": "accept" \| "reject", "reviewer_id": "rv-ana", "reason": null }` | AS-06 (C, M1/M2) |
-| `POST /api/assurance/evaluate` | `{ "baseline": "baseline-a", "policy": null }` | AS-01…AS-03 (C-PR1, M1/M2) |
 
 ```json
 {
   "type": "urn:cta:error:not-implemented",
   "title": "Not implemented in this milestone",
   "status": 501,
-  "detail": "Deterministic rule evaluation is implemented with AS-01…AS-03 against the fixture oracle. GET /api/findings currently returns the reviewed sample findings.",
-  "instance": "/api/assurance/evaluate",
+  "detail": "Link review with reviewer identity, timestamp, reason, and immutable decision history is implemented with AS-06. Accepting a link will not change verification status: an accepted link is not evidence of behaviour.",
+  "instance": "/api/links/LNK-007/review",
   "code": "not-implemented",
-  "story": "AS-01, AS-02, AS-03 (C-PR1)",
+  "story": "AS-06 (C-PR1 onward)",
   "milestone": "M1/M2"
 }
 ```
diff --git a/docs/architecture.md b/docs/architecture.md
index fa59b3d..51ec830 100644
--- a/docs/architecture.md
+++ b/docs/architecture.md
@@ -39,7 +39,8 @@ Two rules explain most of the layout:
 | `app/domain/policy.py` | Rule → finding type and severity policy | Contract |
 | `app/persistence/` | `IngestedStore`: ingests a revision and caches artifacts, links, evidence, and assembled threads | Working implementation (in-process) |
 | `app/discovery/fake.py` | Fixture-backed candidate provider | Working implementation (deliberately fake) |
-| `app/assurance/sample_findings.py` | Replay of reviewed sample findings | Mock service (rule engine arrives with AS-01) |
+| `app/assurance/rules.py` | `DeterministicAssuranceEvaluator` (M1: missing-verification rule) | Working implementation (M1 subset) |
+| `app/assurance/sample_findings.py` | Replay of reviewed sample findings for `GET /api/findings` | Mock service (full rule set in M2) |
 | `app/api/` | Routes, dependencies, RFC 9457 problem documents | Working |
 | `app/ingestion/` | Revision-pinned parsing: requirements/Gherkin (DT-01), source/test (DT-02), links (DT-03), evidence + thread assembly (DT-04) | Implemented |
 | `frontend/` | React/TypeScript dashboard | Absent by design; created in C-PR1 |
diff --git a/docs/domain-contracts.md b/docs/domain-contracts.md
index eac5ac8..84fd1cc 100644
--- a/docs/domain-contracts.md
+++ b/docs/domain-contracts.md
@@ -109,6 +109,11 @@ response), `score` (0..1), `discovery_provider`, `model_version`, `index_revisio
 Severity and type come from the policy tables in `app/domain/policy.py`; the oracle is asserted
 against those tables, so changing the policy is a deliberate, reviewed edit.
 
+M1 implements `RULE-MISSING-VERIFICATION-LINK` in `POST /api/assurance/evaluate`; the remaining
+rules are specified here and implemented with AS-02/AS-03 (M2). `GET /api/findings` keeps replaying
+the reviewed sample findings until that rule set is complete, so M2 findings are not silently
+dropped.
+
 **Fingerprint.** `finding_id = "FND-" + sha256(rule_id | finding_type | sorted artifact_ids)[:16]`
 with `sha256` truncated to 16 hex characters. It deliberately excludes the baseline, the evidence
 set, and all prose, so the same underlying problem keeps one identity across baselines — which is
```

## 5. Implementation context

* The evaluator resolves the canonical baseline, gets the pinned commit via `commit_of`, reads all
  artifacts and accepted links through `ArtifactRepository`, and emits a finding for each
  requirement with no accepted `verified_by` link to an existing scenario.
* `make_finding` supplies the canonical fingerprint; severity/type come from `policy.py`;
  `artifact_revisions` pins the requirement's revision.
* `GET /api/findings` still replays the reviewed sample; the API docs state that explicitly and
  identify the remaining M2 rules.
* Targeted reads: `backend/app/domain/models.py`, `backend/app/domain/policy.py`,
  `docs/domain-contracts.md`, `backend/tests/conftest.py`.

## 6. Evidence

| Criterion | Check | Result |
| --- | --- | --- |
| SCN-701 | `tests/test_assurance_rules.py::test_evaluate_matches_the_oracle_missing_verification_finding` (both baselines, full finding comparison) | PASS |
| SCN-702 | `::test_evaluate_does_not_count_proposals` | PASS |
| SCN-703 | `::test_evaluate_leaves_a_covered_requirement_alone` | PASS |
| SCN-704 | oracle comparison at baseline-b + `::test_evaluate_by_tag_and_sha_identical` | PASS |
| SCN-705 | `::test_unknown_baseline_is_404`, `::test_unknown_policy_is_400` | PASS |

Actual invocations and exits, captured 2026-11-13T04:01:09Z–04:01:18Z:

```text
uv run --project backend pytest backend/tests -q exit 0  233 passed, 1 warning in 7.62s
uv run --project backend python tools/fixturectl.py verify  exit 0  reproducible and current
uv run --project backend ruff check .            exit 0  All checks passed
uv run --project backend ruff format --check .   exit 0  all files formatted
git diff --check                                 exit 0
unshare -rn backend/.venv/bin/python -m pytest backend/tests -q  exit 0  233 passed
```

HTTP probe on port 8012 (server started/stopped by OMP; captures in the run directory):

```text
POST /api/assurance/evaluate baseline-a → 200
  FND-8e701f84ea44fa6c, missing_verification_link, high, ["REQ-002"],
  evaluated_baseline 0f8607b29d1ccb423062d856835f5310c9f54aa3
baseline-b by tag and by SHA → byte-identical 200
baseline-z → 404 baseline-not-found; policy "invented" → 400 invalid-request
```

NOT RUN: frontend (AS-04), M2 rules, link-review mutations.

## 7. File-integrity requirement

The manifest in section 3 is the reviewed snapshot. If any manifest hash changed, the snapshot is
not the one reviewed. Do not edit files, install dependencies, regenerate fixtures, or commit.

## Reviewer instructions (mandatory)

You are the independent CTA implementation reviewer using GPT-6.1 Sol xhigh. Decide whether this exact snapshot satisfies the supplied story, every applicable Gherkin criterion, and repository invariants. Treat OMP's summaries and test results as claims to check against the supplied artifacts and targeted source inspection. Check proposal/accepted/evidence separation, real port compatibility, revision/content-hash semantics, honest errors/501s, independent oracle expectations, offline defaults, and generated-file discipline where relevant. Do not demand implementation of a later milestone. Do not edit files, implement repairs, regenerate fixtures, commit, or delegate. Ask OMP for missing runtime evidence; distinguish observed defects from hypotheses and unavailable checks. Return an AC-by-AC PASS, FAIL, or NOT VERIFIED assessment and actionable findings with stable IDs, severity, blocking status, AC/invariant, path/line, expected/actual behavior, and smallest correction/recheck. Keep optional suggestions and unrelated pre-existing defects separate. Return exactly one verdict: APPROVE, REQUEST_CHANGES, or NEEDS_INPUT. APPROVE requires every applicable criterion/check to be satisfied, no unresolved blocker, and the exact snapshot identified. In later rounds verify prior dispositions and regressions while retaining the complete acceptance assessment. A passing process, passing tests, or exhausted review limit is not approval. Agent review cannot attest human labeling or human link decisions.
