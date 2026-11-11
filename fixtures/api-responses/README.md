# Generated API responses

**Do not edit by hand.** Every file here is produced by
`uv run --project backend python tools/fixturectl.py materialize` and drift-checked by
`fixturectl.py verify`, CI, and `backend/tests/test_fixture_drift.py`.

| File | Model | Served by / useful for |
| --- | --- | --- |
| `snapshot.json` | `FixtureSnapshot` | `FixtureStore`: artifacts, accepted links, proposed links, and evidence for every fixture baseline |
| `findings.baseline-a.json`, `findings.baseline-b.json` | `MaterializedFindings` | `GET /api/findings`; UI fixtures; rule-engine tests |
| `threads/REQ-001.baseline-a.json`, … (3 requirements × 2 baselines) | `ThreadResponse` | `GET /api/threads/{id}`; UI fixtures |
| `discovery.REQ-002.json`, `discovery.SCN-001.json`, `discovery.SCN-002.json`, `discovery.SCN-003.json` | `DiscoveryResponse` | `POST /api/discovery`; samples for every artifact that appears as a candidate source |

Provenance per family: `snapshot.json` is scanned from the generated Git revisions;
`findings.*.json` are stamped from the hand-labeled oracle (revisions, fingerprints); `threads/*`
are assembled from accepted links plus evidence; `discovery.*.json` are produced by calling the
real fake-provider code over the hand-labeled index.

Because these files are generated *and* validated against the same Pydantic models the API returns,
a fixture that no longer satisfies its contract fails the suite instead of reaching a client.
