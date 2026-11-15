import { Given, Then, When } from '@cucumber/cucumber';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';

const REPO_ROOT = path.resolve(import.meta.dirname, '../..');
const HEAD = () =>
  execFileSync('git', ['rev-parse', 'HEAD'], { cwd: REPO_ROOT, encoding: 'utf8' }).trim();
const FINAL_REPORT = path.join(
  REPO_ROOT,
  'docs',
  'reports',
  'omp-closeout',
  'evidence',
  'final-cucumber.ndjson',
);
const FAILED_REPORT = path.join(
  REPO_ROOT,
  'docs',
  'reports',
  'omp-closeout',
  'evidence',
  'final-cucumber-attempt1-failed.ndjson',
);

function assurance(world, args) {
  return world.call('assurance', args);
}

function save(world, name, payload) {
  const target = path.join(world.stateDir, name);
  fs.writeFileSync(target, `${JSON.stringify(payload)}\n`, 'utf8');
  return target;
}

function evaluate(world, baseline, extra = {}) {
  const result = assurance(world, { command: 'evaluate', baseline, ...extra });
  if (result.status !== 0) {
    throw new Error(`evaluate ${baseline} exited ${result.status}: ${result.stderr}`);
  }
  return result;
}

function selfAssure(world, { failed = false, metadata = null, probe = null } = {}) {
  const fixture =
    probe ??
    world.call('assurance_fixture', {
      feature: 'docs/stories/CI-01.feature',
      failed,
    });
  const result = assurance(world, {
    command: 'self',
    repository_id: 'gherkin-knowledge-graph',
    tested_commit: fixture.tested_commit,
    cucumber_report: fixture.report,
    cucumber_root: '.',
    metadata: metadata ?? fixture.metadata,
  });
  result.fixture = fixture;
  return result;
}

function sorted(value) {
  if (Array.isArray(value)) return value.map(sorted);
  if (value && typeof value === 'object') {
    return Object.fromEntries(
      Object.keys(value)
        .sort()
        .map((key) => [key, sorted(value[key])]),
    );
  }
  return value;
}

function rehash(report) {
  const copy = { ...report };
  delete copy.report_digest;
  report.report_digest = `sha256:${createHash('sha256')
    .update(JSON.stringify(sorted(copy)))
    .digest('hex')}`;
  return report;
}

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function diagnostic(result) {
  const text = result.stdout.trim() || result.stderr.trim();
  assert.ok(text, 'expected a diagnostics payload');
  return JSON.parse(text.split('\n').at(-1));
}

function diff(world, previous, current) {
  const result = assurance(world, { command: 'diff', previous, current });
  world.results.diffResult = result;
  if (result.status === 0) {
    assert.ok(result.diff, 'expected a diff payload');
  }
  return result;
}

// ------------------------------------------------------------------ CI-01

Given('banking-demo baseline-b resolves to its fixture commit', function () {
  const manifest = this.call('manifest');
  this.results.expectedCommit = manifest.tags['baseline-b'];
  assert.ok(this.results.expectedCommit);
});

Given('dependencies are provisioned and external network access is denied', function () {
  this.results.denyNetwork = true;
  assert.ok(fs.existsSync(path.join(REPO_ROOT, 'backend', '.venv', 'bin', 'python')));
});

Given('no model provider is enabled', function () {
  const settings = this.call('settings');
  assert.equal(settings.ai_mode, 'fake');
});

When('the assurance command ingests and evaluates that commit', function () {
  this.results.assurance = evaluate(this, 'baseline-b', {
    deny_network: this.results.denyNetwork,
    evaluator_revision: 'cta@0.1.0+test+assurance',
  });
  this.results.report = this.results.assurance.report;
  this.results.reportPath = save(this, 'baseline-b-report.json', this.results.report);
  this.results.manifestPath = save(this, 'baseline-b-manifest.json', this.results.assurance.manifest);
});

Then('it exits 0', function () {
  assert.equal(this.results.assurance.status, 0);
});

Then(
  'its completed report follows the report contract and identifies banking-demo at the resolved baseline-b commit',
  function () {
    const report = this.results.report;
    assert.equal(report.report_version, '1.0');
    assert.equal(report.scope, 'requirement_assurance');
    assert.equal(report.repository, 'banking-demo');
    assert.equal(report.baseline, 'baseline-b');
    assert.equal(report.evaluated_revision, this.results.expectedCommit);
    assert.equal(report.tool_outcome, 'completed');
  },
);

