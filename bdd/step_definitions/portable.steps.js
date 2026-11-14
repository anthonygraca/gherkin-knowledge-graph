import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { Given, Then, When } from '@cucumber/cucumber';

const BDD_ROOT = path.resolve(import.meta.dirname, '..');
const REPO_ROOT = path.resolve(BDD_ROOT, '..');
const REPORT_V1 = path.join(
  REPO_ROOT,
  'docs',
  'reports',
  'omp-m2-portability',
  'evidence',
  'cucumber-report.v1.ndjson',
);

function external(world) {
  if (!world.results.external) {
    world.results.external = world.call('external_build', {}).repositories;
  }
  return world.results.external;
}

function setup(world) {
  if (!world.results.portableSetup) {
    world.results.portableSetup = { indexes: [], reports: [] };
  }
  return world.results.portableSetup;
}

function indexExternal(world, name, ref) {
  const repo = external(world)[name];
  const indexes = setup(world).indexes;
  const entry = { path: repo.path, repository_id: name, revision: ref };
  if (!indexes.some((item) => item.repository_id === name && item.revision === ref)) {
    indexes.push(entry);
  }
  return { repo, entry };
}

function api(world, method, target, options = {}) {
  return world.call('api', {
    method,
    path: target,
    json: options.json,
    setup_portable: setup(world),
  });
}

function indexRepository(world, name, ref) {
  const repo = external(world)[name];
  const indexes = setup(world).indexes;
  if (!indexes.some((item) => item.repository_id === name && item.revision === ref)) {
    indexes.push({ path: repo.path, repository_id: name, revision: ref });
  }
  const response = api(world, 'POST', '/api/repositories/index', {
    json: { path: repo.path, repository_id: name, revision: ref },
  });
  assert.equal(response.status, 200, JSON.stringify(response.body));
  world.results.indexSummary = response.body;
  return response.body;
}

// ---------------------------------------------------------------- PG-01

Given('an independent Git repository contains valid untagged Gherkin scenarios', function () {
  const repo = external(this)['external-recipes'];
  this.results.externalRepo = 'external-recipes';
  this.results.externalRef = 'v1';
  this.results.beforeHashes = this.call('hashes', { path: repo.path });
  const inventory = this.call('inventory', { fixture: 'external-recipes' }).inventory;
  assert.equal(inventory.cta_annotations.length, 0);
  assert.equal(inventory.cta_requirement_files, 0);
  assert.equal(inventory.refs.v1.untagged_scenarios, 3);
});

Given('it has no CTA-specific source annotations or requirements inventory', function () {
  const repo = external(this)[this.results.externalRepo];
  const inventory = this.call('inventory', { fixture: this.results.externalRepo }).inventory;
  assert.deepEqual(inventory.cta_annotations, []);
  const hashes = this.call('hashes', { path: repo.path });
  assert.ok(!Object.keys(hashes.hashes).some((file) => file.startsWith('requirements/')));
});

When('CTA indexes a pinned commit in read-only mode', function () {
  this.results.indexSummary = indexRepository(
    this,
    this.results.externalRepo || 'external-recipes',
    this.results.externalRef || 'v1',
  );
});

Then('the scenarios and their steps are available through repository-scoped queries', function () {
  this.results.scenarios = api(
    this,
    'GET',
    '/api/repositories/external-recipes/scenarios?revision=v1',
  );
  assert.equal(this.results.scenarios.status, 200);
  assert.equal(this.results.scenarios.body.scenarios.length, 4);
  const tagged = this.results.scenarios.body.scenarios.find((scenario) =>
    scenario.tags.includes('@SCN-001'),
  );
  this.results.tagged = tagged;
  const steps = api(
    this,
    'GET',
    `/api/repositories/external-recipes/steps?revision=v1&scenario_key=${encodeURIComponent(tagged.scenario_key)}`,
  );
  assert.equal(steps.status, 200);
  assert.ok(steps.body.steps.length >= 3);
});

Then('their exact source locations and revision are returned', function () {
  const summary = this.results.indexSummary;
  assert.equal(summary.revision.length, 40);
  assert.equal(this.results.tagged.path, 'features/browse.feature');
  assert.equal(this.results.tagged.line, 16);
  assert.ok(this.results.tagged.scenario_key.startsWith('external-recipes:features/browse.feature#SCN-L'));
  assert.equal(this.results.scenarios.body.revision, summary.revision);
  assert.match(this.results.scenarios.body.source_digest, /^sha256:[0-9a-f]{64}$/);
});

