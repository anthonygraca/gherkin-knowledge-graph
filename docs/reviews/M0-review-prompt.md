# Prompt: independent review of Milestone M0

Copy the block below into a fresh agent session in this repository. It is written to be
self-contained: the reviewer should not need this conversation's context, and should not trust any
summary of the work — including this one.

---

You are reviewing a completed milestone of **Continuous Traceability Assurance (CTA)**, a
Gherkin-based digital thread connecting requirements, Gherkin scenarios, source code, tests, Git
revisions, and verification evidence. Three workstreams develop it in parallel: A (semantic
discovery), B (ingestion/digital thread), C (assurance/UI).

**Your job: adversarially verify Milestone M0 ("contract + fixture foundation"). Do not implement
fixes, do not write new features, and do not review the roadmap's ambitions.** Report only findings
you can back with evidence you produced yourself.

## Read first

1. `CONTINUOUS_TRACEABILITY_ROADMAP.md` — the plan (esp. §4 domain contract, §5 fixture oracle,
   §7 M0 exit criteria, §9 quality gates).
2. `docs/stories/M0-foundation.md` — the acceptance criteria and exit-criteria evidence table for
   M0, including AC-1.1…AC-1.8 and AC-2.1…AC-2.5.
3. `AGENTS.md` — the invariants the code is supposed to uphold.
4. `docs/architecture.md`, `docs/domain-contracts.md`, `docs/api-contracts.md`, `docs/STATUS.md`.
5. The implementation: `backend/app/**`, `backend/tests/**`, `tools/fixturectl.py`,
   `fixtures/banking-demo/**`, `fixtures/api-responses/**`, `.github/workflows/ci.yml`.

## Ground rules

* Evidence over reading: for every claim below, run something. Quote the command and its output.
* Do not accept a doc's assertion, a test's existence, or a comment as proof of behaviour.
* Treat the hand-labeled oracle (`fixtures/banking-demo/expected/*.json`) as the specification, and
  the code as the thing on trial — but check that the oracle itself is labeled by a human and not
  derived from the code.
* If a claim cannot be verified with the tools available, say so explicitly and mark it unverified.

## Commands you should run (from the repository root)

```bash
uv sync --project backend
uv run --project backend pytest backend/tests -q                 # expect: all pass, offline
uv run --project backend python tools/fixturectl.py verify       # expect: exit 0, "reproducible"
uv run --project backend python tools/fixturectl.py build        # note the four commit SHAs
uv run --project backend python tools/fixturectl.py build        # again: SHAs must be identical
uv run --project backend ruff check backend/app backend/tests tools
uv run --project backend ruff format --check backend/app backend/tests tools
uv run --project backend uvicorn app.main:app --port 8011 &      # then hit the endpoints below
curl -s localhost:8011/health
curl -s "localhost:8011/api/threads/REQ-001?baseline=baseline-b"
curl -s -X POST localhost:8011/api/discovery -H 'content-type: application/json' \
     -d '{"artifact_id":"SCN-001"}'
curl -s -X POST localhost:8011/api/assurance/evaluate -H 'content-type: application/json' \
     -d '{"baseline":"baseline-a"}' -i
```

Also useful: run the fixture's own suite at both tags (the fixture tests are inside the generated
repository). Run each from its worktree root — the fixture repository's `conftest.py` is what puts
`src` on `sys.path`, so pointing pytest at a path from outside fails collection:

```bash
REPO="$PWD/fixtures/banking-demo/.build/repo"
git -C "$REPO" worktree add --detach /tmp/cta-a baseline-a
git -C "$REPO" worktree add --detach /tmp/cta-b baseline-b
(cd /tmp/cta-a && "$OLDPWD/backend/.venv/bin/python" -m pytest -q --tb=short)   # expect: 5 passed
(cd /tmp/cta-b && "$OLDPWD/backend/.venv/bin/python" -m pytest -q --tb=short)   # expect: exactly 2 failures
git -C "$REPO" worktree remove --force /tmp/cta-a; git -C "$REPO" worktree remove --force /tmp/cta-b
```

## Claims to falsify