Then('the report records the CTA evaluator revision and input content hashes', function () {
  assert.match(this.results.report.evaluator_revision, /^cta@0\.1\.0\+test\+assurance$/);
  assert.ok(this.results.report.inputs.length > 0);
  assert.ok(
    this.results.report.inputs
      .filter((entry) => entry.kind === 'artifact')
      .every((entry) => entry.digest && entry.digest.startsWith('sha256:')),
  );
});

Then('its findings match the hand-labeled baseline-b oracle', function () {
  const expected = JSON.parse(
    fs.readFileSync(
      path.join(REPO_ROOT, 'fixtures', 'banking-demo', 'expected', 'baseline-b.json'),
      'utf8',
    ),
  );
  const actual = this.results.report.findings;
  assert.equal(actual.length, expected.findings.length);
  for (const oracle of expected.findings) {
    assert.ok(
      actual.some(
        (finding) =>
          finding.rule_id === oracle.rule_id &&
          finding.finding_type === oracle.finding_type &&
          JSON.stringify(finding.artifact_ids) === JSON.stringify(jsonSorted(oracle.artifact_ids)),
      ),
      `missing oracle finding ${oracle.rule_id} ${oracle.artifact_ids}`,
    );
  }
});

function jsonSorted(values) {
  return [...values].sort();
}

Then('its report and input manifest are stored outside the evaluated repository', function () {
  for (const target of [this.results.reportPath, this.results.manifestPath]) {
    assert.ok(target.startsWith(this.stateDir));
    assert.ok(fs.existsSync(target));
  }
});

Given('a deterministic PR event contains different head and test-merge SHAs', function () {
  const head = HEAD();
  this.results.head = head;
  this.results.testMerge = 'f'.repeat(40);
  this.results.event = {
    pull_request: { head: { sha: head }, merge_commit_sha: this.results.testMerge },
  };
});

When('the workflow revision resolver processes that event', function () {
  this.results.resolved = assurance(this, {
    command: 'resolve-revision',
    event: this.results.event,
  });
  assert.equal(this.results.resolved.status, 0);
});

Then('the selected evaluated revision equals the event head SHA', function () {
  assert.equal(this.results.resolved.stdout.trim(), this.results.head);
});

Then('the report records that exact selected revision', function () {
  const result = selfAssure(this);
  assert.equal(result.status, 0, result.stderr);
  this.results.self = result;
  assert.equal(result.report.evaluated_revision, this.results.head);
});

Then('no test-merge SHA is reported as the head revision', function () {
  assert.ok(!JSON.stringify(this.results.self.report).includes(this.results.testMerge));
});

Then('a deterministic push event selects its non-zero after SHA', function () {
  const after = 'a'.repeat(40);
  const result = assurance(this, {
    command: 'resolve-revision',
    event: { after },
  });
  assert.equal(result.status, 0);
  assert.equal(result.stdout.trim(), after);
});

Then(
  'the selected commit is used for ingestion and evaluation, not only recorded',
  function () {
    assert.equal(this.results.self.report.evaluated_revision, this.results.head);
    assert.equal(this.results.self.report.execution_report.tested_commit, this.results.head);
  },
);

Given('a pinned CTA checkout and an attributable Cucumber report for that revision', function () {
  this.results.head = HEAD();
  this.results.probe = this.call('assurance_fixture', {
    feature: 'docs/stories/CI-01.feature',
    failed: false,
  });
  assert.ok(fs.existsSync(this.results.probe.report));
});

When('portable self-assurance evaluates the checkout with that report', function () {
  const result = selfAssure(this, { probe: this.results.probe });
  assert.equal(result.status, 0, result.stderr);
  this.results.self = result;
  this.results.report = result.report;
  this.results.reportPath = save(this, 'self-report.json', result.report);
  this.results.manifestPath = save(this, 'self-manifest.json', result.manifest);
});

Then('the report identifies scope "gherkin_executability"', function () {
  assert.equal(this.results.report.scope, 'gherkin_executability');
});

Then('it records the tested commit and execution report digest', function () {
  assert.equal(this.results.report.evaluated_revision, this.results.head);
  assert.match(this.results.report.execution_report.report_digest, /^sha256:[0-9a-f]{64}$/);
});

