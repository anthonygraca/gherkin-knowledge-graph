# Executable Gherkin retrospective

**Outcome.** CTA's M0/M1 acceptance specifications execute through Cucumber-JS against the real
application, with a captured messages report and a gate that fails on undefined/ambiguous/pending
steps. The portable and M2 assurance surfaces have their own canonical features and execute too.

**Defects and rework**

1. `DT-02` SCN-527 was not valid Gherkin: one step was split across two physical lines. Found by the
   official parser on the first suite run. Repaired by joining the lines; wording unchanged.
2. Probe suites inherited `bdd/cucumber.mjs` and re-entered the whole acceptance suite, recursively.
   Found as a 20-minute hang; repaired with `bdd/probes/cucumber.mjs` (empty imports/paths) and
   `--config`. This was a harness bug, not a product bug.
3. An early gate implementation mixed step results across test cases. Repaired by iterating the
   started attempt ids per case before this report.
4. Duplicate step definitions (`a {string} finding is produced for {string}`, `the revision is
   ingested`) produced ambiguity; removed the duplicates and anchored the links regex.
5. A step assertion compared `EV-002`'s timestamp format (`Z` vs `+00:00`); repaired by parsing.
6. `FT-02` SCN-205 encodes the M0 501 contract that AS-01 superseded. Tagged and excluded; not
   rewritten.

**What worked.** Pushing assumptions into the Python bridge kept one implementation of the domain.
Hand-counting the external inventories before indexing made the benchmark meaningful. Building the
gate before trusting the suite caught the recursion and the parser defect.

**What remains.** Browser-level bindings for AS-04/AS-05 and commit-history bindings for SETUP-01.
GT-02 is therefore open; the inventory states this and M2 is reported as checkpointed, not complete.

**Resources.** No subagents. One-time `npm install` (87 packages) and `uv add gherkin-official`.
Codex acceptance review not yet run at record time.
