# Independent implementation review — DT-04, submission 2 of 7

## 1. Submission context and prior dispositions

**Task:** DT-04 — Retrieve the thread associated with a requirement.
**Roadmap:** F-03 Links, roadmap §6 DT-04; milestone **M1 — AI-free vertical slice**.
**GitHub story:** issue **#23**, verified OPEN 2026-11-13T03:12:49Z. **Owner:** B.
**Implementer/integrator:** OMP. **Repository:** `<task_repo>` (read-only sandbox).
**Base:** `0970f7aa3334d88b3b19e29fae446e0eeb84593d`. **Branch:** `feat/23-dt-04-thread`.
**Submission:** 2 of 7.

Round 1 (`docs/reviews/DT-04-review.md`) returned REQUEST_CHANGES:

* **R1** — missing-repository ingestion returned 404 `baseline-not-found` instead of 500
  `fixture-data-missing` (blocking).
* **R2** — the findings description said evaluate runs implemented rules while it returns 501.
* **R3** — SCN-611’s mapping cited an artifact tag/SHA test, not the thread endpoint.

All three are addressed; none was dismissed.

### User outcome

A reviewer can request one requirement's thread at a baseline and see its accepted chain and
evidence in one call, with proposals kept separate and the response assembled from ingested
repository data.

### Scope / non-goals (unchanged)

Ingested store, evidence, shared thread assembly, API cutover, additive inventory endpoint, contract
0.2.0, fixture regeneration. Non-goals: general repository hosting, durable storage, non-requirement
roots, link review mutations, assurance rules.

### Proposed commit reference

`feat(thread): [issue #23] serve requirement threads from ingested revisions`, body `Refs #23`.

## 2. Acceptance criteria (canonical snapshot)

File `docs/stories/DT-04.feature`, sha256
`02301bee448f33efc07d9e0e1d37ccafa1d1a2b9a9bd303bfa622a0fd5eb94e9` (unchanged).

```gherkin
# Canonical acceptance specification for DT-04 (#23), M1.
# Source criteria: the GitHub story intake at
# https://github.com/anthonygraca/gherkin-knowledge-graph/issues/23 (verified 2026-11-13T03:12:49Z)
# and roadmap §6 F-03. Failure, boundary, and cutover scenarios were added during refinement; the
# two intake scenarios keep their wording.
# Verified by the pytest selectors mapped in DT-04.md. These scenarios are not currently bound
# to or executed by a Gherkin runner.
@DT-04 @issue-23 @M1
Feature: DT-04: Retrieve the thread associated with a requirement
  A thread is assembled from the ingested revision: the requirement, the accepted links reachable
  from it, the artifacts those links reach, and the evidence for the scenarios and tests in the
  thread. Proposals remain a separate array. The response is independent of tag-vs-SHA wording and
  of any precomputed example file.

  @SCN-611
  Scenario: Thread for a fully linked requirement
    Given the fixture repository is ingested at "baseline-b"
    When the thread for "REQ-001" is requested
    Then the response contains "REQ-001", "SCN-001", "CODE-001", and "TEST-001"
    And the accepted links "LNK-001", "LNK-002", and "LNK-003"
    And the evidence recorded for "SCN-001"
    And the response is identical whether the baseline is given as the tag or the commit SHA

  @SCN-612
  Scenario: Thread for a requirement with only a proposal
    Given "REQ-002" has no accepted links
    When the thread for "REQ-002" is requested
    Then "accepted_links" is empty
    And "LNK-007" appears only in "proposed_links"

  @SCN-613
  Scenario: The thread is assembled from the ingested revision
    Given the committed thread example files are unavailable
    When the thread for "REQ-001" is requested
    Then the same thread is served from parsed repository data
    And its schema_version matches the running contract

  @SCN-614
  Scenario: Unknown and non-requirement roots are documented 404s
    Given "REQ-999" does not exist
    When its thread is requested
    Then the response is 404 "artifact-not-found"
    And a thread for an existing source artifact "CODE-001" is 404 "thread-not-found"

  @SCN-615
  Scenario: Re-ingesting a revision reports what it found
    Given the fixture repository at "baseline-a"
    When an ingestion run is requested
    Then it reports the artifact, accepted-link, proposed-link, and evidence counts
    And its run id is deterministically derived from the resolved commit

  @SCN-616
  Scenario: Artifact inventory for a baseline
    Given the fixture repository is ingested at "baseline-a"
    When artifacts are listed for that baseline
    Then every requirement, scenario, source, and test artifact is returned
    And filtering by artifact type returns only that type
```

Refinement disposition: owner-authored issue intake + roadmap §6; cutover/failure/boundary
scenarios were added. No separate human refinement sign-off is recorded.

Repository constraints (AGENTS.md): contract changes bump `SCHEMA_VERSION` and update docs in the
same change; generated fixtures are regenerated, never hand-edited; proposals ≠ accepted links ≠
verification; offline defaults.

## 3. Snapshot and manifest

Snapshot captured 2026-11-13T03:42Z. Manifest (sha256 of every task file, including fixtures):