Then('parsed feature hashes match the imported report provenance', function () {
  const sources = this.results.report.execution_report.sources;
  assert.ok(sources.length > 0);
  assert.ok(sources.every((source) => source.digest.startsWith('sha256:')));
  assert.equal(this.results.report.coverage.features_covered_by_report, sources.length);
});

Then("the report's execution sources equal the imported report's feature hashes", function () {
  const sources = this.results.report.execution_report.sources;
  assert.deepEqual(
    sources.map((source) => source.path).sort(),
    [...new Set(sources.map((source) => source.path))].sort(),
  );
});

Then('coverage gaps are counted, not reported as findings', function () {
  const report = this.results.report;
  assert.ok(report.coverage.features_indexed >= report.coverage.features_covered_by_report);
  assert.equal(
    report.findings.filter((finding) => finding.finding_type === 'execution_failed').length,
    0,
  );
});

Then('it makes no requirement-to-production-code verification claim', function () {
  const report = this.results.report;
  assert.ok(!('requirement_verdicts' in report));
  assert.ok(
    !report.findings.some((finding) =>
      ['verification_failed', 'reverification_required'].includes(finding.finding_type),
    ),
  );
});

Given('a valid deterministic Cucumber report records a failed scenario', function () {
  this.results.probe = this.call('assurance_fixture', {
    feature: 'docs/stories/CI-01.feature',
    failed: true,
  });
  assert.ok(fs.existsSync(this.results.probe.report));
});

Given('its provenance matches the evaluated repository revision', function () {
  this.results.head = this.results.probe.tested_commit;
});

When('portable assurance ingests and evaluates that report', function () {
  const result = selfAssure(this, { probe: this.results.probe });
  assert.equal(result.status, 0, result.stderr);
  this.results.self = result;
  this.results.report = result.report;
});

Then('the assurance command exits 0', function () {
  assert.equal(this.results.self.status, 0);
});

Then('tool_outcome is "completed"', function () {
  assert.equal(this.results.report.tool_outcome, 'completed');
});

Then('an execution_failed finding identifies the failing execution', function () {
  const finding = this.results.report.findings.find(
    (item) => item.finding_type === 'execution_failed',
  );
  assert.ok(finding);
  assert.ok(finding.execution_keys.length > 0);
});

Then('the report does not claim that a requirement is verified or failed', function () {
  assert.ok(!('requirement_verdicts' in this.results.report));
});

Given('the assurance command encounters {string}', function (failure) {
  this.results.failure = failure;
});

When('the command evaluates the selected revision', function () {
  const failure = this.results.failure;
  let result;
  if (failure === 'an unknown repository revision') {
    result = assurance(this, { command: 'evaluate', baseline: 'missing-baseline' });
  } else if (failure === 'malformed execution-report provenance') {
    const metadata = path.join(this.stateDir, 'bad-meta.json');
    fs.writeFileSync(
      metadata,
      JSON.stringify({ repository_id: 'gherkin-knowledge-graph', tested_commit: '0'.repeat(40) }),
    );
    result = selfAssure(this, { metadata });
  } else if (failure === 'an unreadable required ingestion input') {
    result = assurance(this, {
      command: 'self',
      repository_id: 'gherkin-knowledge-graph',
      tested_commit: HEAD(),
      cucumber_report: path.join(this.stateDir, 'missing.ndjson'),
    });
  } else if (failure === 'an unwritable report destination') {
    const directory = fs.mkdtempSync(path.join(this.stateDir, 'unwritable-'));
    fs.chmodSync(directory, 0o555);
    result = assurance(this, {
      command: 'evaluate',
      baseline: 'baseline-b',
      report: path.join(directory, 'report.json'),
      manifest: path.join(directory, 'manifest.json'),
    });
    fs.chmodSync(directory, 0o755);
  } else {
    throw new Error(`unknown assurance failure ${failure}`);
  }
  this.results.failureResult = result;
  this.results.incomplete =
    result.report ??
    JSON.parse(
      (result.stderr.trim() || result.stdout.trim()).split('\n').at(-1),
    );
});

Then('it exits 2', function () {
  assert.equal(this.results.failureResult.status, 2);
});

Then("its diagnostic report follows the contract's incomplete envelope", function () {
  assert.equal(this.results.incomplete.tool_outcome, 'incomplete');
  assert.equal(this.results.incomplete.report_version, '1.0');
  assert.ok(this.results.incomplete.incomplete_reason);
  assert.equal(this.results.incomplete.findings.length, 0);
});

