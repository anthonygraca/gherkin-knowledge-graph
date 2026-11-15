# AI-03 acceptance review 1 — repair record

**Snapshot:** cumulative close-out working tree based on `827e487`; final local suite and report
paths are recorded in `docs/reports/omp-closeout/evidence/`. Hosted CI is recorded on the close-out
PR when it exists.

| Finding | Disposition | Evidence |
|---|---|---|
| **AI03-ACC-R1** — structurally valid corrupt manifests were served | Repaired. `_read_snapshot` validates the filename/binding name, derives the manifest baseline from the file name, rejects a requested binding whose baseline or endpoint/content hashes disagree, recomputes the corpus cache key from the stored settings and current corpus content, and rejects a configuration digest mismatch. `manifest_for` catches the refusal instead of serving it. | `backend/app/retrieval/lifecycle.py`; `test_corrupt_manifest_is_not_served`; SCN-3401/3403. |
| **AI03-ACC-R2** — pointer publication failure left a usable snapshot | Repaired. The immutable snapshot is written first, baseline/publication state is tracked, and pointer publication failure rolls back the snapshot and restores the previous pointer. A retry publishes baseline-b and recovery works. Storage failure is typed `RetrievalUnavailable`. | `backend/app/retrieval/lifecycle.py`; `test_pointer_failure_rolls_back_snapshot`, `test_pointer_failure_writes_no_pointer`, `test_retry_after_pointer_failure_succeeds`; SCN-3405. |
| **AI03-ACC-R3** — elapsed time excluded key construction | Repaired. The clock starts before `_resolve` and key construction for a new publication; exact-binding hits retain their historical measurement. | `backend/app/retrieval/lifecycle.py`; `test_elapsed_includes_key_construction`; SCN-3405. |

**Residual risk:** publication is transactional within one local filesystem and process; it does not
claim crash consistency across a power loss. The accepted limitation is stated in the companion.