Then("the repository's tracked files remain byte-identical", function () {
  const repo = external(this)[this.results.externalRepo];
  const after = this.call('hashes', { path: repo.path });
  assert.deepEqual(after.hashes, this.results.beforeHashes.hashes);
  assert.equal(after.status, '');
});

Then('missing requirement links are not reported as an implementation failure', function () {
  const findings = api(
    this,
    'GET',
    '/api/repositories/external-recipes/executable-findings?revision=v1',
  );
  assert.equal(findings.status, 200);
  assert.deepEqual(findings.body.findings, []);
  assert.ok(!JSON.stringify(findings.body).includes('missing_verification_link'));
});

Given('an independent repository whose test hooks would write a sentinel file', function () {
  const repo = external(this)['external-twin'];
  this.results.externalRepo = 'external-twin';
  this.results.externalRef = 'v1';
  assert.ok(!fs.existsSync(path.join(repo.path, 'sentinel.txt')));
});

When('CTA indexes it', function () {
  this.results.indexSummary = indexRepository(
    this,
    this.results.externalRepo,
    this.results.externalRef,
  );
});

Then('no hook or step definition from it was executed', function () {
  const repo = external(this)[this.results.externalRepo];
  assert.ok(!fs.existsSync(path.join(repo.path, 'sentinel.txt')), 'the twin hook executed');
});

Then('the index reports zero modified files', function () {
  assert.equal(this.results.indexSummary.files_modified, 0);
  assert.equal(this.results.indexSummary.hooks_executed, false);
});

Given('an external repository contains Gherkin steps', function () {
  indexExternal(this, 'external-recipes', 'v1');
  this.results.queryRepo = 'external-recipes';
});

Given('no supported framework matching report is available', function () {
  assert.equal(setup(this).reports.length, 0);
});

When('CTA queries step-to-definition resolution', function () {
  this.results.bindings = api(
    this,
    'GET',
    '/api/repositories/external-recipes/bindings?revision=v1',
  );
  this.results.unresolved = api(
    this,
    'GET',
    '/api/repositories/external-recipes/unresolved-steps?revision=v1',
  );
});

Then('the result is UNKNOWN or NOT_AVAILABLE', function () {
  assert.equal(this.results.bindings.status, 200);
  assert.equal(this.results.bindings.body.availability, 'not_available');
  assert.deepEqual(this.results.bindings.body.resolutions, []);
  assert.match(this.results.bindings.body.reason, /unknown, not undefined/);
});

Then('no undefined-step defect is asserted from missing metadata alone', function () {
  assert.equal(this.results.unresolved.body.availability, 'not_available');
  assert.deepEqual(this.results.unresolved.body.resolutions, []);
  const findings = api(
    this,
    'GET',
    '/api/repositories/external-recipes/executable-findings?revision=v1',
  );
  assert.deepEqual(findings.body.findings, []);
});

Given('an external repository has a trusted Cucumber execution report', function () {
  const { repo } = indexExternal(this, 'external-recipes', 'v1');
  this.results.testedCommit = repo.tags.v1;
  assert.ok(fs.existsSync(REPORT_V1));
});

When('CTA ingests the report against the corresponding Git revision', function () {
  setup(this).reports.push({
    repository_id: 'external-recipes',
    report_path: REPORT_V1,
    metadata_path: REPORT_V1.replace(/\.ndjson$/, '.meta.json'),
    tested_commit: this.results.testedCommit,
  });
  this.results.import = api(this, 'POST', '/api/repositories/external-recipes/reports', {
    json: {
      report_path: REPORT_V1,
      metadata_path: REPORT_V1.replace(/\.ndjson$/, '.meta.json'),
      tested_commit: this.results.testedCommit,
    },
  });
  assert.equal(this.results.import.status, 200, JSON.stringify(this.results.import.body));
  this.results.bindings = api(
    this,
    'GET',
    '/api/repositories/external-recipes/bindings?revision=v1',
  );
  this.results.executions = api(
    this,
    'GET',
    '/api/repositories/external-recipes/executions?revision=v1',
  );
  this.results.relations = api(
    this,
    'GET',
    '/api/repositories/external-recipes/relations?revision=v1',
  );
});

