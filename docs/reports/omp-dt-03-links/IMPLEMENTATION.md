# DT-03 implementation record — typed, provenance-aware links with review state

| Field | Value |
| --- | --- |
| Story | DT-03 — [#22](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/22), verified OPEN 2026-11-13T02:50:26Z (`gh issue view`, milestone "M1 — AI-free vertical slice") |
| Canonical criteria | [DT-03.feature](../../stories/DT-03.feature), sha256 `d6e390d908616388cbc69ae2dbabd5371ef6a15115a83b447f7696dbf6c83200` |
| Brief / verification map | [DT-03.md](../../stories/DT-03.md) |
| Branch / base | `feat/22-dt-03-links` from `590e776b67d9e340f9e68df04472222ee4fd0720` (DT-02 merge) |
| Contract version | `SCHEMA_VERSION = 0.1.0`, `PACKAGE_VERSION = 0.1.0` (validation only; no shape change) |
| Submission | **2 of 7** — round 1 REQUEST_CHANGES, round 2 **APPROVE** (2026-11-13T03:08Z; R1–R3 closed) |
| Snapshot captured | 2026-11-13T03:01Z (approved snapshot) |

## What changed

| Path | sha256 | Purpose |
| --- | --- | --- |
| `backend/app/domain/enums.py` | `a2464c7f2edba85f8af1dac6af24efc4a05693fef6188ab6948fb2be4cb554c2` | Adds `RELATION_DIRECTION`, the executable direction contract |
| `backend/app/domain/oracle.py` | `679eea69414764999a4770725c01000521bbd508135840359ae5949e297e7889` | `FixtureLinkFile` rejects duplicate ids within a file |
| `backend/app/ingestion/__init__.py` | `3282cea94ca923a47571127b7b0a69c7ee89313ef7014458f48f8dd55ed57397` | Exports `IngestedRevision` / `ingest_revision` |
| `backend/app/ingestion/links.py` | `3c284b7e421182507ff0b7443b3b1ff036553ec8dc8b0ad1fdfaa497704f4aed` | Reads and validates accepted/proposed link files; state errors name affected links |
| `backend/app/ingestion/revision.py` | `0e954a7de6b29700eeb53da38e4ade983428193386a7ccb99fc149b75f0e8e06` | Assembles one revision's artifacts + links |
| `backend/tests/test_ingestion_links.py` | `f4ef0b02e4d51b1f1712b527fb69aed92e00cf75a44279a27e878e8c3289acc9` | Eleven link-ingestion tests (within/across-file duplicates, state diagnostics) |
| `docs/stories/DT-03.feature` | `d6e390d908616388cbc69ae2dbabd5371ef6a15115a83b447f7696dbf6c83200` | Canonical criteria (SCN-601…606) |
| `docs/stories/DT-03.md` | `aa2560a7838af3ae1134ba934d61d8758ce9936c90ddab89a60bf56ea4d4290c` | Brief, assumptions, verification map |
| `docs/domain-contracts.md` | `824a17b8ba243530036b61dbe12dda59caad65d5fd8102056b8c0669b66ab666` | Documents link validation and duplicate ids |
| `docs/architecture.md` | `f2157cad7d2b7b3518f950cc46787bad7c098d977fbc3bf66753b59d39a4d303` | Ingestion status includes links |
| `docs/STATUS.md` | `45a2af82317439f53a169ac595547acc55640c2220158eb151d3ba2bfde9b8c8` | DT-02 landed; DT-03 active |

Generated fixtures, oracle labels, generated responses, and the API are untouched.

## Review round 1 — REQUEST_CHANGES (submission 1 of 7)

Reviewer: Codex `gpt-6.1-sol`, `xhigh`, read-only; session `01a1d2d4-9cc6-7dd2-b772-761f67718f7f`;
2026-11-13T02:55:11Z → 02:58:57Z (226.49 s), exit 0; 14/14 task hashes matched.
Verdict: `docs/reviews/DT-03-review.md`.

| Finding | Severity | Repair | Recheck |
| --- | --- | --- | --- |
| DT03-R1 the file-level review-state error omitted the affected link ids (SCN-605) | medium, blocking | The error names the file, the expected/declared state, and the sorted affected link ids; the test asserts the filename and `LNK-902`, and a proposed member inside an accepted file is separately rejected naming that link | `test_file_with_the_wrong_review_state_is_rejected`, `test_a_proposed_member_in_an_accepted_file_is_rejected_naming_the_link` |
| DT03-R2 the packet's `scan.py` dependency pointer was stale (DT-01 hash instead of the DT-02 file) | medium, blocking evidence | Corrected to `2a602ee3668bd1560e42aa8870c6a1875b3977a082d449109892852c73e0a613` in submission 2; no implementation change | manifest check in the resubmission |
| DT03-R3 the duplicate-id mapping claimed cross-file coverage the test did not exercise | low, nonblocking | Added a cross-file duplicate test and corrected the brief/record | `test_duplicate_link_ids_across_files_are_rejected` |

The packet inconsistency was an evidence-identity defect, not a source edit; the resubmission's
manifest is the corrected snapshot.

## Review round 2 — APPROVE (submission 2 of 7)

Reviewer: same model/effort and read-only sandbox; session `01a1d2dd-1cec-7fd0-8ef7-7e37d26fb065`;
2026-11-13T03:04:28Z → 03:08:26Z (238.29 s), exit 0; 16/16 task hashes and all three dependency
hashes matched. Verdict: `docs/reviews/DT-03-review-2.md`.

* R1–R3 closed; no open blocker.
* SCN-601…606, schema/duplicate/absent-file boundaries: PASS.
* Invariants inspected as passing: proposal/acceptance separation, read-only ingestion, existing
  port behavior, offline defaults, and generated-file discipline.
* Independently replayed 11 mapped link checks and 34 domain/provider/port tests; retained logs
  support 219 passes in both normal and network-denied runs.

Approval covers the identified snapshot. It does not attest human labeling, human link decisions,
refinement sign-off, stakeholder acceptance, or M1 completion.

## Acceptance results

| Criterion | Check | Result |
| --- | --- | --- |
| SCN-601 accepted provenance | `tests/test_ingestion_links.py::test_ingested_links_match_the_committed_snapshot` (all accepted links, both baselines) | PASS |
| SCN-602 proposal separation | `::test_proposals_are_ingested_separately` | PASS |
| SCN-603 wrong direction | `::test_wrong_relation_direction_is_rejected` (names `requirement -> scenario`) | PASS |
| SCN-604 unknown endpoint | `::test_link_to_unknown_artifact_is_rejected` (names `SCN-999`) | PASS |
| SCN-605 wrong file state | `::test_file_with_the_wrong_review_state_is_rejected` (file + LNK-902), `::test_a_proposed_member_in_an_accepted_file_is_rejected_naming_the_link` | PASS |
| SCN-606 repeated ingestion | `::test_repeated_ingestion_returns_identical_links` | PASS |
| DoD duplicate ids | `::test_duplicate_link_ids_are_rejected` (within a file), `::test_duplicate_link_ids_across_files_are_rejected` (across accepted/proposed) | PASS |
| DoD schema version | `::test_unsupported_link_schema_version_is_rejected` | PASS |
| DoD absent files | `::test_absent_link_files_are_empty` | PASS |

Axis coverage: success (601), separation (602), failure (603/604/605/schema/duplicates), boundary
(absent files), stability (606).

## Commands and outcomes (as captured)

```text
captured_start=2026-11-13T03:00:50Z
pytest backend/tests -q                          exit 0  219 passed, 1 warning in 5.88s
fixturectl.py verify                             exit 0  reproducible and committed files current
ruff check .                                     exit 0  All checks passed
ruff format --check .                            exit 0  all files formatted
git diff --check                                 exit 0
captured_end=2026-11-13T03:00:58Z

network denial at 2026-11-13T03:00:58Z: `unshare -rn backend/.venv/bin/python -m pytest
backend/tests -q` → exit 0, 219 passed.
```

Raw logs are in the external run directory `…/m1-roadmap-20261112/dt-03/`.

## Self-review

* **Proposal/acceptance separation:** two files, two collections; a wrong file state or a duplicate
  id is rejected; no code path merges or promotes proposals.
* **Direction and endpoints:** `RELATION_DIRECTION` is the single executable table; unknown
  endpoints and type mismatches fail ingestion instead of producing a plausibly typed edge.
* **Revision-aware:** links are read from the resolved commit; repeated ingestion is identical.
* **No mutation:** ingestion is read-only; append-only review decisions remain AS-06.
* **No contract change:** models/enums already existed; this adds validation. `fixturectl verify`
  confirms no generated bytes changed.
* **Offline:** local Git and JSON only; network-denied suite passes.

Known limits: review writes/history are AS-06 (M3); evidence ingestion and thread assembly are
DT-04; candidate proposals from discovery are not links until recorded (ADR 0004).

## Independent review

**APPROVE** — submission 2 of 7, snapshot captured 2026-11-13T03:01Z, reviewer `gpt-6.1-sol` at
`xhigh`, 16/16 task hashes and three dependency hashes confirmed. Verdict:
`docs/reviews/DT-03-review-2.md`. No open finding at this snapshot. Commit, PR, CI, and merge state
are recorded separately after landing; this approval does not close #22 by itself.
