# Independent implementation review — DT-04, submission 1 of 7

## 1. Story and authorization

**Task:** DT-04 — Retrieve the thread associated with a requirement.
**Roadmap/feature:** F-03 Links, roadmap §6 DT-04; milestone **M1 — AI-free vertical slice**.
**GitHub story:** anthonygraca/gherkin-knowledge-graph issue **#23**, verified OPEN at
2026-11-13T03:12:49Z (`gh issue view`), milestone "M1 — AI-free vertical slice".
**Owner:** B; **Implementer/integrator:** OMP (shared API integration).
**Repository:** `<task_repo>` (read-only sandbox).
**Base:** `0970f7aa3334d88b3b19e29fae446e0eeb84593d` (`main`, DT-03 merge).
**Branch:** `feat/23-dt-04-thread`. **Submission:** 1 of 7.

### User outcome

A reviewer can request one requirement's thread at a baseline and see its accepted chain and
evidence in one call, with proposals kept separate and the response assembled from ingested
repository data rather than a precomputed example.

### Scope

`IngestedStore` over the nested Git repository; evidence ingestion; shared thread assembly; API
cutover (threads/inventory/ingestion); `commit_of` on the port; additive `GET /api/artifacts` with
a **MINOR contract bump to 0.2.0**; fixture regeneration. Non-goals: general repository hosting,
durable storage, non-requirement thread roots, link review mutations, assurance rules (AS-01).

### Proposed commit reference

`feat(thread): [issue #23] serve requirement threads from ingested revisions`, body `Refs #23`.

## 2. Acceptance criteria (canonical snapshot)

File `docs/stories/DT-04.feature`, sha256
`02301bee448f33efc07d9e0e1d37ccafa1d1a2b9a9bd303bfa622a0fd5eb94e9`.

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
verification; offline defaults; independent oracle expectations.

## 3. Snapshot and manifest

Snapshot captured 2026-11-13T03:29Z. Manifest (sha256 of every task file, including fixtures):

```text
b486374b06ad0f1f6492a95b8a2af2a0c52b27039011e8566f13d75762a0f65d  backend/app/domain/api.py
17e65def989f2c24c5f4a7dc8514fe9c9e6c72b1a1eb52602f174de45292382d  backend/app/domain/ports.py
4200999207d79bffbd59cd30b72959b2039c4b1067e827087ee75b037918ea0e  backend/app/ingestion/__init__.py
88db8934b47d78f2256a40b6f5bfca0e72cc062a4c297b282a66c0242ae385cf  backend/app/ingestion/evidence.py
761fee3b1944516158773161b49747b6430853f7456d3c6be7028a148c783f07  backend/app/ingestion/revision.py
e930e3043bb952c63ac3d9afb05bf7227ea3437284946188083187a04a4d47a4  backend/app/ingestion/thread.py
b97341218d37c7f2ae78f03f2259478ab4b321f658cee0737a14397e9488c064  backend/app/persistence/__init__.py
cd02d1b3cfbd4e60d0c28659dcd568aff46af04465a83c5dcd36d7481374813b  backend/app/persistence/ingested.py
397de92385a945305a221da84f98841dd031281c64acc3c1f96c87055d749341  backend/app/settings.py
cd722cd24a15b23666731258391f8b6c1d1b943838248f3d81df6e5f3cf8275b  backend/app/version.py
b41c46ce5c0df6e781cdee3b4915aec6f4e59863501305e2040d6e9a6dd9b9cc  backend/app/api/deps.py
1194fe2a73196cd1f84639d66d20298f8b9cafeac9608715dce5accb7f0a359d  backend/app/api/routes.py
e016b3651009cd3e02e21ac58bc17cbb06e3f1404dfe3581b9602608dae534cd  backend/app/main.py
0072e017e27ff488b575300f1be324efe0a11ef7f84e92a5b960df210ac7bcae  tools/fixturectl.py
db4b86fe1d073ec0c0c4b0c6cf7c76e7d3a9833f079576364e6e042d59e4ff47  backend/tests/conftest.py
7fed2967742392fc7b96d3b7255ca68e9555606d52f62e2c84bb6587da38cc4b  backend/tests/test_api_contract.py
cec02ad839f3765aea67b2778a978eab3ef03d791e679c714f51320c8500566a  backend/tests/test_contract_boundaries.py
e000af68929cd65e750c94f2dc8e80f17872841abebeedc0ed68f65ac27c47bc  backend/tests/test_fixture_oracle.py
5c9f61ccfca33fc53cddc3727291aaa037f60466ccd9052892c78350b892d82c  backend/tests/test_ingested_store.py
02301bee448f33efc07d9e0e1d37ccafa1d1a2b9a9bd303bfa622a0fd5eb94e9  docs/stories/DT-04.feature
881774732805c89d46b18cb984cd0b376048a4cf0863a5758d66c618f31f456f  docs/stories/DT-04.md
755d750500d169038b7fbcd38b7b14367ed006350229fcf6906e686fb24723e6  docs/api-contracts.md
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
f842703889f62fd80be1e1522da14ad6679f7954783b7494273b72c2af4fbd17  docs/reports/omp-dt-04-thread/IMPLEMENTATION.md
71cd1ccc03119e1445b4a4bb844be13967500e32191739d3b163a359c1838b47  docs/reports/omp-dt-04-thread/PROMPT_LOG.md
8238108594315ffbc3184bfbc850713a6050834fcfe55cbd97c91a67196668d8  docs/reports/omp-dt-04-thread/METRICS.md
```

`SCHEMA_VERSION = 0.2.0` (MINOR: new endpoint), `PACKAGE_VERSION = 0.1.0`. No dependency change.

### Fixture regeneration (deliberate)

Eight input files changed only `schema_version`; `fixturectl all` regenerated 13 files. The baseline
SHAs changed because the link/evidence blobs changed:

```text
baseline-a  0f8607b29d1ccb423062d856835f5310c9f54aa3
baseline-b  156ad72b01b361970cc22229e7a2b17f9d6bcb85
```

Source/requirement/scenario/test content hashes are unchanged; oracle expectations are unchanged;
`fixturectl verify` passes. The tracked diffstat:

```text
 backend/app/api/deps.py                            |   8 +-
 backend/app/api/routes.py                          |  67 ++++++++---
 backend/app/domain/api.py                          |   8 ++
 backend/app/domain/ports.py                        |   4 +
 backend/app/ingestion/__init__.py                  |  10 +-
 backend/app/ingestion/revision.py                  |  12 +-
 backend/app/main.py                                |  13 +-
 backend/app/persistence/__init__.py                |   6 +-
 backend/app/persistence/store.py                   | 128 --------------------
 backend/app/settings.py                            |   9 ++
 backend/app/version.py                             |   2 +-
 backend/tests/conftest.py                          |  14 ++-
 backend/tests/test_api_contract.py                 | 102 +++++++++++++++-
 backend/tests/test_contract_boundaries.py          |  54 ++++-----
 backend/tests/test_fixture_oracle.py               |   4 +-
 docs/STATUS.md                                     |  15 +--
 docs/api-contracts.md                              | 104 ++++++++++++----
 docs/architecture.md                               |  22 ++--
 docs/domain-contracts.md                           |   6 +-
 fixtures/api-responses/discovery.REQ-002.json      |   2 +-
 fixtures/api-responses/discovery.SCN-001.json      |   2 +-
 fixtures/api-responses/discovery.SCN-002.json      |   2 +-
 fixtures/api-responses/discovery.SCN-003.json      |   2 +-
 fixtures/api-responses/findings.baseline-a.json    |  20 ++--
 fixtures/api-responses/findings.baseline-b.json    |  36 +++---
 fixtures/api-responses/snapshot.json               |  56 ++++-----
 .../api-responses/threads/REQ-001.baseline-a.json  |  12 +-
 .../api-responses/threads/REQ-001.baseline-b.json  |  12 +-
 .../api-responses/threads/REQ-002.baseline-a.json  |   4 +-
 .../api-responses/threads/REQ-002.baseline-b.json  |   4 +-
 .../api-responses/threads/REQ-003.baseline-a.json  |  12 +-
 .../api-responses/threads/REQ-003.baseline-b.json  |  14 +--
 .../evidence/verification-runs.json                |   2 +-
 .../evidence/verification-runs.json                |   2 +-
 fixtures/banking-demo/expected/baseline-a.json     |   2 +-
 fixtures/banking-demo/expected/baseline-b.json     |   2 +-
 fixtures/banking-demo/expected/baselines.json      |  14 +--
 .../banking-demo/expected/candidate-links.json     |   2 +-
 fixtures/banking-demo/history.json                 |   2 +-
 .../banking-demo/tree/evidence/accepted-links.json |   2 +-
 .../banking-demo/tree/evidence/proposed-links.json |   2 +-
 tools/fixturectl.py                                | 131 ++++-----------------
 42 files changed, 469 insertions(+), 458 deletions(-)
```

## 4. Code, docs, and tests

### Domain, store, and API diffs

