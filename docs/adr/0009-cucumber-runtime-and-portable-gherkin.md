# ADR 0009 — Cucumber-JS for executable acceptance, with a Python bridge and portable Gherkin

**Status:** Accepted · 2026-11-13 · **Story:** GT-01 (#60), GT-02 (#61), GT-03 (#62), PG-01 (#63)

## Context

M0/M1 acceptance criteria lived in `docs/stories/*.feature` but were verified by mapped pytest
checks. M2 must make those specifications execute, capture the framework's own step-resolution and
execution facts, and additionally index external repositories that never adopted CTA conventions.

Two runtimes were plausible: Cucumber-JS (Node is already a project toolchain for the dashboard and
has official `@cucumber/messages`) and a Python BDD runner (`pytest-bdd`/`behave`). The backend is
Python; a JavaScript runner needs a boundary to exercise it.

## Decision

* **Runtime:** `@cucumber/cucumber` 13.3.0, configured in `bdd/cucumber.mjs`. It emits official
  Cucumber Messages NDJSON (`--format message:`), which is the same format the portable adapter
  reads. A second runtime is not installed.
* **Boundary:** step definitions call `bdd/support/cta_bridge.py` once per step. The bridge imports
  the real application modules (store, evaluator, discovery registry, FastAPI app) and returns one
  JSON document. There is no second implementation of the domain in JavaScript.
* **Why not run a network server for every scenario:** an in-process FastAPI `TestClient` exercises
  routing, validation, and problem documents without port allocation or process leakage. The
  browser/HTTP demonstration in the milestone report uses a real `uvicorn` process and real HTTP.
* **Portable Gherkin parsing:** `gherkin-official` 43.0.0 (the official Python port of the Cucumber
  Gherkin parser), not a hand-written subset. Scanner rules for CTA's strict fixture contract stay
  in `app/ingestion/scan.py` and are untouched.
* **Report ingestion:** the adapter reads `stepDefinition` envelopes (registered definitions and
  source locators), `testCase.testSteps[].stepDefinitionIds` (the framework's resolution), and
  `testStepStarted/Finished` (observed outcomes). No second matching algorithm is implemented.
* **Source binding:** a report is only attributed to a revision when every `source` envelope's
  SHA-256 equals the feature content hash at that revision. A commit that stores a report never
  becomes the tested commit.

## Consequences

* Python is required to execute the acceptance suite; Node is required to run it. Both are already
  documented prerequisites. `uv sync --project backend` and `npm ci` in `bdd/` are one-time setup,
  after which the suite is offline.
* Each step spawns a short-lived Python process. That costs ~0.3 s per step and makes the suite
  slower than an in-process runner; it buys an honest boundary and identical behavior to the CLI.
* Cucumber-JS 13 does not emit `stepDefinition` envelopes in older versions; the adapter rejects a
  report without them instead of inventing matches.
* Frontend scenarios execute in a real Chromium tab through `playwright-core`, against the built
  dashboard and an isolated `uvicorn` process serving the fixture repository; the harness owns both
  process lifecycles. Vitest component tests remain independent evidence. The browser executable is
  a prerequisite (`CTA_CHROME_PATH` or a system Chrome/Chromium).
* A second framework adapter (Behave, Cucumber-JVM) is explicitly out of M2 scope. The adapter
  interface is the portable record set in `app/domain/portable.py`.
