# Independent acceptance review — expanded M2 (submission 1 of 7)

## Snapshot

* Repository: `anthonygraca/gherkin-knowledge-graph` (local working tree).
* Base commit: `4659e011c7adbe56940c71891f857d6225a5df10` (`main`).
* The M2 slice is **uncommitted**. Review the working tree, not the base commit. `.agents/`,
  `.omp/`, and `skills-lock.json` are the operator's environment and are out of scope; the AI-06
  CocoIndex files are unchanged by this slice.
* Schema `0.3.0`; fixtures regenerated with `tools/fixturectl.py all`.
* Network: dependency installation only (`gherkin-official 43.0.0`,
  `@cucumber/cucumber 13.3.0`); tests run offline.

## Served work items (verified via `gh issue view`)

| ID | Issue | Milestone | Canonical feature |
| --- | --- | --- | --- |
| DT-05 | #24 | M2 | `docs/stories/DT-05.feature` |
| DT-06 | #25 | M2 | `docs/stories/DT-06.feature` |
| AS-02 | #3 | M2 | `docs/stories/AS-02.feature` |
| AS-03 | #4 | M2 | `docs/stories/AS-03.feature` |
| AS-05 | #27 | M2 | `docs/stories/AS-05.feature` |
| GT-01 | #60 | M2 | `docs/stories/GT-01.feature` |
| GT-02 | #61 | M2 | `docs/stories/GT-02.feature` |
| GT-03 | #62 | M2 | `docs/stories/GT-03.feature` |
| PG-01 | #63 | M2 | `docs/stories/PG-01.feature` |