```diff
diff --git a/backend/app/api/deps.py b/backend/app/api/deps.py
index 98e2bb7..e5613a7 100644
--- a/backend/app/api/deps.py
+++ b/backend/app/api/deps.py
@@ -13,7 +13,7 @@ from fastapi import Depends, Request
 from app.assurance.sample_findings import SampleFindingsSource
 from app.discovery.registry import ProviderRegistry
 from app.domain.ports import ArtifactRepository
-from app.persistence.store import FixtureStore
+from app.persistence.ingested import IngestedStore
 from app.settings import Settings
 
 
@@ -26,8 +26,8 @@ def provide_repository(request: Request) -> ArtifactRepository:
     return request.app.state.store
 
 
-def provide_store(request: Request) -> FixtureStore:
-    """The concrete M0 store, for the fixture-only surfaces (thread replay, baseline commit map)."""
+def provide_store(request: Request) -> IngestedStore:
+    """The concrete store, for ingestion and fixture-facing helpers."""
     return request.app.state.store
 
 
@@ -41,6 +41,6 @@ def provide_providers(request: Request) -> ProviderRegistry:
 
 SettingsDep = Annotated[Settings, Depends(provide_settings)]
 RepositoryDep = Annotated[ArtifactRepository, Depends(provide_repository)]
-StoreDep = Annotated[FixtureStore, Depends(provide_store)]
+StoreDep = Annotated[IngestedStore, Depends(provide_store)]
 FindingsDep = Annotated[SampleFindingsSource, Depends(provide_findings_source)]
 ProvidersDep = Annotated[ProviderRegistry, Depends(provide_providers)]
diff --git a/backend/app/api/routes.py b/backend/app/api/routes.py
index ae5ec6b..5d33151 100644
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
+        "`POST /api/assurance/evaluate` runs the implemented deterministic rules; `GET` keeps the "
+        "reviewed sample until AS-02/AS-03 complete the rule set, so M2 findings are not silently "
+        "dropped."
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
 
 
diff --git a/backend/app/domain/api.py b/backend/app/domain/api.py
index c4bbf9f..cbe04c1 100644
--- a/backend/app/domain/api.py
+++ b/backend/app/domain/api.py
@@ -68,6 +68,14 @@ class FindingsResponse(_FrozenModel):
     findings: list[AssuranceFinding]
 
 
+class ArtifactListResponse(_FrozenModel):
+    """Artifact inventory at one baseline (additive in schema 0.2.0)."""
+
+    schema_version: str
+    baseline: str
+    artifacts: list[Artifact]
+
+
 class DiscoveryRequest(BaseModel):
     model_config = ConfigDict(extra="forbid")
 
diff --git a/backend/app/domain/ports.py b/backend/app/domain/ports.py
index 01bd3fa..909ce32 100644
--- a/backend/app/domain/ports.py
+++ b/backend/app/domain/ports.py
@@ -57,6 +57,10 @@ class ArtifactRepository(Protocol):
 
     def resolve_baseline(self, baseline: str | None) -> str: ...
 
+    def commit_of(self, baseline: str) -> str:
+        """Resolved commit SHA that findings and evidence are pinned to."""
+        ...
+
     def get_artifact(self, artifact_id: str, *, baseline: str | None = None) -> Artifact: ...
 
     def list_artifacts(self, baseline: str) -> list[Artifact]: ...
diff --git a/backend/app/ingestion/__init__.py b/backend/app/ingestion/__init__.py
index f126fea..db81b3f 100644
--- a/backend/app/ingestion/__init__.py
+++ b/backend/app/ingestion/__init__.py
@@ -1,20 +1,22 @@
 """Repository ingestion (roadmap §3): revision-pinned parsing into domain artifacts.
 
-The package is intentionally small. DT-01 adds requirement and Gherkin parsing; DT-02 adds
-source/test annotations; DT-03 adds link ingestion; DT-04 assembles threads and cuts reads over
-to the ingested store. Nothing here writes accepted links, review states, or verification
-evidence on its own: links and evidence are *read* from declared repository files.
+DT-01 adds requirement and Gherkin parsing; DT-02 adds source/test annotations; DT-03 adds link
+ingestion; DT-04 adds evidence, thread assembly, and the store cutover. Nothing here writes
+accepted links, review states, or verification evidence on its own: links and evidence are *read*
+from declared repository files.
 """
 
 from app.ingestion.errors import IngestionError
 from app.ingestion.repository import GitRepository
 from app.ingestion.revision import IngestedRevision, ingest_revision
 from app.ingestion.scan import scan_artifacts
+from app.ingestion.thread import assemble_thread
 
 __all__ = [
     "GitRepository",
     "IngestedRevision",
     "IngestionError",
+    "assemble_thread",
     "ingest_revision",
     "scan_artifacts",
 ]
diff --git a/backend/app/ingestion/revision.py b/backend/app/ingestion/revision.py
index 4cf6dba..2f4909e 100644
--- a/backend/app/ingestion/revision.py
+++ b/backend/app/ingestion/revision.py
@@ -1,13 +1,14 @@
-"""One revision's ingested facts: artifacts and declared links.
+"""One revision's ingested facts: artifacts, declared links, and recorded evidence.
 
-Evidence joins this record with DT-04 (thread assembly needs it); DT-05/M2 owns evidence policy.
+Freshness policy is DT-05/M2; this record only holds what the repository declares at one commit.
 """
 
 from __future__ import annotations
 
 from dataclasses import dataclass
 
-from app.domain.models import Artifact, TraceLink
+from app.domain.models import Artifact, TraceLink, VerificationEvidence
+from app.ingestion.evidence import load_evidence
 from app.ingestion.links import load_links
 from app.ingestion.repository import GitRepository
 from app.ingestion.scan import scan_artifacts
@@ -21,6 +22,7 @@ class IngestedRevision:
     artifacts: list[Artifact]
     accepted_links: list[TraceLink]
     proposed_links: list[TraceLink]
+    evidence: list[VerificationEvidence]
 
     def artifact(self, artifact_id: str) -> Artifact | None:
         return next(
@@ -32,14 +34,16 @@ class IngestedRevision:
 def ingest_revision(
     repository: GitRepository, revision: str | None, *, repository_name: str
 ) -> IngestedRevision:
-    """Resolve once, scan artifacts, and read the declared links at that commit."""
+    """Resolve once, then read artifacts, links, and evidence at that commit."""
     commit = repository.resolve(revision)
     artifacts = scan_artifacts(repository, commit, repository_name=repository_name)
     by_id = {artifact.artifact_id: artifact for artifact in artifacts}
     accepted, proposed = load_links(repository, commit, artifacts=by_id)
+    evidence = load_evidence(repository, commit, artifacts=by_id)
     return IngestedRevision(
         commit=commit,
         artifacts=artifacts,
         accepted_links=accepted,
         proposed_links=proposed,
+        evidence=evidence,
     )
diff --git a/backend/app/main.py b/backend/app/main.py
index f7b6cb9..3b7daa8 100644
--- a/backend/app/main.py
+++ b/backend/app/main.py
@@ -13,7 +13,7 @@ from app.api.errors import register_exception_handlers
 from app.api.routes import router
 from app.assurance.sample_findings import SampleFindingsSource
 from app.discovery.registry import ProviderRegistry
-from app.persistence.store import FixtureStore
+from app.persistence.ingested import IngestedStore
 from app.settings import Settings, load_settings
 from app.version import PACKAGE_VERSION
 
@@ -33,8 +33,10 @@ Invariants this API upholds:
 * **Version-aware.** Artifacts carry a revision and a content hash; findings and evidence
   are pinned to the baseline they were evaluated at.
 
-M0 status: reads and discovery are implemented over committed fixture data. The endpoints
-tagged `contract-only` return 501 and name the story that will implement them.
+M1 status: artifacts, links, evidence, and threads are parsed from the nested fixture repository
+at the requested revision; `POST /api/ingestion/run` reports what it ingested. `GET /api/findings`
+still replays reviewed sample findings. The endpoints tagged `contract-only` return 501 and name the
+story that will implement them.
 """
 
 
@@ -45,7 +47,8 @@ def create_app(settings: Settings | None = None) -> FastAPI:
         version=PACKAGE_VERSION,
         description=DESCRIPTION,
         openapi_tags=[
-            {"name": "reads", "description": "Implemented over the fixture-backed store."},
+            {"name": "reads", "description": "Implemented over the ingested fixture repository."},
+            {"name": "ingestion", "description": "Parses the configured repository at a revision."},
             {"name": "discovery", "description": "Candidate proposals only; never writes links."},
             {
                 "name": "contract-only",
@@ -54,7 +57,7 @@ def create_app(settings: Settings | None = None) -> FastAPI:
         ],
     )
     app.state.settings = resolved
-    app.state.store = FixtureStore.from_settings(resolved)
+    app.state.store = IngestedStore.from_settings(resolved)
     app.state.findings_source = SampleFindingsSource.from_settings(resolved)
     app.state.providers = ProviderRegistry(resolved)
     register_exception_handlers(app)
diff --git a/backend/app/persistence/__init__.py b/backend/app/persistence/__init__.py
index 1a912c9..efdfb21 100644
--- a/backend/app/persistence/__init__.py
+++ b/backend/app/persistence/__init__.py
@@ -1,6 +1,6 @@
-"""Fixture-backed persistence (M0 mock services)."""
+"""Fixture-backed persistence and the ingested repository store."""
 
 from app.persistence.fixtures import load_json, load_model
-from app.persistence.store import FixtureStore
+from app.persistence.ingested import IngestedStore
 
-__all__ = ["FixtureStore", "load_json", "load_model"]
+__all__ = ["IngestedStore", "load_json", "load_model"]
diff --git a/backend/app/settings.py b/backend/app/settings.py
index 8ed2469..ce6395b 100644
--- a/backend/app/settings.py
+++ b/backend/app/settings.py
@@ -16,6 +16,7 @@ DEFAULT_FIXTURE = "banking-demo"
 ENV_REPO_ROOT = "CTA_REPO_ROOT"
 ENV_FIXTURES_DIR = "CTA_FIXTURES_DIR"
 ENV_FIXTURE = "CTA_FIXTURE"
+ENV_FIXTURE_REPO = "CTA_FIXTURE_REPO"
 ENV_DISCOVERY_PROVIDER = "CTA_DISCOVERY_PROVIDER"
 
 
@@ -30,11 +31,17 @@ class Settings:
     fixtures_dir: Path
     fixture: str = DEFAULT_FIXTURE
     discovery_provider: str = "fake"
+    fixture_repo_path: Path | None = None
 
     @property
     def fixture_dir(self) -> Path:
         return self.fixtures_dir / self.fixture
 
+    @property
+    def fixture_repo(self) -> Path:
+        """Nested Git repository ingested for reads; built by ``fixturectl build``."""
+        return self.fixture_repo_path or (self.fixture_dir / ".build" / "repo")
+
     @property
     def expected_dir(self) -> Path:
         return self.fixture_dir / "expected"
@@ -59,9 +66,11 @@ class Settings:
 def load_settings() -> Settings:
     repo_root = Path(os.environ.get(ENV_REPO_ROOT, default_repo_root())).resolve()
     fixtures_dir = Path(os.environ.get(ENV_FIXTURES_DIR, repo_root / "fixtures")).resolve()
+    fixture_repo = os.environ.get(ENV_FIXTURE_REPO)
     return Settings(
         repo_root=repo_root,
         fixtures_dir=fixtures_dir,
         fixture=os.environ.get(ENV_FIXTURE, DEFAULT_FIXTURE),
         discovery_provider=os.environ.get(ENV_DISCOVERY_PROVIDER, "fake"),
+        fixture_repo_path=Path(fixture_repo).resolve() if fixture_repo else None,
     )
diff --git a/backend/app/version.py b/backend/app/version.py
index d360954..4c59baa 100644
--- a/backend/app/version.py
+++ b/backend/app/version.py
@@ -9,4 +9,4 @@ PACKAGE_VERSION = "0.1.0"
 #:   MAJOR — breaking: removed/renamed field, changed field meaning, changed relation
 #:           direction, changed fingerprint inputs.
 #: Fixture files carry the value they were generated against; loaders reject mismatches.
-SCHEMA_VERSION = "0.1.0"
+SCHEMA_VERSION = "0.2.0"
```

