# API contracts

Base URL: `http://127.0.0.1:8000`. Interactive schema: `GET /docs`, machine-readable:
`GET /openapi.json`. All shapes are Pydantic models in `backend/app/domain/api.py`; full
examples are committed under `fixtures/api-responses/`.

**Baseline resolution (applies to every endpoint).** A baseline parameter accepts a fixture tag
(`baseline-a`) or a commit SHA. Omitting it selects the latest baseline. Responses report the
canonical baseline name when the revision resolves to a known baseline, otherwise the SHA; calling
with a tag and with that tag's SHA returns identical bodies. Version-pinning fields
(`artifact.revision`, `finding.evaluated_baseline`) always contain the resolved commit SHA.

## Reads

### `GET /health`

```json
{
  "status": "ok",
  "package_version": "0.1.0",
  "schema_version": "0.5.0",
  "fixture": "banking-demo",
  "baselines": ["baseline-a", "baseline-b"],
  "baseline_commits": {
    "baseline-a": "0f8607b29d1ccb423062d856835f5310c9f54aa3",
    "baseline-b": "156ad72b01b361970cc22229e7a2b17f9d6bcb85"
  },
  "discovery_providers": ["fake"]
}
```

### `GET /api/artifacts?baseline=…&artifact_type=…`

The artifact inventory at one baseline, sorted by `artifact_id`. `artifact_type` is optional
(`requirement`, `scenario`, `source`, `test`). Added in schema 0.2.0; it lets the dashboard derive
coverage without hard-coded identities.

```json
{
  "schema_version": "0.5.0",
  "baseline": "baseline-a",
  "artifacts": [
    {
      "artifact_id": "REQ-001",
      "artifact_type": "requirement",
      "title": "Instant withdrawal availability",
      "source_uri": "fixture://banking-demo/requirements/REQ-001.md",
      "repository": "banking-demo",
      "revision": "0f8607b29d1ccb423062d856835f5310c9f54aa3",
      "content_hash": "sha256:…",
      "locator": "requirements/REQ-001.md",
      "metadata": { "status": "active" }
    }
  ]
}
```

### `GET /api/artifacts/{artifact_id}?baseline=…`

Returns one version-specific `Artifact`. `artifact_id` must match `^(REQ|SCN|CODE|TEST)-\d{3}$`;
a malformed id is a 422, an unknown but well-formed id is a 404.

```json
{
  "artifact_id": "REQ-001",
  "artifact_type": "requirement",
  "title": "Instant withdrawal availability",
  "source_uri": "fixture://banking-demo/requirements/REQ-001.md",
  "repository": "banking-demo",
  "revision": "0f8607b29d1ccb423062d856835f5310c9f54aa3",
  "content_hash": "sha256:7f97fd8702c4b6456f6d3e57db82b78ede9103967d9fb29cbeb02843d0fd0b95",
  "locator": "requirements/REQ-001.md",
  "metadata": { "status": "active" }
}
```

### `GET /api/threads/{artifact_id}?baseline=…`

The digital thread for one requirement, assembled from the ingested revision: reachable artifacts,
accepted links, proposals kept in a separate array, and evidence for the scenarios and tests in the
thread. The response is identical whether the request names the baseline tag or its commit SHA, and
it does not read the generated example files.

```json
{
  "schema_version": "0.5.0",
  "root_id": "REQ-002",
  "baseline": "baseline-a",
  "artifacts": [
    {
      "artifact_id": "REQ-002",
      "artifact_type": "requirement",
      "title": "Daily transfer limit enforcement",
      "source_uri": "fixture://banking-demo/requirements/REQ-002.md",
      "repository": "banking-demo",
      "revision": "0f8607b29d1ccb423062d856835f5310c9f54aa3",
      "content_hash": "sha256:…",
      "locator": "requirements/REQ-002.md",
      "metadata": { "status": "active" }
    }
  ],
  "accepted_links": [],
  "proposed_links": [
    {
      "link_id": "LNK-007",
      "source_id": "REQ-002",
      "target_id": "SCN-002",
      "relation_type": "verified_by",
      "review_state": "proposed",
      "provenance": { "discovery_provider": "fake", "score": 0.88, "index_revision": "sha256:…" },
      "created_at": "2026-09-30T08:15:00Z",
      "updated_at": "2026-09-30T08:15:00Z"
    }
  ],
  "evidence": []
}
```

