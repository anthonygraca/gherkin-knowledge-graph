# Independent acceptance review — expanded M2 (submission 2 of 7)

## Snapshot

* Repository: `anthonygraca/gherkin-knowledge-graph`, local working tree at base
  `4659e011c7adbe56940c71891f857d6225a5df10`. The M2 slice is still uncommitted; review the working
  tree.
* Schema `0.3.0`; fixtures regenerated.
* `dirty-tree-manifest.txt` lists every changed/untracked file with SHA-256. Feature hashes are below.
* The previous submission (`review-1.md`) returned **REQUEST_CHANGES** with findings M2-R01…R12.
  `review-1-disposition.md` records each repair. This submission asks you to verify the repairs and
  the remaining declared blockers.

## Repairs since submission 1

| Finding | Repair |
| --- | --- |
| R01 hashes | Current feature hashes below; `dirty-tree-manifest.txt` covers the whole slice; `review-packet-1-errata.md` explains the stale table. |
| R02/R03 applicability | `backend/app/assurance/rules.py`: passing runs are compared across scenario+implementations+tests; failure applies only when every relevant artifact matches. New tests: `test_a_changed_test_still_requires_reverification`, `test_a_changed_scenario_still_requires_reverification`, `test_an_old_failure_is_not_current_after_implementation_change`. |
| R04 report attribution | `ExecutionImportRequest.metadata_path` is required; `metadata.tested_commit` must equal the requested commit; reports are keyed by `(tested_commit, digest)` and the same bytes cannot be rebound. Evidence reports/sidecars regenerated; manifest updated. Tests: `test_cucumber_report_honesty.py`. |
| R05 skipped execution | `HAS_STEP_EXECUTION`/`EXECUTED_DEFINITION` and coverage require `PASSED`/`FAILED`. `test_skipped_run_is_not_observed_execution`. |
| R06 hook failure | Scenario outcome includes hook results; a missing result is `UNKNOWN`. `test_hook_failure_fails_the_scenario`. |
| R07 gate | Rejects `SKIPPED`/`UNKNOWN`, prints competing definition `uri:line`, and GT-01 SCN-2105 executes a real `--dry-run` probe. |
| R09 inventory | Status/counts derived from the messages report; generator fails on absent/unstarted declared-executed features; GT-02 reconciliation covers every entry. |
| R10 paths with spaces | Key pattern permits any non-newline character; `test_feature_paths_with_spaces_are_indexable_and_queryable`. |
| R11 drill-down | Opening a finding fetches its own requirement's evidence and caches it; component test + live browser re-verification with REQ-001 selected. |
| R08 GT-02 incomplete | **Not repaired.** AS-04, AS-05, SETUP-01 remain unbound and are explicitly `not_executed`. |
| R12 human oracle review | **Not repaired.** Requires the repository owner's attestation for the two external inventories. |

## Current feature hashes (sha256)

| `docs/stories/DT-05.feature` | `f348df16d5bb28945e6a16bbab116fb40cf5f6cb2ceeb69fe26ef2c4b36ece20` |
| `docs/stories/DT-06.feature` | `8b6630b2408e5ced946ec69fc97a014c45fcdf5e3c31eeb9a8603f007de703cd` |
| `docs/stories/AS-02.feature` | `4ea37ca50432b92113e4272826d7b75555677aaf3ff01cb91a46b1d4c29ede78` |
| `docs/stories/AS-03.feature` | `320cfdc2e32625e9dc4b6da11d6f1594e227eb3971ff17f8974d963b30ed00ee` |
| `docs/stories/AS-05.feature` | `2172b7f437f682753df4479b4329e8e73f7d267dc2776b2a7473c207116ac797` |
| `docs/stories/GT-01.feature` | `aac42c24723aa02166d9f534946750e6d49c74f14db7c7ae8bcfe1790a6ba8bf` |
| `docs/stories/GT-02.feature` | `7706223c5355fccbe3b05c37494b0ea48c2beda3bec0db07367a5d4f3d73af69` |
| `docs/stories/GT-03.feature` | `f81b51c4891e4a98da7bf02956ca9fc1a376f46df0ac4325f925d0a14432a85d` |
| `docs/stories/PG-01.feature` | `4739afda0c627835524126bddd5d8db2abee2565f155b668ee80348a460ad766` |
| `docs/stories/DT-01.feature` | `7c597f70673654a0e048ec923cc04073b9b424fd7c54b7254b635b4936b3b5e8` |
| `docs/stories/DT-02.feature` | `4e9ff5c1891763ea4160ab4bf7b55a86ddacdf0a7765cfa6dcd5b7694ffc3774` |
| `docs/stories/DT-03.feature` | `4c581fc95949e64ece04bfacadb6aa59a61358921ca58c2a9159aad0a1a193dc` |
| `docs/stories/DT-04.feature` | `3d525a0a7bdb2dbfc8a555e3e57e88a28f5574667b6f043b2903361d1c68d64a` |
| `docs/stories/AS-01.feature` | `bb214629f16293b719ce42a23a67ee21735163d5f1ad13861507086cdf6592b2` |
| `docs/stories/FT-01.feature` | `d58eeec05ce2072b81fd656531369ae2d329a9fcc09975688d2750fc044c217a` |
| `docs/stories/FT-02.feature` | `bdf55dafaa3fa498242c5fd5d3e27961281679ea612766dce207542cb7cacae8` |
| `docs/stories/AI-01.feature` | `381663033f88f4915481f292c912e94041774497aa74d22bb41a34b17276ef67` |

