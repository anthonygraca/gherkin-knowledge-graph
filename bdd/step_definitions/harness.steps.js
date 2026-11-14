import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { Given, Then, When } from '@cucumber/cucumber';

const BDD_ROOT = path.resolve(import.meta.dirname, '..');
const REPO_ROOT = path.resolve(BDD_ROOT, '..');
const CUCUMBER = path.join(BDD_ROOT, 'node_modules', '.bin', 'cucumber-js');
const GATE = path.join(BDD_ROOT, 'tools', 'step-resolution.mjs');

function runProbe(name, extraArgs = []) {
  const report = path.join(BDD_ROOT, 'reports', `probe-${name}.ndjson`);
  fs.mkdirSync(path.dirname(report), { recursive: true });
  const result = spawnSync(
    CUCUMBER,
    [
      '--config',
      'probes/cucumber.mjs',
      '--import',
      `probes/${name}/steps.js`,
      '--format',
      `message:${report}`,
      ...extraArgs,
      `probes/${name}/feature.feature`,
    ],
    { cwd: BDD_ROOT, encoding: 'utf8' },
  );
  return { status: result.status, stdout: result.stdout, stderr: result.stderr, report };
}

function envelopes(report) {
  return fs
    .readFileSync(report, 'utf8')
    .split('\n')
    .filter((line) => line.trim())
    .map((line) => JSON.parse(line));
}

function gate(report) {
  const result = spawnSync(process.execPath, [GATE, report], {
    cwd: BDD_ROOT,
    encoding: 'utf8',
  });
  return { status: result.status, stdout: result.stdout, stderr: result.stderr };
}

Given('a probe acceptance suite whose step performs a real assertion', function () {
  this.results.probe = 'passing';
});

Given('a probe acceptance suite with an undefined step', function () {
  this.results.probe = 'undefined';
});

Given('a probe acceptance suite with an ambiguous step', function () {
  this.results.probe = 'ambiguous';
});

Given('a probe acceptance suite with a deliberately failing assertion', function () {
  this.results.probe = 'failing';
});

Given('a probe acceptance suite run without executing steps', function () {
  this.results.probe = 'passing';
  this.results.dryRun = true;
});

When('the probe suite runs through the selected Cucumber runtime', function () {
  this.results.run = runProbe(this.results.probe);
});

When('strict step-resolution validation runs', function () {
  this.results.run = runProbe(this.results.probe, this.results.dryRun ? ['--dry-run'] : []);
  this.results.gate = gate(this.results.run.report);
});

Then('the scenario executes and passes', function () {
  assert.equal(this.results.run.status, 0, this.results.run.stderr);
});

Then('the structured report records the scenario and each step outcome', function () {
  const messages = envelopes(this.results.run.report);
  const pickle = messages.find((envelope) => envelope.pickle).pickle;
  assert.equal(pickle.name, 'A real assertion runs');
  const finished = messages
    .filter((envelope) => envelope.testStepFinished)
    .map((envelope) => envelope.testStepFinished.testStepResult.status);
  assert.deepEqual(finished, ['PASSED', 'PASSED']);
  const run = messages.find((envelope) => envelope.testRunFinished).testRunFinished;
  assert.equal(run.success, true);
});

Then('validation fails', function () {
  assert.notEqual(this.results.gate.status, 0);
  assert.match(this.results.gate.stderr, /step-resolution: FAILED/);
});

Then('the unresolved step and its source location are reported', function () {
  assert.match(this.results.gate.stderr, /feature\.feature:\d+/);
  assert.match(this.results.gate.stderr, /UNDEFINED/);
  assert.match(this.results.gate.stderr, /no matching definition/);
});

Then('the ambiguity names the competing definitions', function () {
  assert.match(this.results.gate.stderr, /AMBIGUOUS/);
  assert.match(this.results.gate.stderr, /2 definitions/);
});

Then('the scenario is reported failed', function () {
  assert.notEqual(this.results.run.status, 0);
  const messages = envelopes(this.results.run.report);
  const failed = messages.filter(
    (envelope) => envelope.testStepFinished?.testStepResult.status === 'FAILED',
  );
  assert.equal(failed.length, 1);
  const run = messages.find((envelope) => envelope.testRunFinished).testRunFinished;
  assert.equal(run.success, false);
});

