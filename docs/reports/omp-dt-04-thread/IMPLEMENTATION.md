# DT-04 implementation record — requirement thread and the store/API cutover

| Field | Value |
| --- | --- |
| Story | DT-04 — [#23](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/23), verified OPEN 2026-11-13T03:12:49Z (`gh issue view`, milestone "M1 — AI-free vertical slice") |
| Canonical criteria | [DT-04.feature](../../stories/DT-04.feature), sha256 `02301bee448f33efc07d9e0e1d37ccafa1d1a2b9a9bd303bfa622a0fd5eb94e9` |
| Brief / verification map | [DT-04.md](../../stories/DT-04.md) |
| Branch / base | `feat/23-dt-04-thread` from `0970f7aa3334d88b3b19e29fae446e0eeb84593d` (DT-03 merge) |
| Contract version | `SCHEMA_VERSION = 0.2.0` (additive: `GET /api/artifacts`), `PACKAGE_VERSION = 0.1.0` |
| Submission | **2 of 7** — round 1 REQUEST_CHANGES, round 2 **APPROVE** (2026-11-13T03:53Z; R1–R3 closed) |
| Snapshot captured | 2026-11-13T03:42Z (approved snapshot) |

## What changed

| Path | sha256 | Purpose |
| --- | --- | --- |
| `backend/app/domain/api.py` | `b486374b06ad0f1f6492a95b8a2af2a0c52b27039011e8566f13d75762a0f65d` | `ArtifactListResponse` |
| `backend/app/domain/ports.py` | `17e65def989f2c24c5f4a7dc8514fe9c9e6c72b1a1eb52602f174de45292382d` | `commit_of` on `ArtifactRepository` |
| `backend/app/ingestion/__init__.py` | `4200999207d79bffbd59cd30b72959b2039c4b1067e827087ee75b037918ea0e` | Exports assembly/revision |
| `backend/app/ingestion/evidence.py` | `88db8934b47d78f2256a40b6f5bfca0e72cc062a4c297b282a66c0242ae385cf` | Evidence ingestion + artifact-reference validation |
| `backend/app/ingestion/revision.py` | `761fee3b1944516158773161b49747b6430853f7456d3c6be7028a148c783f07` | `IngestedRevision` gains evidence |
| `backend/app/ingestion/thread.py` | `e930e3043bb952c63ac3d9afb05bf7227ea3437284946188083187a04a4d47a4` | Shared thread assembly |
| `backend/app/persistence/__init__.py` | `b97341218d37c7f2ae78f03f2259478ab4b321f658cee0737a14397e9488c064` | Exports `IngestedStore` |
| `backend/app/persistence/ingested.py` | `5aa0cac1fa9bc5ccc997c9d6a335de42e6e0f0ef984e0ad82b64fb7e85535e44` | Store over ingested Git data; repository presence checked before resolution |
| `backend/app/persistence/store.py` | deleted | M0 fixture replay store removed |
| `backend/app/settings.py` | `397de92385a945305a221da84f98841dd031281c64acc3c1f96c87055d749341` | `CTA_FIXTURE_REPO` / `fixture_repo` |
| `backend/app/version.py` | `cd722cd24a15b23666731258391f8b6c1d1b943838248f3d81df6e5f3cf8275b` | Contract 0.2.0 |
| `backend/app/api/deps.py` | `b41c46ce5c0df6e781cdee3b4915aec6f4e59863501305e2040d6e9a6dd9b9cc` | Store dependency |
| `backend/app/api/routes.py` | `d19e2236c28e20db9a7d997bfaed63cf578ec9018d9c5fab3142b8dfb68a2eb6` | Inventory, ingestion, assembled thread; honest evaluate status |
| `backend/app/main.py` | `e016b3651009cd3e02e21ac58bc17cbb06e3f1404dfe3581b9602608dae534cd` | Wiring and status text |
| `tools/fixturectl.py` | `0072e017e27ff488b575300f1be324efe0a11ef7f84e92a5b960df210ac7bcae` | Generator uses the shared scanner/loaders/assembly |
| `backend/tests/conftest.py` | `db4b86fe1d073ec0c0c4b0c6cf7c76e7d3a9833f079576364e6e042d59e4ff47` | Built repo in test settings; ingested store |
| `backend/tests/test_api_contract.py` | `47b14c71abdc49150cb3a4ce160491649192255e03f79791ebd565620ebc5444` | Inventory, ingestion, thread tag/SHA, missing-repo tests |
| `backend/tests/test_contract_boundaries.py` | `cec02ad839f3765aea67b2778a978eab3ef03d791e679c714f51320c8500566a` | Port/instance checks and cutover probe |
| `backend/tests/test_fixture_oracle.py` | `e000af68929cd65e750c94f2dc8e80f17872841abebeedc0ed68f65ac27c47bc` | Store type updated |
| `backend/tests/test_ingested_store.py` | `7ba5d4729babe505ce7376b211d9c148cad15671b671da748895cab9405df6ba` | Configuration/content/revision error tests |
| `docs/stories/DT-04.feature` | `02301bee448f33efc07d9e0e1d37ccafa1d1a2b9a9bd303bfa622a0fd5eb94e9` | Canonical criteria (SCN-611…616) |
| `docs/stories/DT-04.md` | `77a94775b3697b80e6b7f4d6d1f9aad5f66d0909b82157cf917f94d978523841` | Brief, assumptions, map |
| `docs/api-contracts.md` | `98c1d9bfbf0f03a8522ab24ff146edb1fcc61ddd9a135ef8466d39a378d9f5dc` | Inventory/ingestion; 0.2.0 examples; honest evaluate status |
| `docs/domain-contracts.md` | `cabb8145a63df1759c2ada77fae90b9710011e5b7092d6903bf3b9cededf871c` | `commit_of`; link validation |
| `docs/architecture.md` | `e6ee7b22f41873915d75d958ffc3fd1e53cd7d3c581994e0df2a0d12350ef4c0` | Cutover flows and reality |
| `docs/STATUS.md` | `55fd461317745e1305f1104f383d543a0ba50ab896351559f9cc14f6d3d34d11` | DT-03 landed; DT-04 active; 0.2.0 |

### Fixture regeneration (deliberate, schema bump)

Eight input files changed only their `schema_version` (history, two expected finding files, the
candidate index, both fixture link files, both evidence overlays). `fixturectl all` regenerated 13
files: `expected/baselines.json`, `snapshot.json`, both findings responses, six thread examples,
and four discovery responses. The baseline SHAs changed because the evidence/link blobs changed:

```text
baseline-a  0f8607b29d1ccb423062d856835f5310c9f54aa3
baseline-b  156ad72b01b361970cc22229e7a2b17f9d6bcb85
```

Artifact content hashes for requirements, scenarios, source, and tests are unchanged (the fixture
source files were not edited). No oracle finding expectation changed; `fixturectl verify` passes.

## Review round 1 — REQUEST_CHANGES (submission 1 of 7)

Reviewer: Codex `gpt-6.1-sol`, `xhigh`, read-only; session `01a1d2f7-d05c-7f41-93c7-932192b55230`;
2026-11-13T03:33:38Z → 03:39:39Z (360.93 s), exit 0; 51/51 manifest hashes matched.
Verdict: `docs/reviews/DT-04-review.md`.

| Finding | Severity | Repair | Recheck |
| --- | --- | --- | --- |
| DT04-R1 `POST /api/ingestion/run` with a missing repository returned 404 `baseline-not-found` (“git is not installed”) instead of 500 `fixture-data-missing` | medium, blocking | `ingest()` checks repository availability before resolving the revision; the same `_require_repository` guard is used by reads and ingestion | `test_ingestion_with_a_missing_repo_is_fixture_data_missing` (API, 500 + build instruction), `test_missing_fixture_repo_is_actionable` (read + both ingestion forms), `test_ingestion_unknown_revision_in_an_existing_repo_is_404` |
| DT04-R2 findings description said evaluate runs implemented rules while it returns 501 | low, nonblocking | Route description and API docs state the contract-only status and owning stories | inspection of `routes.py` and `docs/api-contracts.md` |
| DT04-R3 SCN-611 mapping cited an artifact tag/SHA test, not the thread endpoint | low, nonblocking | Added `test_thread_by_tag_and_sha_are_identical` and corrected the mapping | `::test_thread_by_tag_and_sha_are_identical` |

## Review round 2 — APPROVE (submission 2 of 7)

Reviewer: same model/effort and read-only sandbox; session `01a1d304-ac33-7942-90b1-ca08da0eb87a`;
2026-11-13T03:47:40Z → 03:53:17Z (337.01 s), exit 0; 53/53 task hashes matched.
Verdict: `docs/reviews/DT-04-review-2.md`.

* R1–R3 closed; no open blocker.
* SCN-611…616 and the configuration-error boundary: PASS.
* Proposal/acceptance/evidence separation, port compatibility, revision/hash semantics,
  evidence-reference validation, offline defaults, schema bump, and unchanged oracle labels
  passed inspection and probes.
* The reviewer rechecked the missing-repository path and the thread tag/SHA equality.

Approval covers the identified snapshot. It does not attest human labeling, human link decisions,
sign-off, stakeholder acceptance, or milestone completion.

## Acceptance results

| Criterion | Check | Result |
| --- | --- | --- |
| SCN-611 fully linked thread | `tests/test_api_contract.py::test_thread_carries_the_accepted_chain_with_evidence`, `::test_thread_matches_the_committed_example`, `::test_thread_by_tag_and_sha_are_identical` | PASS |
| SCN-612 proposal-only thread | `::test_thread_keeps_proposals_out_of_accepted_links` | PASS |
| SCN-613 assembled from ingestion | `tests/test_contract_boundaries.py::test_thread_is_served_without_example_files` (thread dir removed) | PASS |
| SCN-614 documented 404s | `tests/test_api_contract.py::test_thread_reports_missing_roots_clearly` | PASS |
| SCN-615 ingestion counts | `tests/test_api_contract.py::test_ingestion_run_reports_counts` (10/6/1/3 latest; 10/6/1/2 at baseline-a; deterministic run id) | PASS |
| SCN-616 artifact inventory | `::test_artifact_inventory_lists_and_filters` (10 total, type filter, tag/SHA equality, unknown baseline) | PASS |
| DoD store errors | `tests/test_ingested_store.py` (missing repo read/ingestion, unknown revision, malformed content, settings, commit pinning), `tests/test_api_contract.py::test_ingestion_with_a_missing_repo_is_fixture_data_missing` | PASS |

## HTTP probes (observed)

The app was started on port 8011 with the built fixture repository, exercised, and stopped:

```text
GET  /health                                  200  schema_version=0.2.0; baselines a,b
GET  /api/artifacts?baseline=baseline-a       200  10 artifacts, all four types
GET  /api/artifacts?...&artifact_type=requirement 200 [REQ-001, REQ-002, REQ-003]
GET  /api/threads/REQ-001?baseline=baseline-b 200  CODE-001,REQ-001,SCN-001,TEST-001;
                                                   LNK-001..003; EV-001
GET  /api/threads/REQ-001?baseline=<sha>      200  byte-identical to the tag request
POST /api/ingestion/run {baseline-a}          200  ing-0f8607b29d1c; 10/6/1/2
GET  /api/threads/CODE-001                    404  thread-not-found
POST /api/assurance/evaluate                  501  not-implemented, story AS-01…AS-03
```

Captures are in the external run directory (`http-*.json`); the server log shows a clean shutdown.
The probe command's shell exit was 143 because it terminated the server it started; every request
above returned the recorded status/body.

## Commands and outcomes (as captured)

```text
captured_start=2026-11-13T03:41:56Z
pytest backend/tests -q                          exit 0  227 passed, 1 warning in 6.82s
fixturectl.py verify                             exit 0  reproducible and committed files current
ruff check .                                     exit 0  All checks passed
ruff format --check .                            exit 0  all files formatted
git diff --check                                 exit 0
captured_end=2026-11-13T03:42:05Z

network denial at 2026-11-13T03:42:05Z: `unshare -rn backend/.venv/bin/python -m pytest
backend/tests -q` → exit 0, 227 passed.
```

## Self-review

* **Cutover:** no route reads `snapshot.json` or a precomputed thread; `FixtureStore` is deleted.
  The thread example comparison and the example-directory-removal test both pass.
* **Honesty:** findings stay the reviewed replay until the rule set is complete; evaluate remains
  501; unknown roots/baselines use documented problems. Missing repo/content errors are actionable.
* **Revision-aware:** artifacts/links/evidence carry the resolved commit and blob hashes; tag/SHA
  requests are byte-identical.
* **Schema discipline:** one additive endpoint → MINOR bump; every fixture input declares 0.2.0;
  generated files regenerate and drift-check; oracle labels' expectations are unchanged.
* **Offline:** Git + JSON only; the network-denied suite and the HTTP demo require no external
  service.

Known limits: in-process cache (durable storage remains ADR 0006 #1); requirement roots only;
general non-fixture repositories are a later capability; `GET /findings` remains replay.

## Independent review

**APPROVE** — submission 2 of 7, snapshot captured 2026-11-13T03:42Z, reviewer `gpt-6.1-sol` at
`xhigh`, 53/53 manifest hashes confirmed. Verdict: `docs/reviews/DT-04-review-2.md`. No open
finding at this snapshot. Commit, PR, CI, and merge state are recorded separately after landing;
this approval does not close #23 by itself.