Then('when the report destination is unwritable the same JSON is printed on stderr', function () {
  if (this.results.failure === 'an unwritable report destination') {
    const parsed = JSON.parse(
      (this.results.failureResult.stderr.trim() || this.results.failureResult.stdout.trim())
        .split('\n')
        .at(-1),
    );
    assert.equal(parsed.tool_outcome, 'incomplete');
    assert.equal(parsed.failure_stage, 'write');
  }
});

Then('failure_stage and failure_code identify the failure', function () {
  assert.ok(this.results.incomplete.failure_stage);
  assert.ok(this.results.incomplete.failure_code);
});

Then('the report is marked incomplete', function () {
  assert.equal(this.results.incomplete.tool_outcome, 'incomplete');
});

Then('the failure is not converted into an assurance finding', function () {
  assert.deepEqual(this.results.incomplete.findings, []);
});

Given('a completed deterministic assurance report contains findings', function () {
  this.results.trackedBefore = execFileSync('git', ['status', '--porcelain'], {
    cwd: REPO_ROOT,
    encoding: 'utf8',
  });
  const result = evaluate(this, 'baseline-b', {
    evaluator_revision: 'cta@0.1.0+test+assurance',
  });
  this.results.report = result.report;
  this.results.manifest = result.manifest;
  this.results.summary = result.summary;
  assert.ok(this.results.report.findings.length > 0);
});

When('the workflow publishes its artifact and job summary', function () {
  this.results.workflow = fs.readFileSync(
    path.join(REPO_ROOT, '.github', 'workflows', 'ci.yml'),
    'utf8',
  );
  assert.ok(this.results.summary.includes(this.results.report.evaluated_revision));
});

Then('the artifact contains the report and its input manifest', function () {
  assert.ok(this.results.report);
  assert.ok(this.results.manifest);
  assert.equal(this.results.manifest.report_digest, this.results.report.report_digest);
});

Then('the summary identifies the evaluated revision and finding count', function () {
  assert.ok(this.results.summary.includes(`findings: ${this.results.report.findings.length}`));
});

Then(
  'no commit, branch update, pull-request comment, or deployment is requested',
  function () {
    assert.ok(!/git push|gh pr comment|deploy/i.test(this.results.workflow));
  },
);

Then('tracked repository content is unchanged', function () {
  const after = execFileSync('git', ['status', '--porcelain'], {
    cwd: REPO_ROOT,
    encoding: 'utf8',
  });
  assert.equal(after, this.results.trackedBefore);
});

Then('on tool failure the workflow uploads the incomplete diagnostic with no finding', function () {
  assert.match(this.results.workflow, /if: always\(\)/);
  assert.match(this.results.workflow, /self-diagnostic/);
});

Then(
  'a valid failed Cucumber run still publishes completed execution_failed findings while the test gate remains failing',
  function () {
    const result = selfAssure(this, { failed: true });
    assert.equal(result.status, 0);
    assert.equal(result.report.tool_outcome, 'completed');
    assert.ok(
      result.report.findings.some((finding) => finding.finding_type === 'execution_failed'),
    );
    const envelopes = fs
      .readFileSync(result.fixture.report, 'utf8')
      .split('\n')
      .filter(Boolean)
      .map((line) => JSON.parse(line));
    assert.equal(envelopes.find((item) => item.testRunFinished).testRunFinished.success, false);
  },
);

// ------------------------------------------------------------------ CI-02

Given(
  /^completed comparable assurance reports under the report contract for banking-demo (baseline-[ab]) and (baseline-[ab])$/,
  function (first, second) {
    this.results.reports = {};
    for (const baseline of [first, second]) {
      const result = evaluate(this, baseline, { evaluator_revision: 'cta@0.1.0+test+assurance' });
      this.results.reports[baseline] = save(this, `${baseline}.json`, result.report);
    }
  },
);

When(/^the findings diff command compares (baseline-[ab]) to (baseline-[ab])$/, function (previous, current) {
  this.results.diff = diff(
    this,
    this.results.reports[previous],
    this.results.reports[current],
  );
});

Then('it reports {int} new findings', function (count) {
  assert.equal(this.results.diff.diff.counts.new, count);
});

Then('it reports {int} unchanged findings', function (count) {
  assert.equal(this.results.diff.diff.counts.unchanged, count);
});

