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
  "schema_version": "0.1.0",
  "fixture": "banking-demo",
  "baselines": ["baseline-a", "baseline-b"],
  "baseline_commits": {
    "baseline-a": "67109fac965377629c9ab5835541aa64461db785",
    "baseline-b": "c02064fed61bcfc6ade5ea14ac62f9eb1b5f5c54"
  },
  "discovery_providers": ["fake"]
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
  "revision": "67109fac965377629c9ab5835541aa64461db785",
  "content_hash": "sha256:7f97fd8702c4b6456f6d3e57db82b78ede9103967d9fb29cbeb02843d0fd0b95",
  "locator": "requirements/REQ-001.md",
  "metadata": { "status": "active" }
}
```

### `GET /api/threads/{artifact_id}?baseline=…`

The digital thread for one artifact: reachable artifacts, accepted links, proposals kept in a
separate array, and evidence for the scenarios and tests in the thread.

```json
{
  "schema_version": "0.1.0",
  "root_id": "REQ-002",
  "baseline": "baseline-a",
  "artifacts": [
    {
      "artifact_id": "REQ-002",
      "artifact_type": "requirement",
      "title": "Daily transfer limit enforcement",
      "source_uri": "fixture://banking-demo/requirements/REQ-002.md",
      "repository": "banking-demo",
      "revision": "67109fac965377629c9ab5835541aa64461db785",
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

404 `artifact-not-found` for an unknown id; 404 `thread-not-found` when the artifact exists but no
thread is materialized for it (M0 materializes requirement roots; general thread assembly is
DT-04/B-PR1).

### `GET /api/findings?baseline=…`

Findings for one baseline, ordered as in the oracle. **M0 replays reviewed sample findings**
generated from `fixtures/banking-demo/expected/baseline-*.json`; deterministic rule evaluation
arrives with AS-01…AS-03 (C-PR1) and is tested against the same oracle.

```json
{
  "schema_version": "0.1.0",
  "baseline": "baseline-b",
  "findings": [
    {
      "finding_id": "FND-c458a6d4a5494d67",
      "finding_type": "reverification_required",
      "status": "open",
      "severity": "medium",
      "artifact_ids": ["CODE-001", "REQ-001", "SCN-001"],
      "evaluated_baseline": "c02064fed61bcfc6ade5ea14ac62f9eb1b5f5c54",
      "evidence_ids": ["EV-001"],
      "explanation": "SCN-001 verification passed at baseline-a (EV-001). CODE-001 changed at baseline-b and no later evidence for SCN-001 exists, so reverification is required. This is not a verification failure.",
      "rule_id": "RULE-REVERIFICATION-REQUIRED",
      "artifact_revisions": {
        "CODE-001": "c02064fed61bcfc6ade5ea14ac62f9eb1b5f5c54",
        "REQ-001": "c02064fed61bcfc6ade5ea14ac62f9eb1b5f5c54",
        "SCN-001": "c02064fed61bcfc6ade5ea14ac62f9eb1b5f5c54"
      }
    }
  ]
}
```

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
  "schema_version": "0.1.0",
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

## Contract-only endpoints (501 in M0)

Each returns a problem document naming the owning story and milestone, and each validates its body
first, so the contract is real even though the behaviour is not implemented:

| Endpoint | Body | Owning work |
| --- | --- | --- |
| `POST /api/ingestion/run` | `{ "repository": "banking-demo", "revision": null }` | DT-01, DT-02, DT-04 (B-PR1, M1) |
| `POST /api/links/{link_id}/review` | `{ "decision": "accept" \| "reject", "reviewer_id": "rv-ana", "reason": null }` | AS-06 (C, M1/M2) |
| `POST /api/assurance/evaluate` | `{ "baseline": "baseline-a", "policy": null }` | AS-01…AS-03 (C-PR1, M1/M2) |

```json
{
  "type": "urn:cta:error:not-implemented",
  "title": "Not implemented in this milestone",
  "status": 501,
  "detail": "Deterministic rule evaluation is implemented with AS-01…AS-03 against the fixture oracle. GET /api/findings currently returns the reviewed sample findings.",
  "instance": "/api/assurance/evaluate",
  "code": "not-implemented",
  "story": "AS-01, AS-02, AS-03 (C-PR1)",
  "milestone": "M1/M2"
}
```

## Conventions for consumers

* Switch on `status` and `code`, never on message text.
* Treat 501 as "not yet", not as an error to retry.
* Read proposals only from `proposed_links` / `candidates`; never treat them as accepted.
* Do not cache findings across baselines: `evaluated_baseline` is part of their meaning.