Then('the report preserves the failing step', function () {
  const messages = envelopes(this.results.run.report);
  const document = messages.find((envelope) => envelope.gherkinDocument).gherkinDocument;
  const pickle = messages.find((envelope) => envelope.pickle).pickle;
  assert.equal(pickle.name, 'A failing assertion fails the scenario');
  assert.equal(pickle.steps.at(-1).text, 'the probe assertion is deliberately wrong');
  assert.ok(document.feature);
});

// ---------------------------------------------------------------- GT-02

function inventory() {
  return JSON.parse(
    fs.readFileSync(path.join(REPO_ROOT, 'docs', 'feature-inventory.json'), 'utf8'),
  );
}

Given('the repository feature inventory artifact', function () {
  this.results.inventory = inventory();
});

Then('every tracked feature file appears exactly once', function () {
  const tracked = this.call('tracked', { pattern: '*.feature' }).files;
  const listed = this.results.inventory.features.map((entry) => entry.file);
  assert.deepEqual([...listed].sort(), [...tracked].sort());
  assert.equal(listed.length, new Set(listed).size);
});

Then('every non-executed feature carries an explicit reason', function () {
  for (const entry of this.results.inventory.features) {
    if (entry.cucumber_status !== 'executed') {
      assert.ok(entry.reason && entry.reason.length > 10, `${entry.file} has no reason`);
      assert.notEqual(entry.execution_result, 'passing');
    }
  }
  const excluded = this.results.inventory.features.filter(
    (entry) => entry.cucumber_status !== 'executed',
  );
  assert.ok(excluded.length >= 3);
});

Given('the canonical acceptance feature files', function () {
  this.results.canonical = this.call('tracked', { pattern: 'docs/stories/*.feature' }).files;
});

When('their scenario identifiers are collected', function () {
  const identifiers = [];
  for (const file of this.results.canonical) {
    const text = fs.readFileSync(path.join(REPO_ROOT, file), 'utf8');
    for (const line of text.split('\n')) {
      const trimmed = line.trim();
      if (!trimmed.startsWith('@')) continue; // prose mentions of a tag are not identities
      for (const match of trimmed.matchAll(/@SCN-\d{3,4}\b/g)) identifiers.push(match[0]);
    }
  }
  this.results.identifiers = identifiers;
});

Then('every identifier appears exactly once', function () {
  const duplicates = this.results.identifiers.filter(
    (identifier, index) => this.results.identifiers.indexOf(identifier) !== index,
  );
  assert.deepEqual([...new Set(duplicates)], []);
  assert.ok(this.results.identifiers.length >= 60);
});

Given('the latest Cucumber acceptance report', function () {
  if (!this.results.inventory) this.results.inventory = inventory();
  const entry = this.results.inventory.features.find(
    (item) => item.cucumber_status === 'executed' && item.ref,
  );
  assert.ok(entry, 'no executed entry names a report');
  this.results.executionReport = path.join(REPO_ROOT, entry.ref);
  assert.ok(fs.existsSync(this.results.executionReport), 'recorded report is missing');
});

function excludedTags() {
  const text = fs.readFileSync(path.join(BDD_ROOT, 'cucumber.mjs'), 'utf8');
  return new Set([...text.matchAll(/not\s+(@[\w-]+)/g)].map((match) => match[1]));
}

