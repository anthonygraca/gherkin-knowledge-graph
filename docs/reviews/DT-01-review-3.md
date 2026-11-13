# DT-01 — independent review, round 3

**Task:** DT-01 (#20), M1, owner B. **Submission 3 of 7.**
**Reviewer:** Codex, `gpt-6.1-sol`, `xhigh`, read-only — session `01a1d287-8506-75b0-bc93-1ae79391e195`,
2026-11-13T01:30:58Z → 01:35:20Z (261.1 s), exit 0; 116,325 CLI-reported tokens.
**Reviewed snapshot:** branch `feat/20-dt-01-ingestion`, base
`e18cdcfafe058e2f1d99c3c0b4bc2e155e9b16c9`, captured 2026-11-13T01:27Z; 20/20 manifest hashes
matched before and after.
**Packet:** `docs/reviews/DT-01-review-prompt-3.md`, sha256
`cfcfbe6156dcbfc148cfeb467fa0fb1f629cf5bbb74b91819cd4f7bb79d0420d` (77,800 bytes).
**Verdict:** REQUEST_CHANGES — R1–R4 and N1/N2 closed; **R5 blocking** (indented YAML `---`
treated as a front-matter boundary); N3 nonblocking (stale record metadata). Both were repaired
for submission 4 (`docs/reviews/DT-01-review-4.md`).

The verdict below is copied verbatim from the reviewer's final message (raw file sha256
`e0fb0089a7499b535afb1bb931a8d964775173b815635e1a5660f60feda57ba9` before path sanitization);
only the absolute repository path is substituted with `<task_repo>`.

---

**REQUEST_CHANGES**

Reviewed submission 3, captured **2026-11-13T01:27Z**, on `feat/20-dt-01-ingestion`, base `e18cdcfafe058e2f1d99c3c0b4bc2e155e9b16c9`. All **20 manifest hashes matched before and after review**. No files were changed.

The original R1–R4 reproductions now pass, including R2’s repeated-delimiter cases. N1 remains repaired, and N2’s CRLF/EOF examples pass. One new blocking regression remains.

**DT01-R5 — Major; blocking — Front-matter boundary detection mistakes indented YAML content for a closing delimiter.**

**Location:** [parsers.py:75](<task_repo>/backend/app/ingestion/parsers.py:75>).

**Criteria:** YAML value preservation, SCN-510, SCN-511, and loud malformed-input rejection.

The new `line.strip() == "---"` condition removes meaningful indentation. This valid requirement demonstrates the problem:

```yaml
---
id: REQ-900
title: |-
  Before delimiter
  ---
  After delimiter
status: superseded
---
```

**Expected:** Title `"Before delimiter\n---\nAfter delimiter"` and status `"superseded"`. The indented separator belongs to the scalar’s content. [YAML literal-scalar specification](https://yaml.org/spec/1.2.2/#812-literal-style).

**Observed:** Both the parser and artifact constructor return title `"Before delimiter"` and status `"active"`. Everything after the indented separator is excluded from YAML validation.

Two related probes also reproduced the defect:

- A valid multiline **quoted** title containing an indented `---` is rejected as invalid YAML.
- Malformed YAML containing an unterminated quoted title after the false boundary still produces an artifact. Independently parsing the complete front matter rejects it.

**Smallest correction/recheck:** Preserve leading indentation when recognizing front-matter delimiter lines. Retain CRLF/EOF support. Check an indented separator inside block and quoted scalars, malformed YAML following that content, and scanner-level preservation of title/status.

The complete acceptance assessment is:

| Criterion | Result | Basis |
|---|---|---|
| SCN-501 requirement artifact | PASS | Fixture artifact, metadata and exact blob hash match. |
| SCN-502 scenario identity | PASS | Identity, title and anchored locator match. |
| SCN-503 missing front matter | PASS | Contextual error; no inventory returned. |
| SCN-504 untagged scenario | PASS | Only the tagged scenario becomes an artifact. |
| SCN-505 dangling identity | PASS | Dangling, Rule and outline boundaries raise. |
| SCN-506 duplicate identities | PASS | Error names the duplicate and both locators. |
| SCN-507 revision pinning | PASS | Tag/SHA equivalence, expanded SHA and pinned reads verified. |
| SCN-508 doc-string data | PASS | Ordinary, fenced, media-type, repeated-opener and unterminated cases pass. R2 closed. |
| SCN-509 malformed identity | PASS | Malformed tokens raise alone and beside valid identities. |
| SCN-510 quoted YAML | FAIL | Single-line examples pass; valid multiline quoted content is rejected under R5. |
| SCN-511 invalid YAML | FAIL | Ordinary malformed example passes; malformed content beyond a false boundary is accepted under R5. |
| Snapshot equality | PASS | Requirement/scenario artifacts match all committed baselines. |

Other applicable boundaries pass inspection: output contains artifacts only; existing Pydantic models and ports remain unchanged; hashes cover exact blob bytes; the ingestion endpoint retains its 501 response; generated fixtures, contract files and attested oracle hashes are unchanged; no later-story implementation was introduced. The proposed commit reference passes validation.

I independently ran **26 parser tests**, six fixture-based acceptance functions against retained repositories, seven retained success/failure cases, Ruff lint/format checks and whitespace checks. Raw logs support **174 passing tests**, successful fixture verification, and **174 passes under recorded network denial**. Those complete runs were inspected rather than repeated in this read-only sandbox.

**DT01-N3 — Minor; nonblocking — Implementation-record metadata is stale.** [IMPLEMENTATION.md:6](<task_repo>/docs/reports/omp-dt-01-ingestion/IMPLEMENTATION.md:6>) identifies an obsolete canonical-criteria digest, although its manifest table correctly records `5517104a2cfffe255304ff5fc4e67a5186150f6c54c1456e21d8bb7b10bf4b4d`. Line 82 also reports 20 parser tests rather than 26. Reconcile those fields with the reviewed snapshot.

This review does not attest human labeling, product-owner approval, or milestone completion.