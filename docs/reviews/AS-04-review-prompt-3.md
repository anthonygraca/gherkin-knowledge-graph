# Independent implementation review — AS-04, submission 3 of 7

## 1. Submission context and prior dispositions

**Task:** AS-04 — Summary of findings and coverage counts.
**Roadmap:** F-06 UI, roadmap §6 AS-04; milestone **M1 — AI-free vertical slice**.
**GitHub story:** issue **#26**, verified OPEN 2026-11-13T04:13:19Z. **Owner:** C.
**Repository:** `<task_repo>` (read-only sandbox).
**Base:** `d238776bf0b53e6963f8e81721ce9a106f848adb` (`main`, AS-01 merge).
**Branch:** `feat/26-as-04-summary-ui`. **Submission:** 3 of 7.

Round 1 (`docs/reviews/AS-04-review.md`) raised R1/R2 (stale UI state) and N1 (numeric-count
coverage); round 2 (`docs/reviews/AS-04-review-2.md`) found all five criteria PASS and R1/R2/N1
closed, but returned **NEEDS_INPUT** for **E1** (retained logs missing; abbreviated network
invocation) and **N2** (a failed thread's alert persisted after a successful selection). Both are
addressed in this submission; neither was dismissed.

### User outcome

A lead can choose a baseline, see findings counts and per-requirement coverage, and inspect a
requirement's thread with accepted links, proposals, and evidence — offline.

### Scope / non-goals (unchanged)

React + TypeScript + Vite dashboard, baseline selector, summary/coverage, thread view, component
tests against committed fixtures, frontend CI job, setup docs, browser demonstration, and the
AS01-R1 test-strength repair. Non-goals: link review, computed assurance in the UI, auth,
deployment.

### Proposed commit references

1. `test(assurance): [issue #2] bind finding revisions to the manifest tag`, body `Refs #2`.
2. `feat(ui): [issue #26] show findings summary and requirement threads`, body `Refs #26`.

## 2. Acceptance criteria (canonical snapshot)

File `docs/stories/AS-04.feature`, sha256
`44f0ce7d64cdd2f80fa093a0adcdd5964821c5fa4102abbccf503dc7484d6f6e` (unchanged).

```gherkin
# Canonical acceptance specification for AS-04 (#26), M1.
# Source criteria: the GitHub story intake at
# https://github.com/anthonygraca/gherkin-knowledge-graph/issues/26 (verified 2026-11-13T04:13:19Z)
# and roadmap §6 F-06. Boundary scenarios were added during refinement; the two intake scenarios
# keep their wording. Verified by frontend component tests plus a recorded browser demonstration;
# the scenarios are not executed by a Gherkin runner.
@AS-04 @issue-26 @M1
Feature: AS-04: Summary of findings and coverage counts
  The dashboard shows, for the selected baseline, how many findings of each type exist and which
  requirements are covered. Counts come from the findings response. Proposals are displayed as
  proposals and never counted as coverage.

  @SCN-801
  Scenario: Coverage summary for a baseline
    Given the fixture data at "baseline-a"
    When the dashboard loads the summary
    Then it shows the finding counts by type for that baseline
    And it shows "REQ-001" as fully covered
    And it shows "REQ-002" as missing a verification scenario

  @SCN-802
  Scenario: The baseline is always visible
    Given findings for "baseline-a" and "baseline-b" differ
    When the baseline selector changes
    Then the summary reloads for the selected baseline
    And the selected baseline is displayed with the numbers

  @SCN-803
  Scenario: Counts are derived from the response, not hard-coded
    Given a findings response containing a different set of findings
    When the dashboard renders it
    Then the displayed counts change accordingly

  @SCN-804
  Scenario: Proposals are labelled and excluded from coverage
    Given "REQ-002" has proposed link "LNK-007" and no accepted verification link
    When its thread is displayed
    Then "LNK-007" is labelled as a proposal
    And "REQ-002" is not shown as covered

  @SCN-805
  Scenario: The thread view shows the accepted chain and its evidence
    Given the fixture data at "baseline-b"
    When the thread for "REQ-001" is displayed
    Then the accepted links and their relation types are shown
    And the evidence for "SCN-001" is shown
    And the baseline is shown with the thread
```

Refinement disposition: owner-authored issue intake + roadmap §6; boundary scenarios were added.
No separate human refinement sign-off is recorded.

Repository constraints (AGENTS.md): offline test execution; counts derived from responses; proposals
never counted as coverage; no model calls; no hand-edited generated files.

## 3. Snapshot and manifest

Snapshot captured 2026-11-13T04:58Z. Manifest (sha256 of every task file, including committed
evidence logs and screenshots):

```text
7d82d45f0d7bd214b9a014d89ed696ca0c32550bd4b81c3cbfaccc1866908315  frontend/package.json
5fd857b362d57ef48f0ff8862d474770ad5dc98d33c944bc64734dacd1591bac  frontend/package-lock.json
bde007f1fd26fa27cc068f64d8c02ee388ee08d22c7d4a15b211c0cd5870d7d1  frontend/vite.config.ts
770b4140bbb581e2dfd9ea9946ffc9c75a1d86ba7d2db5f77c83e37cbdf9d808  frontend/tsconfig.json
3bee9baf0672e6e0de5fe433bc6ec75ef31eb87f3b319b1111afaac0864d0e28  frontend/tsconfig.app.json
3ced5d22ba9e246c839a695526296a8d067fbe9db838d728516d2eac9215b333  frontend/tsconfig.node.json
4e00b5c1e7c64dfbeb8aa8fca0d0acc71be382a17960305e256c1b76a3f765f2  frontend/index.html
7317566625f28486211673a0e0b42f7bcc5600b9103c775fa541710a46148fc2  frontend/src/App.test.tsx
0ed430a622b6dc3acce7e5f5666ee0a7258034fe8c338a4a01d91d9b4c1de446  frontend/src/App.tsx
704cd9cb2b4b80f3c9d53ffb1a11273c6a4ea59bcd2c64df0920b3659561adfd  frontend/src/main.tsx
edfa55c6421cacbb2f1e1408e84a7b85b946ed3588670d494e0cd9a9326c86b5  frontend/src/api.ts
9b328c4843431fa76d8de00008fc159e95f99a840211085ff3b8f25e53d14409  frontend/src/test-setup.ts
6169bbac5bb00fde197aefd3fbedede17dc33403042059d7de1d3cc3b26f08df  frontend/src/types.ts
22d7c55129eee011cdff3123a98e69adf86b3b534ec97371d8e2cb16c3b1a772  frontend/src/styles.css
3a1b1a4fb55653d5162719932b8fc084e11476f8145b0fe59a3ed7727a15b4c1  .github/workflows/ci.yml
66547bba1717b2338557e503d9700aa3606d995c98f13b2bd1bc89adae2fdca0  docs/setup.md
d81c78a672a65843ff9d7133b1cf55037d6a2bbb3b12859c33feb10a5a6153e9  docs/architecture.md
5b3c32843c8ddb72ee016635e22075c0ed2a7ef3e5e38e24ed2c3c039fc00f2a  docs/STATUS.md
784361e690a18ebcbeebb3b47f403825a5fefd371068e1067b6fda907f613067  backend/tests/test_assurance_rules.py
44f0ce7d64cdd2f80fa093a0adcdd5964821c5fa4102abbccf503dc7484d6f6e  docs/stories/AS-04.feature
a90650fc994157f39bece4d6e5a57864b46806264084f15445e44b30dcad3ea1  docs/stories/AS-04.md
74e5d356642bb9f088f5622b247afb7507b073277b49aef69469e9720327f1dd  docs/reports/omp-as-04-summary/IMPLEMENTATION.md
3e9bbcc988ff2376ccb05507080d02483dfa3f2a35aba2587aea2c0c6c760f52  docs/reports/omp-as-04-summary/PROMPT_LOG.md
dee952e51c713dbbf6588de0e8c677fe2955b9b458c22cabf75a334d782aadba  docs/reports/omp-as-04-summary/METRICS.md
e0a5579a6ad05fc691c6638148099a18db13c1e5692cc0e6c9f9a6751a520996  docs/reports/omp-as-04-summary/evidence/checks.txt
c0a4c5e9c37772b73119d3aca0e9ed372104f77b552ec18a532973cd849da584  docs/reports/omp-as-04-summary/evidence/fixturectl-verify.log
cd345a739335f126a136d84dfaf2f7258e8988e8e0a098822156cb16250baee5  docs/reports/omp-as-04-summary/evidence/network-probe.log
dc756887c31a47996c29ea1e13f5fab8dded0d8a2ee7f8d4ebedf8d8c9d885d0  docs/reports/omp-as-04-summary/evidence/npm-build.log
9b4b52f04c5414f3a3e8cf3bc7df386e17c84a09a5ccdad01e3417177168d743  docs/reports/omp-as-04-summary/evidence/npm-test.log
cddad43188ff9283312cf29405a342a7dfec8e25d13b64c2d1442c1d9a40a6b2  docs/reports/omp-as-04-summary/evidence/pytest-full.log
7a2ca341de0d6822d3dc9b05e2ab9444e55f93d93b47976cc12b75e038c15d77  docs/reports/omp-as-04-summary/evidence/pytest-network-denied.log
82b3e6a6c090a57601d22943bd23fca9218d1031dbe5a7b754092f9a156b4f18  docs/reports/omp-as-04-summary/evidence/ruff-check.log
7df18b42c43329c0833da621f67724dca7a56dfff20a450ae0336efb05e24f06  docs/reports/omp-as-04-summary/evidence/ruff-format.log
a8428945cdd9762ed7c7d59529491e4c0969c8cea11e1565f136735ede92ff30  docs/reports/omp-as-04-summary/evidence/summary-baseline-a.png
150295d610a97195bbf285e5f324c5a72fdab567a8b78215a2f14711883a829a  docs/reports/omp-as-04-summary/evidence/summary-mobile-390.png
de3d3b2929d41f6991064807e39d14a4bdf662e0e084836db48039ae0004ad03  docs/reports/omp-as-04-summary/evidence/thread-req-001-baseline-b.png
6150fa2356813c46a0b940b7c110695000537314ac65c4c9ae5fa33765c1e6a9  docs/reports/omp-as-04-summary/evidence/thread-req-002-proposals.png
ebbbd1675777be9c361e5e842b113777e96da659c8b0310fc18a092160312be1  docs/reviews/AS-04-review.md
1d17c54c08479e90712b331c91186f47200e07c4c2cb0eafe40d35d9e88073d1  docs/reviews/AS-04-review-2.md
42253195ead218481771136b405be228d88a613e356d2f0d4a5aae7a28f68b30  docs/reviews/AS-04-review-prompt.md
0c6c76e7156bd82710a504b9a4f92c4bbec1d3c2ea3b3d6cbbe5f4a8ccc6336d  docs/reviews/AS-04-review-prompt-2.md
```

`SCHEMA_VERSION = 0.2.0`, `PACKAGE_VERSION = 0.1.0`. No backend product change; the AS01-R1 test
assertion is included.

## 4. Changes since submission 2

### Per-request error attribution (`App.tsx`)

```diff
```

Errors are now `healthError` / `summaryError` / `threadError`; starting a request clears only its own
error and success leaves the others untouched. The thread failure→recovery test asserts the alert
disappears when REQ-001 loads.

### Retained evidence (E1)

New committed evidence under `docs/reports/omp-as-04-summary/evidence/`:

```text
snapshot_captured=2026-11-13T04:57:45Z
cmd=uv run --project backend pytest backend/tests -q
exit=0
cmd=uv run --project backend python tools/fixturectl.py verify
exit=0
cmd=uv run --project backend ruff check .
exit=0
cmd=uv run --project backend ruff format --check .
exit=0
cmd=git diff --check
exit=0
probe_captured=2026-11-13T04:57:53Z
cmd=unshare -rn backend/.venv/bin/python - <<<socket probe>>>
exit=0
cmd=unshare -rn backend/.venv/bin/python -m pytest backend/tests -q
exit=0
done_captured=2026-11-13T04:58:01Z
-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
233 passed, 1 warning in 6.70s
-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
233 passed, 1 warning in 6.71s
```

`network-probe.log` contains `DENIED: OSError: [Errno 101] Network is unreachable`; the
network-denied suite ran with the exact invocation
`unshare -rn backend/.venv/bin/python -m pytest backend/tests -q` and exited 0 with 233 passed.
`pytest-full.log` (233 passed), `fixturectl-verify.log`, `ruff-check.log`, `ruff-format.log`,
`npm-build.log` (built), and `npm-test.log` (10 passed) are hash-listed above. The snapshot identity
is the manifest.

## 5. Implementation context

* The app takes an injected `Api`; tests inject committed JSON. Vite proxies `/health` and `/api`
  in development.
* Summary data is keyed by baseline; thread data by baseline+root; unmatched data is never rendered.
* Requirements come from `/api/artifacts`; counts from `/api/findings`; proposals render only from
  `proposed_links` with `not accepted`.
* Targeted reads: `frontend/src/App.test.tsx`, `fixtures/api-responses/*`, `frontend/package.json`,
  `.github/workflows/ci.yml`.

## 6. Evidence

| Criterion | Check | Result |
| --- | --- | --- |
| SCN-801 | "shows counts by type and coverage for baseline-a" | PASS (round 2) |
| SCN-802 | selector reload + transition/failure tests | PASS (round 2) |
| SCN-803 | response-derived counts + numeric `2` test | PASS (round 2) |
| SCN-804 | proposals labelled, not covered | PASS (round 2) |
| SCN-805 | accepted chain/evidence + transition/failure/recovery tests | PASS (round 2) |
| Browser | two baselines, proposal thread, mobile viewport, 0 console errors | PASS (round 2) |

Round 2 independently confirmed all five criteria and R1/R2/N1 closure. This submission adds the
retained logs and the N2 fix; the final checks were re-run at this snapshot (see `checks.txt`).

## 7. File-integrity requirement

The manifest in section 3 is the reviewed snapshot. If any manifest hash changed, the snapshot is
not the one reviewed. Do not edit files, install dependencies, regenerate fixtures, or commit.

## Reviewer instructions (mandatory)

You are the independent CTA implementation reviewer using GPT-6.1 Sol xhigh. Decide whether this exact snapshot satisfies the supplied story, every applicable Gherkin criterion, and repository invariants. Treat OMP's summaries and test results as claims to check against the supplied artifacts and targeted source inspection. Check proposal/accepted/evidence separation, real port compatibility, revision/content-hash semantics, honest errors/501s, independent oracle expectations, offline defaults, and generated-file discipline where relevant. Do not demand implementation of a later milestone. Do not edit files, implement repairs, regenerate fixtures, commit, or delegate. Ask OMP for missing runtime evidence; distinguish observed defects from hypotheses and unavailable checks. Return an AC-by-AC PASS, FAIL, or NOT VERIFIED assessment and actionable findings with stable IDs, severity, blocking status, AC/invariant, path/line, expected/actual behavior, and smallest correction/recheck. Keep optional suggestions and unrelated pre-existing defects separate. Return exactly one verdict: APPROVE, REQUEST_CHANGES, or NEEDS_INPUT. APPROVE requires every applicable criterion/check to be satisfied, no unresolved blocker, and the exact snapshot identified. In later rounds verify prior dispositions and regressions while retaining the complete acceptance assessment. A passing process, passing tests, or exhausted review limit is not approval. Agent review cannot attest human labeling or human link decisions.
