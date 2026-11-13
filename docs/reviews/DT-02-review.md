# DT-02 — independent review, round 1

**Task:** DT-02 (#21), M1, owner B. **Submission 1 of 7.**
**Reviewer:** Codex, `gpt-6.1-sol`, `xhigh`, read-only — session `01a1d2ab-84b3-7690-87b4-6db614ae210d`,
2026-11-13T02:10:17Z → 02:14:21Z (243.9 s), exit 0; 111,394 CLI-reported tokens.
**Reviewed snapshot:** branch `feat/21-dt-02-source-test-artifacts`, base
`26a25d0b739994631e098e6eae5307a47325a0ba`, captured 2026-11-13T02:08Z; 15/15 manifest hashes
matched before and after.
**Packet:** `docs/reviews/DT-02-review-prompt.md`, sha256
`d19c3e93045cbea7658632fdf518df03644683191030266e5c619132150fed30` (77,553 bytes).
**Verdict:** REQUEST_CHANGES — DT02-R1 (minor, blocking; conflict diagnostic omitted the first
identity) and DT02-R2 (major, blocking; annotation examples inside strings were treated as
declarations). Both repaired for submission 2 (`docs/reviews/DT-02-review-2.md`).

The verdict below is copied verbatim from the reviewer's final message (raw file sha256
`b8570782344dd44da4300c8b9d61abaa314c6191efcb3083be4f77cdc2851bd0` before path sanitization);
only the absolute repository and run-directory paths are substituted with `<task_repo>` and
`<run_dir>`.

---

**REQUEST_CHANGES**

Reviewed DT-02 submission 1, captured **2026-11-13T02:08Z**, on `feat/21-dt-02-source-test-artifacts`, base `26a25d0b739994631e098e6eae5307a47325a0ba`. All **15 supplied manifest hashes matched before and after review**. No files were changed.

1. **DT02-R1 — minor, blocking; SCN-525: conflict error omits the first identity.**  
   At [parsers.py:200](<task_repo>/backend/app/ingestion/parsers.py:200>), declaring `CODE-001` followed by `TEST-001` raises an error naming the file and `TEST-001`, but omits `CODE-001`. SCN-525 explicitly requires the conflicting identities. This was reproduced against the retained Git test repository. The mapped test checks only the generic error phrase, so its passing result does not establish the complete criterion.

   **Smallest correction/recheck:** Include both identities and the file in the diagnostic. Strengthen the existing parser and scanner checks to assert those inputs, without pinning incidental wording.

2. **DT02-R2 — major, blocking; declaration contract, SCN-522: Python string contents are mistaken for annotations.**  
   The raw-line searches at [parsers.py:198](<task_repo>/backend/app/ingestion/parsers.py:198>) and line 205 treat annotation examples inside multiline strings as declarations. For example, this valid, unannotated `src/__init__.py` causes ingestion to raise:

   ```python
   """Annotation example:
   # cta:artifact CODE-001
   """
   ```

   An annotated file containing a similar string example also raises a false duplicate error. Direct parser and in-memory scanner probes reproduced both failures; Python tokenization confirmed that the example text is string data. Because scanning aborts on the error, an ordinary documentation string can prevent the entire inventory from being returned.

   **Smallest correction/recheck:** Identify actual Python comment tokens, preserving the physical-first-line requirement. Add independent examples proving that multiline-string contents are ignored in both annotated and unannotated files, while real late and duplicate annotations still fail.

| Criterion | Assessment | Evidence |
|---|---|---|
| SCN-521 source artifact and revision | PASS | Retained Git fixture matches the snapshot; baseline hashes differ as specified. |
| SCN-522 unannotated files | FAIL | Named fixture passes; valid unannotated string-data boundary fails under DT02-R2. |
| SCN-523 test artifact and committed hash | PASS | Snapshot and independently read Git blob hash match. |
| SCN-524 late annotation rejection | PASS | Retained repository raises an error naming the file. |
| SCN-525 conflicting identities | FAIL | Rejection occurs, but the first identity is missing from the diagnostic. |
| SCN-526 working-tree independence | PASS | Retained dirty repository returns the committed blob hash and unchanged revision. |
| SCN-527 complete snapshot equality | PASS | All artifacts match both committed baseline snapshots. |

Applicable boundary checks pass inspection: ingestion returns existing Pydantic artifacts; proposals, accepted links, and evidence remain separate; consumer ports and contracts are unchanged; hashes cover committed blob bytes; dependencies remain offline; generated fixtures and oracle files are unchanged. The ingestion route still raises 501 naming DT-04. The proposed commit message passes commitlint.

I independently ran **38 parser tests**, **three repository-port tests**, nine fixture/revision acceptance and regression functions against retained Git repositories, contextual-error and dirty-tree probes, Ruff checks, and whitespace checks. These checks exposed the findings above despite the existing tests passing.

Inspected raw logs under `<run_dir>/dt-02/` support **197 full-suite passes**, successful fixture verification, and **197 passes under recorded network denial**. Those complete runs were not independently repeated in this read-only sandbox. No new HTTP execution or human-labeling attestation is claimed.