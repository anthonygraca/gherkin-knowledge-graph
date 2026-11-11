# M0 re-review — prompt log and provenance

All times are UTC. "Recorded" means a value captured in a file at call time (see `evidence/` and the
archive `~/cta-runs/omp-m0-rereview-1/`); values not exposed by a tool are marked *unavailable*
rather than reconstructed.

## 1. Invoked prompt

* **File:** `prompts/omp-codex-agentic-loop.md` (working-tree revision of 2026-11-11, sha256
  `0d1519b21ce704042d102d6529ab0ffee2447892d8cb3b6d931dca533afd414a`). The session received the same
  text as its launching attachment; the user did not override any run input.
* **Run inputs in effect:** selected task = reproduce the authorized findings of
  `docs/reviews/M0-review.md` (R1–R7; FT-01 #18, FT-02 #19; M0 platform tasks) and obtain the
  mandatory independent re-review; milestone ceiling = M0; workstream = shared (B lead);
  implementation-review limit = 7 submissions; local commits permitted, no push; continuation = none
  (single task).
* **Deviations from the prompt, recorded (see METRICS for detail):** the loop asks for OMP thinking
  `xhigh`; this session runs at the host's configured `max` level (the `--thinking` flag exists and
  was verified with `omp --help`, but a session's level is fixed by host configuration). `workflowz`
  is not installed. No OMP subagents were spawned (rationale in METRICS). No comparator report was
  supplied.

## 2. Coordinator timeline

| Time (UTC) | Event |
|---|---|
| from 05:10:29 | Recon: git state (`191c829`, branch `feat/8-m0-foundation`, two unrelated user edits), full reads of `AGENTS.md`, roadmap, `docs/STATUS.md`, `docs/stories/M0-foundation.md`, `docs/reviews/M0-review.md` (all 334 lines), `M0-review-prompt.md`, contracts docs, and the repaired source/tests |
| ~05:12–05:14 | Environment: `uv` 0.13.7 installed once (`curl -LsSf https://astral.sh/uv/install.sh \| sh`); `uv sync --project backend --frozen` recreated `backend/.venv` (stale macOS venv removed) on uv-managed CPython 3.12.16; a 3.14.10 collection smoke collected 107 tests before the interpreter was pinned to 3.12.16 for all recorded results |
| ~05:15–05:25 | R1–R7 probes written to `/tmp/cta-rereview-1/p_*.py` and executed (`probe_r1`…`probe_r7`); full gate run (`pytest`, `fixturectl verify`, `ruff check`, `ruff format --check`, `git diff --check`); network-denied suite under `unshare -rn`; live HTTP with two uvicorn services (8031 pristine, 8032 tampered fixture copy); all outputs captured under `evidence/` |
| (before packet 1) | Self-review found `docs/architecture.md` still naming the removed `FixtureStore.resolve()`; fixed in the working tree (later commit `5f5d843`) |
| (packet 1) | `packets/packet_template.md` + snapshot substitutions → `/tmp/cta-rereview-1/review-1-prompt.md`, sha256 `077eaf64d893d392f6baeea736e6ab28a8716e26bd2e6343df3d59827cb5ca3e`, 192,804 bytes, 3,024 lines |
| 05:26:06 → 05:30:49 | **Codex submission 1** (284 s, exit 0, session `01a1c912-1adf-7c21-bd6c-3744561b0a76`, "tokens used 149,880"). Verdict: **NEEDS_INPUT** — R1–R7 repaired, all ACs PASS, blocking R8 (human oracle review missing) |
| 05:43:32 | **User attestation answered** (recorded timestamp): "attested", recorded as "Anthony Graca", no additional note |
| 05:45:19 | Commit `5f5d843` (`docs(architecture)`, message amended pre-push for trailer validation) |
| 05:46–05:47 | Verdict copied byte-identical to `docs/reviews/M0-rereview-1.md`; attestation record written to `docs/reviews/M0-oracle-human-review.md`; `docs/STATUS.md` updated |
| 05:47:23 | Commit `bca69cf` (`docs(review)`) |
| (packet 2) | `packets/packet2_template.md` → `/tmp/cta-rereview-1/review-2-prompt.md`, sha256 `03225153e885f12213c013268b749df43013f07e17f1b33f9cfe9d0bc5d26d39`, 89,237 bytes; embedded round-1 verdict, attestation, incremental diff, blob-hash identity proof, round-2 gates (`evidence2/`) |
| 05:48:17 → 05:51:06 | **Codex submission 2** (169 s, exit 0, session `01a1c926-5f47-7751-b38c-8dc16bdf4c03`, "tokens used 79,482"). Verdict: **APPROVE** at `bca69cf` (tree `e55ff9f`) |
| 05:52:48 | Round-2 verdict copied byte-identical to `docs/reviews/M0-rereview-2.md` (sha256 `08787814859cfc0a1e42e514dec920d430a84b3c8b1da897fc6acf50e5911ac2`) |
| after | Bookkeeping: `docs/STATUS.md` final update and this reports folder; final `docs(reports)` commit (no push) |

## 3. Exact reviewer invocations

```sh
codex exec --model gpt-6.1-sol \
  -c 'model_reasoning_effort="xhigh"' \
  --sandbox read-only --cd "$task_repo" \
  --output-last-message "$task_run/review-1.md" \
  - < "$task_run/review-1-prompt.md"

codex exec --model gpt-6.1-sol \
  -c 'model_reasoning_effort="xhigh"' \
  --sandbox read-only --cd "$task_repo" \
  --output-last-message "$task_run/review-2.md" \
  - < "$task_run/review-2-prompt.md"
```

`task_repo` = the repository root; `task_run` = `/tmp/cta-rereview-1` (archived at
`~/cta-runs/omp-m0-rereview-1/`). Model/effort were preserved explicitly on every call and match the
installed Codex configuration (`~/.codex/config.toml`: `model = "gpt-6.1-sol"`,
`model_reasoning_effort = "xhigh"`). Exit codes, timestamps, session ids and token totals were
written to files at call time (`review-{1,2}-exit-code.txt`, `review-{1,2}-timestamps.txt`,
`review-{1,2}-stderr.log`).

## 4. Attestation request (exact prompt text)

The owner was asked through a single form with the snapshot (`191c829`, tree `29e7ac97…`), the
three oracle files with full sha256 values, and three options. The selected option was:

> **Yes — reviewed, correct as committed.** Record my attestation linked to this revision, then
> submit review 2/7 to clear R8. (The label content: baseline-a findings for
> REQ-002/SCN-002/LNK-007/REQ-003 with healthy REQ-001; baseline-b adds reverification on
> REQ-001/SCN-001/CODE-001 via EV-001 and failure on REQ-003/SCN-003/TEST-002 via EV-003; candidate
> index labels positive/negative.)

Recorded as: `Anthony Graca`, attested at `2026-11-11T05:43:32Z`, note field empty. The resulting
record is `docs/reviews/M0-oracle-human-review.md`.

## 5. Prompts not recoverable in full

* The two packets are reconstructible from `packets/` (templates) plus the recipe in
  `packets/RECIPE.md`; the full round-1 packet text is archived only outside the repository (too
  large to commit here) at `~/cta-runs/omp-m0-rereview-1/review-1-prompt.md` (sha256 recorded in
  METRICS).
* Coordinator-side reasoning text is not part of this log; the actionable content is the recorded
  commands, probes, evidence and decisions above.
