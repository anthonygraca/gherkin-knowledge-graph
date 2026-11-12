# SETUP-01 commit-reference slice — task retrospective

**Task:** resume, verify, review, and land the SETUP-01 commit-reference enforcement slice
(roadmap `SETUP-01`, [issue #8](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/8)).
**Run:** OMP-led loop (task mode) + Codex acceptance review, 2026-11-12.
**Outcome:** approved in review round 2 (submissions 2 of 7) and landed via PR #42
(`d4af73a`, hosted push run `43161043845` success; issue #8 deliberately still open).

## Outcomes and resources

| Measure | Value |
| --- | --- |
| Review submissions | 2 of 7 (attempt 1 = infrastructure failure, no verdict; round 1 REQUEST_CHANGES; round 2 APPROVE) |
| Confirmed findings | 1 blocking (R1: missing `edited` pull-request activity) + 1 nonblocking records finding (R2); both repaired |
| Rework | one repair cycle (R1 trigger fix + recheck probe + YAML validation); record corrections for R2 |
| Codex calls | 3 attempted, 2 completed; cumulative 2,168,919 input tokens (1,971,840 cached) / 25,757 output (15,085 reasoning); cost unavailable |
| Local commits | checkpoint `a82e466`; slice `37135cf`; review records `3bdd476`; run records `df0f376`; status `e4d3f52`; merge `d4af73a` |
| Verification | 28 focused / 135 full / 135 network-denied passing; fixture verify, ruff, `git diff --check`, commitlint modes all exit 0; committed blobs equal the reviewed hashes |
| Wall time | ≈ 00:11Z–05:23Z with a ≈ 2.9 h user pause (credits refill) |

## What went well

- **Resume against ground truth.** Reconciled the status document and the author's record against
  the tree; all recorded artifact hashes matched; stale claims were superseded with evidence rather
  than rewritten. When the owner rewrote `main` mid-session (`2481087` → `f34ae07`), the change was
  adopted and recorded instead of relitigated.
- **The review gate earned its cost.** R1 (a bare `pull_request:` trigger omitting `edited`, so a
  retargeted PR never re-checks its new base) was invisible to the 28 tests, ruff, and the fixtures;
  it required event-semantics reasoning over the real workflow. No local check could have caught it.
- **Gate integrity under failure.** The credit outage produced no substitution and no self-approval;
  the slice stayed uncommitted, the failure was recorded as infrastructure (consuming no
  submission), and the checkpoint preserved everything needed to resume.
- **Reproduction in both directions.** The checker's rejection of the pre-rewrite merge message was
  reproduced with the tool itself, and R1's same-head/two-base behavior was reproduced with a
  throwaway probe before the fix.
- **End-to-end evidence identity.** Frozen packets with hashes; the reviewer independently confirmed
  the 34-file manifest (`34ebf5c3…`); committed blobs were re-verified equal to the reviewed
  snapshot. The repo's own rule then audited the repo's own commits.

## What went poorly

- **Records drifted from actions — the project's own cardinal sin.** `-q` recorded where the
  captured log was `-v`; a PROMPT_LOG success claim alongside a retained failing capture (both
  found as R2); "no user pauses" written before a pause; "unpushed"/"prepared but not opened"
  written before publication. Each was caught and amended, but every one is the error class this
  project exists to detect.
- **Unearned capability.** The ruleset offer preceded the capability check; the PAT lacks
  `Administration: write`, so the first call failed 403.
- **Wrong-tool auth boundary.** A `gh` capture inside the eval kernel (no `GH_TOKEN` there) cost a
  failed attempt and directly caused one R2 record discrepancy.
- **Cost slope.** ~2.17M input tokens for a 137-line tool and 173-line test file; round 2
  re-embedded unchanged full file contents even though hash identity already proved nothing changed.
- **Self-inflicted noise.** A mistyped 41-char SHA in the first fail-closed probe (re-run,
  overwriting the capture); a fabricated hash suffix in a final integrity script that printed a
  false "MISMATCH" before re-verification.

## What to do better

These are now binding run rules in [`prompts/omp-codex-agentic-loop.md`](../../../prompts/omp-codex-agentic-loop.md)
("Run rules added after the first task"):

1. Capture-first records — cite the file captured at call time; never overwrite a capture.
2. Time-qualified claims — no pending/future state in committed records without an as-of stamp.
3. Credential and capability preflight before offering or attempting GitHub writes.
4. Fetch before narrating — confirm remote refs before state narratives, re-confirm after pauses.
5. Packet economy from round 2 — hash-pinned pointers for already-verified unchanged files.
6. Event-semantics self-review for CI-affecting changes (tests cannot cover triggers).
7. Exercise new gates against reality (real target history, hosted where feasible) before landing.
8. Close every task with a short retrospective; fold its items into the rules.

## Open items at the time of writing

- Required-status-check ruleset for `main` (payload prepared; blocked on `Administration: write`).
- The `edited` retargeting trigger path itself has not been exercised hosted.
- Tracker closure of #18/#19; issue #8 stays open by design (`Refs`, not `Closes`).
- FT-03 / draft project-definition owner review; the uncommitted README rewrite needs its own work item.