| # | Claim | How to attack it |
| --- | --- | --- |
| 1 | Fixture Git history is byte-reproducible (identical SHAs across builds/machines) | Build twice into different directories and compare; inspect `tools/fixturectl.py` for unset sources of nondeterminism (timezone, config leakage, branch name, `git` config, file modes). Try with `git config --global commit.gpgsign true` and a non-UTC `TZ`. |
| 2 | Committed generated files cannot silently drift | Tamper with a file under `fixtures/api-responses/`, run `verify`, confirm a non-zero exit and a useful message. Also delete a file and confirm `verify` notices. |
| 3 | A proposal can never become an accepted link through the code | Look for any code path from `TraceCandidate` to accepted storage; check `TraceCandidate`'s fields; check the API response shape; confirm no endpoint writes links. Is "no write surface" enforced by types, or only by convention? |
| 4 | `reverification_required` is never reported as `verification_failed` | Inspect the oracle for the `CODE-001` change at `baseline-b`; confirm no failing run exists for that scenario at that baseline; confirm the API response for `baseline-b` reproduces that. Then try to construct a case where staleness would be mislabeled as failure. |
| 5 | The failing-test case is a *real* failure, not a fabricated label | Run the fixture suite at `baseline-b`; confirm the failing tests correspond to the evidence record `EV-003` and to `REQ-003`/`SCN-003`/`TEST-002`, and that the code defect (at-limit transfer rejected) exists in `src/transfers.py`. |
| 6 | Tests do not compare the implementation to itself | Read the tests: is any expectation derived from the code under test, from the generated snapshot, or from prose? Are the "healthy"/negative expectations present (e.g. `REQ-001` has no finding at `baseline-a`)? |
| 7 | Findings are pinned to revisions, and fingerprint identity is baseline-independent | Recompute a fingerprint from `app/domain/models.py` and compare with the sample response; check the same underlying problem keeps one id across baselines. |
| 8 | Offline by default is real | Read `backend/pyproject.toml` and the app modules for network clients, model libraries, or remote defaults; check that the test suite needs no network (consider running with networking disabled). |
| 9 | Contract-only endpoints are honest | Call each 501 endpoint and confirm the problem document names the owning story and milestone and that request bodies are still validated. |
| 10 | Baseline addressing is exactly as documented | Call an endpoint with a tag and with that tag's SHA; compare bodies byte for byte. Try an unknown tag, a malformed id, and a known artifact whose thread was never materialized — check the status codes and problem `code`s match `docs/domain-contracts.md`. |
| 11 | The docs match reality | Spot-check `docs/api-contracts.md` examples and `docs/STATUS.md` claims against actual responses. A false claim in `docs/STATUS.md` is a high-severity finding. |
| 12 | No dead weight or hidden stubs | Look for empty packages, unused models, unreachable code, placeholders, `TODO`s, or endpoints that return plausible fake success. |
| 13 | Commit-message traceability convention is real and machine-readable | Check the recent commit trailers with `git log --format=%B -n 5 \| git interpret-trailers --parse`; flag any commit that lacks `Story:`. |
| 14 | CI would actually pass from a clean clone | Read `.github/workflows/ci.yml` and reason about a fresh checkout: lockfile, Python version, git availability, cache, and whether any step needs network beyond dependency installation. |

## Output format

Report as:

1. **Verdict** — one line: `M0 verified` / `M0 verified with findings` / `M0 not verified`, with the
   single most important reason.
2. **Findings** — one section per finding, ordered by severity (critical / major / minor / nit).
   Each finding: what you ran, what you observed, why it matters for the project's invariants, and
   the smallest fix you would accept. Distinguish *observed* from *suspected* explicitly. Include
   file paths and line numbers.
3. **Unverified claims** — anything you could not check, and what you would need.
4. **Falsification attempts that failed** — the attacks above that found nothing, in one line each,
   so the team knows what has been covered. No praise, no summary of the work, no restating the docs.
5. **Recommendation** — whether M1 may start, and which single change should land before it does.

## For a re-review after repairs

Target the findings list in `docs/reviews/M0-review.md` with the same commands you used, against the
new revision. For each finding: confirm the reproduction now fails (the probe is rejected, the guard
exits non-zero, the mutation is caught), confirm a regression test exists that would catch it again,
and confirm nothing regressed elsewhere. Report per finding: `repaired`, `partially repaired`, or
`not repaired`, with the command output that shows it.

Write your review to `docs/reviews/M0-review.md`. Do not modify any other file: this is a read-only
review. If you believe a finding requires a code change, describe it; do not implement it.
