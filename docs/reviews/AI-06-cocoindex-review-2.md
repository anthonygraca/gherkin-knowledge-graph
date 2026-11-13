# AI-06 PR 1 implementation review — submission 2 of 7

| Field | Value |
| --- | --- |
| Reviewer | Codex `gpt-6.1-sol`, reasoning effort `high`, read-only |
| Packet | [AI-06-cocoindex-review-prompt-2.md](AI-06-cocoindex-review-prompt-2.md), sha256 `01350df6229b298c81a32af3c91e50773ddb780f55d6365c7de5724f086e0ec2` |
| Window | 2026-11-13T18:52:57Z → ~18:56:46Z (228.91 s) |
| Process exit | 0 |
| Verdict | **REQUEST_CHANGES** — R1/R2/R5 open; R3/R4/R6/R7/R8 closed |

The verdict below is copied verbatim from the reviewer's final message; only absolute repository
paths are substituted with `<task_repo>`.

---

**REQUEST_CHANGES — AI-06 PR 1, submission 2 of 7.**

Three prior major findings remain open:

1. **AI06-R1 — Major: isolation validation and subprocess path resolution disagree.**  
   [cocoindex_mcp.py:177](<<task_repo>/backend/app/discovery/cocoindex_mcp.py:177>) resolves state/runtime paths against the caller’s working directory but passes their original strings to a child running in the snapshot directory. I confirmed that the constructor accepts runtime `../../..<home>/.cocoindex_code`: validation considers it isolated, while the configured snapshot resolves it to the shared default runtime. Installed CocoIndex uses that raw relative path. No CocoIndex process was started during this check.  
   **Affected:** SCN-1005 shared-daemon protection; SCN-1006 isolation.  
   **Smallest repair:** reject relative paths or pass validated absolute paths consistently to every subprocess. Add a regression with different caller and snapshot directories proving the child cannot resolve its runtime to shared state.

2. **AI06-R2 — Major: incompatible schemas still pass validation.**  
   [cocoindex_mcp.py:626](<<task_repo>/backend/app/discovery/cocoindex_mcp.py:626>) accepts non-nullable string-array filters, although search sends `null` for omitted filters. It also accepts `offset.maximum=0` and `query.maxLength=1`, which exclude valid adapter requests. I reproduced all three acceptances.  
   **Affected:** SCN-1005 capability-error contract.  
   **Smallest repair:** check nullability and reject additional constraints that exclude supported request values. Demonstrate rejection before search while retaining acceptance of the reviewed real schema.

3. **AI06-R5 — Major: structured content can mask malformed or contradictory text content.**  
   [cocoindex_mcp.py:813](<<task_repo>/backend/app/discovery/cocoindex_mcp.py:813>) checks that text parses as an object, then prefers `structuredContent` without checking agreement. I reproduced successful hit returns with valid structured content alongside text containing an invalid absolute-path hit or `success=false`. Explicit `content:null` also succeeds.  
   **Affected:** SCN-1004 whole-envelope rejection.  
   **Smallest repair:** distinguish absent fields from explicit null, validate every supplied payload representation, and reject conflicting representations. Add regression cases for these envelopes.

The other prior findings are **closed for this slice**:

| Finding | Disposition |
|---|---|
| AI06-R3 | Deadline-aware writes implemented; independent pipe-only check timed out in **0.205 s** and reaped the child. |
| AI06-R4 | Original descendant/stderr hang addressed by saved-group signalling and stoppable capture; retained regression evidence inspected. |
| AI06-R6 | Failed-step propagation and zero-hit smoke failure repaired. |
| AI06-R7 | Manifest metadata complete; external artifact digests and retained copies independently matched. |
| AI06-R8 | Exact proposed commit message independently passes commitlint. |

All 15 submitted hashes and both historical review-packet hashes match. **40 read-only tests passed.** I independently verified the pinned snapshot, settings hash, all three hit/file hashes, and sanitized-report derivation. Full-suite, network-denial, lint, fixture, and live execution results were assessed from retained evidence.

Offline defaults, untrusted-text handling, and proposal/accepted-link/evidence separation remain preserved. The three open findings prevent acceptance of all 11 scenarios.

No files were edited, dependencies installed, fixtures regenerated, live services invoked, commits created, or work delegated.