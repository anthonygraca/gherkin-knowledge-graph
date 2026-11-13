# DT-01 — independent review, round 2

**Task:** DT-01 (#20), M1, owner B. **Submission 2 of 7.**
**Reviewer:** Codex, model `gpt-6.1-sol`, reasoning effort `xhigh`, read-only sandbox — session
`01a1d27b-f3e3-7373-8703-fbb61c7e6e38`, 2026-11-13T01:18:20Z → 01:24:05Z (344.9 s), exit 0;
usage 116,127 CLI-reported tokens.
**Reviewed snapshot:** branch `feat/20-dt-01-ingestion`, base
`e18cdcfafe058e2f1d99c3c0b4bc2e155e9b16c9`, captured 2026-11-13T01:14Z; the reviewer confirmed
all 18 manifest hashes matched before and after review.
**Packet:** `docs/reviews/DT-01-review-prompt-2.md`, sha256
`a1d115b3ce3633fd820a5145676d6ff5a73f9b30ab56a59298b50f5f2fb61a64` (90,800 bytes).
**Verdict:** REQUEST_CHANGES — R1, R3, R4 and N1 closed; **R2 remains blocking** for a doc-string
opening line that self-closed; optional N2 for CRLF/EOF front matter. Both were repaired for
submission 3 (`docs/reviews/DT-01-review-3.md`).

The verdict below is copied verbatim from the reviewer's final message (raw file sha256
`9ad3cadb5d1cc239238aca72cfc91c34d7f35997da81a04c4943523dc528eb50` before path sanitization);
only the absolute repository path is substituted with `<task_repo>`.

---

**REQUEST_CHANGES**

Reviewed submission 2, captured **2026-11-13T01:14Z**, on `feat/20-dt-01-ingestion`, base `e18cdcfafe058e2f1d99c3c0b4bc2e155e9b16c9`. All **18 manifest hashes matched before and after review**. No files were changed.

One blocking finding remains.

**DT01-R2 — Major; blocking; partially repaired — Doc-string opening lines can bypass string tracking.**

- **Location:** [parsers.py:124](<task_repo>/backend/app/ingestion/parsers.py:124>).
- **Contract:** Malformed declarations fail loudly; doc-string contents remain data; the SCN-508 verification mapping requires unterminated doc strings to raise.
- **Observed:** This unterminated input returns declarations for both `SCN-900` and `SCN-999`. Artifact construction also returns both IDs.

```gherkin
Feature: Demo
  @SCN-900
  Scenario: Real
    Given a payload
      """"""
      @SCN-999
      Scenario: not real
```

The opening-line substring check treats the second delimiter as a same-line terminator and never enters doc-string state. Six backticks reproduce the same defect.

**Expected:** Raise `IngestionError` naming the input and return no inventory. Gherkin uses separate opening and closing delimiter lines; its tokenizer does not interpret another delimiter on the opening line as closure. [Gherkin reference](https://cucumber.io/docs/gherkin/reference/#doc-strings), [Cucumber tokenizer](https://raw.githubusercontent.com/cucumber/gherkin/master/python/gherkin/token_matcher.py).

**Smallest correction/recheck:** Enter doc-string state whenever an opening separator is recognized. Remove the same-line closure heuristic. Check repeated delimiters at EOF for both supported delimiter types, ordinary terminated strings, and literal identity/scenario text inside strings. No Gherkin runner is required.

The complete acceptance assessment is:

| Criterion | Result | Basis |
|---|---|---|
| SCN-501 requirement artifact | PASS | Matches committed snapshot, metadata and independently read blob hash. |
| SCN-502 scenario identity | PASS | Reference scenario preserves identity, title and locator. |
| SCN-503 missing front matter | PASS | Error names the path; no inventory returned. |
| SCN-504 untagged scenario | PASS | Retained repository produces only the tagged artifact. |
| SCN-505 dangling identity | PASS | Intervening `Rule:`/outline declarations now raise. |
| SCN-506 duplicate identities | PASS | Error identifies the duplicate and both locators. |
| SCN-507 revision pinning | PASS | Tag/SHA equivalence, full-SHA provenance and pinned reads verified. |
| SCN-508 / mapped doc-string boundary | FAIL | Ordinary example passes; unterminated-string rejection remains incomplete under R2. |
| SCN-509 malformed identity | PASS | Malformed tokens raise alone and beside valid identities. |
| SCN-510 quoted YAML | PASS | Quotation marks/comments are excluded from stored values. |
| SCN-511 invalid YAML | PASS | Invalid syntax and non-string values raise contextual errors. |

Prior dispositions: **R1, R3, R4 and N1 are closed. R2 remains blocking**, although its Rule/outline and ordinary doc-string cases are repaired.

Other applicable boundaries pass inspection: artifact-only output preserves proposal/link/evidence separation; existing Pydantic contracts and ports remain unchanged; hashing uses exact blob bytes; ingestion retains its 501 endpoint; generated files and oracle attestations are unchanged; no later-story implementation or schema change was introduced. The proposed commit message passes the existing validator.

I independently ran **21 parser tests**, re-executed the six fixture-based acceptance functions, checked seven retained repository success/failure cases, and ran Ruff and whitespace checks. Raw submission-2 logs support **169 passing tests**, successful fixture verification, and **169 passes under demonstrated network denial**. Those full runs were inspected, not independently repeated in this read-only sandbox.

Separate optional observation, **DT01-N2 — Minor; nonblocking:** [parsers.py:68](<task_repo>/backend/app/ingestion/parsers.py:68>) rejects CRLF front matter and a closing delimiter at EOF without a trailing newline. Consider recognizing delimiter lines independently of newline style while continuing to hash the original bytes.

This review does not attest human labeling, product-owner approval, or milestone completion.