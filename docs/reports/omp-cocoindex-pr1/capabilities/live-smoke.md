# Live CocoIndex Code smoke — sanitized evidence

**Date:** 2026-11-13T19:39:46Z (probe report `generated_at`; repair round 4)
**Scope:** AI-06 PR 1 — CocoIndex Code compatibility, integration contract, and live smoke.
**Outcome:** **RUN — pass** for the configured synthetic snapshot and local embedding runtime.
**Reports:** [`live-summary.json`](live-summary.json) (sanitized) and
[`live-run-manifest.json`](live-run-manifest.json) (raw-report digest, aliases, exits, index build).
The raw report, captured payload, daemon logs, and index stay outside Git.

## Configuration

| Item | Value |
| --- | --- |
| CTA checkout | `a674fb910bb31b866dd7417e45842cfa26a0b265` |
| Adapter hashes | `cocoindex.py` `sha256:7de622…58bc2`; `cocoindex_mcp.py` `sha256:0913d9…aec1e`; `probe_cocoindex.py` `sha256:b994f7…4f0af` |
| Snapshot | isolated `git worktree` of `fixtures/banking-demo` at `baseline-a` (`<snapshot>`) |
| Snapshot revision | `0f8607b29d1ccb423062d856835f5310c9f54aa3`; `snapshot_dirty=false` |
| CocoIndex Code | `0.2.43` (`ccc version`, exit 0) |
| MCP server | `cocoindex-code` `0.2.43`, protocol `2024-11-05` |
| Embedding | LiteLLM model `ollama/embeddinggemma-2:270m-q8_0-text`; Ollama tag `embeddinggemma-2:270m-q8_0-text`; 768 dimensions |
| Endpoint | `<output class: localhost>` via a process-local port-forward to the approved Service; no URL committed |
| State/runtime | isolated `<ccc-state>` / `<ccc-runtime>`; default `~/.cocoindex_code` refused |
| Index snapshot metadata | `sha256:59a34c…57c3e`, 9,535,488 bytes (external hash, **not** a server-reported index identity) |
| Project settings hash | `sha256:ce5c56…a2771` |

Only synthetic fixture content was indexed or searched. No CTA API key, repository secret, or
private source was sent. The shared user daemon was not used; the isolated daemon PID is recorded
in the manifest.

## Commands and outcomes

The exact invocation, environment aliases, timestamps, and raw-report/capture digests are in
[`live-run-manifest.json`](live-run-manifest.json). Summary:

```bash
# Index the isolated snapshot (isolated state; 2m31.9s cold)
cd <snapshot>
COCOINDEX_CODE_DIR=<ccc-state> COCOINDEX_CODE_RUNTIME_DIR=<ccc-runtime> ccc index
# exit 0: 12 files, 16 chunks (python 7, json 6, markdown 3)

# Capability probe (opt-in; synthetic query only)
CTA_CCC_PROJECT_ROOT=<snapshot> CTA_CCC_LIVE_OPT_IN=1 \
COCOINDEX_CODE_DIR=<ccc-state> COCOINDEX_CODE_RUNTIME_DIR=<ccc-runtime> \
  uv run --project backend python tools/probe_cocoindex.py --live \
    --query "withdraw whole dollar amounts" --limit 3 \
    --language python --path 'src/*' --timeout 180 --ollama-timeout 90 \
    --report <external>/capability-report-round5.json \
    --sanitized-report <external>/capability-sanitized-round5.json \
    --capture-response <external>/probe-capture-round5.json
# exit 0; overall=ok; all six steps ok

# Opt-in pytest integration check
CTA_CCC_LIVE_TESTS=1 ... uv run --project backend pytest \
  backend/tests/test_live_cocoindex_integration.py -q
# exit 0; 1 passed
```

| Step | Status | Latency |
| --- | --- | --- |
| `ccc version` | ok | 222.0 ms |
| `ccc status` | ok | 241.1 ms |
| `ccc doctor` | ok | 357.0 ms |
| MCP capabilities + structural `search` schema | ok | — |
| Ollama `/api/tags` + `/api/embed` | ok | 52.2 ms |
| Search + snapshot verification | ok | 886.4 ms (warm) |

## Observed search result

Query: `withdraw whole dollar amounts`; filters `languages=["python"]`, `paths=["src/*"]`,
`limit=3`, `refresh_index=false`.

| Rank | Path | Lines | Score | Content bytes |
| --- | --- | --- | --- | --- |
| 1 | `src/__init__.py` | 1–1 | 0.7128040949509113 | 34 |
| 2 | `src/transfers.py` | 1–29 | 0.704876378553962 | 990 |
| 3 | `src/accounts.py` | 1–10 | 0.6955020310656153 | 258 |

Every hit was verified against the snapshot: the path resolves inside the root, the line range
exists, and the content equals the file's lines after removing one trailing newline. The first hit
is a package docstring, not the semantically strongest file; this is a capability observation, not
a retrieval-quality claim. Ranking quality is AI-05 work.

## Lifecycle observation (review finding AI06-R1)

`ccc mcp` is not side-effect free: it schedules its own asynchronous index update on startup and
its client may start/restart a daemon. CTA therefore requires an isolated state/runtime pair and
refuses the default shared state. The probe records the daemon PID and index-file SHA-256 before
and after the session:

| Observation | Before | After |
| --- | --- | --- |
| Daemon PID | 1676339 | 1676339 |
| Index SHA-256 | `sha256:59a34c…57c3e` | `sha256:59a34c…57c3e` |
| Started by session | — | no |
| Restarted by session | — | no |
| Index changed by session | — | no (at the time of the after-snapshot) |

`refresh_index=false` suppresses only the tool's explicit refresh. The startup index task may
still run after the probe records the after-state; the report does not claim the index is
immutable or that the task finished. The `ccc doctor` step is now part of the overall pass/fail
calculation, and a zero-hit smoke is a failure.

## Capability observations

* The MCP `search` tool advertises `query` (string, required), `limit` (integer 1..100), `offset`
  (non-negative integer), `refresh_index` (boolean), and nullable string-array `languages`/`paths`.
  The adapter validates those types, bounds, required arguments, and array items on every session.
* The server does **not** expose an index revision, chunk hash, or project identity. The adapter
  reports `index_identity=null`; the index-file SHA-256 above is independently computed metadata.
* `ccc` include patterns cover code/text files; `.feature` is not in the default corpus. This smoke
  proves source-code search only.
* Cold embedding latency was 26–53 s in earlier calls; warm search was 0.91 s. The bounded default
  is 90 s with a 600 s hard cap; the probe used 180 s.
* The index build for 12 synthetic files took 2m31.9 s on a cold model.

## NOT RUN

* The default offline suite's live CocoIndex test is skipped (`NOT RUN`); only the explicitly
  opted-in invocation above ran. The skip is not a live pass.
* No `baseline-b` snapshot/index was built; cross-baseline isolation belongs to PR 2.
* No scenario/requirement semantic retrieval was attempted; CocoIndex Code does not establish it.
* No retrieval-quality metrics were computed; that is AI-05.
* No chat/generation or GraphRAG path exists in this slice.
* A production/hosted data-handling review was not performed; this smoke is synthetic only.
