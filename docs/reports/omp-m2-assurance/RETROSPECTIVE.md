# M2 assurance retrospective

**Outcome.** A→B change produces `reverification_required` for REQ-001/SCN-001/CODE-001 with EV-001;
REQ-003/SCN-003/TEST-002 produce `verification_failed` with EV-003; baseline-a produces neither. The
rule engine is compared field-by-field with the hand-labeled oracle.

**Defects found while implementing**

1. Relation grouping assumed every relation's source was a scenario, which made every requirement
   look unverified. Caught immediately by the oracle-equality test.
2. `label_of` returned a raw SHA for the source commit, so the explanation text differed from the
   oracle. Repaired with content-based baseline labelling — the same semantic the freshness rule
   needs.
3. Removing the sample-findings replay broke an M1 contract test that mutated the sample file; the
   test now probes the candidate index, which the app still loads from fixtures. The M1 rule tests
   were narrowed to the finding type they assert instead of the whole response.
4. Dashboard findings region initially duplicated requirement buttons and region names, breaking
   existing accessibility queries; moved to its own section with distinct button labels.

**Tradeoffs.** M2 uses file-level content hashes and only the latest run per scenario (ADR 0005).
`artifacts_at` can read arbitrary commits, which is required for evidence-only commits but widens
the port; an unreadable commit is treated as non-applicable, never as failure.

**Resources.** No subagents; review pending.
