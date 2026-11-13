# AI-06 PR 1 — retrospective

**Slice:** RAG mission PR 1 (CocoIndex variant). **Outcome:** independent **APPROVE** at
submission 5 of 7; one minor metadata finding repaired after approval. The slice is implemented,
verified, and ready for the commit/publication gate. It is not a milestone closure.

## What went well

* The criteria advisory caught provenance/over-claim wording before implementation; the feature
  already distinguished configured context from observed index identity.
* The live smoke exercised the real MCP contract early, producing a captured fixture and exposing
  the actual tool schema instead of assuming it.
* The offline design (fake transport + stub MCP process) covered failure, bounds, cleanup, and
  environment filtering without requiring `ccc`, Ollama, or a network.
* The probe's measured lifecycle observation made the `ccc mcp` background-index effect visible
  rather than hiding it behind `refresh_index=false`.
* The final schema/envelope repairs converged on strict, conservative validation: field-specific
  allowlists and independent normalization.

## Rework

| Round | Findings | Effect |
| --- | --- | --- |
| Criteria advisory | 9 (REVISE) | Revised the feature before code |
| Review 1 | 8 (R1–R8) | Lifecycle isolation, schema structure, write deadline, cleanup, content envelope, probe status, live manifest, commit refs |
| Review 2 | 3 open (R1/R2/R5) | Absolute isolation paths, nullable/constraint checks, envelope agreement |
| Review 3 | 2 open (R2/R5) | Conservative keyword allowlists, strict JSON equality |
| Review 4 | 2 open (R2/R5) | Field-specific allowlists, independent normalization of every representation |
| Review 5 | APPROVE + AI06-R9 minor | Report metadata corrected |

The dominant rework was the external MCP/schema contract: each round exposed a new class of
implicit assertion or Python coercion. The final design validates both representations
independently and uses narrow per-field schema allowlists.

## Resources

* Codex advice: one criteria advisory (48,565 CLI-reported tokens).
* Codex acceptance reviews: five submissions (602.93 s, 228.91 s, 185.69 s, 171.26 s, 229.79 s).
* No OMP delegates were spawned; delegate resource data is `unavailable`, not zero.
* Live resources: one isolated CocoIndex daemon/index, localhost Ollama via a process-local
  port-forward, synthetic banking snapshot. Index build 2m31.9 s cold; warm search 0.86–0.99 s.
* Final tests: 402 backend passed / 3 skipped; 117 CocoIndex contracts; 1 live test; network-denied
  suite 402 passed / 3 skipped.

## What went poorly

* The first live index attempt contended with a pre-existing shared daemon and ran >8 minutes
  before being killed; isolation was adopted only after that.
* The first implementation claimed `refresh_index=false` implied no index mutation. The entry point
  schedules its own background index; that was discovered in review and required a semantic and
  documentation correction.
* Several repair rounds fixed one schema/envelope example at a time before moving to a
  field-specific/independent-validation design.
* The pre-review implementation report retained a stale criteria hash; a reviewer caught it as a
  minor finding.

## Better next time

1. Inspect the external entry point's startup side effects (daemon, background tasks) before
   claiming a read-only/no-mutation behavior.
2. Treat an external tool's schema as a contract to validate per field, not a bag of property
   names; enumerate allowed keywords rather than denying known-bad ones.
3. Validate every representation of a response independently before comparing/selecting it; do not
   rely on Python equality for JSON.
4. Keep report metadata (criteria hash, submission count, test counts) generated or updated as part
   of the final gate, not left for the reviewer.

## New run rule

**Probe an external tool's startup lifecycle before describing it as read-only.** Record daemon,
background-task, and index effects, and validate subprocess paths as absolute/resolved before
spawning. This is folded into the mission run rules for later slices.