```text
b486374b06ad0f1f6492a95b8a2af2a0c52b27039011e8566f13d75762a0f65d  backend/app/domain/api.py
17e65def989f2c24c5f4a7dc8514fe9c9e6c72b1a1eb52602f174de45292382d  backend/app/domain/ports.py
4200999207d79bffbd59cd30b72959b2039c4b1067e827087ee75b037918ea0e  backend/app/ingestion/__init__.py
88db8934b47d78f2256a40b6f5bfca0e72cc062a4c297b282a66c0242ae385cf  backend/app/ingestion/evidence.py
761fee3b1944516158773161b49747b6430853f7456d3c6be7028a148c783f07  backend/app/ingestion/revision.py
e930e3043bb952c63ac3d9afb05bf7227ea3437284946188083187a04a4d47a4  backend/app/ingestion/thread.py
b97341218d37c7f2ae78f03f2259478ab4b321f658cee0737a14397e9488c064  backend/app/persistence/__init__.py
5aa0cac1fa9bc5ccc997c9d6a335de42e6e0f0ef984e0ad82b64fb7e85535e44  backend/app/persistence/ingested.py
397de92385a945305a221da84f98841dd031281c64acc3c1f96c87055d749341  backend/app/settings.py
cd722cd24a15b23666731258391f8b6c1d1b943838248f3d81df6e5f3cf8275b  backend/app/version.py
b41c46ce5c0df6e781cdee3b4915aec6f4e59863501305e2040d6e9a6dd9b9cc  backend/app/api/deps.py
d19e2236c28e20db9a7d997bfaed63cf578ec9018d9c5fab3142b8dfb68a2eb6  backend/app/api/routes.py
e016b3651009cd3e02e21ac58bc17cbb06e3f1404dfe3581b9602608dae534cd  backend/app/main.py
0072e017e27ff488b575300f1be324efe0a11ef7f84e92a5b960df210ac7bcae  tools/fixturectl.py
db4b86fe1d073ec0c0c4b0c6cf7c76e7d3a9833f079576364e6e042d59e4ff47  backend/tests/conftest.py
47b14c71abdc49150cb3a4ce160491649192255e03f79791ebd565620ebc5444  backend/tests/test_api_contract.py
cec02ad839f3765aea67b2778a978eab3ef03d791e679c714f51320c8500566a  backend/tests/test_contract_boundaries.py
e000af68929cd65e750c94f2dc8e80f17872841abebeedc0ed68f65ac27c47bc  backend/tests/test_fixture_oracle.py
7ba5d4729babe505ce7376b211d9c148cad15671b671da748895cab9405df6ba  backend/tests/test_ingested_store.py
02301bee448f33efc07d9e0e1d37ccafa1d1a2b9a9bd303bfa622a0fd5eb94e9  docs/stories/DT-04.feature
77a94775b3697b80e6b7f4d6d1f9aad5f66d0909b82157cf917f94d978523841  docs/stories/DT-04.md
98c1d9bfbf0f03a8522ab24ff146edb1fcc61ddd9a135ef8466d39a378d9f5dc  docs/api-contracts.md
cabb8145a63df1759c2ada77fae90b9710011e5b7092d6903bf3b9cededf871c  docs/domain-contracts.md
e6ee7b22f41873915d75d958ffc3fd1e53cd7d3c581994e0df2a0d12350ef4c0  docs/architecture.md
55fd461317745e1305f1104f383d543a0ba50ab896351559f9cc14f6d3d34d11  docs/STATUS.md
d627db84f64daa865db84806ec9bb9bae1532581fb833e0a1846b00be9e09ec7  fixtures/banking-demo/history.json
788fd1382c7c2123fcde872065e9027e8fec9ab15781cdba5be708e1cf017b9f  fixtures/banking-demo/expected/baseline-a.json
8354e0115845fa6706d9a207f040e61e4d6be35bf1e5d47e8ed87200e488b89e  fixtures/banking-demo/expected/baseline-b.json
7b0eccbdfb2575b07eea414d966a22638394c2ea65d33e9b7b5a976f557116ac  fixtures/banking-demo/expected/baselines.json
287bed870b486c939cfdb7e02edc7ba3d37e0778aed3321fe2a55a07e1565b21  fixtures/banking-demo/expected/candidate-links.json
39e11eb7a2257d420b20dcb9a52174426105258adacfad6ac1fca70eb057b2cc  fixtures/banking-demo/tree/evidence/accepted-links.json
3b9bbf60af0d46d353c29037bcf8f13e7b7ef63138ddf5e330de0b5bafefce4d  fixtures/banking-demo/tree/evidence/proposed-links.json
22d15bcb8893aff4a83e221cf034a87b9fdb20a6378517e5902ea358def315b8  fixtures/banking-demo/changes/02-baseline-a-evidence/evidence/verification-runs.json
f0dbc962aef0aaff5453c75208c9961dc940584d05d2735213cc540680890236  fixtures/banking-demo/changes/04-baseline-b-evidence/evidence/verification-runs.json
91b43a33e2c09418fdd49fa19149abd764d227c7855c8763d0d56bbff2cca35b  fixtures/api-responses/README.md
3aa2987be0c85299f40ec609f6ee8684e4eaceebb52f7723b8d85cd2b99a6a82  fixtures/api-responses/snapshot.json
1f84a55839d37fcb916fc14e9b028af0df72a02a41e8d3c81be3f80542980c64  fixtures/api-responses/findings.baseline-a.json
ce2e05049da4cc0dfee4a9d1ca4aba235c0336ce71b3f971b602f9e191b70a37  fixtures/api-responses/findings.baseline-b.json
a39153a07e9500d12000487b343e9ac658ccde0be56694f7ddbb6294990070ad  fixtures/api-responses/discovery.REQ-002.json
f176b89407efc7b4f24911fec76417a9a4581ed1ea81f1b1c999b9dd4500a4c0  fixtures/api-responses/discovery.SCN-001.json
ca8d612d31fe20ca6d7decc8339e4a397470d7ae224552e498da9c4c0208c4df  fixtures/api-responses/discovery.SCN-002.json
b49b97d4474e588875c16ce700762fc742ffbb70b83ac140a8ba9aad97c9c93f  fixtures/api-responses/discovery.SCN-003.json
fad6f39e91be28907b71cf19878b62babf9802986ad57aa32547dbb56126cd5e  fixtures/api-responses/threads/REQ-001.baseline-a.json
989b551b700f7035af335789306a9bcb36c2779d0384305b5a1695cdc8ac9e4d  fixtures/api-responses/threads/REQ-001.baseline-b.json
0a988cfc90fea96a8b968735aec552a0d3173f2137820a4174672d2718f2f0cf  fixtures/api-responses/threads/REQ-002.baseline-a.json
69117eea3eac9f978f0516627e56cec24882bad20609d2263e88aefee0fced70  fixtures/api-responses/threads/REQ-002.baseline-b.json
1c7f3dee2536ac7bf523b22df93cbdcf107cbb13bc52b18b5c328a00d80dfc10  fixtures/api-responses/threads/REQ-003.baseline-a.json
dabff48526cd7e8586a7860fcd6c7d2ae78abb30e82459d71792416a76c0441c  fixtures/api-responses/threads/REQ-003.baseline-b.json
52975cc7cd38d4336bd054002a278a38ba88a029e0fd29ce9df41cf953808532  docs/reports/omp-dt-04-thread/IMPLEMENTATION.md
5d23081e3b932574dc612f1ee0380725d7e736c0a0ca8fc5dc11ec3ef60e34b5  docs/reports/omp-dt-04-thread/PROMPT_LOG.md
d8d577ffafa6a22a51a395ab5f49f5a251dde7e7b3cedb30f541b5f5374f139e  docs/reports/omp-dt-04-thread/METRICS.md
6fed84539e3c5267389b0bac5d88025631254e77121c588e9dacff5791aa11ff  docs/reviews/DT-04-review.md
5d933330c1797c319f9c2eb74fccdd16186bd6efbec51be36c4b73a02584417a  docs/reviews/DT-04-review-prompt.md
```