`backend/app/persistence/store.py` is deleted (the M0 replay store).

### New ingestion and store files (complete)

`backend/app/ingestion/evidence.py`:
```python
"""Ingest recorded verification evidence from a revision.

Evidence is read, never written here. DT-05/M2 owns freshness policy; this module only validates the
declared record and its artifact references.
"""

from __future__ import annotations

import json

from pydantic import ValidationError

from app.domain.enums import ArtifactType
from app.domain.models import Artifact, VerificationEvidence
from app.domain.oracle import FixtureEvidenceFile
from app.ingestion.errors import IngestionError
from app.ingestion.repository import GitRepository
from app.version import SCHEMA_VERSION

EVIDENCE_PATH = "evidence/verification-runs.json"


def load_evidence(
    repository: GitRepository, commit: str, *, artifacts: dict[str, Artifact]
) -> list[VerificationEvidence]:
    """Evidence runs at ``commit``, sorted by id; an absent file means no recorded runs."""
    paths = set(repository.list_paths(commit))
    if EVIDENCE_PATH not in paths:
        return []
    where = f"{commit}:{EVIDENCE_PATH}"
    raw = repository.read_blob(commit, EVIDENCE_PATH)
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise IngestionError(f"{where}: evidence file is not valid UTF-8 JSON: {exc}") from exc
    try:
        parsed = FixtureEvidenceFile.model_validate(payload)
    except ValidationError as exc:
        raise IngestionError(
            f"{where}: evidence file does not satisfy FixtureEvidenceFile:\n{exc}"
        ) from exc
    if parsed.schema_version != SCHEMA_VERSION:
        raise IngestionError(
            f"{where}: declares schema_version {parsed.schema_version!r}; this build implements "
            f"{SCHEMA_VERSION!r}"
        )
    for run in parsed.runs:
        test = artifacts.get(run.test_id)
        if test is None or test.artifact_type is not ArtifactType.TEST:
            raise IngestionError(
                f"{where}: evidence {run.evidence_id} references unknown test artifact "
                f"{run.test_id!r}"
            )
        if run.scenario_id is not None:
            scenario = artifacts.get(run.scenario_id)
            if scenario is None or scenario.artifact_type is not ArtifactType.SCENARIO:
                raise IngestionError(
                    f"{where}: evidence {run.evidence_id} references unknown scenario artifact "
                    f"{run.scenario_id!r}"
                )
    return sorted(parsed.runs, key=lambda run: run.evidence_id)
```

`backend/app/ingestion/thread.py`:
```python
"""Assemble one artifact's digital thread from ingested facts.

One implementation is shared by the API store and the fixture generator, so a generated example and
a served response cannot drift. The thread contains only artifacts reachable through accepted
links; proposals and evidence are separate collections.
"""

from __future__ import annotations

from collections.abc import Sequence

from app.domain.api import ThreadResponse
from app.domain.models import Artifact, TraceLink, VerificationEvidence
from app.version import SCHEMA_VERSION


def assemble_thread(
    *,
    root_id: str,
    baseline: str,
    artifacts: Sequence[Artifact],
    accepted_links: Sequence[TraceLink],
    proposed_links: Sequence[TraceLink],
    evidence: Sequence[VerificationEvidence],
) -> ThreadResponse:
    """Build the thread rooted at ``root_id`` (the caller validates that the root exists)."""
    accepted_by_source: dict[str, list[TraceLink]] = {}
    for link in accepted_links:
        accepted_by_source.setdefault(link.source_id, []).append(link)

    visited = {root_id}
    frontier = [root_id]
    while frontier:
        following: list[str] = []
        for artifact_id in frontier:
            for link in accepted_by_source.get(artifact_id, []):
                if link.target_id not in visited:
                    visited.add(link.target_id)
                    following.append(link.target_id)
        frontier = following

    return ThreadResponse(
        schema_version=SCHEMA_VERSION,
        root_id=root_id,
        baseline=baseline,
        artifacts=sorted(
            (artifact for artifact in artifacts if artifact.artifact_id in visited),
            key=lambda artifact: artifact.artifact_id,
        ),
        accepted_links=sorted(
            (
                link
                for link in accepted_links
                if link.source_id in visited and link.target_id in visited
            ),
            key=lambda link: link.link_id,
        ),
        proposed_links=sorted(
            (
                link
                for link in proposed_links
                if link.source_id in visited or link.target_id in visited
            ),
            key=lambda link: link.link_id,
        ),
        evidence=sorted(
            (run for run in evidence if run.scenario_id in visited or run.test_id in visited),
            key=lambda run: run.evidence_id,
        ),
    )
```

`backend/app/persistence/ingested.py`:
```python
"""In-process store over the ingested fixture repository.

The store ingests a revision on first use and caches it by resolved commit. It implements the same
``ArtifactRepository`` port as the M0 mock, so consumers did not change; the precomputed thread
replay is gone and threads are assembled from parsed repository data.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.domain.api import ThreadResponse
from app.domain.enums import ArtifactType, ReviewState
from app.domain.errors import (
    ArtifactNotFound,
    BaselineNotFound,
    FixtureDataInvalid,
    FixtureDataMissing,
    InvalidRequest,
    ThreadNotFound,
)
from app.domain.models import Artifact, TraceLink, VerificationEvidence
from app.domain.oracle import BaselinesManifest
from app.ingestion import GitRepository, IngestedRevision, IngestionError, ingest_revision
from app.ingestion.thread import assemble_thread
from app.persistence.fixtures import load_model, require_supported_schema_version
from app.settings import Settings


@dataclass
class IngestedStore:
    """Facts parsed from the configured repository, cached by commit."""

    repository: GitRepository
    manifest: BaselinesManifest
    repository_name: str
    _cache: dict[str, IngestedRevision] = field(default_factory=dict)

    @classmethod
    def from_settings(cls, settings: Settings) -> IngestedStore:
        manifest = load_model(settings.baselines_manifest_path, BaselinesManifest)
        require_supported_schema_version(manifest.schema_version, settings.baselines_manifest_path)
        return cls(
            repository=GitRepository(settings.fixture_repo),
            manifest=manifest,
            repository_name=settings.fixture,
        )

    # --------------------------------------------------- ArtifactRepository port

    def baselines(self) -> list[str]:
        return [tag for commit in self.manifest.commits for tag in commit.tags]

    def resolve_baseline(self, baseline: str | None) -> str:
        if baseline is None:
            return self.baselines()[-1]
        if baseline in self.manifest.tags:
            return baseline
        for name, commit in self.manifest.tags.items():
            if commit == baseline:
                return name
        known = ", ".join(f"{name} ({commit})" for name, commit in self.manifest.tags.items())
        raise BaselineNotFound(f"Unknown baseline '{baseline}'. Known baselines: {known}")

    def commit_of(self, baseline: str) -> str:
        return self.manifest.tags[self.resolve_baseline(baseline)]

    def get_artifact(self, artifact_id: str, *, baseline: str | None = None) -> Artifact:
        canonical, revision = self._revision(baseline)
        artifact = revision.artifact(artifact_id)
        if artifact is None:
            known = ", ".join(item.artifact_id for item in revision.artifacts)
            raise ArtifactNotFound(
                f"No artifact '{artifact_id}' at baseline '{canonical}'. Known artifacts: {known}"
            )
        return artifact

    def list_artifacts(self, baseline: str) -> list[Artifact]:
        return list(self._revision(baseline)[1].artifacts)

    def list_links(
        self, baseline: str, *, review_state: ReviewState | None = None
    ) -> list[TraceLink]:
        revision = self._revision(baseline)[1]
        links = [*revision.accepted_links, *revision.proposed_links]
        if review_state is not None:
            links = [link for link in links if link.review_state is review_state]
        return sorted(links, key=lambda link: link.link_id)

    def list_evidence(self, baseline: str) -> list[VerificationEvidence]:
        return list(self._revision(baseline)[1].evidence)

    def changed_artifacts(self, baseline: str, previous: str) -> list[str]:
        current = {
            artifact.artifact_id: artifact.content_hash
            for artifact in self._revision(baseline)[1].artifacts
        }
        before = {
            artifact.artifact_id: artifact.content_hash
            for artifact in self._revision(previous)[1].artifacts
        }
        return sorted(
            artifact_id
            for artifact_id in current.keys() | before.keys()
            if current.get(artifact_id) != before.get(artifact_id)
        )

    # ------------------------------------------- fixture-facing read helpers

    def baseline_commits(self) -> dict[str, str]:
        """Fixture addition used by ``/health``: baseline name -> resolved commit SHA."""
        return dict(self.manifest.tags)

    def label_of(self, commit: str) -> str:
        return next((name for name, value in self.manifest.tags.items() if value == commit), commit)

    def thread(self, root_id: str, *, baseline: str | None = None) -> ThreadResponse:
        canonical, revision = self._revision(baseline)
        artifact = revision.artifact(root_id)
        if artifact is None:
            raise ArtifactNotFound(f"No artifact '{root_id}' at baseline '{canonical}'.")
        if artifact.artifact_type is not ArtifactType.REQUIREMENT:
            raise ThreadNotFound(
                f"No thread materialized for '{root_id}' at baseline '{canonical}'. "
                f"M1 materializes threads for requirement roots only."
            )
        return assemble_thread(
            root_id=root_id,
            baseline=canonical,
            artifacts=revision.artifacts,
            accepted_links=revision.accepted_links,
            proposed_links=revision.proposed_links,
            evidence=revision.evidence,
        )

    def ingest(self, repository_name: str, revision: str | None) -> IngestedRevision:
        """Ingest one revision of the configured repository (``POST /api/ingestion/run``)."""
        if repository_name != self.repository_name:
            raise InvalidRequest(
                f"Repository {repository_name!r} is not configured; this build serves "
                f"{self.repository_name!r}."
            )
        try:
            commit = self.repository.resolve(revision)
        except IngestionError as exc:
            raise BaselineNotFound(f"Unknown revision {revision!r}: {exc}") from exc
        return self._ingest(commit)

    # ------------------------------------------------------------- internals

    def _revision(self, baseline: str | None) -> tuple[str, IngestedRevision]:
        canonical = self.resolve_baseline(baseline)
        return canonical, self._ingest(self.manifest.tags[canonical])

    def _ingest(self, commit: str) -> IngestedRevision:
        cached = self._cache.get(commit)
        if cached is not None:
            return cached
        if not self.repository.root.is_dir():
            raise FixtureDataMissing(
                f"Fixture repository '{self.repository.root}' is missing. Run "
                f"'uv run --project backend python tools/fixturectl.py build' from the repository "
                f"root, or set CTA_FIXTURE_REPO."
            )
        try:
            revision = ingest_revision(
                self.repository, commit, repository_name=self.repository_name
            )
        except IngestionError as exc:
            raise FixtureDataInvalid(str(exc)) from exc
        self._cache[commit] = revision
        return revision

### Generator convergence

`tools/fixturectl.py` now delegates artifact scanning, link/evidence loading, and thread assembly to
the ingestion package; the duplicate loaders and assembler are deleted. Diff:

```diff
diff --git a/tools/fixturectl.py b/tools/fixturectl.py
index 2294fb5..2f20f3c 100755
--- a/tools/fixturectl.py
+++ b/tools/fixturectl.py
@@ -37,27 +37,22 @@ from typing import TypeVar
 from pydantic import BaseModel
 
 from app.discovery.fake import FakeCandidateDiscovery, compute_index_revision
