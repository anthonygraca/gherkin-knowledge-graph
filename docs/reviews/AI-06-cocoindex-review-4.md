# AI-06 PR 1 implementation review — submission 4 of 7

| Field | Value |
| --- | --- |
| Reviewer | Codex `gpt-6.1-sol`, reasoning effort `high`, read-only |
| Packet | [AI-06-cocoindex-review-prompt-4.md](AI-06-cocoindex-review-prompt-4.md), sha256 `81fb74fdf6b4cd7c3e45797c5f1945c02a4bab663c1e498920f95c9d5b2f3645` |
| Window | 2026-11-13T19:29:30Z → ~19:32:21Z (171.26 s) |
| Process exit | 0 |
| Verdict | **REQUEST_CHANGES** — R2/R5 open; R1/R3/R4/R6/R7/R8 closed |

The verdict below is copied verbatim from the reviewer's final message; only absolute repository
paths are substituted with `<task_repo>`.

---

**REQUEST_CHANGES — AI-06 PR 1, submission 4 of 7.**

**AI06-R2 and AI06-R5 remain open, both major.** The specific review-3 examples are repaired, but both underlying defects persist.

1. **AI06-R2 — Major: permitted schema assertions are still ignored.**  
   Affected: **SCN-1005**, incompatible schemas must raise `cocoindex-capability-error`.

   At [cocoindex_mcp.py:104](<<task_repo>/backend/app/discovery/cocoindex_mcp.py:104>), the shared allowlist permits assertions that subsequent validation does not evaluate. Starting with the accepted schema, I independently reproduced acceptance of:

   - `query.anyOf=[{"const":"x"}]`, excluding valid query `"q"`.
   - `offset.anyOf=[{"maximum":0}]`, excluding supported positive offsets.
   - Outer `paths.type="array"` alongside the existing nullable `anyOf`, excluding the `null` sent for omitted filters.
   - Outer `paths.items=false`, excluding every nonempty filter array.

   **Smallest repair/evidence:** use field-specific allowlists and reject unsupported schema combinations, or evaluate every simultaneous constraint. Add regressions proving these examples fail during capability validation while the reviewed schema and supported nullable union remain accepted.

2. **AI06-R5 — Major: numeric equality still masks invalid text fields.**  
   Affected: **SCN-1004**, wrong-field-type and whole-envelope rejection.

   At [cocoindex_mcp.py:282](<<task_repo>/backend/app/discovery/cocoindex_mcp.py:282>), `_same_json` treats integers and floats as equal, while normalization requires exact integers for line numbers and counts.

   I independently reproduced successful hit returns with valid structured content alongside text containing `start_line: 1.0`. The text alone raises `cocoindex-protocol-error`. The same bypass works for floating-point `end_line`, `total_returned`, and `offset`.

   **Smallest repair/evidence:** validate each supplied representation independently before selecting one, preserving exact integer requirements. Add these regressions while retaining matching-envelope and structured-only success cases. The submitted boolean/integer regressions now reject correctly.

**R1/R3/R4/R6/R7/R8 remain closed.** The remaining nine scenarios are supported within this slice; SCN-1011 rests on retained live evidence, which I checked without rerunning live services. Offline defaults, untrusted-text handling, and separation from accepted links and verification evidence remain preserved.

Verification: **39 read-only tests passed**; all **20 submitted incompatible-schema rows** rejected independently. Submitted hashes and external evidence digests matched; sanitized-report derivation matched; all three captured hits and content hashes matched the pinned Git snapshot. The proposed commit references pass validation. Full-suite, network-denial, fixture, lint, and live outcomes were assessed from retained evidence.

No files were changed, dependencies installed, artifacts regenerated, commits created, or work delegated.