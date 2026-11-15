## Verdict

**REQUEST_CHANGES**

Reviewed `9fb390b2c821a3a4fc5618e10424727a89e756d5` against the supplied base. All six hosted checks pass, but **CI01-ACC-R4 remains partially unrepaired and blocking**.

No files were changed, fixtures regenerated, commits created, or work delegated.

## Criterion assessment

Both retained and hosted Cucumber reports contain **203 passing scenarios / 1,972 passing steps**, including all nine CI-01 instances. This supersedes the submission’s 202/1,963 count.

| Criterion | Assessment | Evidence |
|---|---|---|
| SCN-3401 | **PASS** | Banking report pins banking-demo/baseline-b to `623b81adcb7fb9e0e5023d82bae206f44cac733e`, records `cta@0.1.0+9fb390b2…`, and includes 17 inputs. Six findings match the oracle’s semantic fields; fingerprints, revision fields, artifact byte hashes, manifest and report bindings validate. Independent evaluation completed under confirmed OS-level network denial. |
| SCN-3402 | **PASS** | PR resolver selects head over a distinct merge SHA; push selects `after`, with zero-SHA fallback checked. Real indexing at selected head/base commits produces different source digests. Relabeling the current execution report to the base is rejected. |
| SCN-3403 | **PASS** | Hosted scope, tested commit, normalized execution digest, 31 imported source hashes and all 41 indexed feature hashes validate. Mixed-outline coverage is now disjoint; skipped and unknown coverage remain distinct. No requirement verdict is produced. |
| SCN-3404 | **PASS** | Independent failed-report replay exits `0`, retains `completed`, and produces an attributable `execution_failed` finding without a requirement verdict. |
| SCN-3405 | **FAIL** | Failure classifications, stderr diagnostics and unavailable-input markers are repaired. A banking manifest read failure after evaluation still discards known input provenance: R4 below. |
| SCN-3406 | **PASS** | Hosted report/manifest/diagnostic uploads succeed. Run-unique publication paths prevent reuse of earlier outputs. CLI summaries identify revisions and finding counts; publisher failure preserves evaluator completion. Earlier hosted failed-gate evidence confirms publication without masking BDD failure. |

## Findings

1. **CI01-ACC-R4 — Major; blocking; partially repaired — late banking input failure still loses known provenance.**

   **Location:** `tools/assurance.py:225–275`, particularly the replacement of `collected_inputs` at line 252.

   **Expected:** Contract §1.4 requires incomplete diagnostics to retain inputs known at failure, marking the unreadable input `available=false`, `digest=null`.

   **Actual:** I reran the previous banking-manifest probe: initial manifest loading succeeds, real ingestion/evaluation completes, then `Path.read_bytes()` for the manifest raises `PermissionError`. The command returns exit `2`, `input/input-unreadable`, and no findings, but its diagnostic contains **only the unavailable fixture-manifest entry**. It omits the already-consumed artifacts, accepted/proposed link sets, evidence set and historical inputs.

   Report/metadata permission failures, malformed provenance retention, unknown revisions, and output failure after successful input collection now behave correctly.

   **Smallest correction/recheck:** Collect banking input provenance progressively before the late manifest read; append or update its unavailable entry without replacing prior entries. Repeat this probe and verify the incomplete report and manifest retain all previously known inputs.

**Other prior findings rechecked and closed:**

- **R1:** Forbidden report and manifest paths receive no write attempt in either scope.
- **R2:** Denying all cleanup/replacement can preserve an immutable old CLI destination, but current workflow publication uses distinct run/attempt paths and excludes it.
- **R3:** Summary failure exits `2` with `publication-failed`, preserving the completed evaluator report.
- **R5:** Mixed-outline coverage is now `174 executed / 0 skipped / 32 unknown`; all-skipped coverage is `0 / 174 / 32`, with no failure findings.
- **R6:** Both hosted artifacts contain captured diagnostic files.
- **R7:** Both hosted evaluator identifiers include package version and exact CTA commit.
- **R8:** All three `final-run-hashes.txt` entries validate.

## Check verification

- Observed the requested `gh run view 43707421956 --json databaseId,conclusion,status,headSha,jobs` and `gh pr checks 78`: **all six checks green at the exact submitted head**. PR head/base match the snapshot. [Hosted run](https://github.com/anthonygraca/gherkin-knowledge-graph/actions/runs/43707421956).
- Inspected artifacts directly in memory: `assurance-banking` **14159520470**, `assurance-self` **14158814297**, and `cucumber-messages` **14159078299**.
- Hosted logs confirm **553 backend passed / 4 skipped**, fixture verification, Ruff lint/format, **203 Cucumber scenarios / 1,972 steps passed**, and strict step resolution.
- Fresh local strict step resolution, Ruff lint/format, evidence hashes and `git diff --check` pass.
- Failure probes ran production CLI handlers and real ingestion/import/evaluation with filesystem mutations replaced by memory.
- Independently inspected [run 43695481792](https://github.com/anthonygraca/gherkin-knowledge-graph/actions/runs/43695481792): BDD failed while self-assurance successfully published a completed report containing six attributable execution failures.
- **Unobserved:** fresh full local suites or fixture verification, rendered hosted summaries, hosted publisher/tool-failure injection, and a hosted push-triggered assurance run. Push selection was checked deterministically. No weakened offline default was found.
