# DT-01 — independent review, round 4

**Task:** DT-01 (#20), M1, owner B. **Submission 4 of 7.**
**Reviewer:** Codex, `gpt-6.1-sol`, `xhigh`, read-only — session `01a1d290-fa5e-7cb2-83ac-a348037c9340`,
2026-11-13T01:41:18Z → 01:45:42Z (263.7 s), exit 0; 109,635 CLI-reported tokens.
**Reviewed snapshot:** branch `feat/20-dt-01-ingestion`, base
`e18cdcfafe058e2f1d99c3c0b4bc2e155e9b16c9`, captured 2026-11-13T01:38Z; 22/22 manifest hashes
matched before and after.
**Packet:** `docs/reviews/DT-01-review-prompt-4.md`, sha256
`3788918a6eaa1b71e42a139e05567241cc7a37e54a983fe2912377d41e7ed111` (90,260 bytes).
**Verdict:** REQUEST_CHANGES — R1–R5 and N1–N3 closed; **R6 blocking** (front-matter preprocessing
rewrote the YAML stream before validation). Repaired for submission 5
(`docs/reviews/DT-01-review-5.md`).

The verdict below is copied verbatim from the reviewer's final message (raw file sha256
`0a386aeb37a1f16bf774a6facded43046910cefa6ba1c2f94dbe08f04afc21dc` before path sanitization);
only the absolute repository path is substituted with `<task_repo>`.

---

**REQUEST_CHANGES**

Reviewed submission 4, captured **2026-11-13T01:38Z**, on `feat/20-dt-01-ingestion`, base `e18cdcfafe058e2f1d99c3c0b4bc2e155e9b16c9`. All **22 manifest hashes matched before and after review**. No files were changed.

**Prior dispositions:** R1–R5 and N1–N3 are closed. The indented-separator repairs preserve title/status, expose malformed YAML after the separator, and retain CRLF/EOF support. The implementation-record metadata is corrected.

**DT01-R6 — Major; blocking — Front-matter preprocessing changes YAML before validation.**

**Location:** [parsers.py:65](<task_repo>/backend/app/ingestion/parsers.py:65), with reconstruction at line 78.

**Criteria:** SCN-510 value preservation, SCN-511 invalid-YAML rejection, and the story’s loud malformed-input rejection requirement.

`str.splitlines()` recognizes additional control and Unicode separators. Rejoining its output with `"\n"` changes the document supplied to PyYAML.

This Python string reproduces malformed-input acceptance; `\x0b` denotes an actual vertical-tab character:

```python
text = (
    "---\nid: REQ-900\ntitle: |-\n"
    "  Before\x0b  After\n"
    "status: superseded\n---\n"
)
```

**Expected:** Reject with `IngestionError` naming the requirement. PyYAML rejects the original front matter with `ReaderError: unacceptable character #x000b`.

**Observed:** The parser accepts it with title `"Before\nAfter"`. The production blob-to-artifact constructor also returns an `Artifact`. Form feed (`\x0c`) reproduces the same defect.

Valid content changes too: a quoted title containing `"Before\u2028  After"` parses directly through PyYAML as `"Before\u2028After"`, while ingestion produces `"Before After"`.

**Smallest correction/recheck:** Recognize delimiter boundaries without rewriting the enclosed YAML stream. Preserve the original content passed to the YAML loader. Add parser and artifact-level checks for rejected control characters and preserved Unicode separators; retain the indented-delimiter, CRLF/EOF and existing YAML checks.

| Criterion | Result | Basis |
|---|---|---|
| SCN-501 requirement artifact | PASS | Snapshot, metadata, revision and independently read blob hash match. |
| SCN-502 scenario identity | PASS | Tagged identity, title and anchored locator match. |
| SCN-503 missing front matter | PASS | Contextual error; no inventory returned. |
| SCN-504 untagged scenario | PASS | Only the tagged scenario becomes an artifact. |
| SCN-505 dangling tag | PASS | Dangling, Rule and outline boundaries raise. |
| SCN-506 duplicate identities | PASS | Error identifies the duplicate and both locators. |
| SCN-507 revision pinning | PASS | Tag/SHA equivalence, expanded SHA and pinned reads verified. |
| SCN-508 doc-string data | PASS | Ordinary, fenced, media-type, repeated-opener and unterminated cases pass. |
| SCN-509 malformed identity | PASS | Malformed tokens raise alone and beside valid identities. |
| SCN-510 YAML value preservation | FAIL | Existing examples and R5 repairs pass; Unicode separator content changes under R6. |
| SCN-511 invalid YAML rejection | FAIL | Unterminated-quote examples pass; malformed controls are accepted under R6. |
| Snapshot equality | PASS | Requirement/scenario artifacts match both committed baselines. |

Other applicable boundaries pass inspection: ingestion produces artifacts only; existing Pydantic contracts and ports remain unchanged; hashes cover exact blob bytes; the ingestion endpoint retains its 501; generated files, schemas and attested oracle hashes are unchanged; no later-story implementation was introduced. The proposed commit reference passes validation.

I independently ran **30 parser tests**, six fixture-based acceptance functions, eight retained repository success/failure cases, Ruff lint/format checks and whitespace checks. Raw submission-4 logs support **179 passing tests**, successful fixture verification, and **179 passes under recorded network denial**. Those full runs were inspected, not independently repeated. An additional HTTP/contract rerun was interrupted; no passing result is claimed for it.

This review does not attest human labeling, stakeholder acceptance or milestone completion.