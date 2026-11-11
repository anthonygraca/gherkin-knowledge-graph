# Continuous Traceability Assurance (CTA)

Also called the **Gherkin Digital Thread**: a Gherkin-based digital thread connecting
requirements, acceptance criteria, source code, tests, Git revisions, and verification
evidence — then continuously reporting coverage gaps, confirmed failures, evidence that needs
reverification after a change, and unreviewed semantic link suggestions.

Nothing about normal development or testing requires a GPU, LLM, embedding service, vector
database, or network access. The whole project runs from committed fixture data.

**Status: Milestone M0 complete** (contract + fixture foundation). See `docs/STATUS.md` for
current state and the next three tasks.

## Quickstart

```bash
uv sync --project backend
uv run --project backend pytest backend/tests
uv run --project backend uvicorn app.main:app --reload   # http://127.0.0.1:8000/docs
```

That is the whole setup. No services, no models, no GPU. `uv sync` needs a package index once;
everything afterwards is offline.

## What works today (M0)

| Capability | Endpoint / command |
| --- | --- |
| One artifact at one baseline | `GET /api/artifacts/REQ-001?baseline=baseline-a` |
| Digital thread with accepted links, proposals kept separate, and evidence | `GET /api/threads/REQ-001?baseline=baseline-b` |
| Sample assurance findings for a baseline | `GET /api/findings?baseline=baseline-b` |
| Candidate link proposals (fixture provider; never auto-accepted) | `POST /api/discovery` |
| Reproducible fixture Git history with tags `baseline-a` / `baseline-b` | `tools/fixturectl.py build` |
| Offline contract, oracle, and API tests | `pytest backend/tests` |

The endpoints `POST /api/ingestion/run`, `POST /api/links/{link_id}/review`, and
`POST /api/assurance/evaluate` exist as **frozen contracts** and answer `501` with the owning
story and milestone. They are not silently stubbed, and no rule engine runs yet: `GET
/api/findings` replays reviewed sample findings generated from the hand-labeled oracle.

## The demonstration the project is aiming at

Given `REQ-001`, show its linked scenario, implementation, test, and baseline-specific evidence;
change the implementation at a second Git baseline; then report `reverification_required`
without ever claiming the requirement failed. The fixture already encodes both properties —
`REQ-001` is healthy at `baseline-a` and needs reverification at `baseline-b`, while the
separate failing test of `SCN-003` is a *confirmed failure* at that baseline.

## Repository layout

```text
CONTINUOUS_TRACEABILITY_ROADMAP.md  plan, backlog, milestones (source of story numbers)
AGENTS.md                           conventions and invariants for contributors and agents
backend/app/domain/                 contracts: enums, models, envelopes, ports, oracle schemas
backend/app/{persistence,discovery,assurance,api}/  implementations behind those ports
backend/tests/                      offline test suite
docs/                               architecture, contracts, setup, ADRs, stories, status
fixtures/banking-demo/              synthetic engineering repository + hand-labeled oracle
fixtures/api-responses/             generated mock responses served by the API
tools/fixturectl.py                 builds the fixture history and generated responses
```

## Documentation

* `docs/setup.md` — setup, commands, offline guarantees, troubleshooting
* `docs/architecture.md` — components, ports, request flows, what is real vs mock
* `docs/domain-contracts.md` — artifact identity, revisions, relations, findings, error codes
* `docs/api-contracts.md` — endpoint reference with request/response examples
* `docs/stories/M0-foundation.md` — M0 acceptance criteria and follow-on assignments
* `docs/adr/` — architecture decision records, including deferred decisions
* `docs/STATUS.md` — milestone state, tests executed, next tasks
* `docs/reviews/M0-review-prompt.md` — prompt for an independent review of this milestone
* `fixtures/banking-demo/README.md` — the fixture repository and its oracle
