# DT-02 implementation record — source and test artifacts tied to path and Git revision

| Field | Value |
| --- | --- |
| Story | DT-02 — [#21](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/21), verified OPEN 2026-11-13T02:01:06Z (`gh issue view`, milestone "M1 — AI-free vertical slice") |
| Canonical criteria | [DT-02.feature](../../stories/DT-02.feature), sha256 `08c0e96d371724a9d640cefdc1e07d060e7c72cbfe141877022d662489d90e8a` |
| Brief / verification map | [DT-02.md](../../stories/DT-02.md) |
| Branch / base | `feat/21-dt-02-source-test-artifacts` from `26a25d0b739994631e098e6eae5307a47325a0ba` (DT-01 merge) |
| Contract version | `SCHEMA_VERSION = 0.1.0`, `PACKAGE_VERSION = 0.1.0` (no contract change) |
| Submission | **4 of 7** — rounds 1–3 REQUEST_CHANGES, round 4 **APPROVE** (2026-11-13T02:46Z; R1–R5 closed) |
| Snapshot captured | 2026-11-13T02:40Z (approved snapshot) |

## What changed

| Path | sha256 | Purpose |
| --- | --- | --- |
| `backend/app/ingestion/parsers.py` | `80554d82097e88b0e83bf4b535aafd843359bec5e0cc956ea8cd0eb2ab232e1c` | Tokenizer-based, standalone-comment-aware first-line annotation parsing |
| `backend/app/ingestion/scan.py` | `2a602ee3668bd1560e42aa8870c6a1875b3977a082d449109892852c73e0a613` | Adds the `.py` branch and source/test type inference |
| `tools/fixturectl.py` | `43483704398312b94ab55ff45f0e98ec496fde12ef4fc6ed9a730dd20b99b7c2` | Deletes the duplicate scanner and delegates to `app.ingestion` |
| `backend/tests/test_ingestion_parsers.py` | `1c68bec5233d4a30e53326b485851ee41ca098018ea1e904328e226ec9a327fe` | Annotation parser tests (indented standalone, trailing, strings, conflicts, tokenization failure) |
| `backend/tests/test_ingestion_artifacts.py` | `7d6ab5e34df1d1b80c9cc6ea487a90d3d779aec1203cfe62c37b23c38738ae30` | DT-02 acceptance tests, including indented-standalone and tokenization-failure cases |
| `docs/stories/DT-02.feature` | `08c0e96d371724a9d640cefdc1e07d060e7c72cbfe141877022d662489d90e8a` | Canonical criteria (SCN-521…527) |
| `docs/stories/DT-02.md` | `2599902ee5f6bec2960c2c04b78da900707ec764b32ffba5ff105eb3c496c6b1` | Brief, assumptions, verification map |
| `docs/architecture.md` | `a00a510fc5fd37c3b913656434d70891e17d4ad5d3f123ec010b79eccf1c7485` | Ingestion status includes source/test |
| `docs/STATUS.md` | `0574dfde81c148af3ac02fd5e732337332fd013159e198eed0d55149e1e05cc3` | DT-01 landed; DT-02 active |

Generated fixtures, oracle labels, and contracts are unchanged. The generator now uses the shared
scanner; `fixturectl verify` confirms the committed generated files are still byte-identical.

## Review round 1 — REQUEST_CHANGES (submission 1 of 7)

Reviewer: Codex `gpt-6.1-sol`, `xhigh`, read-only; session `01a1d2ab-84b3-7690-87b4-6db614ae210d`;
2026-11-13T02:10:17Z → 02:14:21Z (243.9 s), exit 0; 15/15 manifest hashes matched.
Verdict: `docs/reviews/DT-02-review.md`.

| Finding | Severity | Repair | Recheck |
| --- | --- | --- | --- |
| DT02-R1 the duplicate-identity error named only the second annotation | minor, blocking | The conflict message lists both declared identities; the parser and scanner tests assert both | `test_a_second_annotation_is_rejected_naming_both_identities`, `test_two_annotations_in_one_file_are_rejected` |
| DT02-R2 annotation examples inside Python string literals were treated as declarations | major, blocking | `parse_annotation` now uses Python's `tokenize`: only COMMENT tokens can declare an identity, so docstrings and other strings are data | `test_no_annotation_returns_none`, `test_annotation_text_inside_a_string_is_not_a_declaration` |

Both findings were reproduced from the verdict before repair. The tokenizer is the standard-
library parser for the same language the artifacts are written in; it removes the class of false
positives rather than special-casing the probe text.

## Review round 2 — REQUEST_CHANGES (submission 2 of 7)

Reviewer: same model/effort and read-only sandbox; session `01a1d2b7-d3f5-7d51-91f6-d612dffb66a2`;
2026-11-13T02:23:44Z → 02:27:44Z (239.35 s), exit 0; 17/17 manifest hashes matched.
Verdict: `docs/reviews/DT-02-review-2.md`. R1/R2 were confirmed closed.

| Finding | Severity | Repair | Recheck |
| --- | --- | --- | --- |
| DT02-R3 a trailing comment on the first line (`VALUE = 1  # cta:artifact CODE-001`) declared an artifact | major, blocking | Only column-0 comment tokens are declaration candidates; a trailing comment is data and declares nothing | `test_a_trailing_comment_is_not_a_declaration`, `test_a_trailing_comment_after_a_valid_declaration_is_ignored` (parser and scanner) |
| DT02-R4 a tokenization error silently ended the comment scan and hid later/conflicting declarations | major, blocking | Tokenization failure raises a contextual `IngestionError` naming the file; no partial inventory is returned | `test_incomplete_tokenization_is_rejected`, `test_incomplete_tokenization_is_rejected_by_the_scanner` |

The fail-closed choice is deliberate: a partial comment inventory cannot prove the absence or
uniqueness of a declaration, so the scanner refuses to certify the artifact rather than guessing.

## Review round 3 — REQUEST_CHANGES (submission 3 of 7)

Reviewer: same model/effort and read-only sandbox; session `01a1d2c1-7d86-7921-8f29-cfa9d47fe69f`;
2026-11-13T02:34:18Z → 02:37:48Z (210.0 s), exit 0; 19/19 manifest hashes matched.
Verdict: `docs/reviews/DT-02-review-3.md`. R1–R4 were confirmed closed.

| Finding | Severity | Repair | Recheck |
| --- | --- | --- | --- |
| DT02-R5 indented standalone annotations were discarded with trailing comments | major, blocking | Declaration candidates are now comment-only lines (any indentation); a comment following code is trailing data. A late standalone candidate raises, and a first-line candidate must be at column 0. | `test_an_indented_standalone_annotation_is_rejected`, `test_a_late_standalone_annotation_is_rejected`, `test_an_indented_standalone_annotation_is_rejected_by_the_scanner`, plus the trailing-comment cases |

The rule is now "comment-only line vs trailing comment", not "column 0 vs everything else"; this
distinguishes documentation after code from a real declaration attempt.

## Review round 4 — APPROVE (submission 4 of 7)

Reviewer: same model/effort and read-only sandbox; session `01a1d2c9-eba0-7481-915e-36bb9536a116`;
2026-11-13T02:43:30Z → 02:46:44Z (193.82 s), exit 0; 21/21 manifest hashes matched.
Verdict: `docs/reviews/DT-02-review-4.md`.

* R1–R5 closed; no new blocking finding.
* SCN-521…527 and generator reuse: all PASS.
* Invariants inspected as passing: validated artifacts only, proposal/acceptance/evidence
  separation, committed-blob hashing, offline defaults, and the ingestion endpoint's 501 naming
  DT-04. Contracts, fixtures, generated files, and oracle labels are unchanged.
* The reviewer independently ran 44 parser tests, three repository-port tests, ten
  retained-repository acceptance/regression functions, and 32 boundary probes; the 208-test suite
  was inspected from the captured logs, not re-run.

Approval covers the identified snapshot. It does not attest human labeling or link decisions,
supply stakeholder sign-off, or close M1's remaining gate.

## Acceptance results

| Criterion | Check | Result |
| --- | --- | --- |
| SCN-521 source artifact at the requested revision | `tests/test_ingestion_artifacts.py::test_source_annotation_is_parsed_at_the_requested_revision` | PASS |
| SCN-522 files without annotations | `::test_files_without_annotations_are_not_artifacts`, `::test_annotation_text_inside_a_string_is_not_a_declaration`, `::test_a_trailing_comment_is_not_a_declaration` | PASS |
| SCN-523 test artifact + blob hash | `::test_test_annotation_is_parsed` | PASS |
| SCN-524 annotation not on the first line | `::test_annotation_after_the_first_line_is_rejected`, `::test_an_indented_standalone_annotation_is_rejected_by_the_scanner`, `::test_incomplete_tokenization_is_rejected_by_the_scanner` | PASS |
| SCN-525 two identities in one file | `::test_two_annotations_in_one_file_are_rejected` (asserts both ids), `tests/test_ingestion_parsers.py::test_a_second_annotation_is_rejected_naming_both_identities` | PASS |
| SCN-526 committed blob, not working tree | `::test_content_hash_comes_from_the_committed_blob` | PASS |
| SCN-527 full snapshot equality | `::test_every_artifact_matches_the_committed_snapshot` (all 10 artifacts, both baselines) | PASS |
| DoD generator reuse | `fixturectl.py verify` passes with the generator delegating to `app.ingestion`; no generated bytes changed | PASS |
| Parser malformed inputs | `tests/test_ingestion_parsers.py` annotation cases (first-line rule, malformed, duplicate, prose ignored) | PASS |

Axis coverage: success (521/523), failure (524/525/malformed), boundary (522, 526, 527).

## Commands and outcomes (as captured)

```text
captured_start=2026-11-13T02:39:52Z
pytest backend/tests -q                          exit 0  208 passed, 1 warning in 5.27s
fixturectl.py verify                             exit 0  reproducible and committed files current
ruff check .                                     exit 0  All checks passed
ruff format --check .                            exit 0  all files formatted
git diff --check                                 exit 0
captured_end=2026-11-13T02:39:58Z

network denial at 2026-11-13T02:39:58Z: `unshare -rn backend/.venv/bin/python -m pytest
backend/tests -q` → exit 0, 208 passed.
```

`tests/test_ingestion_parsers.py` collects 44 tests. Raw logs are in the external run directory
`…/m1-roadmap-20261112/dt-02/`.

## Self-review

* **Revision-aware:** source/test artifacts use the same resolved commit and blob hashes as DT-01;
  the working-tree probe shows a modified file is not reflected when re-ingesting the commit.
* **Loud failures:** an annotation anywhere but the first line, a malformed declaration, and a
  second identity all raise `IngestionError` naming the file.
* **Generator equivalence:** the duplicate scanner is deleted; `verify` proves the committed
  snapshot/responses are still exactly what the generator produces. This is the strongest available
  check that the shared parser did not change fixture identity.
* **No contract change:** no schema bump, no API change, no generated-file edit.
* **Offline:** parsing plus the local Git CLI; the network-denied suite passes.

Known limits: Python files only; the annotation is a first-line comment; links/evidence/threads and
the API cutover remain DT-03/DT-04.

## Independent review

**APPROVE** — submission 4 of 7, snapshot captured 2026-11-13T02:40Z, reviewer `gpt-6.1-sol` at
`xhigh`, 21/21 manifest hashes confirmed. Verdict: `docs/reviews/DT-02-review-4.md`. No open
finding at this snapshot. Commit, PR, CI, and merge state are recorded separately after landing;
this approval does not close #21 by itself.
