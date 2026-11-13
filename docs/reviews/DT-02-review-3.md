# DT-02 — independent review, round 3

**Task:** DT-02 (#21), M1, owner B. **Submission 3 of 7.**
**Reviewer:** Codex, `gpt-6.1-sol`, `xhigh`, read-only — session `01a1d2c1-7d86-7921-8f29-cfa9d47fe69f`,
2026-11-13T02:34:18Z → 02:37:48Z (210.0 s), exit 0; 105,534 CLI-reported tokens.
**Reviewed snapshot:** branch `feat/21-dt-02-source-test-artifacts`, base
`26a25d0b739994631e098e6eae5307a47325a0ba`, captured 2026-11-13T02:31Z; 19/19 manifest hashes
matched before and after.
**Packet:** `docs/reviews/DT-02-review-prompt-3.md`, sha256
`1384a4b306e5a580ac6242eddf0dbeab8c2214bb640c7f973d9be764bb83b771` (80,718 bytes).
**Verdict:** REQUEST_CHANGES — R1–R4 closed; **R5** (indented standalone annotations silently
discarded) blocking. Repaired for submission 4 (`docs/reviews/DT-02-review-4.md`).

The verdict below is copied verbatim from the reviewer's final message (raw file sha256
`7a9add26217b8f60427d1289a3c31ce59f13520665f3d38948e96c52ace6ef0d` before path sanitization);
only the absolute repository path is substituted with `<task_repo>`.

---

**REQUEST_CHANGES**

Reviewed submission 3, captured **2026-11-13T02:31Z**, on `feat/21-dt-02-source-test-artifacts`, base `26a25d0b739994631e098e6eae5307a47325a0ba`. All **19 manifest hashes matched before and after review**. No files were changed.

DT02-R1–R4 are **closed for their original reproductions**: conflict diagnostics name both identities, string examples and trailing comments are ignored, and incomplete tokenization raises a contextual error.

**DT02-R5 — major, blocking; SCN-524/525: indented standalone annotations are silently discarded.**

The `column == 0` filter at [parsers.py:200](<task_repo>/backend/app/ingestion/parsers.py:200>) excludes indented standalone comments along with trailing comments. This valid Python therefore bypasses conflict rejection:

```python
# cta:artifact CODE-001
def example():
    # cta:artifact TEST-002
    pass
```

**Expected:** Reject the file, naming `CODE-001`, `TEST-002`, and the file. Removing the first annotation should instead trigger late-annotation rejection.

**Actual:** The parser returns `CODE-001`, and the scanner accepts that artifact. Removing the first annotation returns no artifacts without an error. Both behaviors were independently reproduced through parser and in-memory scanner probes. There is no code before the indented comment.

The companion document’s column-0 assumption can constrain a valid first-line declaration; it does not exempt standalone late or conflicting annotations from the unchanged canonical criteria.

**Smallest correction/recheck:** Retain standalone reserved-marker comments whose preceding text is only indentation, then validate their position and formatting. Keep first-line column-0 validation separate from trailing-comment exclusion. Check indented late and conflicting annotations through both parser and scanner, preserving the existing string, trailing-comment, conflict-diagnostic, and tokenization regressions.

| Criterion | Assessment | Evidence |
|---|---|---|
| SCN-521 source artifact and revision | PASS | Retained Git fixture matches the snapshot; hashes differ across baselines. |
| SCN-522 unannotated files | PASS | Fixture exclusions, string examples, and trailing comments behave correctly. |
| SCN-523 test artifact and committed hash | PASS | Snapshot and independently read blob hash match. |
| SCN-524 late annotation rejection | FAIL | Ordinary case passes; indented standalone annotation bypasses rejection under R5. |
| SCN-525 conflicting identities | FAIL | Ordinary conflicts name both identities; indented second annotation bypasses rejection under R5. |
| SCN-526 working-tree independence | PASS | Retained dirty repository returns the committed hash and unchanged revision. |
| SCN-527 complete snapshot equality | PASS | Every artifact matches both baseline snapshots. |
| Generator reuse and preservation | PASS | Shared scanner inspected; retained verification log reports zero drift; generated files are unchanged. |

I independently ran **42 parser tests**, **three repository-port checks**, ten acceptance/regression functions against retained Git repositories, additional error and dirty-tree probes, Ruff checks, formatting, whitespace checks, and proposed-message commitlint. These passed apart from the newly identified boundary probes.

Applicable boundaries remain intact: existing Pydantic artifacts and consumer ports are compatible; proposals, accepted links, and evidence remain separate; hashes cover committed blob bytes; defaults remain offline; and the ingestion endpoint retains its contract-only error identifying DT-04. Contracts, fixtures, and oracle files are unchanged.

Retained raw logs support **205 full-suite passes**, successful fixture verification, and **205 passes under recorded network denial**. Those complete runs were not independently repeated in this read-only sandbox. No new human-labeling or human-link approval is attested.