# AI-02 — Live and offline evidence

**Captured:** 2026-11-14 · **Story:** AI-02 (#31)
**Model manifest:** [AI-02-MODEL-MANIFEST.md](AI-02-MODEL-MANIFEST.md)
**Evidence directory:** `docs/reports/omp-closeout/evidence/`

## Offline evidence (default suite / no model)

|Command|Result|
|---|---|
|`uv run --project backend pytest backend/tests/test_local_embedding.py -q`|**18 passed**|
|`npx cucumber-js --tags @AI-02` (offline scenarios SCN-3201…3204, 3206; SCN-3203 outline ×3)|**7 scenarios / 73 steps passed**|
|`uv run --project backend pytest backend/tests -q`|**552 passed, 4 skipped** (final close-out suite)|

The offline scenarios cover: default `fake` with no model/runtime import and no socket attempt
(SCN-3201); remote endpoint `400 invalid-request` before any connection (SCN-3202); absent weights,
digest mismatch, and missing runtime package each `503 retrieval-unavailable` with no fallback
(SCN-3203); the shared contract with a deterministic embedding runtime, including a legitimate
empty result with retained provenance and an explicit unavailable-provenance failure (SCN-3204);
and non-finite output `503 retrieval-unavailable` with no partial list or mutation (SCN-3206).

## Live evidence (real local model, non-loopback egress denied)

### Live pytest

```text
cmd=unshare -rn env CTA_LOCAL_EMBEDDING_LIVE_TESTS=1 \
  CTA_LOCAL_EMBEDDING_MODEL_DIR=$HOME/.local/share/cta/models/embeddinggemma-2-text-270m-onnx \
  PYTHONPATH=$PWD/backend backend/.venv/bin/python -m pytest \
  backend/tests/test_local_embedding_live.py -q -s
exit=0
1 passed, 1 warning in 30.66s
log=docs/reports/omp-closeout/evidence/AI-02-live-pytest.log
log_sha256=sha256:4650224e0d685e11c8ab1e81fc019915fd163c05138e32f464d51d33df8cd34e
measurement=docs/reports/omp-closeout/evidence/AI-02-live-measurement.jsonl
measurement_sha256=sha256:387213e862dae33a8a28909d642ab415594bf9b6d1732e9c355f0a9133560f01
```

`LIVE_MEASUREMENT` (the full verbatim line is retained in
`evidence/AI-02-live-measurement.jsonl`; this is the abridged reviewed view):

```json
{
  "binding_matches_fixture": true,
  "egress_denied_env": true,
  "expected_binding": "sha256:814eb9914310d4d18f68859fbb5e89230773f026a50e931cb16889b1e3eaac52",
  "external_egress": false,
  "formatting": "ai02-code-query-v1/document-title-text-v1",
  "git": "28c70cb4e0587f06898c0ebd1c14bcf1b25b0d72",
  "index_revision": "sha256:814eb9914310d4d18f68859fbb5e89230773f026a50e931cb16889b1e3eaac52",
  "index_seconds": 21.812,
  "load_seconds": 2.536,
  "manifest_weights_digest": "sha256:b396bde0f7a85398c9c42d08a3c0b68d30952e91dcd408bfa327c727e86457a3",
  "median_query_latency_ms": 664.0,
  "model_dir": "/home/anthonygraca/.local/share/cta/models/embeddinggemma-2-text-270m-onnx",
  "model_version": "embeddinggemma-2-text-270m-q8_0@sha256:b396bde0f7a8",
  "network_namespace": "net:[4026532663]",
  "query_latency_ms": [638.0, 923.5, 664.0],
  "results": {
    "REQ-001": ["SCN-001", "SCN-003", "SCN-002"],
    "SCN-001": ["CODE-001", "TEST-001", "CODE-002", "TEST-002"],
    "SCN-002": ["CODE-002", "TEST-002", "CODE-001", "TEST-001"]
  },
  "rss_after_kib": 583568,
  "rss_before_kib": 63388,
  "rss_delta_kib": 520180,
  "runtime": "onnxruntime 1.32.0",
  "thread_accepted_links": 3,
  "thread_equal": true,
  "thread_proposed_links": 0,
  "top_k_rejected": true,
  "weights_digest": "sha256:b396bde0f7a85398c9c42d08a3c0b68d30952e91dcd408bfa327c727e86457a3"
}
```

The live run asserts the selected baseline-a binding equals the reviewed fixed vector above, not a
value recomputed from the provider. It also exercises `top_k=0` rejection (`ValueError` in the
provider contract) and compares the `/api/threads/REQ-001?baseline=baseline-a` response before and
after discovery; `accepted_links` (3) and `proposed_links` (0) remain separate and unchanged.

### Live Cucumber scenario (SCN-3205)

```text
cmd=unshare -rn env CTA_EGRESS_DENIED=1 \
  CTA_LOCAL_EMBEDDING_MODEL_DIR=$HOME/.local/share/cta/models/embeddinggemma-2-text-270m-onnx \
  CTA_LOCAL_EMBEDDING_WEIGHTS_DIGEST=sha256:b396bde0f7a85398c9c42d08a3c0b68d30952e91dcd408bfa327c727e86457a3 \
  CTA_BDD_PYTHON=$PWD/backend/.venv/bin/python CTA_UI_DISABLED=1 \
  npx cucumber-js --config cucumber.live.mjs
exit=0
1 scenario (1 passed)
14 steps (14 passed)
report=docs/reports/omp-closeout/evidence/AI-02-live-cucumber.ndjson
report_sha256=sha256:20ef80b260abd8bc26eecb1580775db5944960748acf8cf4cb12919aabb2af51
observations=docs/reports/omp-closeout/evidence/AI-02-live-observations.json
observations_sha256=sha256:93aa141f0d9bcf36573477d47e13e378e0b117ef955d78524039c665f5ea2c40
```

The live record retains:

* the observed weights digest and `onnxruntime 1.32.0`;
* the formatting version `ai02-code-query-v1/document-title-text-v1`;
* `external_egress=false` from the bridge's probe to `192.0.2.1:9`;
* `egress_denied_env=true`;
* the `/proc/self/ns/net` namespace identity;
* `top_k_rejected=true`, `binding_matches_fixture=true`, and the separate accepted/proposed thread
  arrays with `thread_equal=true`.

The bridge run's raw timing record is **load 3.605 s, index 10.891 s, query median 2.2253 s**
(`AI-02-live-observations.json`); it includes the API/thread checks and is not directly comparable
to the pytest measurement above. Both raw records are retained.

The observed weights digest equals the identified manifest digest. No non-loopback request
completed; the process tree ran in a network namespace with no external interface.

## Failure-mode evidence

|Case|Result|
|---|---|
|SCN-3202 remote endpoint|`400 invalid-request`; `network_attempts=[]`; detail says no connection was attempted|
|SCN-3203 absent weights|`503 retrieval-unavailable`; no download/fallback; baseline links/evidence/findings unchanged|
|SCN-3203 digest mismatch|`503 retrieval-unavailable`; “No download or remote fallback is attempted”|
|SCN-3203 runtime missing|`503 retrieval-unavailable`; no fallback|
|SCN-3206 non-finite embedding|`503 retrieval-unavailable`; no candidates; no mutation|
|SCN-3201 default|`fake` selected with no provider override; `onnxruntime` not imported; no socket attempt|

## Honest limitations

* Measurements are from one synthetic four-file code/test corpus on one 4-core CPU; they are not a
  retrieval-quality benchmark and do not generalize to other hardware or corpora. The corpus-build
  time varied across retained runs (5.94 s to 21.81 s); warm queries varied from 0.365 s to 0.664 s.
* The model is multimodal upstream; CTA loads the text encoder only and supplies empty modality
  tensors.
* The live test and live Cucumber scenario are opt-in. The default suite, CI jobs, and every
  non-live path do not install or import `onnxruntime`, `tokenizers`, or the weights.
* The model directory is provisioned by an explicit download (recorded in the manifest); no
  code path downloads weights.