function reportStats(report) {
  const excluded = excludedTags();
  const messages = envelopes(report);
  const pickles = new Map();
  const cases = new Map();
  const attempts = new Map();
  const finished = new Set();
  const results = new Map();
  const documents = new Set();
  const addResult = (key, stepId, status) => {
    if (!results.has(key)) results.set(key, new Map());
    const outcomes = results.get(key);
    const list = outcomes.get(stepId) ?? [];
    list.push(status);
    outcomes.set(stepId, list);
  };
  for (const envelope of messages) {
    if (envelope.gherkinDocument) documents.add(envelope.gherkinDocument.uri.replace(/^\.\.\//, ''));
    if (envelope.pickle) pickles.set(envelope.pickle.id, envelope.pickle);
    if (envelope.testCase) cases.set(envelope.testCase.id, envelope.testCase);
    if (envelope.testCaseStarted) {
      const list = attempts.get(envelope.testCaseStarted.testCaseId) ?? [];
      list.push(envelope.testCaseStarted.id);
      attempts.set(envelope.testCaseStarted.testCaseId, list);
    }
    if (envelope.testCaseFinished) finished.add(envelope.testCaseFinished.testCaseStartedId);
    if (envelope.testStepFinished) {
      addResult(
        envelope.testStepFinished.testCaseStartedId,
        envelope.testStepFinished.testStepId,
        envelope.testStepFinished.testStepResult.status,
      );
    }
  }
  const blank = () => ({
    pickles: 0,
    eligible: 0,
    cases: 0,
    started: 0,
    failed: 0,
    passed: 0,
    incomplete: 0,
    skipped: 0,
    missing: 0,
    duplicate: 0,
    unknown: 0,
  });
  const stats = new Map();
  const entry = (uri) => {
    if (!stats.has(uri)) stats.set(uri, blank());
    return stats.get(uri);
  };
  for (const uri of documents) entry(uri);
  for (const pickle of pickles.values()) {
    const uri = pickle.uri.replace(/^\.\.\//, '');
    const row = entry(uri);
    row.pickles += 1;
    if (!(pickle.tags ?? []).some((tag) => excluded.has(tag.name))) row.eligible += 1;
  }
  const covered = new Set();
  const orphanCases = [];
  for (const [caseId, testCase] of cases) {
    const pickle = pickles.get(testCase.pickleId);
    if (!pickle) {
      orphanCases.push(caseId);
      continue;
    }
    const row = entry(pickle.uri.replace(/^\.\.\//, ''));
    row.cases += 1;
    covered.add(pickle.id);
    const startedIds = attempts.get(caseId) ?? [];
    if (startedIds.length === 0) continue;
    row.started += 1;
    const expected = new Set((testCase.testSteps ?? []).map((step) => step.id));
    for (const attemptId of startedIds) {
      const supplied = results.get(attemptId) ?? new Map();
      const missing = [...expected].filter((id) => !supplied.has(id));
      const unknown = [...supplied.keys()].filter((id) => !expected.has(id));
      const duplicate = [...supplied.values()].filter((statuses) => statuses.length > 1).length;
      row.missing += missing.length;
      row.unknown += unknown.length;
      row.duplicate += duplicate;
      const statuses = [...expected]
        .filter((id) => supplied.has(id))
        .map((id) => supplied.get(id)[0]);
      row.skipped += statuses.filter((status) => status === 'SKIPPED').length;
      if (!finished.has(attemptId) || missing.length || unknown.length || duplicate) {
        row.incomplete += 1;
      } else if (statuses.includes('FAILED')) {
        row.failed += 1;
      } else if (statuses.every((status) => status === 'PASSED')) {
        row.passed += 1;
      } else {
        row.incomplete += 1;
      }
    }
  }
  for (const pickle of pickles.values()) {
    if ((pickle.tags ?? []).some((tag) => excluded.has(tag.name))) continue;
    if (!covered.has(pickle.id)) {
      entry(pickle.uri.replace(/^\.\.\//, '')).incomplete += 1;
    }
  }
  const startedIds = new Set([...attempts.values()].flat());
  const orphanAttempts = [...attempts.entries()]
    .filter(([caseId]) => !cases.has(caseId))
    .flatMap(([, ids]) => ids);
  const orphanResults = [...results.keys()].filter(
    (key) => !startedIds.has(key.split(':')[0]),
  );
  return { stats, orphanResults, orphanAttempts, orphanCases };
}

When("the inventory's executed entries are compared with the report", function () {
  const { stats, orphanResults, orphanAttempts, orphanCases } = reportStats(
    this.results.executionReport,
  );
  this.results.reportStats = stats;
  this.results.orphanResults = orphanResults;
  this.results.orphanAttempts = orphanAttempts;
  this.results.orphanCases = orphanCases;
});

Then('every executed entry names a scenario present in that report', function () {
  assert.deepEqual(this.results.orphanCases, [], 'report contains cases for unknown pickles');
  assert.deepEqual(this.results.orphanAttempts, [], 'report contains orphan attempts');
  assert.deepEqual(this.results.orphanResults, [], 'report contains orphan results');
  const stats = this.results.reportStats;
  const executed = this.results.inventory.features.filter(
    (entry) => entry.cucumber_status === 'executed',
  );
  assert.ok(executed.length >= 16);
  for (const entry of executed) {
    const row = stats.get(entry.file) ?? { pickles: 0, cases: 0, started: 0, failed: 0 };
    assert.ok(row.pickles > 0, `${entry.file} has no pickle in the report`);
    assert.equal(row.started, row.cases, `${entry.file} has unstarted test cases`);
    assert.equal(entry.eligible_scenarios, row.eligible, `${entry.file} eligible count mismatch`);
    assert.equal(entry.executed_scenarios, row.started, `${entry.file} executed count mismatch`);
    assert.equal(entry.failed_scenarios, row.failed, `${entry.file} failed count mismatch`);
    assert.equal(entry.incomplete_scenarios, row.incomplete, `${entry.file} incomplete mismatch`);
    assert.equal(entry.skipped_results, row.skipped, `${entry.file} skipped mismatch`);
    assert.equal(entry.missing_results, row.missing, `${entry.file} missing-result mismatch`);
    assert.equal(entry.duplicate_results, row.duplicate, `${entry.file} duplicate mismatch`);
    assert.equal(entry.unknown_results, row.unknown, `${entry.file} unknown-result mismatch`);
    const complete =
      row.eligible > 0 &&
      row.cases >= row.eligible &&
      row.started === row.cases &&
      row.passed === row.cases &&
      row.failed === 0 &&
      row.incomplete === 0 &&
      row.skipped === 0 &&
      row.missing === 0 &&
      row.duplicate === 0 &&
      row.unknown === 0;
    assert.equal(
      entry.execution_result,
      row.failed ? 'failed' : complete ? 'passing' : 'incomplete',
      `${entry.file} execution result mismatch`,
    );
    assert.equal(entry.report, 'docs/reports/omp-m2-bdd/evidence/cucumber-messages.ndjson');
    assert.equal(entry.migration_status, complete ? 'complete' : 'pending');
  }
  // Parsed-but-never-started scenarios must not be counted as executed.
  const unexecutedWithPickles = this.results.inventory.features.filter(
    (entry) => entry.cucumber_status !== 'executed' && (stats.get(entry.file)?.pickles ?? 0) > 0,
  );
  assert.ok(unexecutedWithPickles.length > 0);
  for (const entry of unexecutedWithPickles) {
    assert.equal(stats.get(entry.file).started, 0);
  }
});

Then('a pytest mapping is not counted as execution', function () {
  const stats = this.results.reportStats;
  for (const entry of this.results.inventory.features) {
    if (entry.cucumber_status === 'executed') continue;
    assert.equal(entry.executed_scenarios, 0, `${entry.file} claims executed scenarios`);
    assert.equal(entry.failed_scenarios, 0);
    assert.equal(entry.incomplete_scenarios, 0);
    assert.equal(entry.skipped_results, 0);
    assert.equal(entry.missing_results, 0);
    assert.equal(entry.duplicate_results, 0);
    assert.equal(entry.unknown_results, 0);
    assert.equal(entry.report, null);
    assert.equal(stats.get(entry.file)?.started ?? 0, 0, `${entry.file} started but is not executed`);
  }
  const setup = this.results.inventory.features.find((entry) =>
    entry.file.endsWith('SETUP-01.feature'),
  );
  // SETUP-01 is migrated now; a pytest mapping is still not the source of that claim.
  assert.equal(setup.cucumber_status, 'executed');
  assert.equal(setup.migration_status, 'complete');
  assert.ok(setup.report);
  assert.ok(setup.executed_scenarios > 0);
});


Then('the report shows steps that were not executed', function () {
  assert.notEqual(this.results.gate.status, 0);
  assert.match(this.results.gate.stderr, /SKIPPED/);
  assert.match(this.results.gate.stderr, /was not executed/);
});
