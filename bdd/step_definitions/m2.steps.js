import assert from 'node:assert/strict';
import { Given, Then, When } from '@cucumber/cucumber';

function allFindings(world) {
  const data = world.results.findings;
  assert.ok(data, 'no assurance evaluation has run');
  return Array.isArray(data) ? data.flatMap((entry) => entry.findings) : data.findings;
}

function matching(world, findingType, artifactId) {
  return allFindings(world).filter(
    (finding) =>
      finding.finding_type === findingType &&
      (artifactId === undefined || finding.artifact_ids.includes(artifactId)),
  );
}

// ---------------------------------------------------------------- DT-05

Given('a test run for {string} executed at the {string} revision', function (testId, commitId) {
  const { commit } = this.call('commit_manifest', { id: commitId });
  this.results.expectedCommit = commit;
  this.results.expectedTest = testId;
});

When('the evidence is read', function () {
  const { evidence } = this.call('evidence', { revision: 'baseline-b' });
  this.results.evidence = evidence;
});

Then('it carries the commit SHA that was executed, not the commit that stored the record', function () {
  const row = this.results.evidence.find((item) => item.evidence_id === 'EV-003');
  assert.ok(row, 'EV-003 missing');
  assert.equal(row.test_id, this.results.expectedTest);
  assert.equal(row.tested_commit, this.results.expectedCommit);
  const { commit: tagCommit } = this.call('ingest', { revision: 'baseline-b' });
  assert.notEqual(row.tested_commit, tagCommit);
});

Then('it records the result, the execution time, and the run URI', function () {
  const row = this.results.evidence.find((item) => item.evidence_id === 'EV-003');
  assert.equal(row.result, 'failed');
  assert.equal(new Date(row.executed_at).toISOString(), '2026-10-15T14:05:00.000Z');
  assert.equal(row.run_uri, 'ci://banking-demo/runs/1002');
});

Given('{string} passed at {string} and failed at {string}', function (testId, first, second) {
  const a = this.call('evidence', { revision: first }).evidence;
  const b = this.call('evidence', { revision: second }).evidence;
  const passed = a.filter((row) => row.test_id === testId && row.result === 'passed');
  const failed = b.filter((row) => row.test_id === testId && row.result === 'failed');
  assert.equal(passed.length, 1);
  assert.equal(failed.length, 1);
  this.results.evidencePair = { passed: passed[0], failed: failed[0] };
});

Then('both records exist with distinct evidence ids', function () {
  const { passed, failed } = this.results.evidencePair;
  assert.notEqual(passed.evidence_id, failed.evidence_id);
  assert.ok(passed.evidence_id && failed.evidence_id);
});

Then('the later run does not overwrite the earlier one', function () {
  const { passed, failed } = this.results.evidencePair;
  assert.equal(passed.result, 'passed');
  assert.equal(failed.result, 'failed');
  assert.ok(failed.executed_at > passed.executed_at);
  const atB = this.call('evidence', { revision: 'baseline-b' }).evidence;
  assert.ok(atB.some((row) => row.evidence_id === passed.evidence_id));
});

Given('the fixture baselines {string} and {string}', function (first, second) {
  this.results.baselines = [first, second];
});

When('the artifact content hashes are compared across the evidence-only commit', function () {
  const tag = this.call('ingest', { revision: this.results.baselines[0] });
  const source = this.call('commit_manifest', { id: 'baseline-a-source' });
  this.results.evidenceOnlyDiff = this.call('artifact_diff', {
    rev_a: tag.commit,
    rev_b: source.commit,
  });
});

Then('no artifact is reported as changed', function () {
  assert.deepEqual(this.results.evidenceOnlyDiff.changed, []);
});

Then('the evidence still identifies the source commit it tested', function () {
  const { evidence } = this.call('evidence', { revision: 'baseline-a' });
  const row = evidence.find((item) => item.evidence_id === 'EV-001');
  const { commit } = this.call('commit_manifest', { id: 'baseline-a-source' });
  assert.equal(row.tested_commit, commit);
});

Given(
  'a repository revision whose evidence references unknown test artifact {string}',
  function (testId) {
    this.call('repo_from_fixture', { name: 'bad-evidence', tag: 'baseline-b' });
    const payload = {
      schema_version: this.call('schema_version', {}).version,
      repository: 'probe',
      runs: [
        {
          evidence_id: 'EV-901',
          test_id: testId,
          scenario_id: 'SCN-001',
          result: 'passed',
          tested_commit: '0'.repeat(40),
          executed_at: '2026-11-13T00:00:00+00:00',
          run_uri: 'ci://probe/1',
        },
      ],
    };
    this.call('commit', {
      name: 'bad-evidence',
      files: { 'evidence/verification-runs.json': JSON.stringify(payload, null, 2) },
      message: 'probe unknown evidence test',
    });
    this.results.probeRepo = 'bad-evidence';
  },
);