404 `artifact-not-found` for an unknown id; 404 `thread-not-found` when the artifact exists but is
not a requirement root (M1 assembles requirement threads; other roots are a documented 404).

### `GET /api/findings?baseline=…`

Findings for one baseline, ordered as in the oracle. **M1 replays reviewed sample findings**
generated from `fixtures/banking-demo/expected/baseline-*.json`; `POST /api/assurance/evaluate`
runs the implemented M1 rule subset. The replay remains until the rule set is implemented, so M2
findings are not silently dropped from this response.

```json
{
  "schema_version": "0.5.0",
  "baseline": "baseline-b",
  "findings": [
    {
      "finding_id": "FND-c458a6d4a5494d67",
      "finding_type": "reverification_required",
      "status": "open",
      "severity": "medium",
      "artifact_ids": ["CODE-001", "REQ-001", "SCN-001"],
      "evaluated_baseline": "156ad72b01b361970cc22229e7a2b17f9d6bcb85",
      "evidence_ids": ["EV-001"],
      "explanation": "SCN-001 verification passed at baseline-a (EV-001). CODE-001 changed at baseline-b and no later evidence for SCN-001 exists, so reverification is required. This is not a verification failure.",
      "rule_id": "RULE-REVERIFICATION-REQUIRED",
      "artifact_revisions": {
        "CODE-001": "156ad72b01b361970cc22229e7a2b17f9d6bcb85",
        "REQ-001": "156ad72b01b361970cc22229e7a2b17f9d6bcb85",
        "SCN-001": "156ad72b01b361970cc22229e7a2b17f9d6bcb85"
      }
    }
  ]
}
```

## Ingestion

### `POST /api/ingestion/run`

Ingests the configured fixture repository (`CTA_FIXTURE`, default `banking-demo`) at a revision.
`revision` may be a tag, branch, or SHA; omitted means the repository's current `HEAD`. The run id
is derived from the resolved commit, so repeating a run is deterministic.

Request:

```json
{ "repository": "banking-demo", "revision": "baseline-a" }
```

Response:

```json
{
  "run_id": "ing-0f8607b29d1c",
  "repository": "banking-demo",
  "baseline": "baseline-a",
  "artifact_count": 10,
  "accepted_link_count": 6,
  "proposed_link_count": 1,
  "evidence_count": 2
}
```

Errors: unknown repository → 400 `invalid-request` naming the configured repository; unresolvable
revision → 404 `baseline-not-found`; malformed repository content → 500 `fixture-data-invalid`; a
missing built repository → 500 `fixture-data-missing` with the build instruction. A revision that is
not a named baseline is ingestable; `baseline` then reports the SHA.

## Assurance

### `POST /api/assurance/evaluate`

Runs the implemented deterministic rules for one baseline. M1 implements only
`RULE-MISSING-VERIFICATION-LINK`: a requirement with no accepted `verified_by` link to an existing
scenario. Proposals never satisfy it. `GET /api/findings` continues to replay the reviewed sample
responses until AS-02/AS-03 complete the rule set.

Request:

```json
{ "baseline": "baseline-a", "policy": null }
```

Response:

```json
{
  "schema_version": "0.5.0",
  "baseline": "baseline-a",
  "findings": [
    {
      "finding_id": "FND-8e701f84ea44fa6c",
      "finding_type": "missing_verification_link",
      "status": "open",
      "severity": "high",
      "artifact_ids": ["REQ-002"],
      "evaluated_baseline": "0f8607b29d1ccb423062d856835f5310c9f54aa3",
      "evidence_ids": [],
      "explanation": "REQ-002 has no accepted verification scenario at baseline-a.",
      "rule_id": "RULE-MISSING-VERIFICATION-LINK",
      "artifact_revisions": {
        "REQ-002": "0f8607b29d1ccb423062d856835f5310c9f54aa3"
      }
    }
  ]
}
```

Errors: unknown baseline → 404 `baseline-not-found`; unknown policy → 400 `invalid-request`; invalid
body → 422. Findings are deterministic and offline; `evaluated_baseline` and `artifact_revisions`
always carry the resolved commit SHA.

