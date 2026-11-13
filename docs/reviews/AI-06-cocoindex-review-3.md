# AI-06 PR 1 implementation review — submission 3 of 7

| Field | Value |
| --- | --- |
| Reviewer | Codex `gpt-6.1-sol`, reasoning effort `high`, read-only |
| Packet | [AI-06-cocoindex-review-prompt-3.md](AI-06-cocoindex-review-prompt-3.md), sha256 `86fb2d514699777b884e2804f2c9d7adb8a20e29edae925a416c53d672b0e05f` |
| Window | 2026-11-13T19:12:04Z → ~19:15:10Z (185.69 s) |
| Process exit | 0 |
| Verdict | **REQUEST_CHANGES** — R1 closed; R2/R5 open |

The verdict below is copied verbatim from the reviewer's final message; only absolute repository
paths are substituted with `<task_repo>`.

---

**REQUEST_CHANGES — AI-06 PR 1, submission 3 of 7.**

AI06-R1 is closed. **AI06-R2 and AI06-R5 remain open, both major.**

1. **AI06-R2 — Major: incompatible schema constraints still pass validation.**  
   At [cocoindex_mcp.py:703](<<task_repo>/backend/app/discovery/cocoindex_mcp.py:703>), validation checks selected keywords but ignores other assertions. Starting with the accepted schema, I independently reproduced acceptance of:
   
   - `offset.exclusiveMaximum=1`, excluding supported offsets ≥1.
   - `query.enum=["x"]`, excluding valid queries such as `"q"`.
   - `paths.maxItems=0` alongside the nullable `anyOf`, excluding every nonempty path-filter array.
   
   **Affected:** SCN-1005, incompatible schemas must produce `cocoindex-capability-error`.  
   **Smallest repair/evidence:** reject unsupported validation keywords conservatively or evaluate their compatibility, including constraints outside nullable branches. Add regressions proving these schemas fail before search while the reviewed schema remains accepted.

2. **AI06-R5 — Major: Python equality still lets malformed text hide behind structured content.**  
   At [cocoindex_mcp.py:912](<<task_repo>/backend/app/discovery/cocoindex_mcp.py:912>), dictionary equality treats `True` and `1` as equal. I reproduced successful hit returns with valid structured content alongside text containing either `success: 1` or `start_line: true`. Each text payload alone correctly raises `cocoindex-protocol-error`; the combined envelope succeeds.
   
   **Affected:** SCN-1004, wrong-field-type and whole-envelope rejection.  
   **Smallest repair/evidence:** validate every supplied payload independently before selecting one, and compare representations without masking invalid field types. Add both regressions, retaining matching-envelope and structured-only success cases.

**AI06-R1 — closed:** relative state/runtime paths are rejected before process start; resolved absolute paths reach the session environment and every probe subprocess. R3/R4/R6/R7/R8 remain closed.

The remaining nine scenarios are supported within the stated slice; SCN-1011 rests on retained live evidence, which I did not rerun. Offline defaults, untrusted-text handling, and proposal/accepted-link/evidence separation remain preserved.

Verification: **40 read-only tests passed**; all 14 submitted incompatible-schema rows were independently rejected. Submitted hashes matched, external evidence digests matched, sanitized-report derivation matched, and all three hits matched the pinned Git snapshot and recorded hashes. The proposed commit message passes the commit-reference validator. Full-suite, network-denial, lint, fixture, and live results were assessed from retained evidence.

No files were changed, dependencies installed, artifacts regenerated, live services invoked, commits created, or work delegated.