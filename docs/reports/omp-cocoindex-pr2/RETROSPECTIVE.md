# AI-07 PR 2 retrospective

**Outcome.** Scenario requests now return baseline-bound source/test proposals with path, lines,
revision, hash, method, model identity, and a CTA snapshot binding. Offline lexical and fake
CocoIndex paths pass; live CocoIndex ran on synthetic snapshots at both baselines. The measured
result on this six-file corpus is **negative for CocoIndex**: no Recall@1 gain over lexical and more
false candidates at ~1 s/query. That is recorded as a valid result, not hidden.

**Defects and rework**

1. Live root validation initially compared the built fixture repository instead of the configured
   CocoIndex project root; fixed to use `client.transport.project_root`.
2. The CocoIndex captured response used `src/__init__.py`, which is not an artifact. The mapping
   correctly surfaced it as unresolved; the evaluation labels exclude it, and the test asserts the
   unresolved behavior.
3. A Cucumber scenario originally used the generic "code discovery runs" step, so the injected
   payload was ignored and lexical fallback was measured. The scenario now names the response and
   asserts the method, exposing the mismatch.
4. The inventory bootstrap needed two full suite runs after adding AI-07: the generator refuses a
   declared-executed feature absent from the captured report. The first run produced the report;
   the second is the final green evidence. This is expected with the evidence-derived inventory.
5. The full BDD suite initially omitted AI-07 from the committed inventory; GT-02's list-equality
   check caught it before the slice could be reviewed.

**Resources.** One coordinator (OMP), no delegates. Live indexing used an already-running local
Ollama endpoint; no port-forward was started. Index builds took 12.6 s and 8.1 s on 12 files.

**Process improvement.** Adding a new canonical feature requires regenerating the inventory from a
run that includes it; do the bootstrap run before the review submission so the suite can be green on
the first captured evidence.
