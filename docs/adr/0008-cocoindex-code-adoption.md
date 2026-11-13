# ADR 0008 — Adopt CocoIndex Code for semantic code search

**Status:** Accepted for the AI-06 PR 1 slice; independent review pending at the time of writing.
**Date:** 2026-11-13
**Owner:** A (semantic discovery), with the shared integration owner for settings and docs.

## Context

The RAG mission selects [CocoIndex Code](https://github.com/cocoindex-io/cocoindex-code) for
AST-aware semantic *code* search instead of building a CTA-owned source-code chunker, embedding
pipeline, and vector store. CTA must keep its authoritative artifact model, Gherkin/requirement
parsing, canonical IDs, typed accepted links, Git baselines, verification evidence, review
decisions, and assurance policy. The default application, tests, and CI must remain offline.

At this revision the only registered discovery provider is the fixture-backed `fake`;
`POST /api/discovery` returns `TraceCandidate` proposals and has no CocoIndex path. The optional
chat/embedding boundary from ADR 0007 exists but does not index code.

The installed implementation was inspected and exercised before this decision:

| Observation | Value |
| --- | --- |
| Package / executable | `cocoindex-code` 0.2.43 / `ccc` (pipx venv, Python 3.14) |
| Framework dependency | `cocoindex` 1.0.26 |
| License | Apache-2.0 (`License-Expression: Apache-2.0`, license files present) |
| Embedding backend | LiteLLM → Ollama `embeddinggemma-2:270m-q8_0-text` (768 dimensions) |
| MCP server identity | `cocoindex-code` 0.2.43, protocol `2024-11-05` |
| MCP tool | one `search(query, limit, offset, refresh_index, languages, paths)` tool |
| Search payload | `{success, results:[{file_path, language, content, start_line, end_line, score}], total_returned, offset, message}` |
| Index identity | **not exposed** by the MCP contract |
| Corpus | configured include patterns (code and text); `.feature` is not included by default |

Observed on an isolated worktree of `fixtures/banking-demo` at `baseline-a`
(`0f8607b29d1ccb423062d856835f5310c9f54aa3`): 12 files, 16 chunks, index build 2m32s on a cold
embedding model, warm search 0.9s (cold searches were 26–53s while the model loaded).

## Decision

### Adopt CocoIndex Code as an external search cache

CocoIndex Code owns semantic *code* chunking, incremental indexing, embeddings, and its
project-local SQLite vector store. CTA owns the engineering artifact model and every
authoritative fact. The CocoIndex index is a rebuildable cache, not a source of truth.

The adapter lives in `app.discovery.cocoindex` and exposes:

* `CocoIndexSearchRequest` — bounded query, limit 1..100, non-negative offset, explicit
  `refresh_index` (default **false**; it suppresses only the tool's explicit refresh, not the
  `ccc mcp` startup index), language filters, and relative POSIX path globs.
* `CocoIndexHit` — path, language, 1-based line range, content, and the score **as reported**.
* `CocoIndexSearchResult` — hits in reported order, reported totals, server identity, configured
  project root as caller-supplied context, and `index_identity=None` because the MCP contract does
  not expose one. It has no link, review, evidence, or assurance field.
* A typed error taxonomy: configuration, request, unavailable, timeout, protocol, query, and
  capability.

`app.discovery.cocoindex_mcp.StdioMcpTransport` starts one `ccc mcp` process per call in the
configured project root, performs the MCP initialize/tools handshake, issues one search, and reaps
the process group it started. `ccc mcp` is not side-effect free: it schedules its own asynchronous
index update on startup, and its client may start or restart a daemon. CTA therefore requires an
isolated `COCOINDEX_CODE_DIR`/`COCOINDEX_CODE_RUNTIME_DIR` pair; those effects are confined to that
pair and the configured disposable snapshot. The adapter refuses the default shared
`~/.cocoindex_code` state and never targets the shared daemon.

### Structured MCP, not CLI scraping

The adapter uses the MCP tool result (`content[0].text` JSON, or `structuredContent` when a future
version provides it). Human-formatted `ccc search` output is not parsed. The observed server name,
version, and `search` tool schema are validated structurally on every session: property types,
required arguments, supported `limit`/`offset` bounds, and nullable string-array filters. A
different version or incompatible schema is a capability error until it is reviewed here.

### Version pin and compatibility policy

The tested and accepted version is **0.2.43**, encoded in `SUPPORTED_SERVER_VERSIONS`. Any other
server version fails with `cocoindex-capability-error`. A version change requires a recorded
contract observation, fixture update, and review; it is never silently accepted.

### Project selection and isolation

The project root must be an explicit, existing directory containing
`.cocoindex_code/settings.yml`. The user home directory is rejected, and the adapter does not fall
back to an ancestor project. The subprocess receives an allow-listed environment (PATH, HOME,
locale, temporary/runtime directories, `COCOINDEX_CODE_DIR`, `COCOINDEX_CODE_RUNTIME_DIR`,
`OLLAMA_API_BASE`, and CA-bundle variables); CTA keys, `GITHUB_TOKEN`, and unrelated secrets are
dropped.

`COCOINDEX_CODE_DIR` (user settings/daemon state) and `COCOINDEX_CODE_RUNTIME_DIR` (socket, PID,
log) are **required** and must not resolve to the default `~/.cocoindex_code`. The state directory
must contain `global_settings.yml`; the project-local `.cocoindex_code` index directory is not a
valid substitute. This confines daemon starts/restarts and the `ccc mcp` background index to the
isolated pair and the configured snapshot. PR 2 must still use a distinct immutable worktree and
index per Git baseline; a shared index must never be retargeted and then described as representing
two historical revisions.

### Lifecycle effects we do not control

`ccc mcp` starts an asynchronous `client.index(project_root)` task before serving requests,
regardless of the `refresh_index` argument on the `search` tool call. CTA cannot disable that task
without forking the entry point. Consequences:

* `refresh_index=false` only suppresses the tool's explicit refresh; it does **not** make a session
  read-only with respect to the project index.
* Every session is treated as potentially index-mutating. Use a disposable snapshot/index, not a
  historical index whose immutability is being claimed.
* The capability probe records the daemon PID and index-file SHA-256 before and after a session and
  reports whether the daemon started/restarted or the index changed. It does not claim the
  background task finished or that the index is unchanged.
* A shared daemon is protected by refusing the default state path, not by trying to stop it.

### Bounds and failure semantics

* A total deadline covers process start, initialize, `tools/list`, and the search. Default 90s;
  hard cap 600s; the live probe used 180s.
* On timeout the adapter sends SIGTERM to the process group it created, waits, then SIGKILLs and
  reaps. Cleanup is bounded.
* Response lines and search payloads are capped (512 KiB), hit content is capped (256 KiB), and
  stderr is drained concurrently and retained only as a bounded tail. stderr never becomes
  protocol data.
* Malformed envelopes, mismatched ids, missing/non-text content, non-finite scores, inconsistent
  counts, and invalid paths/line ranges are rejected **whole**; a valid subset is never returned.
* `success=false` (even with partial results) is a query error with no hit list; an MCP
  `isError` flag or malformed content envelope is a protocol error with no hit list.
* A valid empty result is a success with no hits.

### Untrusted content

Indexed repository text stays data. A hit can carry instruction-like comments, but the result type
has no operation that creates a link, review decision, evidence record, policy change, citation, or
coverage claim. PR 2 must keep retrieved text out of instruction position when it constructs
candidates.

### Offline default and rollback

`FakeCandidateDiscovery` remains the only registered discovery provider. `Settings` defaults keep
CocoIndex disabled; live use requires `CTA_CCC_PROJECT_ROOT` and `CTA_CCC_LIVE_OPT_IN=true`.
Removing the adapter or the optional dependency returns the application to its previous behavior;
deleting the project-local `.cocoindex_code` directory discards only a rebuildable cache.

## Consequences

* CTA does not implement a source-code chunker, embedding pipeline, or vector store.
* `.feature` scenarios and requirements are outside the default CocoIndex corpus. Scenario-aware
  retrieval remains a separate future story; this ADR does not claim it.
* The MCP contract does not expose an index revision or chunk hash. The adapter reports
  `index_identity=None`; the capability probe records an external SHA-256 of the project-local
  index file as snapshot metadata, clearly separated from the server payload.
* The live smoke sends only synthetic fixture content to the configured Ollama endpoint. That
  endpoint is outside the executing machine in the mission configuration, so it does **not**
  satisfy AI-02's canonical "no request leaves the machine" criterion; AI-02 remains open.
* The default shared user-level daemon is never used: the adapter requires an isolated state and
  runtime. A daemon started under the isolated runtime may still inherit that runtime's launching
  environment; start it from a minimized environment if that matters.
* `ccc mcp` always schedules a background index update. Index immutability is not claimed for a
  session; use a disposable snapshot and treat the index as a rebuildable cache.
* A model or settings change invalidates index comparability. PR 2/PR 4 must record the model and
  index identity and rebuild rather than mixing results.

## Alternatives considered

* **Build a CTA-owned chunker + Sentence Transformers + Qdrant.** Rejected for this slice: it
  duplicates a maintained implementation, adds a long-lived service or index format, and consumes
  the slice on plumbing rather than traceability integration.
* **Parse `ccc search` CLI output.** Rejected: human formatting is not a stable structured
  contract; the MCP tool exposes typed fields.
* **Make CocoIndex a `CandidateDiscovery` provider immediately.** Rejected: PR 1 has no
  path/line/revision-to-artifact mapping, and a provider without that mapping would fabricate
  candidate identities. PR 2 owns the mapping and the additive API behavior.
* **Let `refresh_index` default to true.** Rejected: a search must not silently mutate/rebuild an
  index, especially on a historical snapshot; refresh is explicit.
* **Accept any `ccc` version.** Rejected: the response shape and tool schema are the contract;
  untested versions fail closed.
* **Trust the server's paths.** Rejected: returned paths are validated as normalized relative
  POSIX paths; the live probe additionally resolves them inside the snapshot and compares content.
* **Use the agent-side OMP plugin as the integration.** Rejected: agent ergonomics is not a CTA
  runtime adapter and produces no application contract or test evidence.

## Revisit when

* PR 2 maps hits to artifact IDs and needs a ranking/expansion policy or baseline-specific index
  lifecycle.
* A CocoIndex release changes the MCP tool schema, response fields, or adds index identity.
* Scenario/requirement semantic retrieval is proposed; it needs its own reviewed story and
  evaluation, not an assumption that code search covers `.feature` files.
* The embedding endpoint or model changes; the index must be rebuilt and the experiment record
  must name both.
* Production adoption is proposed: complete a dependency/license/security review and a data-handling
  decision for non-synthetic repositories.