`SCHEMA_VERSION = 0.2.0` (MINOR: new endpoint), `PACKAGE_VERSION = 0.1.0`. No dependency change.
Baseline SHAs: `baseline-a 0f8607b29d1ccb423062d856835f5310c9f54aa3`,
`baseline-b 156ad72b01b361970cc22229e7a2b17f9d6bcb85`. Generated fixtures are unchanged from
submission 1 except that the input schema-version bump was already included; `fixturectl verify`
passes.

## 4. Changes since submission 1

### Store error path (R1)

```diff
diff --git a/backend/app/api/routes.py b/backend/app/api/routes.py
index ae5ec6b..94b95f8 100644
--- a/backend/app/api/routes.py
+++ b/backend/app/api/routes.py
@@ -2,7 +2,8 @@
 
 Endpoints are grouped by intent, which is also the honesty axis of the system:
 
-* **reads** — real implementations over the fixture-backed store (M0).
+* **reads** — real implementations over the ingested fixture repository.
+* **ingestion** — parses the configured repository at a revision.
 * **discovery** — real implementation, fixture provider; returns proposals only.
 * **contract-only** — the shape is frozen and documented, the implementation belongs to a
   later milestone; the response is 501 with the owning story, never fake success.
@@ -16,6 +17,7 @@ from fastapi import APIRouter, Path, Query
 
 from app.api.deps import FindingsDep, ProvidersDep, RepositoryDep, SettingsDep, StoreDep
 from app.domain.api import (
+    ArtifactListResponse,
     DiscoveryRequest,
     DiscoveryResponse,
     EvaluateRequest,
@@ -27,6 +29,7 @@ from app.domain.api import (
     ReviewRequest,
     ThreadResponse,
 )
+from app.domain.enums import ArtifactType
 from app.domain.errors import FeatureNotImplemented
 from app.domain.models import ARTIFACT_ID_PATTERN, LINK_ID_PATTERN, Artifact, TraceLink
 from app.version import PACKAGE_VERSION, SCHEMA_VERSION
@@ -47,7 +50,7 @@ _PROBLEM_404: dict[str, object] = {
 }
 _PROBLEM_501: dict[str, object] = {
     "model": ProblemDetails,
-    "description": "Contract-only endpoint in M0; the problem document names the owning story.",
+    "description": "Contract-only endpoint; the problem document names the owning story.",
 }
 
 
@@ -70,6 +73,31 @@ def get_health(settings: SettingsDep, store: StoreDep, providers: ProvidersDep)
     )
 
 
+@router.get(
+    "/api/artifacts",
+    response_model=ArtifactListResponse,
+    tags=["reads"],
+    responses={404: _PROBLEM_404},
+    summary="Artifact inventory for a baseline",
+)
+def list_artifacts(
+    repository: RepositoryDep,
+    baseline: Annotated[str | None, BASELINE_QUERY] = None,
+    artifact_type: Annotated[
+        ArtifactType | None, Query(description="Restrict to one artifact type.")
+    ] = None,
+) -> ArtifactListResponse:
+    canonical = repository.resolve_baseline(baseline)
+    artifacts = repository.list_artifacts(canonical)
+    if artifact_type is not None:
+        artifacts = [artifact for artifact in artifacts if artifact.artifact_type is artifact_type]
+    return ArtifactListResponse(
+        schema_version=SCHEMA_VERSION,
+        baseline=canonical,
+        artifacts=sorted(artifacts, key=lambda artifact: artifact.artifact_id),
+    )
+
+
 @router.get(
     "/api/artifacts/{artifact_id}",
     response_model=Artifact,
@@ -97,7 +125,7 @@ def get_thread(
     store: StoreDep,
     baseline: Annotated[str | None, BASELINE_QUERY] = None,
 ) -> ThreadResponse:
-    """Fixture-only replay of a precomputed thread; DT-04 (#23) replaces it with assembled data."""
+    """Assembled from the ingested revision; proposals and evidence stay separate arrays."""
     return store.thread(artifact_id, baseline=baseline)
 
 
@@ -108,10 +136,11 @@ def get_thread(
     responses={404: _PROBLEM_404},
     summary="Assurance findings for a baseline",
     description=(
-        "M0 replays the reviewed sample findings committed under `fixtures/api-responses/`, "
-        "which are generated from the hand-labeled oracle in `fixtures/banking-demo/expected/`. "
-        "Deterministic rule evaluation (AS-01…AS-03) replaces the replay in M1 and is tested "
-        "against the same oracle files."
+        "M1 replays the reviewed sample findings committed under `fixtures/api-responses/`, "
+        "generated from the hand-labeled oracle in `fixtures/banking-demo/expected/`. "
+        "`POST /api/assurance/evaluate` is contract-only in this snapshot (501; AS-01…AS-03). "
+        "`GET` keeps the reviewed sample until the rule set is implemented, so M2 findings are not "
+        "silently dropped."
     ),
 )
 def get_findings(
@@ -154,18 +183,20 @@ def post_discovery(
 @router.post(
     "/api/ingestion/run",
     response_model=IngestionResponse,
-    tags=["contract-only"],
-    responses={501: _PROBLEM_501, 422: {"model": ProblemDetails}},
-    summary="Ingest a repository revision (contract only in M0)",
+    tags=["ingestion"],
+    responses={400: _PROBLEM_400, 404: _PROBLEM_404, 422: {"model": ProblemDetails}},
+    summary="Ingest the configured repository at a revision",
 )
-def post_ingestion_run(payload: IngestionRequest) -> IngestionResponse:
-    raise FeatureNotImplemented(
-        story="DT-01, DT-02, DT-04 (B-PR1)",
-        milestone="M1",
-        detail=(
-            "Repository ingestion and revision-aware persistence are implemented in B-PR1. "
-            "Until then, reads are served from fixtures/api-responses/snapshot.json."
-        ),
+def post_ingestion_run(payload: IngestionRequest, store: StoreDep) -> IngestionResponse:
+    revision = store.ingest(payload.repository, payload.revision)
+    return IngestionResponse(
+        run_id=f"ing-{revision.commit[:12]}",
+        repository=payload.repository,
+        baseline=store.label_of(revision.commit),
+        artifact_count=len(revision.artifacts),
+        accepted_link_count=len(revision.accepted_links),
+        proposed_link_count=len(revision.proposed_links),
+        evidence_count=len(revision.evidence),
     )
 
 
```

