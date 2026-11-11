# ADR 0001 — Monorepo layout and Python packaging

**Status:** Accepted · 2026-11-10

## Context

`CONTINUOUS_TRACEABILITY_ROADMAP.md` §8 proposes a repository structure and leaves one explicit
choice open: a root `pyproject.toml` or `backend/pyproject.toml`. Three workstreams (A discovery,
B digital thread, C assurance/UI) must develop in parallel without colliding, and everything must
run offline with a single documented command.

## Decision

* One monorepo. No separate service repositories: logical boundaries do not require separate
  deployables at this stage.
* One Python distribution, `cta-backend`, at `backend/pyproject.toml`, using a flat package layout
  `backend/app/…` (matching the roadmap's `backend/app/{api,domain,ingestion,assurance,discovery,persistence}`).
* `backend/uv.lock` is committed; CI installs with `--frozen`.
* Repository-level tooling (`tools/fixturectl.py`, tests) runs through the backend environment:
  `uv run --project backend …`. `uv sync` installs the package in editable mode, so `app.*` is
  importable from the repository root.
* `fixtures/`, `tools/`, `docs/`, `AGENTS.md` live at the repository root. `frontend/` is created
  with C-PR1, not scaffolded empty.

## Consequences

* One install command; tests need no path hacks except the tools directory added by `conftest.py`
  so tests exercise the same generator the CLI uses.
* pytest's rootdir is `backend/`, whose `testpaths = ["tests"]` keeps fixture content from being
  collected accidentally.
* A root-level Python project is deliberately avoided: it would mix frontend and backend tooling
  and give two places to specify dependencies.

## Alternatives considered

* `backend/src/app/` — more conventional packaging, but diverges from the roadmap's named layout
  and buys nothing for an application, not a library.
* Separate repositories per workstream — premature coordination cost; the integration overhead
  exceeds the isolation benefit at this size.
* Root `pyproject.toml` — rejected once the frontend arrives; two ecosystems in one manifest is
  avoidable complexity.

## Revisit when

A second deployable appears (for example M4's optional shared model host), or the frontend needs
its own CI job with different caching.
