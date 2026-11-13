# DT-01 implementation record — requirements and Gherkin parsed into stable artifacts

| Field | Value |
| --- | --- |
| Story | DT-01 — [#20](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/20), verified OPEN on 2026-11-13T00:52:26Z (`gh issue view`, milestone "M1 — AI-free vertical slice") |
| Canonical criteria | [DT-01.feature](../../stories/DT-01.feature), sha256 `5517104a2cfffe255304ff5fc4e67a5186150f6c54c1456e21d8bb7b10bf4b4d` |
| Brief / verification map | [DT-01.md](../../stories/DT-01.md) |
| Branch / base | `feat/20-dt-01-ingestion` from `e18cdcfafe058e2f1d99c3c0b4bc2e155e9b16c9` |
| Contract version | `SCHEMA_VERSION = 0.1.0`, `PACKAGE_VERSION = 0.1.0` (no API/domain contract change) |
| Submission | **5 of 7** — rounds 1–4 REQUEST_CHANGES, round 5 **APPROVE** (2026-11-13T01:57Z; R1–R6 and N1–N3 closed) |
| Snapshot captured | 2026-11-13T01:50Z (approved snapshot) |

## What changed

| Path | sha256 | Purpose |
| --- | --- | --- |
| `backend/app/ingestion/__init__.py` | `c87a149c478ddbcd7322ffbdda723362bda18729da264048be5c3eaa9e58cdbf` | Package exports |
| `backend/app/ingestion/errors.py` | `b33cd36ad1a42f9f18720cf11f5d42aea424646ba8ff5b286587995ab2799a1d` | `IngestionError` for malformed content / Git access |
| `backend/app/ingestion/parsers.py` | `9c1ddbd8b45cbc3d53336bae577de503a9f4b73a0268fac2506613c3701e48b0` | YAML front matter (exact substring) + declaration-aware scenario parsing |
| `backend/app/ingestion/repository.py` | `eaaec286ca5dddff28914b6e3a431338a4082b17edd703548ec9fda811d6c005` | Read-only Git access at explicit revisions |
| `backend/app/ingestion/scan.py` | `6300e39d2bcf1305bd5c69ef337f4ae48999bb5134556a4b457befea4500556f` | Scan resolved once to a full commit; duplicate/prefix guards |
| `backend/tests/test_ingestion_parsers.py` | `7e795863669ed903f2aa990f23da3db1e2a87aa00dbfa577f1b605d3d2fce5cd` | Parser tests, including control characters and Unicode separators |
| `backend/tests/test_ingestion_artifacts.py` | `cf3c7f75eb7cc3ab70c77ee130036308ed76b631003ab879b93d2a1457ba6971` | Acceptance tests against the built fixture and temp repositories |
| `backend/pyproject.toml` | `0d3cf3827bddf31240411461d5c802876f99eab362ca8c6b1ecce3269e38b5e2` | Adds `pyyaml>=6,<7` for declared YAML front matter |
| `backend/uv.lock` | `3328532e7693da5df68c6d3d2d7f74a2d693270e660ac1d9708bcff15b45bfc5` | Locked dependency graph |
| `docs/stories/DT-01.feature` | `5517104a2cfffe255304ff5fc4e67a5186150f6c54c1456e21d8bb7b10bf4b4d` | Canonical criteria (SCN-501…511) |
| `docs/stories/DT-01.md` | `57e269f6f6980b37f0308bd11d28d12bb7f055083a211e6ebf7b43a15c37958c` | Brief, assumptions, verification map |
| `docs/architecture.md` | `5926759c78412da49573bdb745fb1369db2e3e0786f774eb0556280c9ddbcbd9` | Ingestion status is no longer "absent" |
| `docs/STATUS.md` | `72982280dcae3e56e825720fc099bd027be7c8dda4b09594dd3bec016d86868a` | M1 ledger; SETUP-01 figures labelled historical |

Generated fixtures, oracle labels, contract models, API responses, and the API itself are
untouched. `tools/fixturectl.py` still produces the M0 fixtures and is reused by ingestion only in
DT-02, after the scanner also covers source/test artifacts.

## Review round 1 — REQUEST_CHANGES (submission 1 of 7)

Reviewer: Codex `gpt-6.1-sol`, effort `xhigh`, read-only; session `01a1d25d-1906-72e1-bc4a-d40fc65f12f7`;
2026-11-13T01:01:52Z → 01:06:39Z; exit 0; 14/14 supplied hashes matched before and after. Verdict and
full findings: `docs/reviews/DT-01-review.md`.

| Finding | Severity | Repair | Recheck |
| --- | --- | --- | --- |
| DT01-R1 revision expressions leaked into artifact provenance; reads could mix revisions | major, blocking | `scan_artifacts` resolves once to a full commit SHA and uses it for every read and every `Artifact.revision` | `test_tag_and_sha_ingestion_return_identical_artifacts`, `test_abbreviated_sha_is_pinned_to_the_full_commit`, `test_every_read_uses_the_resolved_commit` |
| DT01-R2 a pending tag could attach to a scenario across `Rule:`/`Scenario Outline:` or from doc-string text | major, blocking | Declaration-aware state machine: only a `Scenario:` line (with blank/comment/tag lines allowed) consumes the identity; any other declaration raises; doc strings are lexical data; unterminated doc strings raise | `test_tag_before_a_rule_does_not_capture_a_nested_scenario`, `test_tag_before_a_scenario_outline_is_rejected_as_unsupported`, `test_doc_string_contents_are_data`, `test_an_unterminated_doc_string_is_rejected` |
| DT01-R3 hand-rolled front matter changed YAML meaning and accepted invalid YAML | major, blocking | `PyYAML` safe loader with duplicate-key rejection; string-scalar validation; quoted values/comments preserved; invalid YAML raises | `test_front_matter_parses_quoted_values_and_comments`, `test_front_matter_rejects_invalid_yaml`, `test_front_matter_rejects_non_string_scalars`, `test_quoted_front_matter_values_are_parsed`, `test_invalid_yaml_is_rejected_by_the_scanner` |
| DT01-R4 malformed `@SCN` tokens were silently ignored | major, blocking | Reserved-prefix token validation: any `@SCN…` token that is not `@SCN-nnn` raises, alone or beside a valid identity | `test_a_malformed_identity_token_is_rejected`, `test_a_malformed_identity_beside_a_valid_one_is_rejected` |
| DT01-N1 `STATUS.md` still said "Active task: none" and mixed older SETUP-01 results into current status | minor, nonblocking | Header and results corrected; SETUP-01 figures labelled historical | inspection |

New scenarios SCN-507…511 were added to the canonical specification to make the repaired defect
classes observable; the intake criteria were not weakened.

## Review round 2 — REQUEST_CHANGES (submission 2 of 7)

Reviewer: same model/effort and read-only sandbox; session
`01a1d27b-f3e3-7373-8703-fbb61c7e6e38`; 2026-11-13T01:18:20Z → 01:24:05Z (344.9 s), exit 0;
18/18 manifest hashes matched. Verdict: `docs/reviews/DT-01-review-2.md`.

| Finding | Severity | Repair | Recheck |
| --- | --- | --- | --- |
| DT01-R2 (remaining) an opening delimiter containing a second delimiter (`""""""`, six backticks) was treated as self-closing | major, blocking | Doc strings now enter state on any recognized opener; only a line whose stripped content equals the delimiter closes it. No same-line closure heuristic. | `test_a_repeated_delimiter_line_opens_an_unterminated_doc_string` (both delimiters), plus the existing terminated/media-type/fenced tests |
| DT01-N2 CRLF front matter and a closing delimiter at EOF without a trailing newline were rejected | minor, nonblocking | Front matter delimiters are found line-wise (newline-style independent); the original blob bytes are still what is hashed | `test_front_matter_accepts_crlf_and_a_closing_delimiter_at_eof` |

Prior dispositions in this round: R1, R3, R4 and N1 were closed by the reviewer; R2 is repaired
above. The reviewer's acceptance table was otherwise PASS.

## Review round 3 — REQUEST_CHANGES (submission 3 of 7)

Reviewer: same model/effort and read-only sandbox; session `01a1d287-8506-75b0-bc93-1ae79391e195`;
2026-11-13T01:30:58Z → 01:35:20Z (261.1 s), exit 0; 20/20 manifest hashes matched.
Verdict: `docs/reviews/DT-01-review-3.md`.

| Finding | Severity | Repair | Recheck |
| --- | --- | --- | --- |
| DT01-R5 front-matter boundary used `line.strip()`, so an indented `---` inside a YAML block/quoted scalar closed the block early | major, blocking | Delimiters are recognized only at column 0 (`line.rstrip() == "---"`); indented separators remain scalar content; CRLF/EOF support retained | `test_indented_separator_inside_a_block_scalar_is_content`, `test_indented_separator_inside_a_quoted_scalar_is_content`, `test_malformed_yaml_after_an_indented_separator_is_rejected`, `test_an_indented_opening_delimiter_is_rejected`, `test_block_scalar_with_indented_separator_preserves_title_and_status` |
| DT01-N3 implementation record had a stale criteria digest and parser-test count | minor, nonblocking | Header digest corrected to `5517104a…`; parser test count corrected to 30 | inspection |

The reviewer's SCN-510 and SCN-511 rows are rechecked by the tests above; all other rows were PASS.

## Review round 4 — REQUEST_CHANGES (submission 4 of 7)

Reviewer: same model/effort and read-only sandbox; session `01a1d290-fa5e-7cb2-83ac-a348037c9340`;
2026-11-13T01:41:18Z → 01:45:42Z (263.7 s), exit 0; 22/22 manifest hashes matched.
Verdict: `docs/reviews/DT-01-review-4.md`. R1–R5 and N1–N3 were confirmed closed.

| Finding | Severity | Repair | Recheck |
| --- | --- | --- | --- |
| DT01-R6 `splitlines()` + `"\n".join` rewrote the YAML document before validation: vertical tab/form feed were accepted as line breaks, and U+2028 content changed | major, blocking | Front-matter boundaries are found by index scanning on LF only; the YAML payload is the exact original substring between column-0 delimiters and is never reconstructed. PyYAML is the sole authority on YAML validity. Gherkin line splitting also uses LF only (trailing CR removed). | `test_control_characters_inside_yaml_are_rejected`, `test_unicode_line_separator_in_a_quoted_scalar_is_preserved`, `test_control_character_in_front_matter_is_rejected_by_the_scanner`, `test_unicode_line_separator_title_is_preserved_by_the_scanner`, plus all prior indented/CRLF/EOF/quoted/malformed cases |

This was the third repair in the same lexing area (R2, R5, R6), so the change is a root-cause
replacement of the preprocessing approach rather than another probe-specific patch: no text is
split and rejoined before YAML validation, and line-boundary characters are explicit (LF for
Gherkin, LF-only index scanning for front matter).

## Review round 5 — APPROVE (submission 5 of 7)

Reviewer: same model/effort and read-only sandbox; session `01a1d29b-fcaa-72d1-9f43-d9bdd4d1fdaf`;
2026-11-13T01:53:20Z → 01:57:02Z (222.75 s), exit 0; 24/24 manifest hashes matched.
Verdict: `docs/reviews/DT-01-review-5.md`.

* R6 repaired and closed; R1–R5 and N1–N3 remain closed; no new actionable finding or unresolved
  blocker.
* SCN-501…511 and snapshot equality: all PASS.
* Invariants inspected as passing: artifact-only output (no links/evidence), unchanged contracts and
  ports, exact blob hashing, unchanged generated fixtures/oracle attestations, offline dependencies,
  and no later-story functionality. The ingestion endpoint still returns 501 naming DT-04.
* The reviewer independently ran 32 parser tests, six fixture-based acceptance functions, ten
  retained repository cases, and Ruff/whitespace checks; the full 183-test suite was inspected from
  the captured logs, not re-run.

Approval covers the identified snapshot. It does not attest human labeling, stakeholder
acceptance, issue closure, or M1 completion.

## Acceptance results

| Criterion | Check | Result |
| --- | --- | --- |
| SCN-501 requirement parsed | `tests/test_ingestion_artifacts.py::test_requirement_document_is_parsed_into_an_artifact` | PASS |
| SCN-502 scenario identity | `::test_scenario_identity_comes_from_the_gherkin_tag` | PASS |
| SCN-503 missing front matter | `::test_requirement_without_front_matter_is_rejected` | PASS |
| SCN-504 untagged scenario | `::test_untagged_scenario_creates_no_artifact` | PASS |
| SCN-505 dangling tag | `::test_dangling_scenario_tag_is_rejected` | PASS |
| SCN-506 duplicate identity | `::test_duplicate_artifact_identities_are_rejected` | PASS |
| SCN-507 revision pinning | three tests listed under R1 | PASS |
| SCN-508 doc-string data | five parser tests: ordinary, unterminated, repeated-delimiter, media-type, fenced | PASS |
| SCN-509 malformed identity | two parser tests listed under R4 | PASS |
| SCN-510 quoted YAML | parser + scanner tests listed under R3/R5/R6 (multiline scalars, Unicode separator preserved) | PASS |
| SCN-511 invalid YAML | parser + scanner tests listed under R3/R5/R6 (control characters rejected, malformed content after an indented separator) | PASS |
| DoD parse vs snapshot | `::test_parsed_artifacts_match_the_committed_snapshot_for_requirements_and_scenarios` | PASS |
| DoD malformed parsers | `tests/test_ingestion_parsers.py` (32 tests) | PASS |

Axis coverage: success (501/502), failure (503/505/506/509/511), boundary (504, 507, 508, 510),
plus multi-tag lines, id/type disagreement, duplicates, and doc strings.

## Commands and outcomes (as captured)

```text
captured_start=2026-11-13T01:49:19Z
uv sync --project backend --frozen               exit 0  Checked 25 packages
pytest backend/tests -q                          exit 0  183 passed, 1 warning in 4.23s
fixturectl.py verify                             exit 0  reproducible and committed files current
ruff check .                                     exit 0  All checks passed
ruff format --check .                            exit 0  all files formatted
git diff --check                                 exit 0
captured_end=2026-11-13T01:49:24Z

network denial at 2026-11-13T01:49:30Z: `unshare -rn backend/.venv/bin/python -m pytest
backend/tests -q` → exit 0, 183 passed; the earlier socket probe produced
`OSError: [Errno 101] Network is unreachable`.
```

Raw logs are in the external run directory `…/m1-roadmap-20261112/dt-01/`. The committed
`IMPLEMENTATION.md` is the summary; the review packet carries the file manifest at submission.

## Self-review after repair

* **Revision-aware:** one resolved commit per scan; tag/SHA equivalence and full-SHA provenance are
  asserted; hashes are taken over the exact blob.
* **Loud failures:** invalid YAML, non-string scalars, duplicate keys, dangling/malformed
  identities, declaration-context violations, doc-string imbalance, duplicate artifacts, and type
  prefix mismatches all raise `IngestionError` naming the input.
* **Untrusted input:** YAML uses a safe loader with no object construction; Git arguments use
  `--end-of-options` and NUL-delimited tree output; text is never executed.
* **Offline:** PyYAML is a local library; no network, model, database, or service is involved.
* **Separation:** ingestion still reads artifacts only and cannot create links or evidence.
* **Regression:** full suite, drift check, lint, and the network-denied suite pass.

## Independent review

**APPROVE** — submission 5 of 7, snapshot captured 2026-11-13T01:50Z, reviewer `gpt-6.1-sol` at
`xhigh`, 24/24 manifest hashes confirmed. Verdict and criteria table:
`docs/reviews/DT-01-review-5.md`. No open finding at this snapshot. Commit, PR, CI, and merge state
are recorded separately after landing; this approval does not close #20 by itself.
