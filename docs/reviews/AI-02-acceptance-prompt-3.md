# AI-02 acceptance review — submission 3

## Scope

**Story:** AI-02 (#31), milestone M3 — same-machine EmbeddingGemma 2 inference.
**Canonical criteria:** `docs/stories/AI-02.feature` (6 IDs, SCN-3201…SCN-3206; 7 offline cases plus
SCN-3205 live).
**Companion/normative contract:** `docs/stories/AI-02.md`.
**Specification approval:** `docs/reviews/AI-02-spec-review-2.md`.
**Owner dispositions:** `docs/adr/0012-closeout-scope-decisions.md` §4.
**Prior verdict:** `docs/reviews/AI-02-acceptance-2.md` (R3 partially open, blocking).
**Repair record:** `docs/reviews/AI-02-acceptance-1-repairs.md` (inspect, do not treat as proof).

This is an **independent acceptance review**. Inspect the actual repository; do not edit,
implement, regenerate fixtures, commit, or delegate. Read-only commands are allowed.

## Snapshot

* PR: `#75` (`feat/28-closeout-m3` → `main`)
* Head commit: `e463e9e3b496a6f60644d90c52e04da6f50f7dff`
* Base: `827e487d84be990739e588e9080637c725ecc882`
* Hosted CI: run `43679892961` on that head. Inspect the actual check conclusions.

Use `git diff 827e487..e463e9e3b496a6f60644d90c52e04da6f50f7dff` and inspect the files at that commit.

## What changed since submission 2

Both live paths now execute and retain the missing shared-contract cases:

* `top_k=0` rejection (`ValueError` in the provider contract), alongside trimming.
* The `local-embeddinggemma` baseline-a binding is checked against the reviewed fixed vector
  `sha256:814eb9914310d4d18f68859fbb5e89230773f026a50e931cb16889b1e3eaac52`, computed
  independently of `binding_for`.
* `/api/threads/REQ-001?baseline=baseline-a` is read before and after discovery; `accepted_links` (3)
  and `proposed_links` (0) remain separate and unchanged.
* The retained records carry `top_k_rejected`, `binding_matches_fixture`, `expected_binding`,
  `thread_accepted_links`, `thread_proposed_links`, and `thread_equal`.

The live pytest and live Cucumber runs were recaptured under `unshare -rn` with egress denied. The
new hashes and abridged measurement are in `docs/reports/omp-closeout/AI-02-EVIDENCE.md`.

## Evidence to inspect

* `docs/reports/omp-closeout/AI-02-MODEL-MANIFEST.md` — accepted model, weights digest, licence,
  runtime, hardware, invocation, measured limits.
* `docs/reports/omp-closeout/AI-02-EVIDENCE.md` — live commands, hashes, failure modes.
* `docs/reports/omp-closeout/evidence/AI-02-live-pytest.log`,
  `AI-02-live-measurement.jsonl`, `AI-02-live-cucumber-summary.txt`,
  `AI-02-live-cucumber.ndjson`, `AI-02-live-observations.json`.
* `backend/app/discovery/local_embedding.py`, `backend/tests/test_local_embedding.py`,
  `backend/tests/test_local_embedding_live.py`.
* `bdd/support/cta_bridge.py`, `bdd/step_definitions/local_embedding.steps.js`.
* `docs/stories/AI-02.feature`, `docs/stories/AI-02.md`, `docs/domain-contracts.md`.

Verify, at minimum:

1. The provider is real, same-machine, CPU-capable, and permissively licensed; no remote endpoint,
   proxy, or request leaving the machine. The fake provider remains the deterministic default; live
   tests are opt-in.
2. The observed weights digest, runtime, licence, formatting, model version, and index revision
   agree with the accepted manifest; `items_embedded` is not invented.
3. The live scenario indexes/discoveries against baseline-a only, with truthful commit attribution;
   the retained observation record includes the egress probe, namespace, bindings, candidate
   provenance, empty-result provenance, top-k rejection, fixed binding comparison, and the separate
   thread arrays.
4. The real runtime executes the specified shared discovery contract cases: top-k trimming and
   rejection, incompatible relation filter, baseline binding, empty results, separate
   accepted/proposed arrays, and no accepted link/evidence/finding.
5. Every prior finding **R1–R4** is repaired: baseline-a selection; retained observations;
   substantive shared-case execution; and the model-version/manifest agreement.

## Output format

Return exactly one Markdown document:

* `## Verdict` — `APPROVE`, `REQUEST_CHANGES`, or `NEEDS_INPUT`.
* `## Criterion assessment` — one row per canonical scenario ID: PASS / FAIL / NOT VERIFIED.
* `## Findings` — numbered `AI02-ACC-R<n>` with severity, blocking status, path/line,
  expected/actual, and the smallest correction/recheck. Re-use prior IDs where the finding persists.
* `## Check verification` — observed commands/reports and hosted checks; name anything unobserved.

APPROVE requires every canonical criterion satisfied at this snapshot, the repository invariants
intact, no open major finding, all prior findings repaired, and required local and hosted checks
observed green.