## Discovery

### `POST /api/discovery`

Request:

```json
{ "artifact_id": "SCN-001", "top_k": 5, "relation_types": null, "provider": null, "baseline": "baseline-a" }
```

* `top_k` 1…50 (default 5); `relation_types` restricts proposals; `provider` overrides the
  configured default (`CTA_DISCOVERY_PROVIDER`, default `fake`); `baseline` binds the request to a
  tag or commit SHA.
* A registered provider that cannot execute returns `503 provider-unavailable` with
  `failed_provider`; the application never falls back to `fake`. A valid empty result is `200` with
  `candidates: []` and retained provider/model/index provenance. Provider failure never becomes a
  finding.

Response (abridged; `fixtures/api-responses/discovery.SCN-001.json` is the full sample):

```json
{
  "schema_version": "0.7.0",
  "artifact_id": "SCN-001",
  "provider": "fake",
  "model_version": "fake-fixture-v1",
  "index_revision": "sha256:acb64531ff9e59bdad1de5f61232eff7cb2e4528de28da9bb25c85b58278da3d",
  "candidates": [
    {
      "source_id": "SCN-001",
      "target_id": "CODE-001",
      "proposed_relation_type": "implemented_by",
      "rank": 1,
      "score": 0.94,
      "discovery_provider": "fake",
      "model_version": "fake-fixture-v1",
      "index_revision": "sha256:acb64531ff9e59bdad1de5f61232eff7cb2e4528de28da9bb25c85b58278da3d",
      "rationale": "The scenario steps match Account.withdraw in src/accounts.py."
    }
  ]
}
```

Guarantees, asserted by tests: candidates carry no `link_id` and no `review_state`; no accepted
link or evidence record is created or modified; a known artifact with no proposals returns an
empty list; unknown artifact → 404 `artifact-not-found`; unknown provider → 400
`provider-not-registered` with `failed_provider` and `registered_providers`; provider failure →
503 `provider-unavailable`; no automatic fallback.

### `GET /api/discovery/providers`

Returns the effective registry with presentation kind:

```json
{
  "schema_version": "0.7.0",
  "default": "fake",
  "providers": [
    {"name": "fake", "kind": "fixture", "default": true},
    {"name": "cocoindex", "kind": "model", "default": false}
  ]
}
```

`kind` comes from the versioned provider-kind table, not from the provider name. Optional providers
absent from the effective registry are not listed; historical proposals retain their recorded
provenance and are labelled from the static table.

### Local embedding provider (AI-02, additive)

When `CTA_LOCAL_EMBEDDING=1` and a local model directory is installed, the effective registry also
lists `local-embeddinggemma` (`kind: model`). It implements the same request/response contract; a
remote endpoint is `400 invalid-request` before any connection, and missing weights or malformed
embeddings are `503 retrieval-unavailable`. The exact manifest is in
`docs/reports/omp-closeout/AI-02-MODEL-MANIFEST.md`.

## Review workspace endpoints (schema 0.6.0, additive; AS-06)

All review/workspace routes are loopback-only. A missing `Origin` header is allowed for local
non-browser clients; a present Origin must be an `http(s)` loopback origin. The full normative
contract is in `docs/stories/AS-06.md`.

### `POST /api/link-proposals`

Explicit capture of a discovery candidate as a proposed link. The body names the endpoints, the
relation, a required `baseline`, both submitted endpoint content hashes, and optional reported
provider/model/index provenance. `201` returns `{schema_version, link, snapshot, review_revision,
created: true}`. An identical pending snapshot returns `200` with `created: false`; an unknown or
wrong-direction endpoint is `422 proposal-invalid`; a hash mismatch is `409 proposal-stale`; a
different pending snapshot for the same triple **at the same baseline** is
`409 proposal-conflict`; a terminal decision for that baseline is `409 review-conflict`. A capture
at a different baseline is a distinct proposal. No validation or conflict failure appends an
event. A confirmed journal rollback returns `503 review-storage-unavailable` with
`durability: "not_committed"` and publishes nothing; an unconfirmed rollback returns the same code
with `durability: "indeterminate"`, publishes nothing to the live projection, and may recover as a
complete pending capture after restart — never as an accepted link.

