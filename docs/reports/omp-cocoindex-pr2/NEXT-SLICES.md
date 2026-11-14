# Next slices — independently assignable briefs (not started)

PR 2 is approved at submission 5 of 7. No later slice is authorized by this report.

## PR 3 — GraphRAG evidence retrieval

Requires its own verified story issue and human-reviewed `.feature`. Consume only accepted links and
actual evidence; proposed links remain a separate labelled set. Return authoritative graph context
separately from CocoIndex candidates; validate every citation against the retrieved set; deterministic
assurance decides findings, an optional chat provider only explains. REQ-001 must match the M1 thread;
REQ-002 must abstain from a verification claim; prompt-injection probes cannot create links/evidence.

## PR 4 — evaluation and workflow integration

Compare lexical code retrieval (A), CocoIndex code retrieval (B), accepted-graph traversal (C), and
hybrid retrieval (D) on identical snapshots/queries/labels for A/B and explicitly analyse the extra
information C/D receive. Measure Recall@1/5/10, precision, MRR, path/citation accuracy, unsupported
assertion rate, abstention, false proposals, contamination, latency, index freshness/rebuild cost,
and resources. PR 4 does not close M4 and cannot substitute for M3 acceptance.

## AI-07 follow-ups

- Add scenario-step/feature context to the query template as a separately evaluated change.
- Scenario/requirement semantic indexing remains out of scope for a code corpus.
- A second framework/index or larger real-repository benchmark needs its own reviewed story.
