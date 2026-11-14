/**
 * Cucumber configuration for CTA's own acceptance suite.
 *
 * Feature files stay where the lifecycle put them (`docs/stories/*.feature`); nothing is copied or
 * rewritten. Two features are excluded by tag and documented in the inventory:
 * `@FT-03` (process/governance checks verified by inspection) and `@AI-06` (M3 slice).
 *
 * Reports are written as Cucumber Messages NDJSON, the same format the portable adapter ingests.
 */
export default {
  import: ['support/world.js', 'support/ui.js', 'step_definitions/**/*.js'],
  paths: ['../docs/stories/*.feature'],
  tags: 'not @FT-03 and not @AI-06 and not @superseded-by-AS-01 and not @refinement-draft',
  format: [
    'summary',
    'message:reports/cucumber-messages.ndjson',
    'json:reports/cucumber.json',
  ],
  formatOptions: { snippetInterface: 'async-await' },
  parallel: 1,
  retry: 0,
};