### `POST /api/links/{link_id}/review`

```json
{"decision": "accept", "reviewer_id": "rv-ana", "baseline": "baseline-a", "reason": null}
```

Returns the resulting `TraceLink` (`200`). The response keeps the existing link shape; the
append-only audit record is available from `GET /api/workspace/history`. `reviewer_id` must equal
the server-assigned operator. Reject requires a nonblank reason. Precedence: identity unavailable
`503`, identity mismatch `403`, validation `422`, missing proposal `404`, reason rules `422`,
terminal conflict `409`, stale endpoint content `409`, storage failure `503` with `durability`.
Acceptance never runs assurance or changes evidence/findings.

### Workspace reads

|Endpoint|Response|
|---|---|
|`GET /api/workspace/threads/{artifact_id}?baseline=`|Thread fields plus `review_revision`; decisions projected over immutable baseline facts.|
|`GET /api/workspace/proposals?baseline=`|`{schema_version, baseline, review_revision, proposals: [{link, snapshot \| null, binding}]}` — the pending queue.|
|`GET /api/workspace/history?baseline=`|`{schema_version, baseline, review_revision, events}` — capture/decision events applicable to the baseline.|
|`GET /api/review/config`|`{schema_version, enabled, operator, loopback_only}`.|

Baseline reads (`/api/threads`, `/api/findings`, `/api/artifacts`, `/api/links`) are unchanged by
decisions. The workspace thread follows accepted and proposed links to assemble the review
neighbourhood, then keeps `accepted_links` and `proposed_links` partitioned.

## Retrieval lifecycle endpoints (schema 0.8.0, additive; AI-03)

|Endpoint|Behaviour|
|---|---|
|`POST /api/retrieval/refresh`|Body `{baseline, previous_baseline?, config?}`. Plans content changes and publishes a `RetrievalManifest`. The default adapter reports backend identity and `items_embedded` as `not_available`; an adapter failure is `503 retrieval-unavailable` with no publication. Evidence-only content with identical configuration reuses the corpus cache key and publishes a new commit-bound snapshot binding.|
|`GET /api/retrieval/manifests`|`{schema_version, manifests}` for all published snapshots.|
|`GET /api/retrieval/manifests/{baseline}`|The current manifest for a tag or commit, or `404 retrieval-snapshot-not-found`.|
|`POST /api/retrieval/combine`|Body `{snapshot_binding, batches: [{snapshot_binding, provider, provider_index_revision, model_version, candidates}]}`. A batch whose own candidates disagree with its declared binding is internally inconsistent and returns `422 request-validation`; a valid batch whose binding differs from the request binding returns `409 mixed-index-context`. Neither returns a combined list. Compatible batches are combined and re-ranked; the response retains each batch's provider provenance. The batch adaptation preserves the provider's own index revision separately from the CTA snapshot binding.|

Manifests are application-owned, outside the fixture/evaluated repository, and revision-bound. The
corpus cache key excludes commits; the snapshot binding includes the commit. CTA never claims an
internal CocoIndex embedding count; unavailable backend data is `null`/`not_available`.

## Conventions for consumers

* Switch on `status` and `code`, never on message text.
* Read proposals only from `proposed_links` / `candidates`; never treat them as accepted.
* Do not cache findings across baselines: `evaluated_baseline` is part of their meaning.
* No endpoint currently returns 501; the problem shape remains reserved for a future contract-only
  capability.


## Portable repository endpoints (schema 0.5.0, additive)

