# Executable Gherkin metrics

| Measure | Value |
| --- | --- |
| Tracked `.feature` files in the inventory | 31 |
| Canonical CTA acceptance feature files | 19 |
| Cucumber runtime | `@cucumber/cucumber` 13.3.0 |
| Step definitions implemented | 7 step files (`bdd/step_definitions/*.js`) |
| Reused step patterns | shared Given/When/Then vocabulary across features (see inventory) |
| Historical M0/M1 features migrated to execution | 11 files (DT-01..04, AS-01, AS-04, AS-05, FT-01, FT-02, AI-01, SETUP-01) |
| Total feature files executed | 19 (historical 11 + DT-05, DT-06, AS-02, AS-03, GT-01..03, PG-01) |
| Declared pending | none of the applicable M0/M1 features |
| Declared out of scope | FT-03 (inspection), AI-06 (M3), banking features (monitored) |
| Negative probes | undefined, ambiguous, failing assertion, expected application error |
| Strict gate | `bdd/tools/step-resolution.mjs` |
| Report format | Cucumber Messages NDJSON |
| Full-suite scenarios/steps | 93 scenarios passed (396 Gherkin steps + 372 hook steps) |
| Gate result | ok: 93 test cases, all resolved and started |
| Report digest | `sha256:7dcff8da…` |
| Harness wall time | see captured run; per-step Python subprocess is the dominant cost |