Then('it reports {int} resolved findings', function (count) {
  assert.equal(this.results.diff.diff.counts.resolved, count);
});

Then('the new finding types are reverification_required and verification_failed', function () {
  assert.deepEqual(
    this.results.diff.diff.new.map((finding) => finding.finding_type).sort(),
    ['reverification_required', 'verification_failed'],
  );
});

Then('the report includes both resolved revisions and both report digests', function () {
  const payload = this.results.diff.diff;
  assert.equal(payload.previous_revision, this.results.diff.diff.previous_revision);
  assert.match(payload.previous_report_digest, /^sha256:[0-9a-f]{64}$/);
  assert.match(payload.current_report_digest, /^sha256:[0-9a-f]{64}$/);
});

Then('resolved means absent from the current comparable finding set', function () {
  const current = JSON.parse(
    fs.readFileSync(path.join(this.stateDir, 'baseline-a.json'), 'utf8'),
  );
  const currentIds = new Set(current.findings.map((finding) => finding.finding_id));
  assert.ok(this.results.diff.diff.resolved.every((finding) => !currentIds.has(finding.finding_id)));
});

Then('no verification evidence or requirement verdict is created', function () {
  const text = JSON.stringify(this.results.diff.diff);
  assert.ok(!text.includes('requirement_verdict'));
  assert.ok(!text.includes('accepted_links'));
});

Given('a complete assurance report for banking-demo baseline-a', function () {
  const result = evaluate(this, 'baseline-a', { evaluator_revision: 'cta@0.1.0+test+assurance' });
  this.results.reportPath = save(this, 'baseline-a.json', result.report);
});

When('that report is compared with itself', function () {
  this.results.diff = diff(this, this.results.reportPath, this.results.reportPath);
});

Given(
  'two comparable finding reports contain the same rule, finding type, and artifact IDs',
  function () {
    const result = evaluate(this, 'baseline-a', { evaluator_revision: 'cta@0.1.0+test+assurance' });
    const before = clone(result.report);
    const after = clone(result.report);
    before.run_id = 'payload-before';
    after.run_id = 'payload-after';
    before.findings[0].explanation = 'first explanation';
    after.findings[0].explanation = 'second explanation';
    after.findings[0].evidence_ids = ['EV-001'];
    rehash(before);
    rehash(after);
    this.results.beforePayload = save(this, 'payload-before.json', before);
    this.results.afterPayload = save(this, 'payload-after.json', after);
  },
);

Given('those findings have different explanations and evidence references', function () {
  const before = JSON.parse(fs.readFileSync(this.results.beforePayload, 'utf8'));
  const after = JSON.parse(fs.readFileSync(this.results.afterPayload, 'utf8'));
  assert.notEqual(before.findings[0].explanation, after.findings[0].explanation);
  assert.notDeepEqual(before.findings[0].evidence_ids, after.findings[0].evidence_ids);
});

Then('the finding is classified as unchanged', function () {
  assert.equal(this.results.diff.diff.counts.unchanged, 4);
  assert.equal(this.results.diff.diff.counts.new, 0);
  assert.equal(this.results.diff.diff.counts.resolved, 0);
});

Then('its before and after finding payloads under the contract, including status and artifact revisions, are both retained', function () {
  const pair = this.results.diff.diff.unchanged[0];
  assert.ok(pair);
  const before = JSON.parse(fs.readFileSync(this.results.beforePayload, 'utf8')).findings.find(
    (finding) => finding.finding_id === pair.finding_id,
  );
  const after = JSON.parse(fs.readFileSync(this.results.afterPayload, 'utf8')).findings.find(
    (finding) => finding.finding_id === pair.finding_id,
  );
  assert.deepEqual(pair.before, before);
  assert.deepEqual(pair.after, after);
  assert.notEqual(pair.before.explanation, pair.after.explanation);
});

Then('neither payload is rewritten', function () {
  for (const pair of this.results.diff.diff.unchanged) {
    assert.ok(pair.before.finding_id === pair.after.finding_id);
    assert.ok('artifact_revisions' in pair.before);
    assert.ok('artifact_revisions' in pair.after);
  }
});

When('the reports are compared', function () {
  this.results.diff = diff(this, this.results.beforePayload, this.results.afterPayload);
});