## Checks run after the repairs

| Command | Observed |
| --- | --- |
| `uv run --project backend pytest backend/tests -q` | 441 passed, 3 opt-in skips |
| `uv run --project backend python tools/fixturectl.py verify` | exit 0 |
| `uv run --project backend ruff check .` | all checks passed |
| `uv run --project backend ruff format --check .` | 78 files already formatted |
| `git diff --check` | exit 0 |
| `(cd frontend && npm run build && npm test)` | built; 12 tests passed |
| `(cd bdd && npm run bdd)`, then `node tools/step-resolution.mjs …` | 78 scenarios passed (331 Gherkin steps + 156 hooks, 487 results); gate ok (78 test cases) |
| `tools/portable_benchmark.py` | exact hand-label match, 0 modifications, 0 collisions, 23/23 matched, not_available without a report |
| Live browser | failure drill-down shows EV-003 with tested commit while REQ-001 remains the selected thread; 0 console errors |

Captured report sha256: `420db788df44fa0c3c588ec77f84d0f4f8ca2481ef752fa5c9f3c5b88344ffca`
(`docs/reports/omp-m2-bdd/evidence/cucumber-messages.ndjson`).

## Declared remaining blockers (not claimed as repairs)

1. **GT-02 incomplete (R08).** `AS-04`, `AS-05`, `SETUP-01` still have no Cucumber bindings. The
   evidence-derived inventory marks them `not_executed` with reasons. The expanded-M2 exit is not
   met.
2. **Human oracle review (R12).** The two external inventories are agent-produced hand counts. The
   owner must review and hash-attest them; this review cannot.
3. No second framework adapter; no real third-party repository.

## Reviewer mandate

You are the independent CTA implementation reviewer using GPT-6.1 Sol high.

Assess this exact repository snapshot against every applicable canonical acceptance criterion and
project invariant. Verify each claimed repair by inspecting the code and, where practical, by
reproducing the counterexample. Re-check that repairs did not weaken the original oracle or the
accepted/proposed/evidence separation.

For Cucumber work, verify that historical CTA acceptance feature files have not been silently
omitted, that step definitions are real executable tests, and that the claimed report corresponds to
the included scenarios. For external portability, verify read-only indexing, annotation-free
queries, repository/revision isolation, and UNKNOWN-versus-UNDEFINED behavior.

Distinguish matched steps from executions, executions from production coverage, and evidence from
requirement verification. Do not demand later M3/M4 capabilities or a second framework adapter.

Do not edit files, install dependencies, implement repairs, regenerate fixtures, commit, or
delegate. Return criterion-by-criterion PASS/FAIL/NOT VERIFIED, actionable findings with stable IDs,
and exactly one verdict: APPROVE, REQUEST_CHANGES, or NEEDS_INPUT. State explicitly that R08 and R12
remain blockers unless you find that the declared incompleteness is itself acceptable under the
canonical exit criteria (it is not expected to be). Agent review does not attest human stakeholder
validation or human acceptance of semantic links.
