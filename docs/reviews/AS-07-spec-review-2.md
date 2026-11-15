## Verdict

**REVISE**

All five round-1 findings are repaired. One new blocking gap remains in historical provenance labels when an optional provider is disabled.

This is a read-only specification review. No files were changed, tests run, or work delegated.

## Round-1 dispositions

Locations refer to `docs/stories/AS-07.feature` and its normative companion, `docs/stories/AS-07.md`.

| Finding | Disposition | Exact revised location | Basis |
|---|---|---|---|
| AS07-SPEC-R1 | Repaired | Feature lines 18–20, 28–32; companion lines 27–50, 124–128 | Required problem extensions, effective-registry source, discovery timeout code, surface-specific mapping, and definite MINOR bump are explicit. |
| AS07-SPEC-R2 | Repaired | Feature lines 64–71; companion lines 104–110 | Only external transport is replaced; the real adapter, discovery route, mapping, and dashboard consumption are exercised without API stubs. |
| AS07-SPEC-R3 | Repaired | Feature lines 21–24, 33–38; companion lines 90–102 | The UI names the failed provider, presents registration alternatives, preserves baseline reads, and distinguishes failure from empty success and fallback. |
| AS07-SPEC-R4 | Repaired | Feature lines 50–60, 73–88; companion lines 66–88 | Covered surfaces, nonempty rejection history, consistent provenance presentation, and all six absent/null examples are specified. |
| AS07-SPEC-R5 | Repaired | Companion lines 112–116 | Fake discovery is explicitly the default offline documentation path, with a reproducible invocation deliverable verified by inspection. |

## New findings

1. **AS07-SPEC2-R1 — blocking — Historical provider classification depends on current registration.**

   **Location:** `docs/stories/AS-07.md`, lines 62–64 and 68–86; `docs/stories/AS-06.md`, lines 63–71 and 180–182.

   The new catalogue excludes optional providers absent from the effective registry, while every persisted proposal and history presentation must obtain its fixture/model label from that catalogue. Consider a recorded CocoIndex proposal reopened in default fake-only mode: its provider/model/index provenance survives, but the catalogue supplies no `kind`. AS-06’s snapshot contract does not retain `kind`, and AS-07 defines no missing-classification behavior. The required visible label therefore has no defined outcome in this ordinary offline-history case.

   **Smallest repair:** Define the label when a historical provider has no catalogue entry—for example, show “provider kind not recorded” while retaining its recorded provenance and applicable CTA-binding label—and add an observable example with a historical CocoIndex proposal under a fake-only registry. This need not prescribe a persistence implementation.

## Scenario assessment

PASS denotes readiness of the stated example, not executed behavior or completeness of the full specification. The new finding concerns an uncovered historical/offline combination.

| Scenario ID | Assessment | Basis |
|---|---|---|
| SCN-3101 | PASS | Registration error fields, visible provider/list behavior, and continued baseline access are explicit. |
| SCN-3102 | PASS | Timeout status/code, provider identity, stale-result exclusion, preserved data, and integrated verification boundary are defined. |
| SCN-3103 | PASS | Empty success retains provenance and remains distinct from unavailability. |
| SCN-3104 | PASS | A recorded rejection makes history coverage substantive and preserves fixture provenance. |
| SCN-3105 | PASS | Recorded adapter/API/UI behavior and CTA-binding presentation are distinguished from live inference claims. |
| SCN-3106 | PASS | Each absent/null provenance field has a defined display without configuration substitution. |

## Freeze conditions

- Resolve AS07-SPEC2-R1 with a normative historical-provider label rule and an observable offline-history example, then obtain re-review.