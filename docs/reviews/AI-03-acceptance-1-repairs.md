# AI-03 acceptance review 1 — repair record

**Snapshot:** cumulative close-out working tree based on `827e487`; final local suite and report
paths are recorded in `docs/reports/omp-closeout/evidence/`. Hosted CI is recorded on the close-out
PR when it exists.

| Finding | Disposition | Evidence |
|---|---|---|
| **AI03-ACC-R1** — structurally valid corrupt manifests were served | Repaired. `_read_snapshot_file` requires a canonical `snapshot-sha256-…` filename and a matching binding, validates the stored repository name, resolves the manifest baseline to a canonical baseline and commit, and rejects a mislabeled/cross-baseline manifest. It recomputes the configuration digest, corpus cache key, and snapshot binding, and exact-binding refresh passes the requested baseline. `manifests()` omits non-canonical/corrupt files instead of serving them. | `backend/app/retrieval/lifecycle.py`; `test_corrupt_manifest_is_not_served`, `test_repository_and_mislabeled_baseline_are_not_served`, `test_arbitrary_snapshot_filename_is_not_listed_or_served`; SCN-3301/3304. |
| **AI03-ACC-R2** — pointer publication failure left a usable snapshot | Repaired. The snapshot is written to an isolated staging directory; readers take the lifecycle lock and cannot observe it until the pointer is committed and the snapshot is atomically moved into `snapshots/`. Pointer failure removes staging and restores the previous pointer; the previous-pointer read happens inside the typed boundary before staging; snapshot and pointer storage failures are `RetrievalUnavailable`; a retry succeeds. | `backend/app/retrieval/lifecycle.py`; `test_publication_is_invisible_until_pointer_commit`, `test_snapshot_write_failure_is_typed`, `test_pointer_read_failure_is_typed_and_leaves_previous_publication`, `test_pointer_failure_rolls_back_snapshot`, `test_retry_after_pointer_failure_succeeds`; SCN-3304/3305. |
| **AI03-ACC-R3** — elapsed time excluded key construction | Repaired. The clock starts before `_resolve` and key construction for a new publication; exact-binding hits retain their historical measurement. | `backend/app/retrieval/lifecycle.py`; `test_elapsed_includes_key_construction`; SCN-3405. |

**Residual risk:** publication is transactional within one local filesystem and process; it does not
claim crash consistency across a power loss. The accepted limitation is stated in the companion.
