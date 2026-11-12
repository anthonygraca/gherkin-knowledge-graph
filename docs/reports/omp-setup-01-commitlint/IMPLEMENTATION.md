# SETUP-01 commit-reference enforcement — implementation and verification record

**Task:** resume and complete the SETUP-01 follow-up slice (roadmap `SETUP-01`, GitHub issue
[#8](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/8)): offline commit-format and
issue-map-registration enforcement in CI and locally.

**State at the end of this session (2026-11-12):** the slice is **fully verified locally** on base
`f34ae07` and **BLOCKED on its mandatory independent review** — the Codex submission failed without
a verdict because the workspace has no credits. **No approval exists; the slice is deliberately
left uncommitted.** This checkpoint commit contains only this records folder and `docs/STATUS.md`.

**Review counter:** 0 of 7 submissions consumed (attempt 1 produced no verdict; a launch failure
without a verdict is an infrastructure failure, not an acceptance review).

All times UTC. The claims below were produced by the coordinator (OMP, model
`vllm/deepseek-ai/DeepSeek-V4.1-Flash`); the independent review that would validate them has not
run yet.

## 1. What the slice contains (uncommitted working tree)

| Path | Change |
| --- | --- |
| `tools/commitlint.py` | new; stdlib-only checker: subject format `<type>[(scope)]: [issue #N] <description>`, optional `Refs`/`Closes` body lines, registration against the story/task tables of `docs/traceability-issue-map.md` read **at each checked commit**; exits 0 (pass) / 1 (findings) / 2 (operational, fail-closed) |
| `backend/tests/test_commitlint.py` | new; 28 tests over real temporary Git repositories (incl. a two-parent merge and a `--depth 1` clone) |
| `.github/workflows/ci.yml` | new `commit-reference` job: full-history checkout, actual PR head ref, Python 3.12, no package installs, offline |
| `AGENTS.md`, `CONTRIBUTING.md` | adopt the subject convention; document the gate, the fixed adoption baseline `efa824b…`, PR/push scopes, the synthetic test-merge exclusion, and the required-status-check administration step |
| `docs/stories/SETUP-01.feature` | new canonical criteria, `SCN-301`…`SCN-308` |
| `docs/stories/SETUP-01.md` | new story record with the verification map and the author's record |

## 2. State found, and what changed since the author's record

The previous session recorded verification at `2026-11-11T22:47:40Z` on a tree based on `efa824b…`
with "zero post-adoption commits yet". Since then:

- PR #41 merged into `main`, first as `248108773f4d990c0755a46c6d79a5d0f6d318f42` (GitHub's default
  `Merge pull request #41 …` message), and then the repository owner **replaced that commit** with
  the conforming merge `f34ae0738f3c6e6709f4ba29d12f99348c5cc5b5` ("docs(lifecycle): [issue #39]
  merge the lifecycle traceability change into main"; parents `efa824b…`, `3b25cd1…`; body: "Amended
  subject: the initial merge landed with GitHub's default message, which the commit-reference rule
  rejects."). Push evidence: GitHub Actions push run `43124897661` (main, head `f34ae07…`,
  conclusion `success`, 2026-11-12T00:07:03Z). At resume, `main` == `origin/main` == `f34ae07`.
- Reproduced consequence: the checker **failed on the pre-rewrite tip** —
  `python3 tools/commitlint.py --head 248108773f4d990c0755a46c6d79a5d0f6d318f42` → exit 1,
  `commitlint: 24810877f4d9: expected <type>[optional scope]: [issue #N] <description>; …`
  (`evidence/commitlint-pre-rewrite-tip.log`) — and it **passes on the current history**:
  `commitlint: checked 3 commit(s)` → exit 0 (`evidence/commitlint-default.log`).
- The author record's "zero post-adoption commits" line is therefore superseded by "3 commits
  checked" (`2e9d201`, `3b25cd1`, `f34ae07`, all conforming); all four hashes it recorded still
  match the working-tree files (§4).
- Unrelated dirty work was preserved untouched and is **not** part of this slice: `README.md`,
  `prompts/omp-codex-agentic-loop.md`, `prompts/lifecycle-traceability-handoff.md`.

## 3. Verification executed (base `f34ae07`, dirty working-tree snapshot of §4)

| # | Command (repo root) | Exit | Result | Evidence |
| --- | --- | --- | --- | --- |
| E1 | `uv run --offline --project backend pytest backend/tests/test_commitlint.py -v` (an earlier `-q` run produced the same 28 passes but was not captured) | 0 | 28 passed | `evidence/focused-verbose.log` (28 node IDs) |
| E2 | `uv run --offline --project backend pytest backend/tests -q` | 0 | 135 passed, 1 pre-existing warning | `evidence/suite-full.log` |
| E3 | `unshare -rn -- backend/.venv/bin/python -m pytest backend/tests -q` | 0 | 135 passed under OS-level network denial | `evidence/suite-nonet.log` |
| E4 | `unshare -rn -- python3 -c "<socket probe>"` | 0 | `network denied: [Errno 101] Network is unreachable` (denial effective) | `evidence/nonet-probe.log` |
| E5 | `uv run --offline --project backend python tools/fixturectl.py verify` | 0 | reproducible; committed files current | `evidence/fixture-verify.log` |
| E6 | `uv run --offline --project backend ruff check .` | 0 | all checks passed | `evidence/ruff-check.log` |
| E7 | `uv run --offline --project backend ruff format --check .` | 0 | 35 files already formatted | `evidence/ruff-format.log` |
| E8 | `git diff --check` | 0 | clean | `evidence/diff-check.log` |
| E9 | `python3 tools/commitlint.py` | 0 | checked 3 commits (`2e9d201`, `3b25cd1`, `f34ae07`) | `evidence/commitlint-default.log` |
| E10 | `python3 tools/commitlint.py --message-file <proposed slice message>` | 0 | checked 1 message | `evidence/commitlint-message-ok.log` |
| E11 | `python3 tools/commitlint.py --message-file <body-only reference>` | 1 | rejected: expected subject format (negative case) | `evidence/commitlint-message-bad.log` |
| E12 | `python3 tools/commitlint.py --head 2481087…` | 1 | flags `24810877f4d9` — the rule detects the exact commit the owner repaired | `evidence/commitlint-pre-rewrite-tip.log` |
| E13 | `python3 tools/commitlint.py --head <mistyped 41-char SHA>` | 2 | `fatal: Needed a single revision` — missing revisions fail closed, not silently pass | `evidence/commitlint-missing-revision.log` |

Environment (`evidence/env.log`): Linux x86_64, Python 3.12.16 (backend venv), uv 0.13.7,
git 2.56.0; OMP 18.18.9; codex-cli 0.167.1. Evidence scope: this Linux/Python environment only.

## 4. Snapshot identity (in-scope files at review freeze)

| Path | SHA-256 |
| --- | --- |
| `AGENTS.md` | `468d2d2bd4fe3cd4f473c8c3de406108147b68ea21061aea200134133c9cd8a6` |
| `CONTRIBUTING.md` | `64ee54c3cff5e3cd10b5554b977db24466c8e9a6831cdf08eb7595732777151a` |
| `.github/workflows/ci.yml` | `72a99fe2f0a45e24d1709b7b9e9a1840d32a2236876ae448d82163aa987b2cdd` |
| `tools/commitlint.py` | `e39e523cba087db8ca97f9fbdc138bc476028b650ab00359aa15ffbe98714c29` |
| `backend/tests/test_commitlint.py` | `12cb9504cde7fdfcd7a3dc394bd85978e03c7b58b46a7fabf0cc6a0c38431620` |
| `docs/stories/SETUP-01.feature` | `db2c154567aa96c9492de684c8fccc0b63488ff750987b456a99a7fc97b9c70f` |
| `docs/stories/SETUP-01.md` | `ea742d4b78265a4cc69a56e380fb3e5bab28c51efefd592091e95deb3eac0840` |

Preserved, deliberately outside the slice: `README.md`
(`93b29debd0da44b249eb01d4acea34f9cc8d4f1cb5fbea77ff31dcba9ddfd419`),
`prompts/omp-codex-agentic-loop.md`
(`90dbf541fee77796e6f78dbd5250005d01060d4e298599e297ca5e218719ea1d`),
`prompts/lifecycle-traceability-handoff.md`
(`7e54d0b1e6a16d45472e7195ed15ff36c28f8c5b99546a864d31527b2f8987e1`). The full dirty-tree manifest
is `evidence/manifest.json`.

## 5. Mandatory independent review — attempt record

- **Packet:** `packets/review-1-prompt.md` (committed sanitized copy, sha256
  `264ca338de97e363b73a10689f07443621d101ed6fa20d4d513feae7b01ed245`; the copy sent to the reviewer
  is `/tmp/cta-omp-setup-01/review-1-prompt.md`, 49,619 bytes, sha256
  `2c684345a35370199ece5dbf6f9b7ae2f2daf82ae0aa797aa31032e784388315`; the only difference is the
  `<task_repo>` path substitution).
- **Invocation (exact):**

  ```sh
  codex exec --model gpt-6.1-sol \
    -c 'model_reasoning_effort="xhigh"' \
    --sandbox read-only --cd "$task_repo" \
    --output-last-message "$task_run/review-1.md" --json \
    - < "$task_run/review-1-prompt.md"
  ```

- **Result:** exit 1 at `2026-11-12T00:26:39Z`–`00:26:43Z` (~4 s). stdout JSONL:
  `thread.started` (`01a1cd26-45e3-7e62-ae31-39ea58ebdb17`) → `turn.started` →
  `error: "Your workspace is out of credits. Ask your workspace owner to refill in order to continue."`
  No `review-1.md` was produced; stderr empty. Evidence: `evidence/review-1-stdout.jsonl`,
  `evidence/review-1-stderr.log`.
- **Health check:** `codex doctor` at `2026-11-12T00:34:30Z` — 21 ok · 1 note · 0 warn · 0 fail;
  auth configured (ChatGPT), websocket HTTP 101, endpoints reachable. The failure is the workspace
  credit state, not transport, auth, installation, or configuration. Evidence:
  `evidence/codex-doctor.txt` (trimmed; full output in the archive).
- **No substitution:** same model/effort as specified (`gpt-6.1-sol`, `xhigh`), no self-approval, no
  alternative reviewer, no retry (unchanged condition).

## 6. Commit state and next actions

- Branch `ci/8-commit-reference-enforcement` (from `f34ae07`). This checkpoint commit contains only
  `docs/reports/omp-setup-01-commitlint/` and `docs/STATUS.md`. The slice files remain uncommitted
  at the §4 hashes. No push, no PR (local-only authorization).
- **Next exact action** (after credits are refilled, or after the user authorizes a different
  reviewer — the coordinator will not substitute silently):

  1. Rerun the recorded `codex exec` command against `packets/review-1-prompt.md`.
  2. On `APPROVE`: commit the slice as `ci(traceability): [issue #8] enforce commit references in CI`
     (message validated at E10) plus the review record; on `REQUEST_CHANGES`: repair, re-verify,
     resubmit (≤ 7 submissions total); on `NEEDS_INPUT`: answer and resubmit.
  3. After the slice commit: `python tools/commitlint.py --base f34ae07 --head HEAD` (range audit)
     and record its output.

## 7. Not run / limits

- Hosted CI execution of the new `commit-reference` job — the workflow is not landed; prior CI runs
  verify only the previous workflow.
- Required-status-check branch protection — a repository administration step, not code.
- Independent review — BLOCKED (no verdict, §5).
- The author record's macOS / Git-2.54 environment (accepted limitation; not reproduced here).

## 8. Follow-ups (outside this slice)

- `README.md` (preserved dirty): its commit example predates the new subject convention and its
  status text predates the M0 re-review approval; it needs its own work item before landing.
- Tracker closure of #18/#19 (team action; the M0 approval itself is recorded).
- FT-03 / draft project-definition owner review remains outstanding; it does not change the M0
  approval.

## 9. Review round 1 (submission 1) and dispositions

- **Attempt 1** (2026-11-12T00:26:39Z, ≈ 4 s): no verdict — workspace out of credits (§5).
- **Attempt 2** (2026-11-12T03:37:53Z → 03:44:42Z, 409.7 s, exit 0, session
  `01a1cdd5-57e9-76a2-b48a-9a6dae4e4674`): packet v1.1 (v1 + `packets/review-1-addendum.md`); usage
  1,354,752 input (1,254,528 cached) / 17,233 output (11,763 reasoning). **Verdict: REQUEST_CHANGES**
  — all eight scenarios PASS; R1 (major, blocking) and R2 (minor, nonblocking). Full record:
  `docs/reviews/SETUP-01-review.md`; raw verdict sha256
  `257acec1b808910cb46fc0e1c62b8172bf470352f2cf62eea18356e42bf2b882`.
- **R1 — repaired.** GitHub's default `pull_request` activity types are `opened`, `synchronize`,
  and `reopened`; a retargeted base fires `edited`, so the newly applicable range was never
  re-checked. `.github/workflows/ci.yml` now declares
  `types: [opened, synchronize, reopened, edited]`, and `CONTRIBUTING.md` states the retargeting
  behavior. Recheck: `probes/r1_two_base_repro.py` shows the same head passing when the unlinked
  ancestor is excluded by the base (exit 0) and failing when the adoption baseline is the base
  (exit 1, flagging `65daeff2…`) — `evidence/repair1-r1-repro.log`; the trigger structure is
  validated with PyYAML — `evidence/repair1-yaml-check.log`. Hosted event execution remains a
  publication follow-up.
- **R2 — repaired (records only).** `evidence/issue8-verified.log` attaches the successful `gh`
  verification; the retained `evidence/issue8.log` is unmodified — its exit-4 failure was the eval
  subprocess lacking `GH_TOKEN`, explained by the erratum in `PROMPT_LOG.md` §5. The E1 row above
  now names the captured `-v` invocation.
- **Resubmission (submission 2 of 7) → APPROVE.** Reviewed snapshot v2 (HEAD `a82e466` plus the
  frozen tree; the reviewer confirmed all seven slice hashes and the 34-file manifest, sha256
  `34ebf5c37dd17bf863c57589406f41e99252e821087df5127c17bf11806720e1`). R1 closed — independently
  re-verified by the reviewer (YAML plus the unchanged-head/two-base reproduction); R2 closed on
  record provenance; all eight scenarios PASS; no new blocking finding. Verdict record:
  `docs/reviews/SETUP-01-review-2.md` (committed copy sha256
  `11571c21146e8fdfa195174591b88ee82a0a8c928f01fefe4e87a5316ee44818`). NOT VERIFIED (publication
  follow-ups): hosted execution including the `edited` trigger; required-status-check configuration;
  the post-commit `--base f34ae07 --head HEAD` audit.
- **Commits after approval:** slice `37135cf`
  (`ci(traceability): [issue #8] enforce commit references in CI`, 7 files); the review-record pair
  (`docs(review)`); reports and this file (`docs(reports)`). The slice was unpushed at commit time;
  publication followed the owner's explicit grant (§10).

## 10. Publication (owner-authorized 2026-11-12)

- Branch pushed `2026-11-12T05:00:55Z`: `git push -u origin ci/8-commit-reference-enforcement`
  (`df0f376` on the remote).
- **PR #42** opened: https://github.com/anthonygraca/gherkin-knowledge-graph/pull/42 —
  title "SETUP-01: Enforce commit references in CI", base `main`, head `df0f376`, not a draft,
  `MERGEABLE`; body carries `Refs #8` (no `Closes`).
- Hosted checks (run `43158573099`, 15 s total): **Commit references — pass** (4 s; the new job
  validated the head-vs-base range hosted for the first time) and **Offline contract, fixture, and
  API tests — pass** (11 s). Verified `2026-11-12T05:01:56Z`.
- Still NOT VERIFIED / owner actions: merge (requires the owner's merge with a conforming subject),
  issue closure (#8 stands open; the M0 tracker items #18/#19 likewise), the `edited` retargeting
  path itself, and making **Commit references** a required status check.