-from app.domain.api import DiscoveryResponse, ThreadResponse
-from app.domain.enums import ArtifactType, ReviewState
-from app.domain.models import (
-    AssuranceFinding,
-    TraceLink,
-    VerificationEvidence,
-    make_finding,
-)
+from app.domain.api import DiscoveryResponse
+from app.domain.enums import ArtifactType
+from app.domain.models import AssuranceFinding, make_finding
 from app.domain.oracle import (
     BaselineCommit,
     BaselinesManifest,
     BaselineSnapshot,
     CandidateIndexFile,
     ExpectedFindingsFile,
-    FixtureEvidenceFile,
     FixtureHistory,
-    FixtureLinkFile,
     FixtureSnapshot,
     MaterializedFindings,
 )
-from app.ingestion import GitRepository, IngestionError
+from app.ingestion import GitRepository, IngestionError, assemble_thread
+from app.ingestion.evidence import load_evidence as ingest_evidence
+from app.ingestion.links import load_links as ingest_links
 from app.ingestion.scan import scan_artifacts as scan_revision_artifacts
 from app.persistence.fixtures import load_model
 from app.version import SCHEMA_VERSION
@@ -72,10 +67,6 @@ API_DIR = REPO_ROOT / "fixtures" / "api-responses"
 
 GENERATED_BY = "tools/fixturectl.py"
 