Then('reported Gherkin step matches and outcomes are linked to their definitions', function () {
  assert.equal(this.results.bindings.body.availability, 'available');
  assert.equal(this.results.bindings.body.step_definitions.length, 13);
  const matched = this.results.bindings.body.resolutions.filter(
    (resolution) => resolution.status === 'matched',
  );
  assert.equal(matched.length, 23);
  assert.ok(matched.every((resolution) => resolution.definition_keys.length === 1));
  assert.equal(this.results.executions.body.executions.length, 5);
  assert.ok(
    this.results.executions.body.executions.every((execution) => execution.outcome === 'passed'),
  );
  assert.ok(this.results.executions.body.executions.every((execution) => execution.steps.length >= 3));
});

Then('each relationship identifies its report provenance and tested commit', function () {
  const relations = this.results.relations.body.relations;
  const matched = relations.filter((relation) => relation.relation === 'MATCHES_DEFINITION');
  const observed = relations.filter((relation) => relation.relation === 'EXECUTED_DEFINITION');
  assert.ok(matched.length > 0 && observed.length > 0);
  for (const relation of matched) {
    assert.ok(relation.provenance.report_digest);
    assert.equal(relation.origin, 'matched');
  }
  for (const relation of observed) {
    assert.ok(relation.provenance.execution_key);
    assert.equal(relation.provenance.report_digest, this.results.import.body.report_digest);
    assert.equal(relation.origin, 'observed');
  }
  assert.equal(this.results.import.body.tested_commit, this.results.testedCommit);
});

Then('no unobserved production-code execution is inferred', function () {
  const relations = this.results.relations.body.relations;
  const allowed = new Set([
    'HAS_STEP',
    'EXPANDS_TO',
    'MATCHES_DEFINITION',
    'HAS_STEP_EXECUTION',
    'EXECUTED_DEFINITION',
  ]);
  assert.ok(relations.every((relation) => allowed.has(relation.relation)));
  assert.ok(relations.every((relation) => !['INVOKES', 'CALLS', 'EXERCISED_IN'].includes(relation.relation)));
  const definitions = this.results.bindings.body.step_definitions;
  assert.ok(definitions.every((definition) => definition.source_path.endsWith('.js')));
});

Given('two independent repositories use the same scenario tag and relative path', function () {
  indexExternal(this, 'external-recipes', 'v1');
  indexExternal(this, 'external-twin', 'v1');
  this.results.keys = {};
});

When('CTA indexes each at its own pinned revision', function () {
  for (const name of ['external-recipes', 'external-twin']) {
    const response = api(this, 'GET', `/api/repositories/${name}/scenarios?revision=v1&tag=SCN-001`);
    assert.equal(response.status, 200);
    assert.equal(response.body.scenarios.length, 1);
    this.results.keys[name] = response.body.scenarios[0];
  }
});

Then('each scenario has a distinct repository-scoped identity', function () {
  const first = this.results.keys['external-recipes'];
  const second = this.results.keys['external-twin'];
  assert.equal(first.path, second.path);
  assert.notEqual(first.scenario_key, second.scenario_key);
  assert.ok(first.scenario_key.startsWith('external-recipes:'));
  assert.ok(second.scenario_key.startsWith('external-twin:'));
});

Then("querying one repository does not include the other's records", function () {
  const twin = api(this, 'GET', '/api/repositories/external-twin/scenarios?revision=v1');
  assert.equal(twin.body.scenarios.length, 1);
  assert.equal(twin.body.scenarios[0].path, 'features/browse.feature');
  assert.ok(twin.body.scenarios[0].scenario_key.startsWith('external-twin:'));
  assert.ok(!twin.body.scenarios.some((scenario) => scenario.path === 'features/publish.feature'));
  const recipes = api(this, 'GET', '/api/repositories/external-recipes/scenarios?revision=v1');
  assert.ok(!recipes.body.scenarios.some((scenario) => scenario.scenario_key.startsWith('external-twin:')));
});

Given('an external repository contains a Rule and a Scenario Outline with Examples', function () {
  indexExternal(this, 'external-recipes', 'v1');
});

When('its features are parsed at a pinned commit', function () {
  const response = api(
    this,
    'GET',
    '/api/repositories/external-recipes/scenarios?revision=v1&path=features%2Fbrowse.feature',
  );
  assert.equal(response.status, 200);
  this.results.browse = response.body.scenarios;
});

Then('the rule and both example instances are queryable', function () {
  const outline = this.results.browse.find((scenario) => scenario.kind === 'scenario_outline');
  assert.ok(outline);
  assert.equal(outline.rule_name, 'Only published recipes are visible');
  assert.equal(outline.instances.length, 2);
  assert.deepEqual(
    outline.instances.map((instance) => instance.example_values.term),
    ['soup', 'toast'],
  );
  assert.ok(outline.instances[0].instance_key.endsWith('/EX-1'));
});

