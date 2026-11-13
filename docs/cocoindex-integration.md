# CocoIndex Code integration guide (optional)

CocoIndex Code (`ccc`) is an optional, external semantic **code**-search cache. CTA uses it only
through `app.discovery.cocoindex` and its bounded MCP stdio transport. The default application,
tests, and CI never need it, a daemon, Docker, a network, a GPU, or a model download.

Do not confuse this integration with the agent-side OMP plugin/skill. The plugin helps a coding
agent navigate the repository; it is not a CTA runtime adapter and produces no application
evidence.

## Tested configuration

| Item | Value |
| --- | --- |
| CocoIndex Code | `0.2.43` (pinned; other versions fail with `cocoindex-capability-error`) |
| License | Apache-2.0 |
| MCP server | `ccc mcp`, stdio, protocol `2024-11-05` |
| Embedding model | Ollama `embeddinggemma-2:270m-q8_0-text` (768 dimensions) |
| Project index | `<project>/.cocoindex_code/target_sqlite.db` (rebuildable cache) |

The MCP `search` result exposes `file_path`, `language`, `content`, `start_line`, `end_line`, and
`score`. It does **not** expose an index revision, chunk hash, or project identity. CTA reports
`index_identity=None` and, for a probe, records an external SHA-256 of the index file as snapshot
metadata. Never present that hash as a server-reported index identity.

## Install

Install the pinned release outside the CTA dependency tree:

```bash
pipx install "cocoindex-code==0.2.43"
ccc version                 # 0.2.43
```

`ccc` is not a CTA package dependency. CI does not install it.

## Embedding settings

CocoIndex reads user-level settings from `~/.cocoindex_code/global_settings.yml` (or
`$COCOINDEX_CODE_DIR/global_settings.yml`). A working local configuration:

```yaml
embedding:
  provider: litellm
  model: ollama/embeddinggemma-2:270m-q8_0-text

envs:
  OLLAMA_API_BASE: http://localhost:11434
```

* Ollama's native base URL has **no** `/v1` suffix.
* The `ollama/` prefix belongs to CocoIndex's LiteLLM model string; the native Ollama API takes the
  bare tag `embeddinggemma-2:270m-q8_0-text`.
* Inside Kubernetes, an in-cluster Service such as
  `http://ollama-embeddings.ai.svc.cluster.local:11434` works only for a process running inside
  the cluster. A workstation needs a reachable endpoint or an explicit `kubectl port-forward`, and
  `cluster.local` DNS is not expected to resolve outside.
* Do not commit API keys, private endpoint addresses, or model credentials. Ollama has no API key
  by default.

A configured but unreachable endpoint is a failure/blocked integration, not a pass. A missing
configuration is `NOT RUN`.

## Initialize and index a snapshot

