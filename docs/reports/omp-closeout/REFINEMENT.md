# Close-out refinement — Codex advisory outcome

**Date:** 2026-11-14 · **Base:** `140e98c` · **Advisor:** `gpt-6.1-sol`, reasoning effort high,
read-only, exit 0. Request `advice/request.md`; output `advice/closeout-advice.md`
(`sha256:346e721b…`). This is advice, not acceptance review or approval.

## Readiness verdicts

| Story | Verdict | Blocking decision |
| --- | --- | --- |
| AS-06 #28 | needs-design-decision | Trusted-local-operator identity vs stronger auth; append-only journal/workspace design |
| AS-07 #29 | ready-after-spec | AS-06 proposal UI dependency |
| AI-02 #31 | blocked | Exact same-machine model, weights digest, licence, runtime, hardware |
| AI-03 #32 | needs-design-decision | Adopt proposed snapshot/cache re-scope vs retain unverifiable embedding claim |
| CI-01 #36 | gated | M3 exit plus two-scope framing (self-assurance vs banking fixture) |
| CI-02 #37 | gated | CI-01 report contract plus portable-locator comparison limitation |

## Refined artifacts (drafts, not approved, not executed)

| Feature | Scenarios | sha256 |
| --- | --- | --- |
| `docs/stories/AS-06.feature` | 11 (`SCN-3001…3011`) | `c0dd1523…` |
| `docs/stories/AS-07.feature` | 6 (`SCN-3101…3106`) | `86ef9c44…` |
| `docs/stories/AI-02.feature` | 6 (`SCN-3201…3206`) | `5c583594…` |
| `docs/stories/AI-03.feature` | 6 (`SCN-3301…3306`) | `01f0d5ba…` |
| `docs/stories/CI-01.feature` | 6 (`SCN-3401…3406`) | `ec53d9f0…` |
| `docs/stories/CI-02.feature` | 6 (`SCN-3501…3506`) | `7f5bf349…` |

Companions: `docs/stories/<ID>.md`. Proposed cross-cutting decisions:
`docs/adr/0012-closeout-scope-decisions.md` (status Proposed).

All drafts carry `@refinement-draft`; the Cucumber configuration excludes that tag, and the feature
inventory records them as `not_executed` with reasons. They are specifications, not execution evidence.
The suite remains **115 scenarios / 957 results**, strict gate ok.

## Owner decisions required before implementation

1. **AS-06 identity:** accept trusted-local-operator (loopback, configured operator, server-assigned
   identity, unset disables writes) or require stronger authentication.
2. **AI-02 model:** accept a concrete same-machine model manifest (identifier, weights digest,
   licence, runtime, hardware) and the egress-denial verification method.
3. **AI-03 scope:** adopt the snapshot/cache-lifecycle re-scope, or retain the original obligation and
   accept that it remains blocked.
4. **CI scope/diff:** accept the two-scope framing (CTA self-assurance vs banking fixture) and the
   refusal to classify portable source-locator findings across revisions without a reviewed mapping.

## Recommended implementation order after decisions

1. AS-07 after spec review (no live model).
2. AS-06 after identity/journal design.
3. CI-02 then CI-01 after M3 exit.
4. AI-02/AI-03 deterministic work in parallel; real AI-02 only after model acceptance.
5. M3 milestone review, then M4 integration/review.

## Verification of this refinement

* All six features parse with the official Gherkin parser; 41 scenario IDs total, all unique.
* Inventory regenerated (41 tracked feature files); drafts marked `not_executed` with reasons.
* Full Cucumber suite with drafts excluded: 115/115 scenarios, 957/957 results; gate ok.
* No implementation files changed; no owner decision is represented as approved.