### Tests (R1, R3)

```diff
diff --git a/backend/tests/test_api_contract.py b/backend/tests/test_api_contract.py
index c1120db..0e61565 100644
--- a/backend/tests/test_api_contract.py
+++ b/backend/tests/test_api_contract.py
@@ -6,14 +6,17 @@ import pytest
 from fastapi.testclient import TestClient
 
 from app.domain.api import (
+    ArtifactListResponse,
     DiscoveryResponse,
     FindingsResponse,
     HealthResponse,
+    IngestionResponse,
     ProblemDetails,
     ThreadResponse,
 )
 from app.domain.models import Artifact, finding_fingerprint
 from app.domain.oracle import BaselinesManifest, ExpectedFindingsFile, FixtureSnapshot
+from app.main import create_app
 from app.persistence.fixtures import load_model
 from app.settings import Settings
 from app.version import SCHEMA_VERSION
@@ -22,6 +25,7 @@ BASELINES = ("baseline-a", "baseline-b")
 
 CONTRACTED_PATHS = {
     "/health",
+    "/api/artifacts",
     "/api/artifacts/{artifact_id}",
     "/api/threads/{artifact_id}",
     "/api/findings",
@@ -279,13 +283,137 @@ def test_discovery_validates_its_payload(client: TestClient) -> None:
     assert client.post("/api/discovery", json={}).status_code == 422
 
 
+# ---------------------------------------------------------------------------------- artifacts
+
+
+def test_artifact_inventory_lists_and_filters(
+    client: TestClient, committed_manifest: BaselinesManifest
+) -> None:
+    response = client.get("/api/artifacts", params={"baseline": "baseline-a"})
+    assert response.status_code == 200
+    body = ArtifactListResponse.model_validate(response.json())
+    assert body.baseline == "baseline-a"
+    assert body.schema_version == SCHEMA_VERSION
+    assert len(body.artifacts) == 10
+    assert [item.artifact_id for item in body.artifacts] == sorted(
+        item.artifact_id for item in body.artifacts
+    )
+    assert {item.artifact_type.value for item in body.artifacts} == {
+        "requirement",
+        "scenario",
+        "source",
+        "test",
+    }
+
+    filtered = client.get(
+        "/api/artifacts", params={"baseline": "baseline-a", "artifact_type": "requirement"}
+    )
+    assert [
+        item.artifact_id for item in ArtifactListResponse.model_validate(filtered.json()).artifacts
+    ] == ["REQ-001", "REQ-002", "REQ-003"]
+
+    by_sha = client.get(
+        "/api/artifacts", params={"baseline": committed_manifest.tags["baseline-a"]}
+    )
+    assert by_sha.json() == response.json()
+
+    unknown = client.get("/api/artifacts", params={"baseline": "baseline-z"})
+    assert unknown.status_code == 404
+    assert unknown.json()["code"] == "baseline-not-found"
+
+
+# ---------------------------------------------------------------------------------- ingestion
+
+
+def test_ingestion_run_reports_counts(
+    client: TestClient, committed_manifest: BaselinesManifest
+) -> None:
+    response = client.post("/api/ingestion/run", json={"repository": "banking-demo"})
+    assert response.status_code == 200
+    body = IngestionResponse.model_validate(response.json())
+    assert body.baseline == "baseline-b"
+    assert body.run_id == f"ing-{committed_manifest.tags['baseline-b'][:12]}"
+    assert (
+        body.artifact_count,
+        body.accepted_link_count,
+        body.proposed_link_count,
+        body.evidence_count,
+    ) == (10, 6, 1, 3)
+
+    at_a = client.post(
+        "/api/ingestion/run", json={"repository": "banking-demo", "revision": "baseline-a"}
+    )
+    assert at_a.status_code == 200
+    body_a = IngestionResponse.model_validate(at_a.json())
+    assert body_a.baseline == "baseline-a"
+    assert body_a.run_id == f"ing-{committed_manifest.tags['baseline-a'][:12]}"
+    assert (
+        body_a.artifact_count,
+        body_a.accepted_link_count,
+        body_a.proposed_link_count,
+        body_a.evidence_count,
+    ) == (10, 6, 1, 2)
+
+    unknown_repository = client.post("/api/ingestion/run", json={"repository": "other"})
+    assert unknown_repository.status_code == 400
+    assert unknown_repository.json()["code"] == "invalid-request"
+
+    unknown_revision = client.post(
+        "/api/ingestion/run", json={"repository": "banking-demo", "revision": "no-such-rev"}
+    )
+    assert unknown_revision.status_code == 404
+    assert unknown_revision.json()["code"] == "baseline-not-found"
+
+
+def test_ingestion_with_a_missing_repo_is_fixture_data_missing(
+    fixture_settings: Settings, tmp_path
+) -> None:
+    app = TestClient(
+        create_app(
+            Settings(
+                repo_root=fixture_settings.repo_root,
+                fixtures_dir=fixture_settings.fixtures_dir,
+                fixture_repo_path=tmp_path / "absent",
+            )
+        )
+    )
+    response = app.post("/api/ingestion/run", json={"repository": "banking-demo"})
+    assert response.status_code == 500
+    assert response.json()["code"] == "fixture-data-missing"
+    assert "fixturectl.py build" in response.json()["detail"]
+
+
+def test_thread_by_tag_and_sha_are_identical(
+    client: TestClient, committed_manifest: BaselinesManifest
+) -> None:
+    by_tag = client.get("/api/threads/REQ-001", params={"baseline": "baseline-b"})
+    by_sha = client.get(
+        "/api/threads/REQ-001", params={"baseline": committed_manifest.tags["baseline-b"]}
+    )
+    assert by_tag.status_code == by_sha.status_code == 200
+    assert by_tag.json() == by_sha.json()
+
+
+def test_thread_matches_the_committed_example(
+    client: TestClient, fixture_settings: Settings
+) -> None:
+    for baseline in BASELINES:
+        for artifact_id in ("REQ-001", "REQ-002", "REQ-003"):
+            expected = load_model(
+                fixture_settings.api_responses_dir / "threads" / f"{artifact_id}.{baseline}.json",
+                ThreadResponse,
+            )
+            response = client.get(f"/api/threads/{artifact_id}", params={"baseline": baseline})
+            assert response.status_code == 200
+            assert ThreadResponse.model_validate(response.json()) == expected
+
+
 # ------------------------------------------------------------------- contract-only endpoints
 
 
 @pytest.mark.parametrize(
     ("path", "payload", "story"),
     [
-        ("/api/ingestion/run", {"repository": "banking-demo"}, "B-PR1"),
         ("/api/links/LNK-007/review", {"decision": "accept", "reviewer_id": "rv-ana"}, "AS-06"),
         ("/api/assurance/evaluate", {"baseline": "baseline-a"}, "AS-01"),
     ],
@@ -302,7 +430,7 @@ def test_contract_only_endpoints_are_honest(
     assert problem.milestone
 
 
-def test_contract_only_endpoints_still_validate_their_payloads(client: TestClient) -> None:
+def test_endpoints_still_validate_their_payloads(client: TestClient) -> None:
     assert client.post("/api/ingestion/run", json={}).status_code == 422
     assert (
         client.post(
```

