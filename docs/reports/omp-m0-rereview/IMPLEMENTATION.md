# M0 re-review — implementation and verification report

**Run:** OMP-led story loop (`prompts/omp-codex-agentic-loop.md`), invoked in this session on
2026-11-11. **Selected task:** reproduce the authorized findings of `docs/reviews/M0-review.md`
(R1–R7, mapped to FT-01 #18 / FT-02 #19 and the relevant M0 platform tasks) and carry the mandatory
independent M0 re-review. **Milestone ceiling:** M0. **Workstream:** shared platform / B lead.
**Coordinator:** OMP v18.18.8; model role `default` = `vllm/deepseek-ai/DeepSeek-V4.1-Flash`
(thinking level `max` per host configuration — see METRICS §deviations). **Reviewer:** `gpt-6.1-sol`,
reasoning effort `xhigh`, read-only sandbox, two fresh sessions.

## Outcome

* **Round 1 (submission 1/7): NEEDS_INPUT.** R1–R7 all dispositioned `repaired` with regression
  tests; AC-1.1…AC-1.8 and AC-2.1…AC-2.5 all `PASS`; one blocking evidence gap raised — **R8**: no
  recorded human review of the hand-labeled oracle (`AGENTS.md` invariant 6). Verdict recorded
  verbatim at `docs/reviews/M0-rereview-1.md`.
* **R8 disposition:** the repository owner's explicit attestation is recorded at
  `docs/reviews/M0-oracle-human-review.md`, tied to the three oracle files' sha256 values at
  revision `191c829` (the owner answered a scoped attestation request directly; OMP records the
  statement, it does not attest the labels itself).
* **Round 2 (submission 2/7): APPROVE** at commit
  `bca69cf14a7c94e9ff29ec860fd28fbef83a0798` (tree `e55ff9f9b2d669d1417ee1e4df0c858817a1eb82`),
  recorded verbatim at `docs/reviews/M0-rereview-2.md`. No open major finding; "The independent M0
  review gate is satisfied for the identified snapshot."
* **M0 independent review gate: satisfied.** Milestone closure itself (undraft/merge PR #38, close
  #18/#19, hosted CI on the push) is a team action. This session made no push and started no M1/M2/M3
  work.

**Approved vs. recorded content.** The approved snapshot is `bca69cf`. The bookkeeping commits that
carry this folder add the round-2 verdict record, the run reports, the verdict-recording status
update, and one lint-scope line in `ruff.toml` (see the commit table below) — none of it changes
product behavior, and `bca69cf` remains authoritative for everything approved.

## Starting state

* Branch `feat/8-m0-foundation` at `191c8292f0492d34582f6e33db3cb6f29be9a9e0`; the R1–R7 repair
  commits were already present (`f3fc265`, `ba2fb05`, `50b3bc4`, `44aef02`, `191c829`);
  `docs/STATUS.md` recorded that the independent re-review had not yet happened.
* Working tree additionally held two unrelated uncommitted edits by the user (`README.md`,
  `prompts/omp-codex-agentic-loop.md`). They were preserved untouched and excluded from every review
  packet (stated in both packets; the reviewer confirmed the exclusion).
* **Environment repair (required to run anything):** the checked-in `backend/.venv` was a stale
  macOS venv (homebrew Python 3.12 paths) with no runnable interpreter on this Linux host, and the
  system Python (3.14.10) has no pip. `uv` 0.13.7 was installed once (network used once for tool +
  interpreter/wheel download) and `uv sync --project backend --frozen` recreated the venv on
  **uv-managed CPython 3.12.16** (CI pins 3.12). All recorded test results then ran offline.

## Changes made by this run (all unpushed)

| Commit | Purpose |
|---|---|
| `5f5d843` | `docs(architecture)`: the R1 repair renamed the store resolver (`FixtureStore.resolve` → `resolve_baseline`); the request-flow paragraph still named the removed helper. Self-review repair, docs only. The message was amended before any push so `git interpret-trailers --parse` validates the `Story:`/`Feature:`/`Workstream:` trailers (loop convention). |
| `bca69cf` | `docs(review)`: round-1 verdict recorded verbatim (`docs/reviews/M0-rereview-1.md`), human attestation recorded (`docs/reviews/M0-oracle-human-review.md`), status updated for the open final verdict. |
| `c0b70fa` | `docs(reports)`: `docs/reviews/M0-rereview-2.md`, this report + prompt log + metrics + evidence + probes + packet templates, and the status update recording the approval. |
| final `chore(lint)` commit | `ruff.toml`: exclude `docs/reports` from lint/format scope. The committed run records are archival evidence with their own manifest; linting them broke the root gate (`ruff check .` failed on the probe scripts) and reformatting them would rewrite evidence bytes — the same reason `fixtures` is excluded. No lint behavior changes for any other path; it is the only non-docs change in the post-approval bookkeeping series. |

No backend, tool, fixture, API, or CI file changed in any of these commits — proven in the round-2
packet by identical `git ls-tree` blob sets (`sha256
4ac34915c1828c52d178943a692ac44a6b250cb20997f369a01b2a43bdbd69bd` for both snapshots) and an
empty `git diff 191c829..HEAD -- backend tools fixtures ruff.toml .github` at that point. The only
non-docs change in the later bookkeeping series is the one-line `ruff.toml` exclusion in the commit
table above.

## Verification performed (R1–R7 probes and gates; snapshots and outputs in `evidence/`)

Frozen round-1 snapshot: `191c829` + the single uncommitted in-scope change `docs/architecture.md`
(sha256 `153d7c6f…e264c02b`). Round-2 reruns on the docs-only snapshot: `evidence2/`.

| Check | Probe / command | Result (observed) |
|---|---|---|
| R1 port | `probe_r1` — `isinstance(store, ArtifactRepository)`; all seven methods through the port | `True`; `get_artifact` OK; accepted links `LNK-001…LNK-006`; `changed_artifacts` = `['CODE-001','TEST-002']` |
| R2 partition | `probe_r2_r4` — model + HTTP with a copied response tree | model raises `ValidationError` naming `accepted_links`; served file → `500 fixture-data-invalid` |
| R3 manifest | `probe_r3` — tampered / deleted manifest via `verify --baselines` | tampered → exit 1 "out of date: …/baselines.json"; deleted → exit 1 "missing from the repository: …/baselines.json" |
| R4 versions | `probe_r2_r4` — `999.0.0` in thread + findings + snapshot | thread/findings → `500 fixture-data-invalid` naming `999.0.0`; snapshot rejected at app construction |
| R5 object format | `probe_r5` — two dirs; forged global `commit.gpgsign` + non-UTC `TZ`; `GIT_DEFAULT_HASH=sha256` | all builds' tags equal the committed manifest (`67109fac…`, `c02064fe…`) |
| R6 mutation | `probe_r6` — clone, `sha256 → sha1` in `finding_fingerprint`, regenerate, run suite | suite now **fails**: 3 failed (all three independent vectors), 104 passed — mutation caught |
| R7 worktree recipe | `probe_r7` — suite from each worktree root; plus the old outside-invocation | baseline-a: 5 passed (exit 0); baseline-b: exactly `test_withdraw_allows_fractional_amounts` + `test_transfer_exactly_at_limit_is_permitted` failed (4 passed); outside invocation still exit 2 collection error |
| Offline suite | `uv run --project backend pytest backend/tests -q` | 107 passed, 1 warning (~3 s); re-run on the final docs snapshot: 107 passed |
| Drift guard | `uv run --project backend python tools/fixturectl.py verify` | exit 0, "fixture generation is reproducible and committed files are current (banking-demo)" |
| Lint/format | `ruff check .` + `ruff format --check .` | `All checks passed!`; `33 files already formatted` |
| Lint after bookkeeping | `ruff check .` + `ruff format --check .` + `git diff --check main HEAD` | clean once `docs/reports` is excluded (the committed probe scripts are records, not sources); whitespace check exit 0 |
| Whitespace | `git diff --check` | exit 0 |
| Network denial | `unshare -rn` + socket probe + suite | socket `OSError: [Errno 101] Network is unreachable` (`NET-DENIED-OK`); 107 passed |
| Live HTTP | uvicorn on 8031 (pristine) and 8032 (tampered copy) | health 200 `0.1.0`; thread `REQ-001@baseline-b` = `LNK-001…003` + `EV-001`; findings set at baseline-b includes `reverification_required` + `verification_failed`; discovery rank-1 `CODE-001` with no `link_id`/`review_state` keys; `POST /api/assurance/evaluate` → 501 `AS-01, AS-02, AS-03 (C-PR1)` / `M1/M2`; artifact tag/SHA bodies identical; 404 `artifact-not-found`; 422 `request-validation`; 404 `baseline-not-found`; tampered server → 500 `fixture-data-invalid` on both negative routes, unaffected thread still 200 |
| Fixture build | `fixturectl.py build` | four identical commit SHAs in order; `baselines.json (unchanged)` |

## Acceptance criteria at the approved snapshot

Round-2 reviewer assessment (retained in full in `docs/reviews/M0-rereview-2.md`): AC-1.1…AC-1.8 and
AC-2.1…AC-2.5 **PASS**; the M0 exit-criteria table (repository layout, setup guide, generator, tagged
baselines, labeled outputs, contracts, OpenAPI examples, fake provider, sample findings, CI workflow,
offline tests, schema-valid mock APIs, independent readiness, review without open major findings)
**PASS**. OMP's own probes independently reproduced the decisive behavior for every criterion (see
table above); `evidence/` carries the raw outputs.

## Remaining work and owners (not started here)

| Item | Owner | Trigger / condition |
|---|---|---|
| Undraft + merge PR #38, close #18/#19 | team (Anthony) | publication action — hosted CI runs on the push; the same gate commands pass locally |
| Hosted GitHub Actions execution | whoever pushes | the CI run itself (NOT VERIFIED locally) |
| M1/M2 streams: B-PR1 (DT-01/DT-02/DT-04), C-PR1 (AS-01/AS-04/AS-05) | B / C | after the branch lands |
| M3 stream: A-PR1 (AI-01) | A | roadmap allows parallel M3 work; not started here |
| General staleness/failure classification beyond labeled fixture cases | C | M2 (AS-02/AS-03) |
| Provider-plugin side-effect freedom | A | M3 (AI-02/AI-04) |

## Reproduce

```bash
uv sync --project backend --frozen
uv run --project backend pytest backend/tests -q                    # 107 passed
uv run --project backend python tools/fixturectl.py verify          # exit 0
uv run --project backend ruff check . && uv run --project backend ruff format --check .
unshare -rn sh docs/reports/omp-m0-rereview/probes/net_denied.sh    # network-denied suite
uv run --project backend python docs/reports/omp-m0-rereview/probes/p_r1_port.py  # and p_r2_r4, p_r3, p_r5, p_r6, p_r7
```

Review packets are reproducible from `docs/reports/omp-m0-rereview/packets/` (templates + recipe);
the full round-1 packet and both Codex call logs are archived outside the repository at
`~/cta-runs/omp-m0-rereview-1/`.

## Verification limits (state honestly; see `docs/STATUS.md` for the list with owners)

Hosted GitHub Actions was not executed; the first review's macOS/Git 2.54 environment was not
re-run; `uv run --offline` under an OS-level network denial was not executed (the venv interpreter
was used under `unshare -rn` instead); no browser/UI check (no frontend in M0); general assurance
classification and provider-plugin side-effect freedom remain out of M0 scope.
