# external-recipes — an independently styled Gherkin project

This fixture stands in for a repository that was built **without** CTA. It has never adopted
`@SCN-nnn` identities, `# cta:artifact` annotations, YAML requirement front matter, accepted-link
files, or an evidence JSON file. It contains ordinary Gherkin, ordinary JavaScript step
definitions, and its own tiny application module.

Two properties are load-bearing for the portability gate:

1. **No CTA metadata exists anywhere in `tree/`.** Tests assert that the only `@SCN-`-looking tag
   is `@SCN-001`, and that it is *not* used as an identity by CTA: portable discovery derives its
   own repository-scoped keys from the pinned commit and source locators.
2. **The fixture is read-only input.** Indexing runs no step definition, executes no hook, and
   writes nothing. The optional benchmark executor runs the project's own Cucumber suite in an
   isolated copy, outside the indexing path.

`expected/inventory.json` is hand-labeled: the counts were written from the feature files below,
not produced by the indexer. `tools/external_fixture.py` builds the deterministic Git history used
by tests and demos (tags `v1` and `v2`).