### Documentation (R2, R3)

```diff
diff --git a/docs/api-contracts.md b/docs/api-contracts.md
index 9534520..fa75efc 100644
--- a/docs/api-contracts.md
+++ b/docs/api-contracts.md
@@ -18,17 +18,43 @@ with a tag and with that tag's SHA returns identical bodies. Version-pinning fie
 {
   "status": "ok",
   "package_version": "0.1.0",
-  "schema_version": "0.1.0",
+  "schema_version": "0.2.0",
   "fixture": "banking-demo",
   "baselines": ["baseline-a", "baseline-b"],
   "baseline_commits": {
-    "baseline-a": "67109fac965377629c9ab5835541aa64461db785",
-    "baseline-b": "c02064fed61bcfc6ade5ea14ac62f9eb1b5f5c54"
+    "baseline-a": "0f8607b29d1ccb423062d856835f5310c9f54aa3",
+    "baseline-b": "156ad72b01b361970cc22229e7a2b17f9d6bcb85"
   },
   "discovery_providers": ["fake"]
 }
 ```
 
+### `GET /api/artifacts?baseline=…&artifact_type=…`
+
+The artifact inventory at one baseline, sorted by `artifact_id`. `artifact_type` is optional
+(`requirement`, `scenario`, `source`, `test`). Added in schema 0.2.0; it lets the dashboard derive
+coverage without hard-coded identities.
+
+```json
+{
+  "schema_version": "0.2.0",
+  "baseline": "baseline-a",
+  "artifacts": [
+    {
+      "artifact_id": "REQ-001",
+      "artifact_type": "requirement",
+      "title": "Instant withdrawal availability",
+      "source_uri": "fixture://banking-demo/requirements/REQ-001.md",
+      "repository": "banking-demo",
+      "revision": "0f8607b29d1ccb423062d856835f5310c9f54aa3",
+      "content_hash": "sha256:…",
+      "locator": "requirements/REQ-001.md",
+      "metadata": { "status": "active" }
+    }
+  ]
+}
+```
+
 ### `GET /api/artifacts/{artifact_id}?baseline=…`
 
 Returns one version-specific `Artifact`. `artifact_id` must match `^(REQ|SCN|CODE|TEST)-\d{3}$`;