Run these inside the project root you intend to search. For a historical baseline, use a distinct
worktree and index (see [Snapshot isolation](#snapshot-isolation)).

```bash
cd /path/to/snapshot
ccc init --force             # writes .cocoindex_code/settings.yml
ccc doctor                   # settings, daemon, model, dimensions, project warnings
ccc index                    # create/update the project-local index
ccc status                   # chunks, files, languages, indexing state
```

`ccc doctor` and `ccc status` are bounded diagnostics in the CTA probe (30–45 s). They can block
while another index is running; a timeout is reported, not hidden.

A one-off MCP search can be checked before writing code:

```bash
printf '%s\n' \
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"manual","version":"0"}}}' \
  '{"jsonrpc":"2.0","method":"notifications/initialized"}' \
  '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"search","arguments":{"query":"withdraw whole dollar amounts","limit":3,"refresh_index":false,"languages":["python"],"paths":["src/*"]}}}' \
  | ccc mcp
```

The second newline-delimited object must be sent after the initialize response in a real client;
the snippet is only a framing illustration. Prefer `tools/probe_cocoindex.py`, which performs the
handshake and validates the response.

The MCP `search` tool defaults `refresh_index` to `true`; CTA's adapter defaults it to **false**.
That flag suppresses only the tool's explicit refresh. The `ccc mcp` entry point **always starts
its own asynchronous index update** on session startup, and its client may start or restart a
daemon. CTA cannot disable that behavior without forking the entry point, so every live session is
treated as potentially index-mutating. Use a disposable snapshot/index and an isolated state/runtime
pair; do not claim that a session leaves a historical index untouched.

## CTA configuration

| Variable | Default | Meaning |
| --- | --- | --- |
| `CTA_CCC_EXECUTABLE` | `ccc` | Executable name or absolute path. |
| `CTA_CCC_PROJECT_ROOT` | unset | Absolute snapshot/project root containing `.cocoindex_code/settings.yml`. The user home and uninitialized directories are rejected. |
| `CTA_CCC_LIVE_OPT_IN` | `false` | Explicit opt-in; required with the project root before the probe contacts anything. |
| `CTA_CCC_LIVE_TESTS` | `false` | Enables the opt-in live pytest check. |
| `CTA_DISCOVERY_PROVIDER` | `fake` | Unchanged in AI-06 PR 1; `cocoindex` is **not** a registered provider yet. |

`Settings` validates the configuration without starting a process or contacting an endpoint. Live
opt-in without a project root is a configuration error; a project root without
`.cocoindex_code/settings.yml` is rejected rather than silently searching an ancestor project.

`COCOINDEX_CODE_DIR` and `COCOINDEX_CODE_RUNTIME_DIR` are **required** for live use and are passed
to the child along with the other allow-listed variables. They must identify an isolated
settings/daemon state; the default `~/.cocoindex_code` and the project-local `.cocoindex_code`
index directory are rejected. `CTA_LLM_API_KEY`, `GITHUB_TOKEN`, and other unrelated secrets are
not inherited.

## Capability probe

No contact without `--live`:

```bash
uv run --project backend python tools/probe_cocoindex.py
```

Live synthetic smoke (the only supported live path in this slice):

```bash
export CTA_CCC_PROJECT_ROOT=/path/to/isolated/snapshot
export CTA_CCC_LIVE_OPT_IN=1
uv run --project backend python tools/probe_cocoindex.py --live \
  --query "withdraw whole dollar amounts" --limit 3 \
  --language python --path 'src/*' --timeout 180 \
  --report /tmp/cocoindex-report.json \
  --sanitized-report /tmp/cocoindex-sanitized.json
```

The raw report can contain local paths and endpoint values; write it **outside** the repository.
`--sanitized-report` writes a reduced record (paths replaced, endpoints removed) that is safe to
commit. The probe records `ccc` version, MCP server/tool schema, project index status, embedding
model/dimension, snapshot revision, index-file SHA-256, adapter hashes, latency, result fields, and
explicit missing capabilities. It verifies each returned hit against the snapshot: the path must
resolve inside the root, the line range must exist, and the content must equal the snapshot's lines
after removing one trailing newline.

Exit codes: `0` = pass or `NOT RUN`, `1` = a configured step failed, `2` = configuration error.

## Snapshot and daemon isolation

* One immutable worktree per Git baseline; one project-local index per worktree.
* Do not retarget a shared index and then claim it represents an older revision.
* Every live session requires an isolated state/runtime pair; the adapter **refuses** the default
  `~/.cocoindex_code` path. `ccc mcp` may start/restart a daemon and always schedules its own
  background index, so this is a safety requirement, not an optional test convenience:

```bash
export COCOINDEX_CODE_DIR=/tmp/cta-ccc/state/.cocoindex_code
export COCOINDEX_CODE_RUNTIME_DIR=/tmp/cta-ccc/runtime
```

  Create `$COCOINDEX_CODE_DIR/global_settings.yml` with the embedding configuration before the
  first index. The daemon started for that state is the one the probe owns. Do not point
  `COCOINDEX_CODE_DIR` at the project's `.cocoindex_code` index directory; the adapter rejects it.
* The probe records the daemon PID and index-file SHA-256 before and after a session, plus whether
  the daemon started/restarted or the index changed. It does not claim the background task finished.
* PR 2 establishes the baseline-to-worktree/index lifecycle; PR 1 proves one pinned snapshot only.

## Known limitations

1. `index_identity` is unavailable from the MCP contract. Do not invent a chunk-level revision.
2. `.feature` and requirement parsing are outside the default CocoIndex corpus. Scenario-aware
   retrieval is not delivered by this integration.
3. A live smoke is a capability observation, not retrieval quality. Recall/precision/MRR belong to
   AI-05 with independently labeled cases.
4. A model or settings change invalidates index comparability; rebuild and record the change.
5. The shared user-level daemon is never used; live use requires an isolated state/runtime. The
   isolated daemon may still inherit its launching environment, and `ccc mcp` always schedules a
   background index; do not treat a session as read-only.

## Verification

```bash
uv run --project backend pytest backend/tests/test_cocoindex_client.py -q
uv run --project backend pytest backend/tests -q          # live tests skip by default
```

The opt-in live test:

```bash
CTA_CCC_LIVE_TESTS=1 CTA_CCC_LIVE_OPT_IN=1 \
CTA_CCC_PROJECT_ROOT=/path/to/isolated/snapshot \
uv run --project backend pytest backend/tests/test_live_cocoindex_integration.py -q
```