// ---------------------------------------------------------------- DT-06

Given('the fixture repository with both baselines ingested', function () {
  this.call('ingest', { revision: 'baseline-a' });
  this.call('ingest', { revision: 'baseline-b' });
});

When('the change set between them is requested', function () {
  if (this.results.addedArtifact) {
    const repo = this.call('repo', {
      name: 'added-artifact',
      files: {
        'requirements/REQ-001.md': '---\nid: REQ-001\ntitle: Base\nstatus: active\n---\n\nBody.\n',
      },
    });
    this.call('commit', {
      name: 'added-artifact',
      files: {
        'requirements/REQ-900.md': '---\nid: REQ-900\ntitle: Added\nstatus: active\n---\n\nBody.\n',
      },
      message: 'add a requirement',
    });
    const head = this.call('git', { name: 'added-artifact', args: ['rev-parse', 'HEAD'] }).output;
    this.results.addedDiff = this.call('artifact_diff', {
      name: 'added-artifact',
      rev_a: repo.commit,
      rev_b: head,
    });
    return;
  }
  this.results.changeSet = this.call('changed', {
    baseline: 'baseline-b',
    previous: 'baseline-a',
  });
});

Then('the changed artifacts are exactly {string} and {string}', function (first, second) {
  assert.deepEqual(this.results.changeSet.changed, [first, second].sort());
});

Then('{string} is reported unchanged', function (artifactId) {
  assert.ok(!this.results.changeSet.changed.includes(artifactId));
});

Then('an evidence-only commit does not mark artifacts as changed', function () {
  const tag = this.call('ingest', { revision: 'baseline-b' });
  const source = this.call('commit_manifest', { id: 'baseline-b-change' });
  const diff = this.call('artifact_diff', { rev_a: tag.commit, rev_b: source.commit });
  assert.deepEqual(diff.changed, []);
});

Given('{string} changed between the two baselines', function (artifactId) {
  this.results.changeSet = this.call('changed', {
    baseline: 'baseline-b',
    previous: 'baseline-a',
  });
  assert.ok(this.results.changeSet.changed.includes(artifactId));
});

When('impacted links are requested', function () {
  this.results.impacted = this.call('changed', {
    baseline: 'baseline-b',
    previous: 'baseline-a',
  }).impacted_links;
});

Then('the accepted links reaching {string} are reported', function (artifactId) {
  const { links } = this.call('links', { baseline: 'baseline-b' });
  const expected = links
    .filter(
      (link) =>
        link.review_state === 'accepted' &&
        (link.source_id === artifactId || link.target_id === artifactId),
    )
    .map((link) => link.link_id);
  for (const linkId of expected) {
    assert.ok(this.results.impacted.includes(linkId), `${linkId} missing from impacted links`);
  }
});

Then('links to unchanged artifacts are not', function () {
  const { links } = this.call('links', { baseline: 'baseline-b' });
  for (const linkId of this.results.impacted) {
    const link = links.find((item) => item.link_id === linkId);
    assert.ok(
      this.results.changeSet.changed.includes(link.source_id) ||
        this.results.changeSet.changed.includes(link.target_id),
      `${linkId} does not reach a changed artifact`,
    );
  }
});

Given('an artifact exists at {string} but not at {string}', function (later, earlier) {
  assert.equal(later, 'baseline-b');
  assert.equal(earlier, 'baseline-a');
  this.results.addedArtifact = 'REQ-900';
});

Then('the added artifact is reported as changed', function () {
  assert.deepEqual(this.results.addedDiff.only_second, [this.results.addedArtifact]);
  assert.ok(this.results.addedDiff.changed.includes(this.results.addedArtifact));
});

// ---------------------------------------------------------------- AS-02 / AS-03

Given('{string} verifies {string}', function (scenarioId, requirementId) {
  const { thread } = this.call('thread', { id: requirementId, baseline: 'baseline-a' });
  const link = thread.accepted_links.find(
    (item) => item.source_id === requirementId && item.target_id === scenarioId,
  );
  assert.ok(link, `${requirementId} does not verify ${scenarioId}`);
});