@@ -41,7 +67,7 @@ a malformed id is a 422, an unknown but well-formed id is a 404.
   "title": "Instant withdrawal availability",
   "source_uri": "fixture://banking-demo/requirements/REQ-001.md",
   "repository": "banking-demo",
-  "revision": "67109fac965377629c9ab5835541aa64461db785",
+  "revision": "0f8607b29d1ccb423062d856835f5310c9f54aa3",
   "content_hash": "sha256:7f97fd8702c4b6456f6d3e57db82b78ede9103967d9fb29cbeb02843d0fd0b95",
   "locator": "requirements/REQ-001.md",
   "metadata": { "status": "active" }
@@ -50,12 +76,14 @@ a malformed id is a 422, an unknown but well-formed id is a 404.
 
 ### `GET /api/threads/{artifact_id}?baseline=…`
 
-The digital thread for one artifact: reachable artifacts, accepted links, proposals kept in a
-separate array, and evidence for the scenarios and tests in the thread.
+The digital thread for one requirement, assembled from the ingested revision: reachable artifacts,
+accepted links, proposals kept in a separate array, and evidence for the scenarios and tests in the
+thread. The response is identical whether the request names the baseline tag or its commit SHA, and
+it does not read the generated example files.
 
 ```json
 {
-  "schema_version": "0.1.0",
+  "schema_version": "0.2.0",
   "root_id": "REQ-002",
   "baseline": "baseline-a",
   "artifacts": [
@@ -65,7 +93,7 @@ separate array, and evidence for the scenarios and tests in the thread.
       "title": "Daily transfer limit enforcement",
       "source_uri": "fixture://banking-demo/requirements/REQ-002.md",
       "repository": "banking-demo",
-      "revision": "67109fac965377629c9ab5835541aa64461db785",
+      "revision": "0f8607b29d1ccb423062d856835f5310c9f54aa3",
       "content_hash": "sha256:…",
       "locator": "requirements/REQ-002.md",
       "metadata": { "status": "active" }
@@ -88,19 +116,19 @@ separate array, and evidence for the scenarios and tests in the thread.
 }
 ```
 
-404 `artifact-not-found` for an unknown id; 404 `thread-not-found` when the artifact exists but no
-thread is materialized for it (M0 materializes requirement roots; general thread assembly is
-DT-04/B-PR1).
+404 `artifact-not-found` for an unknown id; 404 `thread-not-found` when the artifact exists but is
+not a requirement root (M1 assembles requirement threads; other roots are a documented 404).
 
 ### `GET /api/findings?baseline=…`
 