-EVIDENCE_PATH = "evidence/verification-runs.json"
-ACCEPTED_LINKS_PATH = "evidence/accepted-links.json"
-PROPOSED_LINKS_PATH = "evidence/proposed-links.json"
-
 GIT_IDENTITY = {
     "GIT_AUTHOR_NAME": "CTA Fixture Bot",
     "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
@@ -240,45 +231,6 @@ def build_repo(fixture_dir: Path, dest: Path) -> BaselinesManifest:
 # ----------------------------------------------------------------------------------------
 
 
-def load_evidence(repo: Path, commit: str) -> list[VerificationEvidence]:
-    listed = git(["ls-tree", "-r", "--name-only", commit], cwd=repo).splitlines()
-    if EVIDENCE_PATH not in listed:
-        return []
-    payload = json.loads(git_blob(repo, commit, EVIDENCE_PATH).decode("utf-8"))
-    try:
-        parsed = FixtureEvidenceFile.model_validate(payload)
-    except Exception as exc:
-        raise FixtureToolError(
-            f"{commit}:{EVIDENCE_PATH} does not satisfy FixtureEvidenceFile:\n{exc}"
-        ) from exc
-    return list(parsed.runs)
-
-
-def load_links(repo: Path, commit: str) -> tuple[list[TraceLink], list[TraceLink]]:
-    listed = git(["ls-tree", "-r", "--name-only", commit], cwd=repo).splitlines()
-
-    def read(path: str, expected_state: ReviewState) -> list[TraceLink]:
-        if path not in listed:
-            return []
-        payload = json.loads(git_blob(repo, commit, path).decode("utf-8"))
-        try:
-            parsed = FixtureLinkFile.model_validate(payload)
-        except Exception as exc:
-            raise FixtureToolError(
-                f"{commit}:{path} does not satisfy FixtureLinkFile:\n{exc}"
-            ) from exc
-        if parsed.review_state != expected_state:
-            raise FixtureToolError(
-                f"{commit}:{path} declares review_state={parsed.review_state} "
-                f"but should be {expected_state}"
-            )
-        return list(parsed.links)
-
-    accepted = read(ACCEPTED_LINKS_PATH, ReviewState.ACCEPTED)
-    proposed = read(PROPOSED_LINKS_PATH, ReviewState.PROPOSED)
-    return accepted, proposed
-
-
 # ----------------------------------------------------------------------------------------
 # Snapshot, findings, threads
 # ----------------------------------------------------------------------------------------
@@ -286,18 +238,19 @@ def load_links(repo: Path, commit: str) -> tuple[list[TraceLink], list[TraceLink
 
 def build_snapshot(manifest: BaselinesManifest, repo: Path) -> FixtureSnapshot:
     baselines: list[BaselineSnapshot] = []
+    repository = GitRepository(repo)
     for tag, commit in manifest.tags.items():
-        accepted, proposed = load_links(repo, commit)
+        artifacts = scan_revision_artifacts(repository, commit, repository_name=manifest.fixture)
+        by_id = {artifact.artifact_id: artifact for artifact in artifacts}
+        accepted, proposed = ingest_links(repository, commit, artifacts=by_id)
         baselines.append(
             BaselineSnapshot(
                 baseline=tag,
                 commit=commit,
-                artifacts=scan_revision_artifacts(
-                    GitRepository(repo), commit, repository_name=manifest.fixture
-                ),
+                artifacts=artifacts,
                 accepted_links=accepted,
                 proposed_links=proposed,
-                evidence=load_evidence(repo, commit),
+                evidence=ingest_evidence(repository, commit, artifacts=by_id),
             )
         )
     return FixtureSnapshot(
@@ -345,56 +298,6 @@ def stamp_findings(
     return findings
 
 
-def build_thread(baseline: BaselineSnapshot, root_id: str) -> ThreadResponse:
-    accepted_by_source: dict[str, list[TraceLink]] = {}
-    for link in baseline.accepted_links:
-        accepted_by_source.setdefault(link.source_id, []).append(link)
-
-    visited = {root_id}
-    frontier = [root_id]
-    while frontier:
-        following: list[str] = []
-        for artifact_id in frontier:
-            for link in accepted_by_source.get(artifact_id, []):
-                if link.target_id not in visited:
-                    visited.add(link.target_id)
-                    following.append(link.target_id)
-        frontier = following
-
-    return ThreadResponse(
-        schema_version=SCHEMA_VERSION,
-        root_id=root_id,
-        baseline=baseline.baseline,
-        artifacts=sorted(
-            (a for a in baseline.artifacts if a.artifact_id in visited), key=lambda a: a.artifact_id
-        ),
-        accepted_links=sorted(
-            (
-                link
-                for link in baseline.accepted_links
-                if link.source_id in visited and link.target_id in visited
-            ),
-            key=lambda link: link.link_id,
-        ),
-        proposed_links=sorted(
-            (
-                link
-                for link in baseline.proposed_links
-                if link.source_id in visited or link.target_id in visited
-            ),
-            key=lambda link: link.link_id,
-        ),
-        evidence=sorted(
-            (
-                item
-                for item in baseline.evidence
-                if item.scenario_id in visited or item.test_id in visited
-            ),
-            key=lambda item: item.evidence_id,
-        ),
-    )
-
-
 # ----------------------------------------------------------------------------------------
 # Writing and comparing generated files
 # ----------------------------------------------------------------------------------------
@@ -449,7 +352,15 @@ def materialize(
             if artifact.artifact_type is not ArtifactType.REQUIREMENT:
                 continue
             thread_path = api_dir / "threads" / f"{artifact.artifact_id}.{baseline.baseline}.json"
-            if write_json(thread_path, build_thread(baseline, artifact.artifact_id)):
+            thread = assemble_thread(
+                root_id=artifact.artifact_id,
+                baseline=baseline.baseline,
+                artifacts=baseline.artifacts,
+                accepted_links=baseline.accepted_links,
+                proposed_links=baseline.proposed_links,
+                evidence=baseline.evidence,
+            )
+            if write_json(thread_path, thread):
                 written.append(thread_path)
 
     provider = FakeCandidateDiscovery.from_fixture(expected_dir / "candidate-links.json")
```

### Tests

```diff
diff --git a/backend/tests/conftest.py b/backend/tests/conftest.py
index b642849..1fd8164 100644
--- a/backend/tests/conftest.py
+++ b/backend/tests/conftest.py
@@ -31,7 +31,7 @@ import fixturectl  # noqa: E402 — tools/ is added to sys.path above
 from app.domain.oracle import BaselinesManifest, FixtureSnapshot  # noqa: E402
 from app.main import create_app  # noqa: E402
 from app.persistence.fixtures import load_model  # noqa: E402
-from app.persistence.store import FixtureStore  # noqa: E402
+from app.persistence.ingested import IngestedStore  # noqa: E402
 from app.settings import Settings  # noqa: E402
 
 FIXTURE_NAME = "banking-demo"
@@ -108,8 +108,12 @@ class BuiltFixture:
 
 
 @pytest.fixture(scope="session")
-def fixture_settings() -> Settings:
-    return Settings(repo_root=REPO_ROOT, fixtures_dir=REPO_ROOT / "fixtures")
+def fixture_settings(built_fixture: BuiltFixture) -> Settings:
+    return Settings(
+        repo_root=REPO_ROOT,
+        fixtures_dir=REPO_ROOT / "fixtures",
+        fixture_repo_path=built_fixture.repo,
+    )
 
 
 @pytest.fixture(scope="session")
@@ -130,8 +134,8 @@ def built_fixture(tmp_path_factory: pytest.TempPathFactory) -> BuiltFixture:
 
 
 @pytest.fixture(scope="session")
-def store(fixture_settings: Settings) -> FixtureStore:
-    return FixtureStore.from_settings(fixture_settings)
+def store(fixture_settings: Settings) -> IngestedStore:
+    return IngestedStore.from_settings(fixture_settings)
 
 
 @pytest.fixture(scope="session")
diff --git a/backend/tests/test_api_contract.py b/backend/tests/test_api_contract.py
index c1120db..c989a3c 100644
--- a/backend/tests/test_api_contract.py
+++ b/backend/tests/test_api_contract.py
@@ -6,9 +6,11 @@ import pytest
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
@@ -22,6 +24,7 @@ BASELINES = ("baseline-a", "baseline-b")
 
 CONTRACTED_PATHS = {
     "/health",
+    "/api/artifacts",
     "/api/artifacts/{artifact_id}",
     "/api/threads/{artifact_id}",
     "/api/findings",
@@ -279,13 +282,108 @@ def test_discovery_validates_its_payload(client: TestClient) -> None:
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
@@ -302,7 +400,7 @@ def test_contract_only_endpoints_are_honest(
     assert problem.milestone
 
 
-def test_contract_only_endpoints_still_validate_their_payloads(client: TestClient) -> None:
+def test_endpoints_still_validate_their_payloads(client: TestClient) -> None:
     assert client.post("/api/ingestion/run", json={}).status_code == 422
     assert (
         client.post(
diff --git a/backend/tests/test_contract_boundaries.py b/backend/tests/test_contract_boundaries.py
index bb9b606..1de22d0 100644
--- a/backend/tests/test_contract_boundaries.py
+++ b/backend/tests/test_contract_boundaries.py
@@ -22,8 +22,9 @@ from app.domain.oracle import CandidateIndexFile
 from app.domain.ports import ArtifactRepository
 from app.main import create_app
 from app.persistence.fixtures import load_model
-from app.persistence.store import FixtureStore
+from app.persistence.ingested import IngestedStore
 from app.settings import Settings
+from app.version import SCHEMA_VERSION
 
 
 def fixture_copy(fixture_settings: Settings, tmp_path: Path) -> Path:
@@ -36,7 +37,13 @@ def fixture_copy(fixture_settings: Settings, tmp_path: Path) -> Path:
 
 def app_over(fixture_settings: Settings, fixtures: Path) -> TestClient:
     return TestClient(
-        create_app(Settings(repo_root=fixture_settings.repo_root, fixtures_dir=fixtures))
+        create_app(
+            Settings(
+                repo_root=fixture_settings.repo_root,
+                fixtures_dir=fixtures,
+                fixture_repo_path=fixture_settings.fixture_repo_path,
+            )
+        )
     )
 
 
@@ -44,12 +51,12 @@ def app_over(fixture_settings: Settings, fixtures: Path) -> TestClient:
 
 
 def test_store_satisfies_the_artifact_repository_port(fixture_settings: Settings) -> None:
-    assert isinstance(FixtureStore.from_settings(fixture_settings), ArtifactRepository)
+    assert isinstance(IngestedStore.from_settings(fixture_settings), ArtifactRepository)
 
 
 def test_consumer_can_read_everything_through_the_port_alone(fixture_settings: Settings) -> None:
     """R1's acceptance condition: one constructor path, port methods only, real data returned."""
-    repository: ArtifactRepository = FixtureStore.from_settings(fixture_settings)
+    repository: ArtifactRepository = IngestedStore.from_settings(fixture_settings)
 
     assert repository.baselines() == ["baseline-a", "baseline-b"]
     assert repository.resolve_baseline("baseline-a") == "baseline-a"
@@ -85,7 +92,7 @@ def test_consumer_can_read_everything_through_the_port_alone(fixture_settings: S
 def test_port_reads_raise_documented_errors(fixture_settings: Settings) -> None:
     from app.domain.errors import ArtifactNotFound, BaselineNotFound
 
-    repository: ArtifactRepository = FixtureStore.from_settings(fixture_settings)
+    repository: ArtifactRepository = IngestedStore.from_settings(fixture_settings)
     with pytest.raises(ArtifactNotFound):
         repository.get_artifact("REQ-999", baseline="baseline-a")
     with pytest.raises(BaselineNotFound):
@@ -113,21 +120,22 @@ def test_thread_response_rejects_an_accepted_link_inside_proposals(client: TestC
     assert "proposed_links" in str(failure.value)
 
 
-def test_loader_rejects_a_mispartitioned_thread_file(
-    fixture_settings: Settings, tmp_path: Path
-) -> None:
+def test_thread_is_served_without_example_files(fixture_settings: Settings, tmp_path: Path) -> None:
     fixtures = fixture_copy(fixture_settings, tmp_path)
-    path = fixtures / "api-responses" / "threads" / "REQ-002.baseline-a.json"
-    payload = json.loads(path.read_text(encoding="utf-8"))
-    payload["accepted_links"] = payload.pop("proposed_links")
-    payload["proposed_links"] = []
-    path.write_text(json.dumps(payload), encoding="utf-8")
+    shutil.rmtree(fixtures / "api-responses" / "threads")
 
     response = app_over(fixture_settings, fixtures).get(
-        "/api/threads/REQ-002", params={"baseline": "baseline-a"}
+        "/api/threads/REQ-001", params={"baseline": "baseline-b"}
     )
-    assert response.status_code == 500
-    assert response.json()["code"] == "fixture-data-invalid"
+    assert response.status_code == 200
+    body = ThreadResponse.model_validate(response.json())
+    assert [artifact.artifact_id for artifact in body.artifacts] == [
+        "CODE-001",
+        "REQ-001",
+        "SCN-001",
+        "TEST-001",
+    ]
+    assert body.schema_version == SCHEMA_VERSION
 
 
 # ------------------------------------------------- R4: unsupported contract versions
@@ -136,7 +144,6 @@ def test_loader_rejects_a_mispartitioned_thread_file(
 @pytest.mark.parametrize(
     ("relative_path", "url"),
     [
-        ("threads/REQ-001.baseline-a.json", "/api/threads/REQ-001?baseline=baseline-a"),
         ("findings.baseline-a.json", "/api/findings?baseline=baseline-a"),
     ],
 )
@@ -156,17 +163,8 @@ def test_served_responses_reject_an_unsupported_schema_version(
     assert "999.0.0" in problem["detail"]
 
 
-def test_snapshot_and_index_versions_are_enforced(
-    fixture_settings: Settings, tmp_path: Path
-) -> None:
-    fixtures = fixture_copy(fixture_settings, tmp_path)
-    snapshot_path = fixtures / "api-responses" / "snapshot.json"
-    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
-    snapshot["schema_version"] = "999.0.0"
-    snapshot_path.write_text(json.dumps(snapshot), encoding="utf-8")
-    with pytest.raises(FixtureDataInvalid):
-        create_app(Settings(repo_root=fixture_settings.repo_root, fixtures_dir=fixtures))
-
+def test_candidate_index_version_is_enforced(fixture_settings: Settings) -> None:
+    """The snapshot is a test oracle now; the served app reads git and the baselines manifest."""
     index = load_model(fixture_settings.candidate_index_path, CandidateIndexFile)
     with pytest.raises(FixtureDataInvalid):
         FakeCandidateDiscovery(index.model_copy(update={"schema_version": "999.0.0"}))
diff --git a/backend/tests/test_fixture_oracle.py b/backend/tests/test_fixture_oracle.py
index 45554d5..e862db7 100644
--- a/backend/tests/test_fixture_oracle.py
+++ b/backend/tests/test_fixture_oracle.py
@@ -21,7 +21,7 @@ from app.domain.oracle import (
 )
 from app.domain.policy import RULE_DEFAULT_SEVERITY, RULE_FINDING_TYPE
 from app.persistence.fixtures import load_model
-from app.persistence.store import FixtureStore
+from app.persistence.ingested import IngestedStore
 from app.settings import Settings
 
 BASELINES = ("baseline-a", "baseline-b")
@@ -242,7 +242,7 @@ def test_case_5_failure_is_distinct_from_staleness(
 
 
 def test_change_summary_matches_content_hash_comparison(
-    store: FixtureStore, fixture_settings: Settings
+    store: IngestedStore, fixture_settings: Settings
 ) -> None:
     parsed = oracle(fixture_settings, "baseline-b")
     assert parsed.change_summary is not None
```

`backend/tests/test_ingested_store.py`:
```python
"""DT-04 store behaviour: configuration errors, content errors, and commit pinning."""

from __future__ import annotations

import shutil
from datetime import UTC, datetime
from pathlib import Path

import fixturectl
import pytest
from conftest import BuiltFixture

from app.domain.errors import FixtureDataInvalid, FixtureDataMissing
from app.domain.oracle import BaselineCommit, BaselinesManifest
from app.ingestion import GitRepository
from app.persistence.fixtures import load_model
from app.persistence.ingested import IngestedStore
from app.settings import ENV_FIXTURE_REPO, load_settings
from app.version import SCHEMA_VERSION


def test_commit_of_resolves_each_baseline(store: IngestedStore, committed_manifest) -> None:
    for name, commit in committed_manifest.tags.items():
        assert store.commit_of(name) == commit


def test_missing_fixture_repo_is_actionable(fixture_settings, tmp_path: Path) -> None:
    manifest = load_model(fixture_settings.baselines_manifest_path, BaselinesManifest)
    store = IngestedStore(
        repository=GitRepository(tmp_path / "absent"),
        manifest=manifest,
        repository_name="banking-demo",
    )
    with pytest.raises(FixtureDataMissing, match="fixturectl.py build"):
        store.get_artifact("REQ-001", baseline="baseline-a")


def test_settings_env_override(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv(ENV_FIXTURE_REPO, str(tmp_path))
    assert load_settings().fixture_repo == tmp_path.resolve()


def test_invalid_repository_content_is_a_fixture_error(
    built_fixture: BuiltFixture, tmp_path: Path
) -> None:
    repo = tmp_path / "repo"
    shutil.copytree(built_fixture.repo, repo)
    (repo / "evidence" / "accepted-links.json").write_text("{ not json", encoding="utf-8")
    fixturectl.git(["add", "-A"], cwd=repo)
    fixturectl.git(["commit", "-q", "-m", "break the link file"], cwd=repo)
    commit = fixturectl.git(["rev-parse", "HEAD"], cwd=repo)

    manifest = BaselinesManifest(
        schema_version=SCHEMA_VERSION,
        fixture="banking-demo",
        generated_by="test",
        commits=[
            BaselineCommit(
                id="broken",
                commit=commit,
                date=datetime.now(UTC),
                message="break the link file",
                tags=["broken"],
            )
        ],
        tags={"broken": commit},
    )
    store = IngestedStore(GitRepository(repo), manifest, "banking-demo")
    with pytest.raises(FixtureDataInvalid):
        store.list_artifacts("broken")
```

### Documentation

`docs/stories/DT-04.md`:
```markdown
# DT-04 — Retrieve the thread associated with a requirement

**Milestone:** M1 — AI-free vertical slice · **Owner:** B · **Implementer:** OMP (shared API
integration) · **Status:** refined; implementation in progress.

| Record | Value |
| --- | --- |
| Roadmap / feature | F-03 Links · roadmap §6 DT-04 |
| GitHub story | [#23](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/23) — verified OPEN 2026-11-13T03:12:49Z (`gh issue view`), milestone "M1 — AI-free vertical slice" |
| Parent feature issue | [#10](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/10) |
| Canonical criteria | [DT-04.feature](DT-04.feature), sha256 `02301bee448f33efc07d9e0e1d37ccafa1d1a2b9a9bd303bfa622a0fd5eb94e9` |
| Dependencies | DT-03 (#22) merged at `0970f7aa3334d88b3b19e29fae446e0eeb84593d`; DT-01/DT-02 ingestion |
| Upstream obligation | Roadmap §3 `ArtifactRepository`, §6 F-03; ADR 0002/0003; project-definition REQ-101/105 (draft) |

## User outcome

A reviewer can request one requirement's thread at a baseline and see its accepted chain and
evidence in one call, with proposals kept separate and the response assembled from ingested
repository data rather than a precomputed example.

## Scope

* `IngestedStore`: in-process store implementing `ArtifactRepository`, ingesting a revision on
  first use and caching it by resolved commit.
* Evidence ingestion (`evidence/verification-runs.json`) with artifact-reference validation.
* Thread assembly shared by the API and the fixture generator (`app/ingestion/thread.py`).
* API cutover: threads and artifacts come from the ingested store; `FixtureStore` and the
  precomputed thread replay are deleted. `GET /api/findings` remains the reviewed sample replay.
* `POST /api/ingestion/run` implemented for the configured fixture repository with deterministic
  counts and run id.
* Additive `GET /api/artifacts` inventory endpoint (needed by AS-04): `SCHEMA_VERSION` 0.1.0 →
  **0.2.0**, docs updated, fixtures regenerated.
* Add `commit_of(baseline)` to the `ArtifactRepository` port so findings/evidence can be pinned to
  the resolved SHA.

## Non-goals

General repository hosting; durable storage (ADR 0006 #1 remains open; M1 persistence is
in-process); a thread root other than a requirement (non-requirement roots keep the documented
`thread-not-found` 404); mutation of links/evidence; assurance rules (AS-01).

## Preservation boundaries

* Existing response shapes are preserved except the additive artifact-list envelope and the schema
  version bump.
* `GET /api/findings` keeps returning the reviewed sample findings; switching it to computed
  findings is deferred until the rule set is complete (M2), so M2 findings are not silently
  dropped.
* Unknown artifact → 404 `artifact-not-found`; known non-requirement root → 404 `thread-not-found`;
  unknown baseline → 404 `baseline-not-found`; malformed content → 500 `fixture-data-invalid`;
  missing fixture repo → 500 `fixture-data-missing` with the build instruction.
* Fixture inputs/oracle labels are not edited except their `schema_version`; generated files are
  regenerated and reviewed as a deliberate change.

## Design impact

`app/persistence/ingested.py` replaces `FixtureStore`; `app/ingestion/evidence.py` reads evidence;
`app/ingestion/thread.py` owns assembly; `app/domain/api.py` gains `ArtifactListResponse`;
`app/settings.py` gains `CTA_FIXTURE_REPO` (default `fixtures/<fixture>/.build/repo`);
`app/main.py` and `app/api/` wire the store and the implemented ingestion route.
`tools/fixturectl.py` delegates snapshot scanning, link/evidence loading, and thread assembly to
the shared ingestion code, so examples and served responses cannot drift.

Assumptions:

1. The fixture repository is built by `fixturectl build` before serving reads; startup itself only
   needs the committed baselines manifest, and reads give an actionable error if the repo is
   absent.
2. Baseline names/commits come from the committed manifest (the fixture's declared baselines);
   content comes from Git.
3. In-process caching is sufficient for a single-user demo; durable persistence is deferred.
4. Requirement roots only for threads in M1.
5. Evidence `test_id`/`scenario_id` must reference existing artifacts of the right type;
   `tested_commit` existence/freshness is DT-05/M2.

## Refinement disposition

Derived from the owner-authored issue intake and roadmap §6; cutover/failure/boundary scenarios
were added. No separate human refinement sign-off is recorded.

## Verification mapping

| Scenario | Observable check | Pytest selector |
| --- | --- | --- |
| SCN-611 fully linked thread | API body equals the committed example for all requirement/baseline pairs; tag vs SHA bodies identical | `backend/tests/test_api_contract.py::test_thread_matches_the_committed_example`, `::test_thread_carries_the_accepted_chain_with_evidence`, `::test_artifact_is_addressable_by_tag_or_commit` |
| SCN-612 proposal-only thread | `accepted_links == []`, LNK-007 only in `proposed_links` | `::test_thread_keeps_proposals_out_of_accepted_links` |
| SCN-613 assembled from ingestion | With the example thread directory removed, the API still returns the correct thread and current `schema_version` | `backend/tests/test_contract_boundaries.py::test_thread_is_served_without_example_files` |
| SCN-614 documented 404s | unknown artifact and non-requirement root | `::test_thread_reports_missing_roots_clearly` |
| SCN-615 ingestion counts | `POST /api/ingestion/run` counts and deterministic run id; unknown repository/revision | `backend/tests/test_api_contract.py::test_ingestion_run_reports_counts` |
| SCN-616 artifact inventory | all types and type filter; tag/SHA equality; unknown baseline | `::test_artifact_inventory_lists_and_filters` |
| DoD store errors | missing repo and malformed content are documented problems | `backend/tests/test_ingested_store.py::test_missing_fixture_repo_is_actionable`, `::test_invalid_repository_content_is_a_fixture_error` |

A mapping row is not an execution result; the run record carries the actual invocation and result.

## Verification plan

Full offline suite, fixture drift after regeneration, HTTP probes, network-denied suite, ruff.
```

```diff
diff --git a/docs/STATUS.md b/docs/STATUS.md
index ec87118..5de0322 100644
--- a/docs/STATUS.md
+++ b/docs/STATUS.md
@@ -2,10 +2,10 @@
 
 ```text
 Date:                2026-11-13
-Current branch:      feat/22-dt-03-links (from main 590e776)
+Current branch:      feat/23-dt-04-thread (from main 0970f7a)
 Milestone:           M0 — exit gate SATISFIED by re-review round 2 (historical record below)
                      M1 — IN PROGRESS; gate NOT yet satisfied
-Active task:         DT-03 (#22) typed, provenance-aware links with review state
+Active task:         DT-04 (#23) requirement thread, evidence, and the store/API cutover
 Independent review:  docs/reviews/M0-review.md — first review: "M0 not verified"
                      docs/reviews/M0-rereview-1.md — re-review round 1 (GPT-6.1 Sol, xhigh):
                      NEEDS_INPUT; R1–R7 all repaired; AC-1.1…AC-1.8 and AC-2.1…AC-2.5 all PASS;
@@ -20,13 +20,14 @@ Historical (SETUP-01, 2026-11-12): the commit-reference slice landed via PR #42;
                      had 107 passed; the SETUP-01 tree then had 135 passed (also under an
                      OS-level network denial). Outstanding owner actions: #18/#19 closure, the
                      FT-03/project-definition reviews, the required-check ruleset, README work item.
-Tests executed:      DT-03 (2026-11-13T02:53Z): 9 focused link tests passed; full suite recorded
-                     in docs/reports/omp-dt-03-links/.
+Tests executed:      DT-04 (in progress): cutover suite recorded in docs/reports/omp-dt-04-thread/.
+                     DT-03 approved snapshot: 219 passed; PR #46 merged as 0970f7a with both
+                     hosted checks passing; issue #22 closed.
                      DT-02 approved snapshot: 208 passed; PR #45 merged as 590e776 with both
                      hosted checks passing; issue #21 closed.
                      DT-01 approved snapshot: 183 passed; PR #44 merged as 26a25d0 with both
                      hosted checks passing; issue #20 closed.
-Current API/schema version: 0.1.0
+Current API/schema version: 0.2.0 (additive: `GET /api/artifacts`; fixtures regenerated)
 Tracker:             docs/traceability-issue-map.md (features → user stories → tasks)
 Run records:         docs/reports/omp-m0-rereview/ and docs/reports/omp-setup-01-commitlint/
                      (reports, prompt logs, metrics, evidence, packets; excluded from ruff scope
@@ -48,8 +49,8 @@ not claim that draft as an approved baseline.
 | --- | --- | --- | --- | --- |
 | DT-01 requirements + scenarios parsed | [#20](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/20) | B | [DT-01.feature](stories/DT-01.feature) | **merged** PR [#44](https://github.com/anthonygraca/gherkin-knowledge-graph/pull/44) → `26a25d0`; APPROVE at submission 5; issue closed |
 | DT-02 source/test artifacts | [#21](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/21) | B | [DT-02.feature](stories/DT-02.feature) | **merged** PR [#45](https://github.com/anthonygraca/gherkin-knowledge-graph/pull/45) → `590e776`; APPROVE at submission 4; issue closed |
-| DT-03 typed links + review state | [#22](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/22) | B | [DT-03.feature](stories/DT-03.feature) | refined; implementation in review |
-| DT-04 requirement thread | [#23](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/23) | B | not yet written | eligible after DT-03 |
+| DT-03 typed links + review state | [#22](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/22) | B | [DT-03.feature](stories/DT-03.feature) | **merged** PR [#46](https://github.com/anthonygraca/gherkin-knowledge-graph/pull/46) → `0970f7a`; APPROVE at submission 2; issue closed |
+| DT-04 requirement thread | [#23](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/23) | B | [DT-04.feature](stories/DT-04.feature) | refined; implementation in review |
 | AS-01 missing-link finding | [#2](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/2) | C | not yet written | eligible after DT-04 |
 | AS-04 findings/coverage summary | [#26](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/26) | C | not yet written | eligible after AS-01 |
 
diff --git a/docs/api-contracts.md b/docs/api-contracts.md
index 9534520..65f1b55 100644
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
+generated from `fixtures/banking-demo/expected/baseline-*.json`; `POST /api/assurance/evaluate`
+runs the implemented deterministic rules. The replay remains until AS-02/AS-03 complete the rule
+set, so M2 findings are not silently dropped from this response.
 
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
 
diff --git a/docs/architecture.md b/docs/architecture.md
index 553c1d7..fa59b3d 100644
--- a/docs/architecture.md
+++ b/docs/architecture.md
@@ -37,20 +37,24 @@ Two rules explain most of the layout:
 | `app/domain/ports.py` | `ArtifactRepository`, `CandidateDiscovery`, `AssuranceEvaluator`, `ReviewService` | Contract (projects the interfaces for M1+) |
 | `app/domain/oracle.py` | Schemas of fixture inputs and generated snapshot | Contract |
 | `app/domain/policy.py` | Rule → finding type and severity policy | Contract |
-| `app/persistence/` | `FixtureStore`: reads `snapshot.json` and precomputed thread responses | Mock service |
+| `app/persistence/` | `IngestedStore`: ingests a revision and caches artifacts, links, evidence, and assembled threads | Working implementation (in-process) |
 | `app/discovery/fake.py` | Fixture-backed candidate provider | Working implementation (deliberately fake) |
-| `app/assurance/sample_findings.py` | Replay of reviewed sample findings | Mock service (rule engine arrives in C-PR1) |
+| `app/assurance/sample_findings.py` | Replay of reviewed sample findings | Mock service (rule engine arrives with AS-01) |
 | `app/api/` | Routes, dependencies, RFC 9457 problem documents | Working |
-| `app/ingestion/` | Revision-pinned parsing: requirement/Gherkin artifacts (DT-01), source/test annotations (DT-02), links (DT-03), store cutover (DT-04) | Requirements, scenarios, source, test, and links implemented; store cutover remains |
+| `app/ingestion/` | Revision-pinned parsing: requirements/Gherkin (DT-01), source/test (DT-02), links (DT-03), evidence + thread assembly (DT-04) | Implemented |
 | `frontend/` | React/TypeScript dashboard | Absent by design; created in C-PR1 |
 
 ## Request flows
 
-**Read a thread.** `GET /api/threads/{id}?baseline=…` → the baseline expression is resolved to a
-canonical baseline (`FixtureStore.resolve_baseline`) → the precomputed thread response for that
-baseline is loaded and validated against `ThreadResponse` → returned. Accepted links, proposals,
-and evidence are separate arrays, so a caller that walks only `accepted_links` cannot be misled by
-a proposal.
+**Read a thread.** `GET /api/threads/{id}?baseline=…` → the baseline expression resolves to a
+canonical name and commit (`IngestedStore.resolve_baseline`) → the revision is ingested once and
+cached → `assemble_thread` walks accepted links from the requirement root, then returns artifacts,
+accepted links, proposals, and evidence as separate arrays. No precomputed thread file is read.
+
+**Ingest a revision.** `POST /api/ingestion/run` → the configured repository is checked (400 for
+another name) → the expression resolves to a commit (404 if unknown) → artifacts, links, and
+evidence are parsed and validated → counts and a deterministic run id are returned. The cached
+revision then serves reads.
 
 **Propose candidates.** `POST /api/discovery` → source artifact existence is checked (404
 otherwise) → `ProviderRegistry.get(name)` returns the provider (400 for an unknown name) →
@@ -72,7 +76,7 @@ writes the responses. `verify` does all of that into a temporary directory and d
 | Fixture tests passing/failing as labeled | Real: the suite runs the fixture's own tests at both tags. |
 | Findings | **Not computed.** Reviewed sample responses generated from the hand-labeled oracle. |
 | Retrieval quality | **Not measured.** Candidate scores are fixture labels, never model output. |
-| Ingestion from a real repository | Requirements and Gherkin scenarios are parsed from the nested fixture repository at a pinned revision (DT-01). Source/test artifacts, links, and the API cutover land in DT-02…DT-04; `POST /api/ingestion/run` still returns 501 until DT-04. |
+| Ingestion from a real repository | Requirements, scenarios, source, test, link, and evidence declarations are parsed from the nested fixture repository at a pinned revision; threads are assembled from that data (`POST /api/ingestion/run` reports counts). General non-fixture repositories remain a later capability. |
 | Link review and audit history | Not implemented; `POST /api/links/{id}/review` returns 501 naming AS-06. |
 
 This is why the `contract-only` endpoints return 501 instead of plausible-looking data: the
diff --git a/docs/domain-contracts.md b/docs/domain-contracts.md
index 95af502..eac5ac8 100644
--- a/docs/domain-contracts.md
+++ b/docs/domain-contracts.md
@@ -36,8 +36,10 @@ CI commits metadata after a verified revision.
   written against another version (`fixture-data-invalid`, 500). Serving mixed contract versions is
   a defect, not a compatibility mode.
 * `ArtifactRepository` is the consumer-facing read contract: `baselines`, `resolve_baseline`,
-  `get_artifact`, `list_artifacts`, `list_links`, `list_evidence`, `changed_artifacts`. The M0
-  mock satisfies it, and a test reads the whole thread through the port alone.
+  `commit_of`, `get_artifact`, `list_artifacts`, `list_links`, `list_evidence`,
+  `changed_artifacts`. `resolve_baseline` is the display identity (tag when known); `commit_of`
+  returns the resolved SHA that evidence and findings are pinned to. The M0 mock satisfied the
+  port; the M1 store implements it over ingested Git data and passes the same contract tests.
 
 ## Relations
 
```

### Fixture inputs and one generated example

```diff
diff --git a/fixtures/api-responses/threads/REQ-001.baseline-b.json b/fixtures/api-responses/threads/REQ-001.baseline-b.json
index 0c1580a..1a22e08 100644
--- a/fixtures/api-responses/threads/REQ-001.baseline-b.json
+++ b/fixtures/api-responses/threads/REQ-001.baseline-b.json
@@ -1,5 +1,5 @@
 {
-  "schema_version": "0.1.0",
+  "schema_version": "0.2.0",
   "root_id": "REQ-001",
   "baseline": "baseline-b",
   "artifacts": [
@@ -9,7 +9,7 @@
       "title": "src/accounts.py",
       "source_uri": "fixture://banking-demo/src/accounts.py",
       "repository": "banking-demo",
-      "revision": "c02064fed61bcfc6ade5ea14ac62f9eb1b5f5c54",
+      "revision": "156ad72b01b361970cc22229e7a2b17f9d6bcb85",
       "content_hash": "sha256:0baefee8f4dc182521504365fdf9b698586eea5163ca2c9ea82e2253efe0f993",
       "locator": "src/accounts.py",
       "metadata": {}
@@ -20,7 +20,7 @@
       "title": "Instant withdrawal availability",
       "source_uri": "fixture://banking-demo/requirements/REQ-001.md",
       "repository": "banking-demo",
-      "revision": "c02064fed61bcfc6ade5ea14ac62f9eb1b5f5c54",
+      "revision": "156ad72b01b361970cc22229e7a2b17f9d6bcb85",
       "content_hash": "sha256:7f97fd8702c4b6456f6d3e57db82b78ede9103967d9fb29cbeb02843d0fd0b95",
       "locator": "requirements/REQ-001.md",
       "metadata": {
@@ -33,7 +33,7 @@
       "title": "Successful instant withdrawal",
       "source_uri": "fixture://banking-demo/features/withdrawals.feature",
       "repository": "banking-demo",
-      "revision": "c02064fed61bcfc6ade5ea14ac62f9eb1b5f5c54",
+      "revision": "156ad72b01b361970cc22229e7a2b17f9d6bcb85",
       "content_hash": "sha256:f0aa5fd8142558086324c19b2216375b9d6ef4445067791e134d37fee34eb9ad",
       "locator": "features/withdrawals.feature#SCN-001",
       "metadata": {}
@@ -44,7 +44,7 @@
       "title": "tests/test_accounts.py",
       "source_uri": "fixture://banking-demo/tests/test_accounts.py",
       "repository": "banking-demo",
-      "revision": "c02064fed61bcfc6ade5ea14ac62f9eb1b5f5c54",
+      "revision": "156ad72b01b361970cc22229e7a2b17f9d6bcb85",
       "content_hash": "sha256:b42df9febafa4a5e72ef581d833f9f329568024b5e96613c028de4747f164b92",
       "locator": "tests/test_accounts.py",
       "metadata": {}
@@ -104,7 +104,7 @@
       "test_id": "TEST-001",
       "scenario_id": "SCN-001",
       "result": "passed",
-      "tested_commit": "81efe21a8ffd25243cb67485ede76d3be3fd7d24",
+      "tested_commit": "903977de5836fd45fa6e468d33560de2fb1d6eb1",
       "executed_at": "2026-10-01T09:12:00Z",
       "run_uri": "ci://banking-demo/runs/1001"
     }
diff --git a/fixtures/banking-demo/changes/02-baseline-a-evidence/evidence/verification-runs.json b/fixtures/banking-demo/changes/02-baseline-a-evidence/evidence/verification-runs.json
index 69f5d46..dd9f8e5 100644
--- a/fixtures/banking-demo/changes/02-baseline-a-evidence/evidence/verification-runs.json
+++ b/fixtures/banking-demo/changes/02-baseline-a-evidence/evidence/verification-runs.json
@@ -1,5 +1,5 @@
 {
-  "schema_version": "0.1.0",
+  "schema_version": "0.2.0",
   "repository": "banking-demo",
   "runs": [
     {
diff --git a/fixtures/banking-demo/changes/04-baseline-b-evidence/evidence/verification-runs.json b/fixtures/banking-demo/changes/04-baseline-b-evidence/evidence/verification-runs.json
index fb4f1ca..1cfad9e 100644
--- a/fixtures/banking-demo/changes/04-baseline-b-evidence/evidence/verification-runs.json
+++ b/fixtures/banking-demo/changes/04-baseline-b-evidence/evidence/verification-runs.json
@@ -1,5 +1,5 @@
 {
-  "schema_version": "0.1.0",
+  "schema_version": "0.2.0",
   "repository": "banking-demo",
   "runs": [
     {
diff --git a/fixtures/banking-demo/expected/baseline-a.json b/fixtures/banking-demo/expected/baseline-a.json
index a516d53..b801736 100644
--- a/fixtures/banking-demo/expected/baseline-a.json
+++ b/fixtures/banking-demo/expected/baseline-a.json
@@ -1,5 +1,5 @@
 {
-  "schema_version": "0.1.0",
+  "schema_version": "0.2.0",
   "fixture": "banking-demo",
   "baseline": "baseline-a",
   "notes": [
diff --git a/fixtures/banking-demo/expected/baseline-b.json b/fixtures/banking-demo/expected/baseline-b.json
index 6ce7b7d..555adf0 100644
--- a/fixtures/banking-demo/expected/baseline-b.json
+++ b/fixtures/banking-demo/expected/baseline-b.json
@@ -1,5 +1,5 @@
 {
-  "schema_version": "0.1.0",
+  "schema_version": "0.2.0",
   "fixture": "banking-demo",
   "baseline": "baseline-b",
   "notes": [
diff --git a/fixtures/banking-demo/expected/candidate-links.json b/fixtures/banking-demo/expected/candidate-links.json
index c242c04..20572ac 100644
--- a/fixtures/banking-demo/expected/candidate-links.json
+++ b/fixtures/banking-demo/expected/candidate-links.json
@@ -1,5 +1,5 @@
 {
-  "schema_version": "0.1.0",
+  "schema_version": "0.2.0",
   "fixture": "banking-demo",
   "provider": "fake",
   "model_version": "fake-fixture-v1",
diff --git a/fixtures/banking-demo/history.json b/fixtures/banking-demo/history.json
index cd73a87..cbdd7cd 100644
--- a/fixtures/banking-demo/history.json
+++ b/fixtures/banking-demo/history.json
@@ -1,5 +1,5 @@
 {
-  "schema_version": "0.1.0",
+  "schema_version": "0.2.0",
   "fixture": "banking-demo",
   "commits": [
     {
diff --git a/fixtures/banking-demo/tree/evidence/accepted-links.json b/fixtures/banking-demo/tree/evidence/accepted-links.json
index 3e94186..6ff7fdb 100644
--- a/fixtures/banking-demo/tree/evidence/accepted-links.json
+++ b/fixtures/banking-demo/tree/evidence/accepted-links.json
@@ -1,5 +1,5 @@
 {
-  "schema_version": "0.1.0",
+  "schema_version": "0.2.0",
   "repository": "banking-demo",
   "review_state": "accepted",
   "links": [
diff --git a/fixtures/banking-demo/tree/evidence/proposed-links.json b/fixtures/banking-demo/tree/evidence/proposed-links.json
index 9e4c715..6eaaa10 100644
--- a/fixtures/banking-demo/tree/evidence/proposed-links.json
+++ b/fixtures/banking-demo/tree/evidence/proposed-links.json
@@ -1,5 +1,5 @@
 {
-  "schema_version": "0.1.0",
+  "schema_version": "0.2.0",
   "repository": "banking-demo",
   "review_state": "proposed",
   "links": [
```

The remaining generated files (manifest, snapshot, findings, other threads, discovery responses) are
hash-listed above and are produced by `fixturectl all`; they are not hand-edited.

## 5. Implementation context

* `IngestedStore.from_settings` reads the committed baselines manifest and points `GitRepository` at
  `CTA_FIXTURE_REPO` (default `fixtures/<fixture>/.build/repo`). Startup needs only the manifest;
  the first read ingests and caches the commit.
* `ingest_revision` resolves once, scans artifacts, loads links, then evidence (validating test and
  scenario references). `assemble_thread` walks accepted links and keeps proposals/evidence
  separate.
* `GET /api/artifacts` is the additive inventory; `POST /api/ingestion/run` reports counts and a
  deterministic run id; threads and artifacts no longer read `fixtures/api-responses/`.
* Targeted reads: `backend/app/domain/models.py`, `docs/domain-contracts.md`, `docs/api-contracts.md`,
  `backend/tests/conftest.py`, `backend/tests/test_fixture_repo.py`.

## 6. Evidence

| Criterion | Check | Result |
| --- | --- | --- |
| SCN-611 | `tests/test_api_contract.py::test_thread_carries_the_accepted_chain_with_evidence`, `::test_thread_matches_the_committed_example`, `::test_artifact_is_addressable_by_tag_or_commit` | PASS |
| SCN-612 | `::test_thread_keeps_proposals_out_of_accepted_links` | PASS |
| SCN-613 | `tests/test_contract_boundaries.py::test_thread_is_served_without_example_files` | PASS |
| SCN-614 | `tests/test_api_contract.py::test_thread_reports_missing_roots_clearly` | PASS |
| SCN-615 | `tests/test_api_contract.py::test_ingestion_run_reports_counts` | PASS |
| SCN-616 | `tests/test_api_contract.py::test_artifact_inventory_lists_and_filters` | PASS |
| Store errors | `tests/test_ingested_store.py` (4 tests) | PASS |
| Fixture discipline | `fixturectl.py verify` exit 0 after regeneration | PASS |

Actual invocations and exits, captured 2026-11-13T03:28:33Z–03:28:51Z:

```text
uv run --project backend pytest backend/tests -q exit 0  224 passed, 1 warning in 6.65s
uv run --project backend python tools/fixturectl.py verify  exit 0  reproducible and current
uv run --project backend ruff check .            exit 0  All checks passed
uv run --project backend ruff format --check .   exit 0  all files formatted
git diff --check                                 exit 0
unshare -rn backend/.venv/bin/python -m pytest backend/tests -q  exit 0  224 passed
```

HTTP demo on port 8011 (server started and stopped by OMP; captures in the run directory):

```text
GET /health 200 0.2.0 | GET /api/artifacts 200 10 artifacts
GET /api/threads/REQ-001?baseline=baseline-b 200: CODE-001,REQ-001,SCN-001,TEST-001;
  LNK-001..003; EV-001; tag and SHA bodies byte-identical
POST /api/ingestion/run baseline-a 200: ing-0f8607b29d1c, 10/6/1/2
GET /api/threads/CODE-001 404 thread-not-found
POST /api/assurance/evaluate 501 not-implemented (AS-01…AS-03)
```

NOT RUN: frontend (AS-04), link-review mutations (AS-06), general non-fixture repositories.

## 7. File-integrity requirement

The manifest in section 3 is the reviewed snapshot. If any manifest hash changed, the snapshot is
not the one reviewed. Do not edit files, install dependencies, regenerate fixtures, or commit.

## Reviewer instructions (mandatory)

You are the independent CTA implementation reviewer using GPT-6.1 Sol xhigh. Decide whether this exact snapshot satisfies the supplied story, every applicable Gherkin criterion, and repository invariants. Treat OMP's summaries and test results as claims to check against the supplied artifacts and targeted source inspection. Check proposal/accepted/evidence separation, real port compatibility, revision/content-hash semantics, honest errors/501s, independent oracle expectations, offline defaults, and generated-file discipline where relevant. Do not demand implementation of a later milestone. Do not edit files, implement repairs, regenerate fixtures, commit, or delegate. Ask OMP for missing runtime evidence; distinguish observed defects from hypotheses and unavailable checks. Return an AC-by-AC PASS, FAIL, or NOT VERIFIED assessment and actionable findings with stable IDs, severity, blocking status, AC/invariant, path/line, expected/actual behavior, and smallest correction/recheck. Keep optional suggestions and unrelated pre-existing defects separate. Return exactly one verdict: APPROVE, REQUEST_CHANGES, or NEEDS_INPUT. APPROVE requires every applicable criterion/check to be satisfied, no unresolved blocker, and the exact snapshot identified. In later rounds verify prior dispositions and regressions while retaining the complete acceptance assessment. A passing process, passing tests, or exhausted review limit is not approval. Agent review cannot attest human labeling or human link decisions.
