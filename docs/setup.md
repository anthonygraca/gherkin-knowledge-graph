# Setup

## Prerequisites

* Python 3.11 or newer (3.12 is what CI uses)
* [uv](https://docs.astral.sh/uv/) for dependency and environment management
* `git` 2.29 or newer (fixture generation creates real repositories, tags, and pins the object format)

Not required: Docker, a GPU, a model server, a database server, network access during tests.
The first `uv sync` downloads dependencies from a package index; everything after that runs
offline.

## Install and run

```bash
uv sync --project backend                                   # create backend/.venv, install the app + dev tools
uv run --project backend pytest backend/tests                # offline test suite (no network, no AI)
uv run --project backend uvicorn app.main:app --reload       # dev server, OpenAPI at /docs
```

`uv sync` installs `cta-backend` in editable mode, so `app.*` is importable from the repository
root — that is how `tools/fixturectl.py` and the tests import the contracts.

## Fixture commands

```bash
uv run --project backend python tools/fixturectl.py build         # nested fixture Git repo + expected/baselines.json
uv run --project backend python tools/fixturectl.py materialize    # fixtures/api-responses/*
uv run --project backend python tools/fixturectl.py all            # both
uv run --project backend python tools/fixturectl.py verify         # build+materialize in a temp dir, diff, exit 1 on drift
```

`verify` is the drift guard: it proves the committed generated files are exactly what the
generator produces now. CI runs it. If it fails, regenerate with `all` and commit the result
with your fixture edit.

## Quality gates

```bash
uv run --project backend ruff check .
uv run --project backend ruff format --check .
```

## Typical workflows

**Change a requirement, scenario, or fixture source.** Edit files under
`fixtures/banking-demo/tree/` (or `changes/`), run `fixturectl.py all`, update the hand-labeled
oracle if the expectation changed, then `pytest backend/tests`. Commit the fixture edit and the
regenerated files together.

**Add a fixture baseline.** Add a commit entry to `fixtures/banking-demo/history.json` with an
overlay directory, tag it, add `expected/baseline-<name>.json`, and extend the tests. Never
depend on the history of the repository that contains the fixture.

**Add a discovery provider (A).** Implement `app.domain.ports.CandidateDiscovery`, register it
in `app/discovery/registry.py`, and keep the fixture provider passing the same contract tests.
Providers must not write links or evidence.

**Add an assurance rule (C).** Add the rule id and finding type to `app/domain/enums.py` and the
policy tables in `app/domain/policy.py`, label the expected finding in
`fixtures/banking-demo/expected/baseline-*.json`, and implement the rule against
`ArtifactRepository`. Update `docs/domain-contracts.md`. The oracle tests then hold the
implementation to the label.

## Troubleshooting

| Symptom | Cause and fix |
| --- | --- |
| `Fixture file '…/snapshot.json' is missing` | Generated fixtures are absent (fresh clone without them) — run `fixturectl.py all`. |
| Drift test fails listing generated files | Fixture inputs changed without regeneration — run `fixturectl.py all` and commit the result. |
| `AssertionError: Query default value cannot be set in Annotated` | FastAPI requires parameter defaults outside `Annotated`; set the default after the annotation. |
| Tests import `app` but module not found | Run through `uv run --project backend …` so the editable install is used. |
| `git` not found during fixture tests | Install git; the fixture history is real, it is not simulated. |