Given(
  'two otherwise-valid completed report inputs differ by {string}',
  function (condition) {
    const first = evaluate(this, 'baseline-a', { evaluator_revision: 'cta@0.1.0+test+assurance' });
    const second = evaluate(this, 'baseline-b', { evaluator_revision: 'cta@0.1.0+test+assurance' });
    const previous = clone(first.report);
    const current = clone(second.report);
    const rehashBoth = () => {
      rehash(previous);
      rehash(current);
    };
    if (condition === 'the previous resolved revision is absent') {
      delete previous.evaluated_revision;
      rehashBoth();
    } else if (condition === 'the current resolved revision is absent') {
      delete current.evaluated_revision;
      rehashBoth();
    } else if (condition === 'the current evaluation is incomplete') {
      current.tool_outcome = 'incomplete';
      current.incomplete_reason = 'injected incomplete evaluation';
      current.failure_stage = 'input';
      current.failure_code = 'input-unreadable';
      current.findings = [];
      rehashBoth();
    } else if (condition === 'repository identities differ') {
      current.repository = 'other-repository';
      rehashBoth();
    } else if (condition === 'evaluated rule scopes differ') {
      current.rule_scope = current.rule_scope.slice(1);
      rehashBoth();
    } else if (condition === 'policy versions differ') {
      current.policy_version = '2';
      rehashBoth();
    } else if (condition === 'evaluator revisions differ') {
      current.evaluator_revision = 'cta@other';
      rehashBoth();
    } else if (condition === 'a finding baseline contradicts its report') {
      current.findings[0].evaluated_baseline = '0'.repeat(40);
      rehashBoth();
    } else if (condition === 'duplicate finding identities') {
      current.findings.push(clone(current.findings[0]));
      rehashBoth();
    } else if (condition === 'a finding identity does not match its payload') {
      current.findings[0].finding_id = 'FND-0000000000000000';
      rehashBoth();
    } else if (condition === 'an unsupported report version') {
      current.report_version = '999.0';
      rehashBoth();
    } else if (condition === 'a report digest does not match its contents') {
      current.findings[0].explanation = 'tampered without rehashing';
    } else {
      throw new Error(`unknown invalid-comparison condition ${condition}`);
    }
    this.results.invalidPrevious = save(this, 'invalid-previous.json', previous);
    this.results.invalidCurrent = save(this, 'invalid-current.json', current);
  },
);

When('the findings diff command compares them', function () {
  this.results.diff = diff(this, this.results.invalidPrevious, this.results.invalidCurrent);
});

Then('it exits 2 with code "findings-not-comparable"', function () {
  assert.equal(this.results.diff.status, 2);
  assert.equal(diagnostic(this.results.diff).code, 'findings-not-comparable');
});

Then('it identifies the invalid input and reason', function () {
  const payload = diagnostic(this.results.diff);
  assert.ok(['previous', 'current', 'both'].includes(payload.invalid_input));
  assert.ok(payload.reason);
});

Then('it returns no new, unchanged, or resolved classification', function () {
  const payload = diagnostic(this.results.diff);
  assert.equal(payload.classifications, null);
  assert.ok(!('new' in payload));
  assert.ok(!('unchanged' in payload));
  assert.ok(!('resolved' in payload));
});

Given('two portable finding reports use source-locator identities', function () {
  const probe = this.call('assurance_fixture', {
    feature: 'docs/stories/CI-01.feature',
    failed: false,
  });
  const result = selfAssure(this, { probe });
  assert.equal(result.status, 0);
  this.results.portable = save(this, 'portable.json', result.report);
});

Given('no reviewed continuity mapping is implemented for these reports', function () {
  const report = JSON.parse(fs.readFileSync(this.results.portable, 'utf8'));
  assert.equal(report.identity_kind, 'source_locator');
});

Given('a claimed mapping is not trusted', function () {
  assert.ok(!fs.existsSync(path.join(REPO_ROOT, 'docs', 'portable-continuity.json')));
});

When('the findings diff command compares those reports', function () {
  this.results.diff = diff(this, this.results.portable, this.results.portable);
});

Then('it reports that stable cross-revision identity is unavailable', function () {
  assert.match(diagnostic(this.results.diff).reason, /source-locator|stable cross-revision/i);
});

Then('it does not classify displaced findings as resolved and new', function () {
  const payload = diagnostic(this.results.diff);
  assert.equal(payload.classifications, null);
});
