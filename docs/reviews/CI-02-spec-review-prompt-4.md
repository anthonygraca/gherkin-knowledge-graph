# CI-02 specification review — submission 4

**Story:** CI-02 (#37), M4. **Feature:** `docs/stories/CI-02.feature`. **Companion:**
`docs/stories/CI-02.md`. **Prior verdict:** `docs/reviews/CI-02-spec-review-3.md`
(REQUEST_CHANGES: report-digest validation). **Resolution:** the contract now requires each input
report's `report_digest` to equal its recomputed canonical digest, adds the mismatch condition and
`invalid_input` refusal, and SCN-3505's outline includes `a report digest does not match its
contents`. The wrapped Gherkin step and the invalid `Given` step are now single valid lines; the
official parser accepts the feature.

Specification review only. Do not implement/edit/commit/delegate. Re-assess the feature and approve
only if implementation can begin without a silent design choice.

Output: `## Verdict`; `## Criterion assessment`; `## Findings` (`CI02-SPEC-R<n>`); `## Implementation readiness`.
