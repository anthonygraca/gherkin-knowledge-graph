## Verdict

**REVISE**

The owner-approved re-scope honestly supersedes the embedding-count and vector-retention promises. Content-based cache identity, commit-bound snapshots, configuration invalidation, evidence-only reuse, and failure isolation are substantially specified. Two contract ambiguities block freezing.

This is a specification-readiness verdict only. No files were edited, tests run, or work delegated.

## Findings

1. **AI03-SPEC-R1 — blocking — SCN-3305; companion “Candidate combination” and “Contract impact”.**

   AI-03 requires each candidate’s `index_revision` to equal the lifecycle manifest’s `snapshot_binding`. However, the existing `TraceCandidate` contract describes an index content fingerprint, and existing discovery producers calculate their own fingerprints/bindings. The specification does not identify a producer or adaptation boundary that supplies candidates carrying the new lifecycle binding, while claiming no change to `TraceCandidate`.

   The service/API rejection and no-list outcomes are explicit, but independent tests lack a defined relationship between actual discovery outputs and the expected manifest context. Merely replacing candidate provenance with a chosen binding would conceal this gap.

   **Smallest precise repair:** define the producer or validated adaptation boundary for lifecycle-bound candidates; explicitly distinguish the CTA snapshot binding from CocoIndex’s unavailable internal identity; reconcile the existing provenance documentation. Specify a compatible-input success example and a mixed-binding rejection example through the actual combination service/API, preserving the supplied candidate provenance.

2. **AI03-SPEC-R2 — blocking — SCN-3301, “the manifest records both resolved revisions and their artifact content hashes”.**

   The scenario invokes the planner but asserts an unspecified manifest outcome. `ContentChangePlan` identifies both commits, while `RetrievalManifest` holds the current commit/artifact hashes and an optional `previous_snapshot_binding`. Neither directly contains both revisions’ artifact hash sets. The companion does not say that this assertion means following the previous-manifest reference.

   Independent tests could therefore assert different objects and different provenance guarantees.

   **Smallest precise repair:** state that the plan reports both resolved commits, and that the current and referenced previous immutable manifests record their respective artifact hashes. Require the previous reference to resolve to the compared manifest. Adjust SCN-3301 accordingly without changing its ID.

3. **AI03-SPEC-R3 — nonblocking — SCN-3306; companion “Refresh and honest reporting”.**

   `elapsed_ms` is described as measured refresh cost without defining its measurement interval. The exact-binding reuse branch also returns an existing manifest unchanged, leaving readers to infer that its elapsed time and counts describe the original publication rather than the current request.

   **Smallest precise repair:** name the timed phase and exclusions, and explicitly identify returned measurements as historical publication observations on an exact-binding cache hit. Add this distinction to the verification plan.

## Scenario assessment

PASS denotes specification readiness, not passing execution evidence.

| Scenario ID | Readiness | Assessment |
|---|---|---|
| SCN-3301 | FAIL | Change sets are explicit; the object carrying before/after provenance needs R2. |
| SCN-3302 | PASS | Equal content/configuration shares a cache key while retaining distinct commit bindings; companion specifies adapter-free reuse. |
| SCN-3303 | PASS | Weights changes invalidate cache compatibility and preserve the old manifest. |
| SCN-3304 | PASS | Typed failure, no new publication, preservation of the old snapshot, and no baseline substitution are specified. |
| SCN-3305 | FAIL | Rejection and no partial list are explicit; lifecycle candidate provenance needs R1. |
| SCN-3306 | PASS | Required measurements and unavailable embedding data are distinguished; R3 would clarify timing attribution. |

SCN-3301…SCN-3306 retain their identities from the committed refinement draft, occur uniquely among development feature declarations, and match AI-03’s recorded range.

## Freeze conditions

1. Resolve AI03-SPEC-R1 in the canonical criteria, companion, and affected provenance contracts.
2. Resolve AI03-SPEC-R2 with an explicit, observable before/after provenance assertion.
3. Independently re-review the revised specification while preserving all six scenario IDs.