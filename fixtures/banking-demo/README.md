# Fixture: `banking-demo`

A deliberately small synthetic engineering repository used as the project's shared test
oracle. It has real, reproducible Git history with the tags **`baseline-a`** and
**`baseline-b`**; nothing here depends on the commit history of the repository that contains
this fixture.

## Layout

| Path | Provenance | Purpose |
| --- | --- | --- |
| `tree/` | hand-written | Contents committed as the first commit (the baseline-a source state). |
| `changes/02-baseline-a-evidence/` | hand-written | Overlay recorded as the second commit; carries the baseline-a evidence. Tagged `baseline-a`. |
| `changes/03-baseline-b-change/` | hand-written | Overlay recorded as the third commit: the change under evaluation. |
| `changes/04-baseline-b-evidence/` | hand-written | Overlay recorded as the fourth commit; carries the baseline-b evidence. Tagged `baseline-b`. |
| `history.json` | hand-written | Declarative commit list: id, message, date, overlay, tags. |
| `expected/baseline-a.json` | hand-labeled | Findings oracle for `baseline-a`. |
| `expected/baseline-b.json` | hand-labeled | Findings oracle for `baseline-b`, including the change summary. |
| `expected/candidate-links.json` | hand-labeled | Fake discovery index and AI-05 evaluation labels (positive/negative). |
| `expected/baselines.json` | **generated** | Resolved commit SHAs per tag; the reproducibility oracle. |
| `.build/repo/` | **generated** | The nested Git repository (git-ignored). |

`.build/` is git-ignored. Generate everything with:

```bash
uv run --project backend python tools/fixturectl.py all
# or, to check that the committed generated files are still current, and to fail otherwise:
uv run --project backend python tools/fixturectl.py verify
```

## History

Each baseline is two commits: the source state, then the commit that records the CI evidence
for that revision. Evidence records therefore reference the *source* commit that was actually
executed, while the tag points at the evidence commit that contains them — which is why
freshness is decided by comparing **content hashes**, never commit SHAs. Otherwise the
evidence-only commit would look like a source change.

| Commit | Message | Tag |
| --- | --- | --- |
| 1 | Add banking demo sources for baseline A | — |
| 2 | Record baseline A verification evidence | `baseline-a` |
| 3 | Require whole-dollar withdrawals and cover the at-limit transfer boundary | — |
| 4 | Record baseline B verification evidence | `baseline-b` |

The generator pins everything that would otherwise leak in from the caller's environment: author and
committer identity, dates, timezone, git config (global and system config are ignored), the branch
name, and the object format (`sha1`, so a host exporting `GIT_DEFAULT_HASH` cannot change the
baselines). Reproducibility is therefore a property of the fixture, not of the machine.

## Artifacts and conventions

Identity is declared in the artifacts themselves (see `docs/domain-contracts.md`):

* requirement — YAML front matter `id:` in `requirements/*.md`
* scenario — Gherkin tag `@SCN-nnn` on a `Scenario:` in `features/*.feature`
* source / test — first-line annotation `# cta:artifact CODE-nnn` / `TEST-nnn` in `*.py`

Artifacts: `REQ-001`, `REQ-002`, `REQ-003`, `SCN-001`, `SCN-002`, `SCN-003`, `CODE-001`
(`src/accounts.py`), `CODE-002` (`src/transfers.py`), `TEST-001` (`tests/test_accounts.py`),
`TEST-002` (`tests/test_transfers.py`).

Accepted links live in `evidence/accepted-links.json`; pending proposals live in
`evidence/proposed-links.json`, in a separate file with a different review state, so no reader
can confuse a proposal with an accepted relationship.

## Intentional properties (the oracle)

| Case | Property | Where labeled |
| --- | --- | --- |
| 1 | `REQ-001` has a complete accepted chain and a passing run at `baseline-a`; it has no finding there. | `expected/baseline-a.json` (`healthy_artifact_ids`) |
| 2 | `REQ-002` has no accepted verification scenario. | both oracles |
| 3 | `SCN-002` has no accepted implementation link. | both oracles |
| 4 | `CODE-001` changed at `baseline-b` after the `baseline-a` verification of `SCN-001`; no later evidence exists → `reverification_required`, and `REQ-001` is **not** failed. | `expected/baseline-b.json` |
| 5 | `TEST-002` was tightened at `baseline-b` and its recorded run failed → `verification_failed` for `SCN-003`/`REQ-003`. | `expected/baseline-b.json`, evidence `EV-003` |
| 6 | `LNK-007` proposes `REQ-002 verified_by SCN-002` and is still unreviewed → `candidate_pending_review`; no accepted link exists between them. | both oracles, `evidence/proposed-links.json` |
| 7 | `REQ-003` is superseded but still has accepted relationships → `lifecycle_review_required`. | both oracles |

### Known defects, on purpose

* `TransferLedger.transfer` rejects a transfer that reaches exactly the daily limit
  (`>=` instead of `>`). This contradicts `REQ-003`/`SCN-003`. It is a genuine defect in the
  fixture, surfaced by the test tightened at `baseline-b`, so case 5 is a *real* failure and
  case 4 is a *real* gap rather than a manufactured one.
* The change at `baseline-b` to `src/accounts.py` (whole-dollar withdrawals) contradicts
  `REQ-001`/`SCN-001`. Re-running `TEST-001` at `baseline-b` fails, which is why the missing
  run must be reported as reverification, not as a pass and not as a failure.

Both properties are verified by the test suite: `backend/tests/test_fixture_repo.py` runs the
fixture's own tests at both tags and asserts exactly which tests pass and fail.

## Regeneration

Editing any file under `tree/`, `changes/`, or `expected/candidate-links.json` changes the
generated SHAs, the snapshot, and the API samples. Then:

```bash
uv run --project backend python tools/fixturectl.py all
uv run --project backend pytest backend/tests
```

The drift test fails with that instruction when committed generated files are stale. Never
hand-edit `expected/baselines.json` or anything under `fixtures/api-responses/`.
