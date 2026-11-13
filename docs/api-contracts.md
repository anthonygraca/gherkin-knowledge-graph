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
  "schema_version": "0.2.0",
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
  "schema_version": "0.2.0",
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
  "schema_version": "0.2.0",
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
  "schema_version": "0.2.0",
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
  "schema_version": "0.2.0",
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
{ "artifact_id": "SCN-001", "top_k": 5, "relation_types": null, "provider": null }
```

* `top_k` 1…50 (default 5); `relation_types` restricts proposals; `provider` overrides the
  configured default (`CTA_DISCOVERY_PROVIDER`, default `fake`).

Response (abridged; `fixtures/api-responses/discovery.SCN-001.json` is the full sample):

```json
{
  "schema_version": "0.2.0",
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
`provider-not-registered`.

## Contract-only endpoints (501)

Each returns a problem document naming the owning story and milestone, and each validates its body
first, so the contract is real even though the behaviour is not implemented:

| Endpoint | Body | Owning work |
| --- | --- | --- |
| `POST /api/links/{link_id}/review` | `{ "decision": "accept" \| "reject", "reviewer_id": "rv-ana", "reason": null }` | AS-06 (C, M1/M2) |

```json
{
  "type": "urn:cta:error:not-implemented",
  "title": "Not implemented in this milestone",
  "status": 501,
  "detail": "Link review with reviewer identity, timestamp, reason, and immutable decision history is implemented with AS-06. Accepting a link will not change verification status: an accepted link is not evidence of behaviour.",
  "instance": "/api/links/LNK-007/review",
  "code": "not-implemented",
  "story": "AS-06 (C-PR1 onward)",
  "milestone": "M1/M2"
}
```

## Conventions for consumers

* Switch on `status` and `code`, never on message text.
* Treat 501 as "not yet", not as an error to retry.
* Read proposals only from `proposed_links` / `candidates`; never treat them as accepted.
* Do not cache findings across baselines: `evaluated_baseline` is part of their meaning.