-Findings for one baseline, ordered as in the oracle. **M0 replays reviewed sample findings**
-generated from `fixtures/banking-demo/expected/baseline-*.json`; deterministic rule evaluation
-arrives with AS-01…AS-03 (C-PR1) and is tested against the same oracle.
+Findings for one baseline, ordered as in the oracle. **M1 replays reviewed sample findings**
+generated from `fixtures/banking-demo/expected/baseline-*.json`; `POST /api/assurance/evaluate` is
+contract-only in this snapshot (501; AS-01…AS-03). The replay remains until the rule set is
+implemented, so M2 findings are not silently dropped from this response.
 
 ```json
 {
-  "schema_version": "0.1.0",
+  "schema_version": "0.2.0",
   "baseline": "baseline-b",
   "findings": [
     {
@@ -109,20 +137,53 @@ arrives with AS-01…AS-03 (C-PR1) and is tested against the same oracle.
       "status": "open",
       "severity": "medium",
       "artifact_ids": ["CODE-001", "REQ-001", "SCN-001"],
-      "evaluated_baseline": "c02064fed61bcfc6ade5ea14ac62f9eb1b5f5c54",
+      "evaluated_baseline": "156ad72b01b361970cc22229e7a2b17f9d6bcb85",
       "evidence_ids": ["EV-001"],
       "explanation": "SCN-001 verification passed at baseline-a (EV-001). CODE-001 changed at baseline-b and no later evidence for SCN-001 exists, so reverification is required. This is not a verification failure.",
       "rule_id": "RULE-REVERIFICATION-REQUIRED",
       "artifact_revisions": {
-        "CODE-001": "c02064fed61bcfc6ade5ea14ac62f9eb1b5f5c54",
-        "REQ-001": "c02064fed61bcfc6ade5ea14ac62f9eb1b5f5c54",
-        "SCN-001": "c02064fed61bcfc6ade5ea14ac62f9eb1b5f5c54"
+        "CODE-001": "156ad72b01b361970cc22229e7a2b17f9d6bcb85",
+        "REQ-001": "156ad72b01b361970cc22229e7a2b17f9d6bcb85",
+        "SCN-001": "156ad72b01b361970cc22229e7a2b17f9d6bcb85"
       }
     }
   ]
 }
 ```
 
+## Ingestion
+
+### `POST /api/ingestion/run`
+
+Ingests the configured fixture repository (`CTA_FIXTURE`, default `banking-demo`) at a revision.
+`revision` may be a tag, branch, or SHA; omitted means the repository's current `HEAD`. The run id
+is derived from the resolved commit, so repeating a run is deterministic.
+
+Request:
+
+```json
+{ "repository": "banking-demo", "revision": "baseline-a" }
+```
+
+Response:
+
+```json
+{
+  "run_id": "ing-0f8607b29d1c",
+  "repository": "banking-demo",
+  "baseline": "baseline-a",
+  "artifact_count": 10,
+  "accepted_link_count": 6,
+  "proposed_link_count": 1,
+  "evidence_count": 2
+}
+```
+
+Errors: unknown repository → 400 `invalid-request` naming the configured repository; unresolvable
+revision → 404 `baseline-not-found`; malformed repository content → 500 `fixture-data-invalid`; a
+missing built repository → 500 `fixture-data-missing` with the build instruction. A revision that is
+not a named baseline is ingestable; `baseline` then reports the SHA.
+
 ## Discovery
 
 ### `POST /api/discovery`
