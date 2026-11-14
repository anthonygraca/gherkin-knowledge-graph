# GT-01 / GT-02 / GT-03 — executable Gherkin integration

**Served issues:** [GT-01 #60](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/60),
[GT-02 #61](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/61),
[GT-03 #62](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/62); feature F-11
([#58](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/58)). Milestone M2.
**Snapshot:** local `main` at `4659e01` plus this uncommitted slice; schema `0.3.0`.
**Independent review:** not yet submitted at the time of this record.

## Delivered

* `bdd/` Cucumber-JS 13.3.0 harness: `cucumber.mjs`, `support/world.js`, `support/cta_bridge.py`,
  step definitions for the digital thread, assurance, API, fixture, M2, harness, and portable
  surfaces. Sixteen feature files execute (eight historical M0/M1 files plus the new M2/GT/PG
  specifications). ADR 0009 records the runtime choice and the reasons.
* `bdd/tools/step-resolution.mjs` — strict gate over the Cucumber Messages report: fails on
  `UNDEFINED`, `AMBIGUOUS`, `PENDING`, on a run that did not finish, and on a pickle that never
  started.
* `bdd/probes/{passing,undefined,ambiguous,failing}` — isolated probe suites (their own minimal
  Cucumber config) proving each failure mode; GT-01 executes them.
* `docs/feature-inventory.json` / `.md` — every tracked feature classified, with parsed scenario
  counts and step patterns, declared execution status, and an explicit reason for every non-executed
  entry (`tools/feature_inventory.py`).
* Canonical M2/GT/PG features: `DT-05`, `DT-06`, `AS-02`, `AS-03`, `AS-05`, `GT-01`, `GT-02`,
  `GT-03`, `PG-01`.
* CI job `bdd` runs `npm ci`, the suite, and the strict gate, and uploads the messages report.
* One historical defect found by making the specs executable: `DT-02` SCN-527 had a step split
  across two physical lines, which the official Gherkin parser rejects. The wording is unchanged;
  the two lines were joined. `FT-02` SCN-205 asserts the M0 501 contract that AS-01 superseded; it is
  tagged `@superseded-by-AS-01` and excluded, with the supersession documented in the file header.

## Execution status (declared, not inferred)

| Feature set | Status | Evidence |
| --- | --- | --- |
| DT-01..DT-06, AS-01..AS-05, FT-01, FT-02, AI-01, GT-01..GT-03, PG-01, SETUP-01 | executed | `evidence/cucumber-messages.ndjson` |
| AS-04, AS-05 browser layers | executed by the Cucumber browser suite (`@browser`) | 7 browser scenarios + screenshots |
| SETUP-01 | executed via the real `commitlint` functions on temporary Git histories | 8 Cucumber scenarios; mapped pytest stays independent |
| FT-03 | inspection (`@FT-03`) | `docs/stories/FT-03.md` |
| AI-06 | M3, out of scope (`@AI-06`) | — |
| banking-demo features | monitored application specs | that project's own pytest suite |

Full-suite outcome: **78 scenarios passed** (331 Gherkin steps + 156 hook steps), strict gate `ok`
(93 test cases, all resolved and started). Captured report `evidence/cucumber-messages.ndjson`
(`sha256:7dcff8dabf0690244d7b17cfa6a43dcf1c56d20852c450b01257e07520f15df8`). A suite pass is not an
approval.

## Commands

```bash
(cd bdd && npm ci)
(cd bdd && npm run bdd)
node bdd/tools/step-resolution.mjs bdd/reports/cucumber-messages.ndjson
```

## Limitations

* AS-04/AS-05/SETUP-01 Cucumber bindings are pending; GT-02 stays open until they exist or an owner
  accepts the declared exclusions.
* Step execution is per-step Python subprocess; the suite is slower than an in-process runner.
* No second framework adapter.
