# Fixtures

Everything a developer needs to work without a GPU, model, database, or network lives here.

| Path | Provenance | Purpose |
| --- | --- | --- |
| `banking-demo/` | hand-written + generated | The synthetic engineering repository and its labeled oracle. See `banking-demo/README.md`. |
| `banking-demo/tree/`, `banking-demo/changes/` | hand-written | Source content replayed into the nested fixture Git history. |
| `banking-demo/expected/baseline-*.json` | hand-labeled | The findings oracle: what assurance must report at each baseline, including explicit negative expectations. |
| `banking-demo/expected/candidate-links.json` | hand-labeled | Discovery index for the fake provider plus positive/negative evaluation labels (AI-05). |
| `banking-demo/expected/baselines.json` | **generated** | Reproducibility manifest: commit SHAs per fixture commit and tag. |
| `banking-demo/.build/repo/` | **generated**, git-ignored | The nested Git repository used for git-level checks. |
| `api-responses/` | **generated** | Mock responses the API serves and clients can replay. See `api-responses/README.md`. |

## Rules

1. **Never hand-edit generated files.** `expected/baselines.json` and everything under
   `api-responses/` come from `tools/fixturectl.py`.
2. **Never derive expectations from output.** Oracle values are hand-written and reviewed; model
   output and the code under test are not sources of truth.
3. **Never depend on the outer repository's history.** The fixture creates its own commits with
   fixed identity, dates, and messages; `.build/repo` is ignored by the outer repository.
4. **Generated files are committed** so tests and the API work on a fresh clone, and
   `fixturectl.py verify` (plus `backend/tests/test_fixture_drift.py`) fails if they drift.

## Regenerate

```bash
uv run --project backend python tools/fixturectl.py all
uv run --project backend python tools/fixturectl.py verify
uv run --project backend pytest backend/tests
```

Adding a baseline or changing the oracle is a contract change: update the docs and the tests in the
same commit, and use the repository's commit-message trailers (`Story:`, `Feature:`).