Then('the data table and doc string are kept as step arguments', function () {
  const outline = this.results.browse.find((scenario) => scenario.kind === 'scenario_outline');
  const tableStep = outline.steps.find((step) => step.data_table);
  assert.deepEqual(tableStep.data_table[0], ['filter', 'value']);
  const docStep = outline.steps.find((step) => step.doc_string);
  assert.match(docStep.doc_string, /query: <term>/);
  const instance = outline.instances[0];
  assert.equal(instance.steps.find((step) => step.doc_string).doc_string.trim(), 'query: soup');
});

// ---------------------------------------------------------------- GT-03

Given('an external repository indexed at a pinned commit with an imported report', function () {
  const { repo } = indexExternal(this, 'external-recipes', 'v1');
  this.results.testedCommit = repo.tags.v1;
  setup(this).reports.push({
    repository_id: 'external-recipes',
    report_path: REPORT_V1,
    metadata_path: REPORT_V1.replace(/\.ndjson$/, '.meta.json'),
    tested_commit: this.results.testedCommit,
  });
  this.results.bindings = api(
    this,
    'GET',
    '/api/repositories/external-recipes/bindings?revision=v1',
  );
  this.results.relations = api(
    this,
    'GET',
    '/api/repositories/external-recipes/relations?revision=v1',
  );
});

When('the executable relations are queried', function () {
  assert.equal(this.results.relations.status, 200);
});

Then('matched relationships name definitions with source locators', function () {
  const matched = this.results.relations.body.relations.filter(
    (relation) => relation.relation === 'MATCHES_DEFINITION',
  );
  assert.ok(matched.length > 0);
  const keys = new Set(this.results.bindings.body.step_definitions.map((item) => item.definition_key));
  assert.ok(matched.every((relation) => keys.has(relation.target_key)));
  assert.ok(
    this.results.bindings.body.step_definitions.every(
      (definition) => definition.source_path && definition.line >= 1,
    ),
  );
});

Then('observed relationships name an execution key', function () {
  const observed = this.results.relations.body.relations.filter(
    (relation) => relation.relation === 'EXECUTED_DEFINITION',
  );
  assert.ok(observed.length > 0);
  assert.ok(observed.every((relation) => relation.provenance.execution_key));
});

Then('no relation claims production-code execution', function () {
  assert.ok(
    this.results.relations.body.relations.every(
      (relation) => !['INVOKES', 'CALLS', 'EXERCISED_IN'].includes(relation.relation),
    ),
  );
});

Given('an indexed repository without an imported report', function () {
  indexExternal(this, 'external-recipes', 'v1');
  assert.equal(setup(this).reports.length, 0);
});

When('executions are queried', function () {
  this.results.executions = api(
    this,
    'GET',
    '/api/repositories/external-recipes/executions?revision=v1',
  );
});

Then('coverage reports every scenario as unexecuted', function () {
  assert.equal(this.results.executions.status, 200);
  const coverage = this.results.executions.body.coverage;
  assert.deepEqual(this.results.executions.body.executions, []);
  assert.equal(coverage.scenarios_executed, 0);
  assert.equal(coverage.scenarios_without_execution, coverage.scenarios_total);
});

Then('no execution evidence is fabricated', function () {
  assert.deepEqual(this.results.executions.body.reports, []);
  const findings = api(
    this,
    'GET',
    '/api/repositories/external-recipes/executable-findings?revision=v1',
  );
  assert.deepEqual(findings.body.findings, []);
  assert.equal(findings.body.tested_commit, null);
});


Given('an external repository indexed at a pinned commit', function () {
  const { repo } = indexExternal(this, 'external-recipes', 'v1');
  this.results.testedCommit = repo.tags.v1;
});

Given('a Cucumber report whose provenance sidecar is missing', function () {
  assert.ok(fs.existsSync(REPORT_V1));
});

When('CTA imports the report', function () {
  this.results.import = api(this, 'POST', '/api/repositories/external-recipes/reports', {
    json: { report_path: REPORT_V1, tested_commit: this.results.testedCommit },
  });
});

Then('the import is refused with {string}', function (code) {
  assert.equal(this.results.import.status, 400);
  assert.equal(this.results.import.body.code, code);
});

Then('no execution records are stored', function () {
  const executions = api(
    this,
    'GET',
    '/api/repositories/external-recipes/executions?revision=v1',
  );
  assert.deepEqual(executions.body.executions, []);
  assert.deepEqual(executions.body.reports, []);
});
