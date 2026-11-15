## Verdict

REVISE

The accepted manifest fixes the model, licence, runtime, hardware, formatting, and measured limits sufficiently for this scope. The documents correctly distinguish a one-corpus smoke measurement from retrieval quality. Blocking gaps remain in default selection and contract coverage.

This is a specification review only. No files were changed, tests executed, or acceptance evidence verified.

## Findings

1. **AI02-SPEC-R1 — blocking — SCN-3201: explicit fake selection does not verify the default.**  
   “When fake discovery is requested” could pass even if an unqualified discovery request selected another provider.  
   **Smallest repair:** request discovery without a provider override, using default settings with no local opt-in, and retain the assertion that the effective provider is `fake` and no model or network activity occurs.

2. **AI02-SPEC-R2 — blocking — SCN-3203 and companion failure modes: missing runtime has no canonical acceptance case.**  
   SCN-3201 establishes operation without a runtime only when local inference is disabled. SCN-3203 covers absent weights, leaving explicitly enabled local inference with installed weights but a missing runtime unspecified by the scenarios. Digest mismatch is also promised by the companion and domain contract without a corresponding case.  
   **Smallest repair:** retain SCN-3203’s identity and make it an outline covering absent weights, mismatched weights digest, and installed weights with the runtime package unavailable. Each case must return `503 retrieval-unavailable`, without download, fallback, candidates, or accepted-link/evidence/finding mutation.

3. **AI02-SPEC-R3 — blocking — SCN-3204/SCN-3205: the shared contract cases are insufficiently identified and permit vacuous coverage.**  
   The companion names categories, but does not identify the shared cases or their independent inputs and expectations. The listed candidate assertions can all hold for an empty list. A legitimate empty result retaining response provenance and unavailable provenance producing an honest failure are not specified for this adapter. “Embedding and search transports” also leaves unclear how much discovery behavior may be replaced.  
   **Smallest repair:** identify the unchanged shared cases in the companion and explicitly exercise the real `LocalEmbeddingCandidateDiscovery.discover` boundary, substituting only the embedding runtime offline. Include a deterministic nonempty case, a legitimate empty case retaining provider/model/index response provenance, and an unavailable-provenance case that fails explicitly without inventing values. Reuse the applicable cases with the real runtime in SCN-3205.

4. **AI02-SPEC-R4 — nonblocking — SCN-3205: retain the observations supporting the live preconditions.**  
   Namespace isolation and the exact manifest make the requirements independently inspectable. However, the required execution record currently names digest/runtime/formatting values without explicitly retaining the egress-denial observation or their comparison with the accepted manifest. The environment flag alone establishes neither.  
   **Smallest repair:** require the live record to retain the namespace/enforcement check and denied external probe, and confirm that observed weights/runtime/formatting match the identified manifest revision or hash. Unavailable observations must remain unavailable, never be filled from expected values.

## Scenario assessment

| Scenario ID | Readiness | Assessment |
|---|---|---|
| SCN-3201 | FAIL | Fake operation is observable; default selection is not exercised. R1. |
| SCN-3202 | PASS | Remote-endpoint refusal, API error, no connection, and no candidates are observable. |
| SCN-3203 | FAIL | Missing-runtime and digest-mismatch coverage needs canonical cases. R2. |
| SCN-3204 | FAIL | Shared cases, substitution boundary, nonempty/empty outcomes, and unavailable provenance need clarification. R3. |
| SCN-3205 | FAIL | Live isolation and manifest requirements are inspectable, and `@live-local` separation is clear; the shared-case ambiguity remains. R3. |
| SCN-3206 | PASS | Non-finite output has an observable typed failure, no partial results, and explicit no-write outcomes. |

SCN-3201…SCN-3206 are unique among the current development feature declarations, retain their original refinement identities, and match AI-02’s recorded range. PASS denotes specification readiness, not verified execution.

## Freeze conditions

- Resolve AI02-SPEC-R1, R2, and R3 while preserving scenario identities.
- Update the companion’s scenario-to-verification mapping and submit the revised specification for independent re-review.