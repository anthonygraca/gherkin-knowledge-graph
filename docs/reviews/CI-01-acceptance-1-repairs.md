# CI-01 acceptance review 1 — repair record

**Snapshot:** `4df96be` (submission 1) repaired on the feature branch; the acceptance reviewer's
findings are in `docs/reviews/CI-01-acceptance-1.md`. This is an author disposition, not evidence;
the code, tests, and retained reports are the evidence.

| Finding | Disposition | Evidence |
|---|---|---|
| **CI01-ACC-R1** — rejected destinations still reached the writer | Repaired. Destination validation happens before output clearing/evaluation; the diagnostic handler receives `None` for a forbidden destination and prints JSON on stderr. No write is attempted inside the evaluated fixture/repository. | `tools/assurance.py` `_outside`/`safe_report`/`_diagnostic`; manual forbidden-path probe. |
| **CI01-ACC-R2** — unwritable destination retained an old completion | Repaired. The CLI clears the report/manifest destinations before evaluation (and truncates a destination it cannot unlink); the BDD bridge no longer pre-deletes outputs. A failed run cannot leave an earlier completed report at the destination. | `_clear_outputs`; `write_report`; BDD bridge cleanup only for the diff output. |
| **CI01-ACC-R3** — summary failure rewrote the evaluator outcome | Repaired. Summary publication is handled separately after the completed report is written; a publication failure exits 2 with `publication-failed` and preserves the completed report/finding set. | `tools/assurance.py` summary blocks; direct probe with a directory as `--summary`: exit 2, completed report retained. |
| **CI01-ACC-R4** — incomplete diagnostics lost provenance/classification | Repaired. Inputs are retained as processing progresses; missing execution report/metadata entries are recorded as unavailable with null digests; unknown self-assurance revisions classify as `resolution`/`revision-unknown`; write failures retain the collected inputs. | `collected_inputs`; missing-report/metadata branches; registry index boundary; direct probes. |
| **CI01-ACC-R5** — skipped coverage hard-coded to zero | Repaired. `scenarios_skipped` is counted from imported `ExecutionOutcome.SKIPPED`; `scenarios_unknown` is the remaining unexecuted/unskipped indexed scenarios. | `tools/assurance.py` `Coverage` construction. |
| **CI01-ACC-R6** — banking did not upload its stderr diagnostic | Repaired. The banking job captures stderr to `banking-diagnostic.json` and uploads it with the report/manifest under `if: always()`; the self job already did. | `.github/workflows/ci.yml` `banking-assurance`. |
| **CI01-ACC-R7** — hosted evaluator identifier omitted the package version | Repaired. The hosted jobs no longer pass a hand-written identifier; the CLI records `cta@<package-version>+<commit>` via `evaluator_revision()`. | `.github/workflows/ci.yml`; `tools/assurance.py`. |
| **CI01-ACC-R8** — final evidence hashes stale | Repaired. `final-run-hashes.txt` is regenerated from the final report/inventory after the post-repair full suite. | `docs/reports/omp-closeout/evidence/final-run-hashes.txt`. |

**Verification:** final full acceptance suite 203 scenarios / 1972 steps passed; GT-02 recheck 3/3;
backend 553 passed / 4 skipped; strict gate, fixture verify, Ruff and format clean. Hosted CI on the
repaired head is recorded on PR #78; the reviewer must observe it.

## Second acceptance pass (submission 2)

- **CI01-ACC-R2:** the hosted workflow now writes reports, manifests, and diagnostics under a
  run-unique `$RUNNER_TEMP/assurance/${GITHUB_RUN_ID}-${GITHUB_RUN_ATTEMPT}` directory; a previous
  run's completion is never the publication path. The CLI still clears/truncates a reused
  destination, but if the filesystem denies removal, truncation, and replacement, no process can
  invalidate that inode; the contract's publication safeguard is the fresh run path, not a claim that
  an immutable path can be rewritten.
- **CI01-ACC-R4:** execution-report and provenance-sidecar inputs are registered before reading; a
  permission/read failure is `input`/`input-unreadable` with `available=false`/`digest=null`.
  Fixture-manifest read/store failures retain the unavailable `fixture_manifest` input. Mixed
  malformed-provenance failures retain the already readable report entry.
- **CI01-ACC-R5:** coverage uses disjoint scenario keys: executed keys are those with a passed/failed
  execution, skipped keys are skipped-only definitions, and unknown is the indexed total minus their
  union. A mixed outline no longer counts one definition in both buckets.
- **Late banking manifest failure:** the artifact/link/evidence/policy inputs are built before the
  manifest digest is read; a manifest read failure appends an unavailable `fixture_manifest` entry
  and retains all known inputs.