F-11 (#58) and F-12 (#59) are the parent features. No issue was closed. No commit, push, or PR was
created.

## Canonical feature hashes (sha256)

## Canonical feature hashes (sha256)
| `docs/stories/DT-05.feature` | `9791df8c366c1d6ad2bc45bc6d4eb2bbb4f4e5288036a5e4821152c88538020d` |
| `docs/stories/DT-06.feature` | `f738d4ab0f0d964bb09790da8e30acf15f6a186c31f3192bc8bbc8f042f06b34` |
| `docs/stories/AS-02.feature` | `8db8bbc7ab65e1946e96c592a7127ff50ad4ff378af0c93c139012060162819d` |
| `docs/stories/AS-03.feature` | `c2d55eb7802fd28c0f194eae1547648fc1cee5e48436f17d4a06cc6ecf09b740` |
| `docs/stories/AS-05.feature` | `a69a738ee131e28b891c031145c7e27a29099bd5294986f6d2bd3c9dafa4c324` |
| `docs/stories/GT-01.feature` | `8c50c853db38a0d81f2780b0991f0847a3ee20b1675f7d2b4b47ada6102228ec` |
| `docs/stories/GT-02.feature` | `164473ec9e0f1f1d11a66890e7635f3b8c02b3063e2fcf99eabcc8f2d542844e` |
| `docs/stories/GT-03.feature` | `7442575fe46e73997f2da54eebaa35c0a568dead31674cf7b3ea7f2b05b31404` |
| `docs/stories/PG-01.feature` | `9bafc2eb5f8dbe388a747a2501ebd4f5e24abd3787dcf78c5b651e75e964fe14` |
| `docs/stories/DT-01.feature` | `5517104a2cfffe255304ff5fc4e67a5186150f6c54c1456e21d8bb7b10bf4b4d` |
| `docs/stories/DT-02.feature` | `4e9ff5c1891763ea4160ab4bf7b55a86ddacdf0a7765cfa6dcd5b7694ffc3774` |
| `docs/stories/DT-03.feature` | `d6e390d908616388cbc69ae2dbabd5371ef6a15115a83b447f7696dbf6c83200` |
| `docs/stories/DT-04.feature` | `02301bee448f33efc07d9e0e1d37ccafa1d1a2b9a9bd303bfa622a0fd5eb94e9` |
| `docs/stories/AS-01.feature` | `835b6d313960624402eccdcf4b51ca5c87ee790ec0249df7a7e72a0ec95a8c85` |
| `docs/stories/FT-01.feature` | `7f4ec106b8fcc6f18b9ad77d87be50d549968626ea2242b90debd599249cca86` |
| `docs/stories/FT-02.feature` | `bdf55dafaa3fa498242c5fd5d3e27961281679ea612766dce207542cb7cacae8` |
| `docs/stories/AI-01.feature` | `7db53a935889aa68d8659ee8310fb8dde44eea0eac538f1a4f4e73bcd84db7e6` |

## Scope

1. **Version-aware assurance.** Six deterministic rules in `backend/app/assurance/rules.py`;
   `GET /api/findings` now evaluates instead of replaying the recorded sample
   (`app/assurance/sample_findings.py` deleted). Port gains `artifacts_at` and `impacted_links`.
   Dashboard drill-down in `frontend/src/App.tsx`.
2. **Executable Gherkin.** `bdd/` Cucumber-JS harness with a Python bridge, strict
   `bdd/tools/step-resolution.mjs` gate, isolated probe suites, and step definitions for the
   digital thread, assurance, API, fixtures, M2, harness, and portable surfaces. ADR 0009.
3. **Portable ingestion.** `app/domain/portable.py`, `app/ingestion/portable.py`,
   `app/ingestion/cucumber_messages.py`, `app/persistence/portable.py`,
   `app/api/portable_routes.py`, `app/cli.py`; external fixtures and benchmark under
   `fixtures/external-*` and `tools/`.

## AC-to-evidence map (selected)

| Criterion | Evidence |
| --- | --- |
| DT-05 append-only evidence, tested commit | `backend/tests/test_m2_assurance.py::test_evidence_is_append_only_and_pinned_to_the_tested_commit`; `DT-05.feature` |
| DT-06 content-hash change set and impacted links | `::test_change_set_is_content_hash_based_and_matches_the_oracle`, `::test_impacted_links_reach_the_changed_artifacts`; `DT-06.feature` |
| AS-02 reverification, never failure | `::test_evaluated_findings_equal_the_hand_labeled_oracle`, `::test_reverification_and_failure_never_collapse`; `AS-02.feature` |
| AS-03 three states distinct | `::test_baseline_a_has_no_failure_or_reverification`; `AS-03.feature` |
| AS-05 drill-down | `frontend/src/App.test.tsx` (two tests) and `docs/reports/omp-m2-bdd/evidence/browser/` |
| GT-01 real execution + strict gate | `bdd/probes/`, `bdd/tools/step-resolution.mjs`, `GT-01.feature` |
| GT-02 inventory and execution claim | `docs/feature-inventory.json` (generated), `GT-02.feature` |
| GT-03 matched vs observed relations | `test_portable_ingestion.py`, `GT-03.feature` |
| PG-01 read-only, unknown-not-undefined, collision isolation | `test_portable_ingestion.py`, `test_portable_api.py`, `benchmark.json`, `PG-01.feature` |

## Checks actually run (captured in the session)

| Command | Observed |
| --- | --- |
| `uv run --project backend pytest backend/tests -q` | 433 passed, 3 opt-in skips |
| `uv run --project backend python tools/fixturectl.py verify` | exit 0 |
| `uv run --project backend ruff check .` | all checks passed |
| `uv run --project backend ruff format --check .` | 76 files already formatted |
| `git diff --check` | exit 0 |
| `(cd frontend && npm run build && npm test)` | built; 12 tests passed |
| `(cd bdd && npm run bdd)` + gate | 76 scenarios / 474 steps passed; gate ok (76 test cases, 474 results) |
| `tools/portable_benchmark.py` | exact hand-label match; 0 modifications; 0 collisions; 23/23 matched with report; `not_available` without |
| Live HTTP (`uvicorn`) | `/health`, both findings baselines, thread, evaluate: 200 |
| Browser | both drill-downs observed in the live DOM; 0 console errors |

## Declared incompleteness

* **GT-02 is incomplete.** `AS-04`, `AS-05`, and `SETUP-01` have no Cucumber bindings; they are
  tagged `@ui-component` / `@migration-pending`, marked `not_executed` with reasons in the
  inventory. The expanded-M2 exit is therefore not met.
* No independent review had run before this submission; this is submission 1 of 7.
* No second framework adapter and no real third-party repository were available.

## Reviewer mandate

You are the independent CTA implementation reviewer using GPT-6.1 Sol high.

Assess this exact repository snapshot against every applicable canonical acceptance criterion and
project invariant.

For Cucumber work, verify that historical **CTA acceptance** feature files have not been silently
omitted, that step definitions are real executable tests rather than placeholders, and that the
claimed execution reports genuinely correspond to the included scenarios.

For external portability, verify that an ordinary unmodified Git repository with untagged Gherkin
scenarios is parsed and queryable; that requirements and CTA source annotations are optional; that
repository/revision identities do not collide; that index operations do not mutate inputs or run
test hooks; and that missing runtime matching metadata is UNKNOWN rather than a fabricated
undefined-step defect. Do not demand unimplemented second-framework support.

Verify unique step matching, actual assertion execution, correct handling of expected failures,
isolation of test state, correct Git revision provenance, and stable linkage between runtime records
and engineering artifacts.

Distinguish a successful Cucumber step match from successful test execution, and test execution from
production-code coverage or requirements verification.

Preserve the distinction between accepted links, proposed links, and verification evidence.

For original M2 assurance work, check content-hash change detection, append-only evidence,
tested-commit semantics, the independent oracle, reverification versus failure precedence, and
accurate findings presentation.

Do not demand later M3 or M4 capabilities. Do not edit files, install dependencies, implement
repairs, regenerate fixtures, commit, or delegate.

Return an acceptance-criterion-by-criterion PASS, FAIL, or NOT VERIFIED assessment.
Provide actionable findings with stable IDs, severity, blocking status, relevant criterion, source
path/line, expected versus actual behavior, and smallest correction/recheck.
Return exactly one verdict: APPROVE, REQUEST_CHANGES, or NEEDS_INPUT.
Approval requires all applicable criteria to be satisfied with no unresolved major finding.
A passing command, passing pytest suite, successful Cucumber dry run, or exhausted review limit is
not approval. Agent review does not attest human stakeholder validation or human acceptance of
semantic links.

Also state explicitly whether the declared GT-02 incompleteness prevents an expanded-M2 APPROVE.