All responses are repository- and revision-scoped. Omitted `revision` means the most recently
indexed commit for that repository; an unindexed repository or revision is 404
`repository-not-indexed`, never an implicit index of another ref.

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/api/repositories/index` | Index a local Git repository at a pinned commit (read-only; no hooks) |
| GET | `/api/repositories` | Indexed repositories and their pinned revisions |
| GET | `/api/repositories/{id}/scenarios?revision=&path=&tag=` | Scenarios with source locators and outline instances |
| GET | `/api/repositories/{id}/scenario?scenario_key=` | One scenario |
| GET | `/api/repositories/{id}/steps?scenario_key=&text=` | Steps |
| GET | `/api/repositories/{id}/bindings` | Registered definitions and framework resolutions, or `not_available` |
| GET | `/api/repositories/{id}/unresolved-steps` | Undefined/ambiguous steps from a trusted report |
| POST | `/api/repositories/{id}/reports` | Import a Cucumber Messages report plus its provenance sidecar for the indexed commit |
| GET | `/api/repositories/{id}/executions` | Observed scenario executions and coverage counts |
| GET | `/api/repositories/{id}/relations` | Extracted/matched/observed relations |
| GET | `/api/repositories/{id}/executable-findings` | Executability findings |

Example (`GET /api/repositories/external-recipes/bindings?revision=v1`) before any report exists:

```json
{
  "schema_version": "0.5.0",
  "repository_id": "external-recipes",
  "revision": "4851146c92d4c02b1be5e3989a3947fb89997993",
  "availability": "not_available",
  "reason": "no trusted framework matching report has been imported for this revision; step matching is unknown, not undefined",
  "step_definitions": [],
  "resolutions": []
}
```

CLI equivalents (one JSON document each; exit 2 on failure):

```bash
python -m app.cli index ../repo --repo-id repo --ref v1
python -m app.cli scenarios ../repo --repo-id repo --ref v1 [--tag SCN-001]
python -m app.cli steps ../repo --repo-id repo --ref v1 --scenario <key>
python -m app.cli definitions ../repo --repo-id repo --ref v1 --report report.ndjson --tested-commit <sha>
python -m app.cli unresolved ../repo --repo-id repo --ref v1 --report report.ndjson --tested-commit <sha>
python -m app.cli executions ../repo --repo-id repo --ref v1
python -m app.cli findings ../repo --repo-id repo --ref v1
```


An import request carries `report_path`, `metadata_path`, and `tested_commit`. The metadata sidecar
must name the same `tested_commit` and, when present, the same `repository_id`; a report whose exact
bytes were already attributed to another revision is refused (`report-not-applicable`). Duplicate
imports of the same report at the same revision are idempotent (`imported: false`).


## Code retrieval endpoint (schema 0.5.0, additive)

`POST /api/retrieval/code` returns provenance-rich source/test proposals for one scenario at one
baseline. It writes nothing.

```json
{
  "artifact_id": "SCN-001",
  "baseline": "baseline-a",
  "top_k": 3,
  "method": "lexical"
}
```

Response (abridged):

```json
{
  "schema_version": "0.5.0",
  "artifact_id": "SCN-001",
  "baseline": "baseline-a",
  "revision": "<commit>",
  "status": "ok",
  "method": "lexical",
  "provider": "lexical",
  "model_version": "deterministic-token-overlap-v1",
  "index_binding": "snapshot:sha256:<digest>",
  "hits": [
    {
      "rank": 1,
      "score": 0.2857,
      "raw_score": 0.2857,
      "artifact_id": "CODE-001",
      "relation_type": "implemented_by",
      "path": "src/accounts.py",
      "start_line": 1,
      "end_line": 3,
      "revision": "<commit>",
      "content_hash": "sha256:<hash>",
      "method": "lexical"
    }
  ],
  "unresolved": [],
  "latency_ms": 0.7,
  "limitations": ["CocoIndex Code indexes code/test chunks, not Gherkin scenarios."]
}
```

Explicit `method: "cocoindex"` without configuration returns `status: "not_available"` with no
hits and a reason; it is not an empty success. A configured provider error is a 503 problem document
with the adapter's typed code (`cocoindex-*`). `POST /api/discovery` accepts an optional `baseline`
for the `cocoindex` provider; the default `fake` provider remains offline.


## Evidence-answer endpoint (schema 0.5.0, additive)

`POST /api/answers`

```json
{"requirement_id": "REQ-001", "baseline": "baseline-b", "include_semantic_candidates": false}
```

Returns `status`, deterministic `answer`, `evidence_state`, separated `accepted_links`/
`proposed_links`, artifacts, evidence, accepted-only `graph_paths`, deterministic findings,
optional semantic candidates, references, `explanation_method="deterministic"`, and
`chat_model=null`. Unknown requirement ids return 404; unmatched questions return
`status="not_found"` without inventing a requirement.
