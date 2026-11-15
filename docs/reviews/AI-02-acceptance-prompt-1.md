# AI-02 acceptance review — submission 1

## Scope

**Story:** AI-02 (#31), milestone M3 — optional same-machine EmbeddingGemma 2 inference.
**Canonical criteria:** `docs/stories/AI-02.feature` (6 scenarios, SCN-3201…SCN-3206; SCN-3205 is
`@live-local`).
**Companion/normative contract:** `docs/stories/AI-02.md`.
**Specification approval:** `docs/reviews/AI-02-spec-review-2.md` (round 2).
**Owner manifest:** `docs/reports/omp-closeout/AI-02-MODEL-MANIFEST.md`;
**live evidence:** `docs/reports/omp-closeout/AI-02-EVIDENCE.md`.

This is an **independent acceptance review**, not a specification review. Inspect the actual
repository; do not edit, implement, download models, commit, or delegate. Read-only commands are
allowed.

## Snapshot

The cumulative close-out diff is the uncommitted working tree based on `827e487`. Use
`git diff 827e487` and inspect the files directly.

## Evidence to inspect

* `docs/reports/omp-closeout/evidence/final-cucumber.log` and `final-cucumber.ndjson` for the five
  offline scenarios; `docs/reports/omp-closeout/evidence/AI-02-live-cucumber-summary.txt` and
  `.ndjson` for SCN-3205.
* `docs/reports/omp-closeout/evidence/AI-02-live-pytest.log`,
  `AI-02-live-measurement.jsonl`, and `AI-02-MODEL-MANIFEST.md`.
* `backend/tests/test_local_embedding.py` (offline contract/error cases) and
  `backend/tests/test_local_embedding_live.py` (opt-in live).
* `backend/app/discovery/local_embedding.py`, `backend/app/discovery/registry.py`,
  `backend/app/settings.py`.
* `bdd/step_definitions/local_embedding.steps.js`, `bdd/cucumber.live.mjs`, the bridge op.

Verify, at minimum:

1. Default discovery is unqualified `fake`; no model process, weights download, or network attempt;
   `onnxruntime` is not imported by the default path.
2. A remote endpoint is `400 invalid-request` before any connection; no candidates.
3. Absent weights, weights-digest mismatch, and missing runtime package are each
   `503 retrieval-unavailable`, with no download/fallback and no accepted-link/evidence/finding
   mutation.
4. The real `LocalEmbeddingCandidateDiscovery.discover` boundary passes the shared contract with only
   the embedding runtime substituted offline: nonempty ranking, filters, top_k, ranks, provenance,
   no link/review fields, a legitimate empty result retaining API provenance, and an explicit
   unavailable-provenance failure.
5. SCN-3205 live evidence was executed under `unshare -rn` with the real local weights: weights
   digest/runtime/formatting match the manifest, external egress is denied/observed false, and every
   candidate identifies the model and CTA snapshot binding.
6. Non-finite output is a typed `503 retrieval-unavailable` with no partial list or writes.
7. The five offline scenarios are present and passing in the final Cucumber report; the live
   scenario’s separate `@live-local` report is present and passing.

## Output format

Return exactly one Markdown document:

* `## Verdict` — `APPROVE`, `REQUEST_CHANGES`, or `NEEDS_INPUT`.
* `## Criterion assessment` — one row per scenario ID: PASS / FAIL / NOT VERIFIED.
* `## Findings` — numbered `AI02-ACC-R<n>` with severity, blocking, path/line, expected/actual,
  smallest correction/recheck.
* `## Check verification` — commands/reports observed and any unobserved hosted check.

APPROVE requires every criterion satisfied at this snapshot, invariants intact, no open major
finding, and observed green required checks.
