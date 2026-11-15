# Close-out evidence index

Captured on 2026-11-14 from the cumulative close-out working tree based on `827e487`.
Every file here is a capture, not a regenerated summary; the corresponding command is recorded.

| File | Content | Command / source |
|---|---|---|
| `final-backend.log` | Full offline backend suite | `uv run --project backend pytest backend/tests -q` |
| `final-ruff.log` | Lint | `uv run --project backend ruff check .` |
| `final-format.log` | Format check | `uv run --project backend ruff format --check .` |
| `final-fixture.log` | Fixture reproducibility | `uv run --project backend python tools/fixturectl.py verify` |
| `final-diffcheck.log` | Whitespace check | `git diff --check` |
| `final-cucumber.log` | Full Cucumber acceptance summary | `cd bdd && npm run bdd` (captured to this file) |
| `final-cucumber.ndjson` | Cucumber Messages execution report | copied from `bdd/reports/cucumber-messages.ndjson` after the run |
| `final-step-resolution.log` | Strict step-resolution gate | `cd bdd && node tools/step-resolution.mjs ../docs/reports/omp-closeout/evidence/final-cucumber.ndjson` |
| `gt02-recheck.log` / `gt02-recheck.ndjson` | Targeted GT-02 recheck against the regenerated inventory | `cd bdd && npx cucumber-js --tags @GT-02` |
| `final-cucumber-attempt1-failed.log` / `.ndjson` | Preserved first attempt; the GT-02 report-path assertion failed after the inventory moved to the close-out report | `cd bdd && npm run bdd` (attempt 1) |
| `final-frontend-build.log` | Dashboard production build | `cd frontend && npm run build` |
| `final-frontend-test.log` | Dashboard component tests | `cd frontend && npm test -- --run` |
| `final-run-hashes.txt` | Hashes of the final report and regenerated inventory | `sha256sum …` |
| `AI-02-live-pytest.log` | Real local-model pytest under egress denial | `unshare -rn env CTA_LOCAL_EMBEDDING_LIVE_TESTS=1 … pytest backend/tests/test_local_embedding_live.py -q -s` |
| `AI-02-live-measurement.jsonl` | Extracted `LIVE_MEASUREMENT` record | `grep -o 'LIVE_MEASUREMENT .*' AI-02-live-pytest.log` |
| `AI-02-live-cucumber-summary.txt` | SCN-3205 live scenario summary | `unshare -rn env CTA_EGRESS_DENIED=1 … npx cucumber-js --config cucumber.live.mjs` |
| `AI-02-live-cucumber.ndjson` | SCN-3205 Cucumber Messages | copied from `bdd/reports/cucumber-live-messages.ndjson` |
| `AI-02-live-observations.json` | Retained live bridge record: baseline, weights/runtime/formatting, egress probe, namespace, candidate provenance, empty-result provenance, and shared-case results | written by the bridge during the live scenario |
| `AI-02-live-cucumber-summary.txt` | Summary | captured stdout/stderr |
| `final-manifest.sha256` | SHA-256 of the reviewed inputs and evidence | `sha256sum …` |

The model manifest and failure-mode evidence are
[`AI-02-MODEL-MANIFEST.md`](../AI-02-MODEL-MANIFEST.md) and
[`AI-02-EVIDENCE.md`](../AI-02-EVIDENCE.md). The feature inventory generated from the final
Cucumber report is [`docs/feature-inventory.md`](../../../feature-inventory.md) and
[`docs/feature-inventory.json`](../../../feature-inventory.json).

## Reproduce

```bash
uv sync --project backend
uv run --project backend pytest backend/tests -q
uv run --project backend ruff check .
uv run --project backend ruff format --check .
uv run --project backend python tools/fixturectl.py verify
git diff --check
cd bdd && npm ci && npm run bdd
node tools/step-resolution.mjs reports/cucumber-messages.ndjson
```

The local-model live checks additionally require the provisioned weights and the optional extra;
see the model manifest. They are not part of the default suite or CI.
