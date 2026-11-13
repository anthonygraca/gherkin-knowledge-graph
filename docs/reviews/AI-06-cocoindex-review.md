# AI-06 PR 1 implementation review — submission 1 of 7

| Field | Value |
| --- | --- |
| Reviewer | Codex `gpt-6.1-sol`, reasoning effort `high`, read-only |
| Packet | [AI-06-cocoindex-review-prompt.md](AI-06-cocoindex-review-prompt.md), sha256 `8d01f674d87e94372fba9127ccacbcfb45f23234b28efedef4060445a4138fe7` |
| Window | 2026-11-13T18:04:16Z → ~18:14:19Z (602.93 s) |
| Process exit | 0 |
| Verdict | **REQUEST_CHANGES** — 8 findings (`AI06-R1`…`R8`) |

The verdict below is copied verbatim from the reviewer's final message; only absolute repository
paths are substituted with `<task_repo>`.

---

**REQUEST_CHANGES — AI-06 PR 1, submission 1 of 7.**

All 15 submitted manifest hashes match. The authority separation and offline default are preserved. M1’s approved gate stands, and I accept the stated ordering disposition for this slice.

The following are confirmed defects or evidence gaps:

1. **AI06-R1 — Major: `ccc mcp` has unaccounted lifecycle effects.**  
   [cocoindex_mcp.py:370](<task_repo>/backend/app/discovery/cocoindex_mcp.py:370) launches an entry point that schedules background indexing, including during capability checks. `refresh_index=false` does not suppress that startup task. CocoIndex’s client can also start a detached daemon or stop/restart an existing incompatible daemon. These behaviors appear in both the installed package and upstream [0.2.43 CLI](https://raw.githubusercontent.com/cocoindex-io/cocoindex-code/v0.2.43/src/cocoindex_code/cli.py) and [client](https://raw.githubusercontent.com/cocoindex-io/cocoindex-code/v0.2.43/src/cocoindex_code/client.py).  
   **Affected:** SCN-1005’s shared-daemon protection, SCN-1009, SCN-1011 attribution, and the documented no-mutation claim.  
   **Repair:** control these effects explicitly, protect shared daemon state, and demonstrate that capability/search calls obey the chosen lifecycle policy. Correct the documentation and refresh affected live evidence.

2. **AI06-R2 — Major: incompatible search schemas pass validation.**  
   [cocoindex_mcp.py:498](<task_repo>/backend/app/discovery/cocoindex_mcp.py:498) checks property names and whether `query` is required. Read-only probes confirmed acceptance of an integer query schema, `limit.maximum=2`, integer-only paths, and an additional unknown required argument.  
   **Affected:** SCN-1005’s capability-error requirement.  
   **Repair:** validate the structural contract needed by the adapter—types, nullability, array items, supported bounds and required arguments—and reject incompatible schemas before search.

3. **AI06-R3 — Major: blocking writes escape the total deadline.**  
   [cocoindex_mcp.py:552](<task_repo>/backend/app/discovery/cocoindex_mcp.py:552) performs blocking `write`/`flush` without enforcing the deadline. With a 4 KiB stdin pipe and a server that stopped reading after handshake, a valid 2,000-character query remained blocked until my external watchdog interrupted it at one second; the configured timeout was 0.3 seconds.  
   **Affected:** SCN-1005.  
   **Repair:** make sending deadline-aware and verify timeout plus cleanup when the child stops consuming stdin.

4. **AI06-R4 — Major: cleanup can exceed its configured interval indefinitely.**  
   [cocoindex_mcp.py:388](<task_repo>/backend/app/discovery/cocoindex_mcp.py:388) escalates only while the immediate process remains alive. A descendant can survive SIGTERM and hold stderr open; closing that buffered stream then waits behind the capture thread’s blocking read. My controlled stub took **1.125 seconds** to clean up with `cleanup_timeout=0.05`, ending only when its descendant exited naturally.  
   **Affected:** SCN-1005.  
   **Repair:** bound the complete cleanup operation, including descendant handling and stream draining, and close session resources on handshake failures too.

5. **AI06-R5 — Major: malformed MCP content is accepted partially.**  
   [cocoindex_mcp.py:593](<task_repo>/backend/app/discovery/cocoindex_mcp.py:593) returns upon finding the first text payload. I confirmed that valid text followed by an image block or a non-object item succeeds. Non-text blocks before valid text are skipped. Additionally, `isError=true` raises `cocoindex-query-error`, although the normative SCN-1004 requires `cocoindex-protocol-error`.  
   **Affected:** SCN-1004’s whole-response rejection and error contract.  
   **Repair:** validate the complete content envelope before accepting its payload, and align error handling and tests with the frozen criteria.

6. **AI06-R6 — Major: failed probe steps can produce a passing outcome.**  
   [probe_cocoindex.py:425](<task_repo>/tools/probe_cocoindex.py:425) excludes `ccc_status` and `ccc_doctor` from overall success calculation. Controlled probes returned `overall="ok"` with either step explicitly failed. A requested smoke search returning zero hits also receives an “ok” search status.  
   **Affected:** SCN-1010 and SCN-1011.  
   **Repair:** propagate every executed step’s failure to the overall outcome; require at least one snapshot-verified hit for the smoke acceptance path. Preserve empty-result success for ordinary adapter searches.

7. **AI06-R7 — Medium: required live evidence metadata is incomplete.**  
   The retained report lacks the required **raw report digest**. The [live invocation record](<task_repo>/docs/reports/omp-cocoindex-pr1/capabilities/live-smoke.md:30) uses ellipses and placeholders and points to an unspecified external run log.  
   **Affected:** SCN-1011 and lifecycle execution traceability.  
   **Repair:** retain a run manifest identifying the raw report by SHA-256, complete invocation/configuration using explicit sanitized path aliases, and indexing capture/exit. The raw report may remain outside Git.

8. **AI06-R8 — Low: the proposed commit body fails commitlint.**  
   Checking the exact proposed message returned: `issue #14 is not a story/task in docs/traceability-issue-map.md`. Feature-only references are excluded by the authoritative convention.  
   **Affected:** commit-traceability definition of done.  
   **Repair:** remove `#14` from the parsed `Refs` line, retain its parent relationship in ordinary prose, and validate the complete message before committing.

Independent verification: **38 selected read-only tests passed**. I also verified all three captured hits against the clean pinned snapshot, including their content/file hashes and settings hash. The retained summary matches the external sanitized capture, and external live exit records report success. Full-suite, network-denial, lint and fixture checks were assessed from retained captures; I did not rerun live services.

No files were edited, dependencies installed, fixtures regenerated, commits created, or work delegated.