@@ -140,7 +201,7 @@ Response (abridged; `fixtures/api-responses/discovery.SCN-001.json` is the full
 
 ```json
 {
-  "schema_version": "0.1.0",
+  "schema_version": "0.2.0",
   "artifact_id": "SCN-001",
   "provider": "fake",
   "model_version": "fake-fixture-v1",
@@ -166,14 +227,13 @@ link or evidence record is created or modified; a known artifact with no proposa
 empty list; unknown artifact → 404 `artifact-not-found`; unknown provider → 400
 `provider-not-registered`.
 
-## Contract-only endpoints (501 in M0)
+## Contract-only endpoints (501)
 
 Each returns a problem document naming the owning story and milestone, and each validates its body
 first, so the contract is real even though the behaviour is not implemented:
 
 | Endpoint | Body | Owning work |
 | --- | --- | --- |
-| `POST /api/ingestion/run` | `{ "repository": "banking-demo", "revision": null }` | DT-01, DT-02, DT-04 (B-PR1, M1) |
 | `POST /api/links/{link_id}/review` | `{ "decision": "accept" \| "reject", "reviewer_id": "rv-ana", "reason": null }` | AS-06 (C, M1/M2) |
 | `POST /api/assurance/evaluate` | `{ "baseline": "baseline-a", "policy": null }` | AS-01…AS-03 (C-PR1, M1/M2) |
 
```

The cumulative code/test/docs diff against the base is the submission-1 diff plus these repairs;
the submission-1 packet (`docs/reviews/DT-04-review-prompt.md`) carries the previously reviewed
files, and the manifest above is the current snapshot. Fixture files are unchanged since
submission 1.

### Repair summary

| Finding | Severity | Repair | Recheck |
| --- | --- | --- | --- |
| DT04-R1 missing repository misreported as an unknown baseline | medium, blocking | `ingest()` checks repository availability before resolving; a shared `_require_repository` guard is used by reads and ingestion, so both return 500 `fixture-data-missing` with the build instruction | `test_ingestion_with_a_missing_repo_is_fixture_data_missing` (endpoint), `test_missing_fixture_repo_is_actionable` (read + ingestion), `test_ingestion_unknown_revision_in_an_existing_repo_is_404` |
| DT04-R2 evaluate status text overstated implementation | low, nonblocking | Route description and API docs state the current 501 and owning stories | inspection of `routes.py` and `docs/api-contracts.md` |
| DT04-R3 SCN-611 mapping cited the wrong tag/SHA test | low, nonblocking | Added a thread-endpoint tag/SHA equality test and corrected the mapping | `test_thread_by_tag_and_sha_are_identical` |

## 5. Implementation context

* `IngestedStore.from_settings` reads the committed manifest; the repository path is
  `CTA_FIXTURE_REPO` or `fixtures/<fixture>/.build/repo`.
* `ingest_revision` resolves once, scans artifacts, loads links/evidence, and validates evidence
  references; `assemble_thread` is shared with the generator.
* `GET /api/artifacts` is the additive inventory; `POST /api/ingestion/run` reports counts;
  threads no longer read generated examples.
* Targeted reads: `backend/app/domain/models.py`, `docs/domain-contracts.md`,
  `docs/api-contracts.md`, `backend/tests/conftest.py`, `backend/tests/test_fixture_repo.py`.

## 6. Evidence

| Criterion | Check | Result |
| --- | --- | --- |
| SCN-611 | `tests/test_api_contract.py::test_thread_carries_the_accepted_chain_with_evidence`, `::test_thread_matches_the_committed_example`, `::test_thread_by_tag_and_sha_are_identical` | PASS |
| SCN-612 | `::test_thread_keeps_proposals_out_of_accepted_links` | PASS |
| SCN-613 | `tests/test_contract_boundaries.py::test_thread_is_served_without_example_files` | PASS |
| SCN-614 | `::test_thread_reports_missing_roots_clearly` | PASS |
| SCN-615 | `::test_ingestion_run_reports_counts` | PASS |
| SCN-616 | `::test_artifact_inventory_lists_and_filters` | PASS |
| Configuration errors | `tests/test_ingested_store.py` (5 tests) and the missing-repo endpoint test | PASS |
| Fixture discipline | `fixturectl.py verify` exit 0 after regeneration | PASS |

Actual invocations and exits, captured 2026-11-13T03:41:56Z–03:42:05Z:

```text
uv run --project backend pytest backend/tests -q exit 0  227 passed, 1 warning in 6.82s
uv run --project backend python tools/fixturectl.py verify  exit 0  reproducible and current
uv run --project backend ruff check .            exit 0  All checks passed
uv run --project backend ruff format --check .   exit 0  all files formatted
git diff --check                                 exit 0
unshare -rn backend/.venv/bin/python -m pytest backend/tests -q  exit 0  227 passed
```

HTTP demo (submission 1, unchanged behavior): health 0.2.0; inventory 10 artifacts; REQ-001 thread
with LNK-001..003 and EV-001; ingestion counts 10/6/1/2; CODE-001 404 `thread-not-found`;
evaluate 501. The missing-repo path now returns 500 `fixture-data-missing` (endpoint test).

NOT RUN: frontend (AS-04), link-review mutations (AS-06), general non-fixture repositories.

## 7. File-integrity requirement

The manifest in section 3 is the reviewed snapshot. If any manifest hash changed, the snapshot is
not the one reviewed. Do not edit files, install dependencies, regenerate fixtures, or commit.

## Reviewer instructions (mandatory)

You are the independent CTA implementation reviewer using GPT-6.1 Sol xhigh. Decide whether this exact snapshot satisfies the supplied story, every applicable Gherkin criterion, and repository invariants. Treat OMP's summaries and test results as claims to check against the supplied artifacts and targeted source inspection. Check proposal/accepted/evidence separation, real port compatibility, revision/content-hash semantics, honest errors/501s, independent oracle expectations, offline defaults, and generated-file discipline where relevant. Do not demand implementation of a later milestone. Do not edit files, implement repairs, regenerate fixtures, commit, or delegate. Ask OMP for missing runtime evidence; distinguish observed defects from hypotheses and unavailable checks. Return an AC-by-AC PASS, FAIL, or NOT VERIFIED assessment and actionable findings with stable IDs, severity, blocking status, AC/invariant, path/line, expected/actual behavior, and smallest correction/recheck. Keep optional suggestions and unrelated pre-existing defects separate. Return exactly one verdict: APPROVE, REQUEST_CHANGES, or NEEDS_INPUT. APPROVE requires every applicable criterion/check to be satisfied, no unresolved blocker, and the exact snapshot identified. In later rounds verify prior dispositions and regressions while retaining the complete acceptance assessment. A passing process, passing tests, or exhausted review limit is not approval. Agent review cannot attest human labeling or human link decisions.
