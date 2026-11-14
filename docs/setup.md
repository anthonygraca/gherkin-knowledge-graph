# Setup

## Prerequisites

* Python 3.11 or newer (3.12 is what CI uses)
* [uv](https://docs.astral.sh/uv/) for dependency and environment management
* `git` 2.29 or newer (fixture generation creates real repositories, tags, and pins the object format)
* Node.js 22 and npm (frontend build and component tests only)

Not required: Docker, a GPU, a model server, a database server, network access during tests.
The first `uv sync` downloads dependencies from a package index; everything after that runs
offline. `httpx` is installed as a runtime dependency for the optional AI adapters; fake mode
does not import the transport.

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

## Frontend

Dependencies install from the registry once; build and tests run offline.

```bash
cd frontend
npm ci            # install the locked dependency tree
npm run build     # TypeScript build + Vite bundle
npm test          # Vitest component tests against committed fixture responses
npm run dev       # dashboard at http://127.0.0.1:5173
```

Start the backend first (`uv run --project backend uvicorn app.main:app --port 8000`) with built
fixtures. Vite proxies `/health` and `/api` to the backend. The dashboard shows the reviewed
fixture findings and the assembled thread for the selected baseline; it needs no model or external
service.

## Optional AI providers (offline by default)

The application never contacts a model endpoint by default. The optional providers are configured
from the process environment only; do not add a `.env` file or commit a key.

```bash
# Default: deterministic fake providers; no network, no model, no vector index.
export CTA_AI_MODE=fake

# Optional live configuration. Base URLs are the OpenAI-compatible API root (include /v1).
export CTA_AI_MODE=live
export CTA_LLM_BASE_URL="http://your-endpoint:8000/v1"
export CTA_LLM_MODEL="your-chat-model"
# export CTA_LLM_API_KEY="..."          # optional, process environment only

export CTA_EMBED_BASE_URL="http://your-embedding-endpoint:11434/v1"
export CTA_EMBED_MODEL="your-embedding-model"
# export CTA_EMBED_API_KEY="..."        # optional, process environment only

export CTA_VECTOR_BACKEND=memory        # validated in PR 1; the index arrives in PR 2
```

Inspect the configuration without contacting anything:

```bash
uv run --project backend python tools/probe_ai_capabilities.py
```

Probe the endpoint explicitly with synthetic canary text only:

```bash
uv run --project backend python tools/probe_ai_capabilities.py --live \
  --report /tmp/cta-ai-capabilities.json
```

A live report may contain local endpoint details; write it outside the repository. The CLI refuses
a repository path unless `--allow-repo-report` is explicit, and even then the content is sanitized.
The probe never sends repository artifacts, fixture content, or user data. Sending those to a
hosted endpoint requires a separate owner-approved data-handling configuration.

The live integration test is opt-in and skips by default:

```bash
CTA_AI_LIVE_TESTS=1 CTA_AI_MODE=live \
  uv run --project backend pytest backend/tests/test_live_provider_integration.py -q
```

If the configuration is absent, the live path is `NOT RUN`, not passed. The adapters use explicit
timeouts, bounded retries (429/5xx/timeouts only, honoring a capped `Retry-After`), and sanitized
error types. They cannot accept links, write evidence, or change assurance policy.

## Optional CocoIndex Code code search (AI-06)

CocoIndex Code is a separate, optional external search cache. It is not a CTA dependency, not a
registered discovery provider in AI-06 PR 1, and not required by tests or CI. A live probe needs a
pinned `ccc` executable, an initialized project snapshot, an embedding runtime, and explicit opt-in:

```bash
export CTA_CCC_PROJECT_ROOT=/path/to/isolated/snapshot
export CTA_CCC_LIVE_OPT_IN=1
uv run --project backend python tools/probe_cocoindex.py --live \
  --query "withdraw whole dollar amounts" --limit 3 --path 'src/*' \
  --report /tmp/cocoindex-report.json
```

Without `--live` the probe contacts nothing. Read
[CocoIndex integration](cocoindex-integration.md) for installation, global settings, snapshot
isolation, MCP framing, sanitized reports, and the "index identity is unavailable" limitation.
The injected hits are non-authoritative: they cannot create links, review decisions, or evidence.

## Executable acceptance suite (Cucumber-JS)

One-time install (Node 22 and the backend environment are already required):

```bash
npm ci --prefix bdd
```

Run CTA's own reviewed acceptance specifications (`docs/stories/*.feature`) and the strict
step-resolution gate:

```bash
(cd frontend && npm ci && npm run build)   # the browser scenarios load the built dashboard
(cd bdd && npm run bdd)
node bdd/tools/step-resolution.mjs bdd/reports/cucumber-messages.ndjson
```

The browser scenarios start an isolated `uvicorn` process with the built fixture repository and a
small static/proxy server, then drive the real dashboard with `playwright-core`. They require a
Chromium/Chrome executable; the harness looks in the usual system locations and honours
`CTA_CHROME_PATH`. No browser download is performed. Set `CTA_UI_DISABLED=1` only to skip the
browser scenarios deliberately (they are then reported as not executed, not as passing).

The gate fails on an undefined, ambiguous, or pending step and on any scenario that never started,
even when Cucumber's own exit code is zero. Two deliberately broken probe suites and one failing
probe are under `bdd/probes/`; GT-01 executes them to prove the gate works.

Exclusions are tag-based and recorded in `docs/feature-inventory.json`: `@FT-03` (process criteria
verified by inspection), `@AI-06` (M3 slice), `@superseded-by-AS-01` (M0 501 contract implemented in
M1), `@ui-component` (dashboard rendering verified by Vitest plus a recorded browser demonstration),
and `@migration-pending` (SETUP-01, verified by mapped pytest checks). No excluded feature is counted
as executed.

## Portable repository indexing (read-only)

Point CTA at any local Git repository; it reads the pinned commit, never the working tree, writes
nothing, and runs no hooks or test commands:

```bash
uv run --project backend python -m app.cli index /path/to/repo --repo-id my-repo --ref HEAD
uv run --project backend python -m app.cli scenarios /path/to/repo --repo-id my-repo --ref HEAD
uv run --project backend python -m app.cli steps /path/to/repo --repo-id my-repo --ref HEAD --scenario '<key>'
```

When a Cucumber Messages NDJSON report already exists, import it against the exact tested commit.
The import additionally requires a provenance sidecar (JSON with `tested_commit` and optionally
`repository_id`) because a messages stream alone cannot say which revision its definitions and
implementation belonged to; an import without it is refused:

```bash
cat > report.meta.json <<'JSON'
{"repository_id": "my-repo", "tested_commit": "<sha>"}
JSON
uv run --project backend python -m app.cli definitions /path/to/repo --repo-id my-repo --ref <sha> \
  --report report.ndjson --metadata report.meta.json --tested-commit <sha>
```

Without a report, step resolution answers `not_available` ("unknown, not undefined"). The same
surface is available over HTTP; see `docs/api-contracts.md`.

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