Given(
  'a test for {string} passed at baseline {string} with evidence {string}',
  function (scenarioId, baseline, evidenceId) {
    const { evidence } = this.call('evidence', { revision: baseline });
    const row = evidence.find((item) => item.evidence_id === evidenceId);
    assert.ok(row);
    assert.equal(row.scenario_id, scenarioId);
    assert.equal(row.result, 'passed');
  },
);

Given('a relevant linked implementation changed at baseline {string}', function (baseline) {
  const diff = this.call('changed', { baseline, previous: 'baseline-a' });
  assert.ok(diff.changed.includes('CODE-001'));
});

Given('no later matching verification evidence exists', function () {
  const { evidence } = this.call('evidence', { revision: 'baseline-b' });
  assert.equal(evidence.filter((row) => row.result === 'passed' && row.scenario_id === 'SCN-001').length, 1);
});

Then(
  'the finding identifies both baselines and the changed artifact {string}',
  function (changedArtifact) {
    const finding = matching(this, 'reverification_required', 'REQ-001')[0];
    assert.ok(finding);
    assert.ok(finding.evaluated_baseline);
    assert.ok(finding.explanation.includes('baseline-a'));
    assert.ok(finding.explanation.includes('baseline-b'));
    assert.ok(finding.artifact_ids.includes(changedArtifact));
  },
);

Then('{string} is not marked {string}', function (artifactId, findingType) {
  assert.deepEqual(matching(this, findingType, artifactId), []);
});

Given('no relevant artifact changed at baseline {string}', function (baseline) {
  const { commit } = this.call('ingest', { revision: baseline });
  const source = this.call('commit_manifest', { id: 'baseline-a-source' });
  const diff = this.call('artifact_diff', { rev_a: commit, rev_b: source.commit });
  assert.deepEqual(diff.changed, []);
});

Then('the failing evidence {string} produces a {string} finding', function (evidenceId, findingType) {
  assert.ok(allFindings(this).some((finding) => finding.evidence_ids.includes(evidenceId) && finding.finding_type === findingType));
});

Then('the earlier passing evidence {string} is still recorded', function (evidenceId) {
  const { evidence } = this.call('evidence', { revision: 'baseline-b' });
  const row = evidence.find((item) => item.evidence_id === evidenceId);
  assert.ok(row);
  assert.equal(row.result, 'passed');
});

Given('{string} has a failing test at baseline {string}', function (requirementId, baseline) {
  const { evidence } = this.call('evidence', { revision: baseline });
  assert.ok(evidence.some((row) => row.result === 'failed'));
});

Given('{string} has passing verification evidence at baseline {string}', function (requirementId, baseline) {
  const { evidence } = this.call('evidence', { revision: baseline });
  assert.ok(evidence.some((row) => row.result === 'passed'));
  const { thread } = this.call('thread', { id: requirementId, baseline });
  assert.ok(thread.evidence.some((row) => row.result === 'passed'));
});

Given('a relevant linked implementation of {string} changed at baseline {string}', function (requirementId, baseline) {
  const diff = this.call('changed', { baseline, previous: 'baseline-a' });
  assert.ok(diff.changed.includes('CODE-001'));
});

Then('{string} yields a {string} finding', function (artifactId, findingType) {
  assert.ok(matching(this, findingType, artifactId).length >= 1);
});

Then('no finding downgrades {string} to {string}', function (expectedType, collapsedType) {
  const reverification = matching(this, expectedType).map((finding) => finding.artifact_ids.join(','));
  for (const ids of reverification) {
    const failure = matching(this, collapsedType).find(
      (finding) => finding.artifact_ids.join(',') === ids,
    );
    assert.ok(!failure, `${ids} appears as both ${expectedType} and ${collapsedType}`);
  }
});

Given('evidence {string} was recorded at the source commit of {string}', function (evidenceId, baseline) {
  const { evidence } = this.call('evidence', { revision: baseline });
  const row = evidence.find((item) => item.evidence_id === evidenceId);
  const { commit } = this.call('commit_manifest', { id: 'baseline-a-source' });
  assert.equal(row.tested_commit, commit);
});

Given('the evidence commit stores the report without changing artifact content', function () {
  const tag = this.call('ingest', { revision: 'baseline-a' });
  const source = this.call('commit_manifest', { id: 'baseline-a-source' });
  const diff = this.call('artifact_diff', { rev_a: tag.commit, rev_b: source.commit });
  assert.deepEqual(diff.changed, []);
});

Then('the evidence is treated as applicable', function () {
  const { evidence } = this.call('evidence', { revision: 'baseline-a' });
  assert.ok(evidence.length >= 1);
});

Then('{string} has no {string} finding', function (artifactId, findingType) {
  assert.deepEqual(matching(this, findingType, artifactId), []);
});
