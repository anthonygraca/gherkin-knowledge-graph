# AI-02 specification review request

You are the independent specification reviewer for CTA story AI-02 (#31), milestone M3. This is a
**specification freeze review**, not an implementation or acceptance review. Read-only inspection
only. Do not edit files, run tests, implement, commit, or delegate.

## Inputs

- Canonical draft: `docs/stories/AI-02.feature` (6 scenarios, SCN-3201…SCN-3206; SCN-3205 is
  `@live-local` and excluded from the default offline suite).
- Companion: `docs/stories/AI-02.md`.
- Accepted owner manifest: `docs/reports/omp-closeout/AI-02-MODEL-MANIFEST.md` (Apache-2.0
  EmbeddingGemma 2 text 270M ONNX, onnxruntime CPU, same machine, exact weights digests/runtime).
- Owner dispositions: `docs/adr/0012-closeout-scope-decisions.md` §4.
- Repository invariants: `AGENTS.md`; roadmap AI-02/F-08; the GitHub issue body below.
- Existing provider contract: `backend/app/domain/ports.py`,
  `backend/app/discovery/local_embedding.py`, `backend/app/discovery/registry.py`,
  `docs/domain-contracts.md`.

GitHub issue #31 intake (verbatim):

```text
As a developer, I want local model inference without shared DGX services, so that semantic discovery works on a laptop with no cluster.

Scenario: Local provider behind the existing contract
  Given a local embedding model is installed
  When the shared contract tests run against the local provider
  Then they pass unchanged
  And no request leaves the machine

Scenario: Model details are recorded with every candidate
  Given the local provider produced a candidate
  Then the candidate reports the model version and the index revision it came from

Definition of done:
- Model identifier, instructions, runtime compatibility, and licence verified at implementation time (roadmap §3 caveat), not assumed from an example
- Fake provider remains the default; tests never require the model
- Documented invocation, hardware expectations, and failure modes
```

## What to decide

Assess only whether the canonical specification is ready to freeze for implementation/acceptance:

1. Is every scenario observable and testable through the real provider boundary, with the optional
   live check clearly separated from the default offline path?
2. Are remote-endpoint refusal, missing weights/runtime, malformed output, empty/default fake mode,
   and no-write outcomes covered without contradiction?
3. Is the model/runtime/licence/hardware evidence requirement specific enough to close the story,
   without turning a one-corpus smoke measurement into a retrieval-quality claim?
4. Does the specification preserve every repository invariant: fake default, offline default,
   opt-in live model tests, no external egress, proposals never become accepted/evidence, and
   missing provenance is reported rather than invented?
5. Are scenario IDs stable, unique, and correctly ranged?
6. Are the live egress-denial and manifest-record requirements directly verifiable?

## Output format

Return exactly one Markdown document:

- `## Verdict` — `APPROVE` or `REVISE`.
- `## Findings` — numbered `AI02-SPEC-R<n>` with severity (`blocking`/`nonblocking`), scenario or
  section, ambiguity/contradiction, and smallest precise repair.
- `## Scenario assessment` — one row per scenario ID with PASS/FAIL/NOT VERIFIED for specification
  readiness.
- `## Freeze conditions` — empty if APPROVE.

APPROVE only when no blocking ambiguity or contradiction remains.
