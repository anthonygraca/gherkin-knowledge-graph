# PG-01 retrospective

**Outcome.** An unmodified, CTA-free Gherkin repository is indexed read-only from a pinned commit
and queried by repository and revision; framework evidence is imported when supplied and abstained
from when absent.

**Defects found and repaired during the slice**

1. Adapter keys were built without the repository prefix, which would have collided across repos.
   Found by the collision test before any report was imported; repaired by passing the repository id
   into AST indexing.
2. `reports_for` initially selected reports by "executions exist" rather than tested-commit equality;
   repaired to require the snapshot's commit for every execution.
3. Report attribution originally relabelled the tested commit with the query revision. Repaired with
   `source` envelope content-hash comparison.
4. The external-project step assertion for the search-filter table was wrong (asserted header keys as
   data). Found when running the project's own suite; the fixture, not CTA, was at fault.
5. Clock-format mismatch (`Z` vs `+00:00`) in a BDD assertion; repaired by parsing the timestamp.

**Rework.** Two iterations on the registry ref/tag resolution (tags were not queryable after
indexing by tag), one on coverage counts (background steps double-counted), one on the inventory
schema (a list and a count shared the key `scenarios`).

**Process improvements.** Hand-label counts before running the indexer (done here), and keep a
"without evidence" assertion for every new evidence-shaped field. The benchmark is now the cheapest
way to re-check portability after a schema change.

**Resources.** No subagents; Codex review not yet submitted. Two dependency installs (`gherkin-official
43.0.0`, `@cucumber/cucumber 13.3.0`) were the only network steps.
