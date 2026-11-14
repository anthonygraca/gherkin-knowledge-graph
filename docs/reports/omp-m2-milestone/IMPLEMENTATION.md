# Expanded M2 — integrated implementation record

**Snapshot:** local `main` at `4659e01` plus an uncommitted working tree. Schema `0.3.0`.
No branch was pushed, no PR opened, no issue closed, and no local commit was created: independent
review has not run, so the slice is presented as unreviewed work for inspection.

## Scope delivered

| Track | Stories | Result |
| --- | --- | --- |
| Version-aware assurance | DT-05 #24, DT-06 #25, AS-02 #3, AS-03 #4, AS-05 #27 | rules evaluate all six findings; oracle equality; drill-down in UI and live browser |
| Executable Gherkin | GT-01 #60, GT-02 #61, GT-03 #62 | Cucumber-JS harness, strict gate, probes, 13 historical feature files executed, executable relations |
| Portable ingestion | PG-01 #63 | annotation-free indexing, repository-scoped identity, query API/CLI, one report adapter, benchmark |

## What changed (high level)

* Schema 0.3.0: additive portable/executable models, three executability finding types, three error
  codes, eleven repository-scoped endpoints. Fixtures regenerated (`fixturectl all`), oracle
  expectations unchanged (their `schema_version` metadata was updated).
* `app/assurance/rules.py`: six rules with declared precedence; `GET /api/findings` now evaluates;
  the sample-findings replay class was removed.
* `app/ingestion/portable.py` + `app/domain/portable.py` + `app/persistence/portable.py` +
  `app/api/portable_routes.py` + `app/cli.py`: portable surface.
* `app/ingestion/cucumber_messages.py`, `app/domain/executable.py`,
  `app/assurance/executable_rules.py`: report adapter, relations, executability findings.
* `bdd/`: Cucumber-JS harness, step definitions, probes, strict gate, report evidence.
* `fixtures/external-recipes/`, `fixtures/external-twin/`, `tools/external_fixture.py`,
  `tools/portable_benchmark.py`: independent portability fixtures and benchmark.
* `frontend/src/App.tsx`: findings drill-down.

## Verification record

| Check | Result |
| --- | --- |
| `uv run --project backend pytest backend/tests -q` | 443 passed, 3 opt-in skips |
| `uv run --project backend python tools/fixturectl.py verify` | exit 0 |
| `uv run --project backend ruff check .` | all checks passed |
| `uv run --project backend ruff format --check .` | 76 files already formatted |
| `git diff --check` | exit 0 |
| `(cd frontend && npm run build)` | built |
| `(cd frontend && npm test)` | 13 passed |
| `(cd bdd && npm run bdd)` | 93 scenarios (396 Gherkin steps + 372 hooks) passed; gate ok |
| `node bdd/tools/step-resolution.mjs …` | recorded with the suite |
| `tools/portable_benchmark.py` | exact hand-label match, 0 modifications, 0 collisions |
| Live HTTP | health, findings A/B, thread, evaluate captured under `omp-m2-bdd/evidence/http/` |
| Browser | AS-05 drill-down for both finding types, 0 console errors |

## Remaining limits and open gates

1. **Migration is complete locally.** All 19 applicable M0/M1/M2 acceptance features execute,
   including AS-04/AS-05 in a real browser and SETUP-01 through the real commitlint functions.
   The inventory derives that status from the captured report; 12 features remain intentionally
   unexecuted with reasons (FT-03 inspection, AI-06 M3, four external indexed specifications, four
   harness probes, two monitored banking specifications).
2. **Independent approval is pending.** Reviews 1–5 returned REQUEST_CHANGES; their findings are
   repaired. Submission 6 of 7 requests task and milestone approval. No approval, human stakeholder
   validation, or human acceptance of semantic links is claimed by this record.
3. No second framework adapter; no real user-supplied third-party repository was available.
4. Local commits were not created because the repository requires an approved issue-linked commit
   and approval has not been granted.
