# Continuous Traceability Assurance (CTA)

Also called the **Gherkin Digital Thread**: a Gherkin-based digital thread connecting
requirements, acceptance criteria, source code, tests, Git revisions, and verification
evidence — then continuously reporting coverage gaps, confirmed failures, evidence that needs
reverification after a change, and unreviewed semantic link suggestions.

Nothing about normal development or testing requires a GPU, LLM, embedding service, vector
database, or network access. The whole project runs from committed fixture data. CocoIndex and
local EmbeddingGemma 2 inference are optional, explicit plugins; live model tests are opt-in.

## Status

**M0, M1, and the expanded M2 engineering gates are satisfied.** M0 was approved at `bca69cf`;
M1 was approved at `e1497cf`; expanded M2 was approved at review 7 and merged via PR #64
(`de4f37a`). The M3 slices AI-06, AI-07, AI-08, and AI-09 are independently approved and merged.

**M3 close-out is implemented locally but not yet accepted or merged.** AS-06 (#28), AS-07 (#29),
AI-03 (#32), and AI-02 (#31) have approved specifications, implementation, offline tests, and
canonical Cucumber execution in the working tree. Independent acceptance reviews, the M3 milestone
review, a PR, and hosted CI are still required. CI-01 (#36) and CI-02 (#37), the M4 automation
stories, have not started.

The current milestone state, evidence, and remaining gates are recorded in
[`docs/STATUS.md`](docs/STATUS.md). The close-out design decisions are in
[`docs/adr/0012-closeout-scope-decisions.md`](docs/adr/0012-closeout-scope-decisions.md).

## Quickstart

```bash
uv sync --project backend
uv run --project backend pytest backend/tests
uv run --project backend uvicorn app.main:app --reload   # http://127.0.0.1:8000/docs
```

That is the whole backend setup. No services, no models, no GPU. `uv sync` needs a package index
once; everything afterwards is offline.

For the dashboard:

```bash
npm ci --prefix frontend
npm run build --prefix frontend
npm test --prefix frontend
```

For the executable acceptance suite:

```bash
npm ci --prefix bdd
(cd bdd && npm run bdd)
node bdd/tools/step-resolution.mjs bdd/reports/cucumber-messages.ndjson
```

## What works today

| Capability | Endpoint / command |
| --- | --- |
| Artifact inventory and one artifact at a baseline | `GET /api/artifacts`, `GET /api/artifacts/{id}?baseline=…` |
| Digital thread: accepted links, proposals separate, evidence | `GET /api/threads/{id}?baseline=…` |
| Deterministic assurance findings over the ingested revision | `GET /api/findings?baseline=…`, `POST /api/assurance/evaluate` |
| Ingestion of the configured fixture repository at a revision | `POST /api/ingestion/run` |
| Discovery proposals from the default fixture provider | `POST /api/discovery` |
| Provider catalogue and typed provider failures | `GET /api/discovery/providers` |
| Capture a discovery candidate as a proposed link | `POST /api/link-proposals` |
| Append-only accept/reject decisions with operator, time, reason, and snapshot hashes | `POST /api/links/{link_id}/review` |
| Review workspace projection and audit history | `GET /api/workspace/threads/{id}`, `/api/workspace/proposals`, `/api/workspace/history` |
| Trusted-local-operator review configuration | `GET /api/review/config` |
| CTA-owned retrieval manifests and refresh planning | `POST /api/retrieval/refresh`, `GET /api/retrieval/manifests[/{baseline}]` |
| Snapshot-bound candidate combination | `POST /api/retrieval/combine` |
| Code retrieval proposals from lexical or CocoIndex-backed search | `POST /api/retrieval/code` |
| Evidence-grounded requirement answers over accepted links | `POST /api/answers` |
| Portable, read-only Gherkin repository indexing and queries | `python -m app.cli index/scenarios/…`; `/api/repositories/*` |
| Reproducible fixture Git history with `baseline-a` / `baseline-b` | `python tools/fixturectl.py all` |
| Offline backend tests, Cucumber acceptance, and the strict step gate | `pytest backend/tests`; `bdd/npm run bdd`; `node bdd/tools/step-resolution.mjs …` |

`POST /api/links/{link_id}/review` is implemented; it no longer returns the M0 `501` contract
response. Acceptance changes review state and the workspace projection only — it never changes
verification status, evidence, findings, baseline reads, or fixture bytes. The review journal is
application-owned, append-only, and must live outside the fixture/evaluated repository.

### Optional local inference (AI-02)

The default discovery provider is `fake`. To use the same-machine EmbeddingGemma 2 provider:

```bash
uv sync --project backend --extra local-embedding
export CTA_LOCAL_EMBEDDING=1
export CTA_LOCAL_EMBEDDING_MODEL_DIR="$HOME/.local/share/cta/models/embeddinggemma-2-text-270m-onnx"
uv run --project backend uvicorn app.main:app
```

The exact model, weights digests, Apache-2.0 licence, CPU runtime, hardware, formatting versions,
and measured limits are recorded in
[`docs/reports/omp-closeout/AI-02-MODEL-MANIFEST.md`](docs/reports/omp-closeout/AI-02-MODEL-MANIFEST.md).
Live evidence was captured under `unshare -rn`; see
[`AI-02-EVIDENCE.md`](docs/reports/omp-closeout/AI-02-EVIDENCE.md). A remote endpoint is refused
before any connection; missing weights/runtime and malformed embeddings are typed
`retrieval-unavailable` failures.

### Review mode (AS-06)

```bash
export CTA_REVIEW_OPERATOR=rv-ana
export CTA_REVIEW_JOURNAL="$PWD/.cta/review-journal.ndjson"
```

Review and workspace routes are loopback-only. The configured operator is server-assigned; an
unset operator disables review writes. See [`docs/stories/AS-06.md`](docs/stories/AS-06.md) for the
journal, snapshot, error-precedence, and restart contracts.

### CocoIndex (AI-06/AI-07)

CocoIndex Code remains an optional external code-search cache. Configure
`CTA_CCC_PROJECT_ROOT` and set `CTA_CCC_LIVE_OPT_IN=true`; the default app and every test/CI job
run without it. CocoIndex owns chunking/embeddings/index storage. CTA reports its internal index
identity and embedding counts as `not_available` where the MCP contract does not expose them.

## The demonstration

Given `REQ-001`, the dashboard shows its linked scenario, implementation, test, and
baseline-specific evidence. At `baseline-b`, `CODE-001` changed after the recorded pass, so CTA
reports `reverification_required` — not `verification_failed`. The separate failing execution of
`SCN-003` at `baseline-b` is a confirmed `verification_failed`. Discovery proposals remain
proposals until an explicit capture and a human accept/reject decision.

## Issue tracker

The GitHub tracker is the work-item source of record; `docs/traceability-issue-map.md` maps
roadmap IDs to issues. As of 2026-11-14:

| State | Issues |
| --- | --- |
| **Open — M3 close-out** | [#28](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/28) AS-06 review decisions · [#29](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/29) AS-07 provider honesty/provenance · [#31](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/31) AI-02 local EmbeddingGemma 2 · [#32](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/32) AI-03 snapshot/cache lifecycle |
| **Open — M4 automation** | [#36](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/36) CI-01 revision-triggered assurance · [#37](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/37) CI-02 finding-set diff |
| **Open — parent features** | [#13](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/13) F-07 Review · [#14](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/14) F-08 Retrieval · [#16](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/16) F-10 Automation |
| **Closed** | M0/M1/M2 stories and foundation features (`FT-01/02/03`, `SETUP-01`, `DT-01…06`, `AS-01…05`, `GT-01…03`, `PG-01`, `F-01…F-06`, `F-09`, `F-11`, `F-12`), plus the merged M3 slices `AI-01`, `AI-04`, `AI-05`, `AI-06`, `AI-07`, `AI-08`, `AI-09` |

[#33](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/33) is the closed duplicate of
the open AI-03 story; #32 is the current story. The M1 milestone record remains open with all six
of its issues closed; M0 and M2 are closed. Issue closure here records delivery, not merely file
creation or a green local test.

**What remains:** independent acceptance review and merge of #28/#29/#31/#32; the M3 milestone
review; CI-01/CI-02; the M4 milestone review; and closing the parent features once all children are
complete. Do not read the open close-out issues as unimplemented code: the engineering slice is
complete and locally verified; the hosted CI and acceptance/merge gate are not yet satisfied.

## Repository layout

```text
CONTINUOUS_TRACEABILITY_ROADMAP.md  plan, backlog, milestones (source of story numbers)
AGENTS.md                           conventions and invariants for contributors and agents
backend/app/domain/                 contracts: enums, models, envelopes, ports, review, retrieval
backend/app/{persistence,discovery,assurance,retrieval,api,ingestion}/  implementations behind those ports
backend/tests/                      offline test suite (including opt-in live tests)
frontend/                           React + TypeScript dashboard (review workspace, findings, candidates)
bdd/                                Cucumber-JS acceptance harness, bridge, and step definitions
docs/                               architecture, contracts, setup, ADRs, stories, reviews, status
fixtures/banking-demo/              synthetic engineering repository + hand-labeled oracle
fixtures/api-responses/             generated mock responses served by the API
tools/fixturectl.py                 builds the fixture history and generated responses
```

## Documentation

* [`docs/setup.md`](docs/setup.md) — setup, commands, offline guarantees, troubleshooting
* [`docs/architecture.md`](docs/architecture.md) — components, ports, request flows
* [`docs/domain-contracts.md`](docs/domain-contracts.md) — artifact identity, revisions, relations,
  review workspace, retrieval lifecycle, findings, error codes
* [`docs/api-contracts.md`](docs/api-contracts.md) — endpoint reference with examples
* [`docs/development-lifecycle.md`](docs/development-lifecycle.md) — the project's own traceability
  lifecycle
* [`docs/feature-inventory.md`](docs/feature-inventory.md) — every tracked feature, execution status,
  and declared exclusion reason
* [`docs/STATUS.md`](docs/STATUS.md) — milestone state, evidence, and next gates
* [`docs/adr/`](docs/adr/) — architecture decisions, including deferred decisions
* [`docs/reports/omp-closeout/`](docs/reports/omp-closeout/) — close-out refinement, AI-02 model
  manifest, evidence, and reviews
* [`CONTRIBUTING.md`](CONTRIBUTING.md) — tracker shape, commit/branch/PR conventions
* [`fixtures/banking-demo/README.md`](fixtures/banking-demo/README.md) — the fixture repository and
  its oracle
