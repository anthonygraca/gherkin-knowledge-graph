import assert from 'node:assert/strict';
import { Given, Then, When } from '@cucumber/cucumber';

function quoted(text) {
  return [...text.matchAll(/"([^"]+)"/g)].map((match) => match[1]);
}

function findings(world) {
  return world.results.findings.findings;
}

Given('the fixture generator builds {string} twice in different directories', function (fixture) {
  assert.equal(fixture, 'banking-demo');
  this.results.builds = [this.call('build_fixture', {}), this.call('build_fixture', {})];
});

When('each generated repository is asked for the tags {string} and {string}', function (a, b) {
  this.results.askedTags = [a, b];
});

Then('both repositories report the same commit SHA for each tag', function () {
  const [first, second] = this.results.builds;
  assert.notEqual(first.path, second.path, 'the two builds must use different directories');
  for (const tag of this.results.askedTags) {
    assert.equal(first.tags[tag], second.tags[tag], `tag ${tag} differs between builds`);
    assert.equal(first.tags[tag].length, 40);
  }
});

Then('those SHAs match the committed manifest {string}', function (path) {
  assert.ok(path.endsWith('baselines.json'));
  const { tags } = this.call('manifest', {});
  for (const tag of this.results.askedTags) {
    assert.equal(this.results.builds[0].tags[tag], tags[tag]);
  }
});

Given('{string} has accepted links to {string}, {string}, and {string}', function (
  rootId,
  first,
  second,
  third,
) {
  const { thread } = this.call('thread', { id: rootId, baseline: 'baseline-a' });
  const targets = thread.accepted_links.flatMap((link) => [link.source_id, link.target_id]);
  for (const id of [first, second, third]) {
    assert.ok(targets.includes(id), `thread does not reach ${id}`);
  }
});

Given(
  'evidence {string} recorded a passing run for {string} at baseline {string}',
  function (evidenceId, testId, baseline) {
    const { evidence } = this.call('ingest', { revision: baseline });
    const row = evidence.find((item) => item.evidence_id === evidenceId);
    assert.ok(row, `${evidenceId} missing at ${baseline}`);
    assert.equal(row.test_id, testId);
    assert.equal(row.result, 'passed');
    assert.equal(row.scenario_id, 'SCN-001');
  },
);

When('findings for baseline {string} are inspected', function (baseline) {
  this.results.findings = this.call('findings', { baseline });
});

When('findings for baseline {string} or {string} are inspected', function (first, second) {
  this.results.findings = [this.call('findings', { baseline: first }), this.call('findings', { baseline: second })];
});

Then('no finding references {string}', function (artifactId) {
  const all = Array.isArray(this.results.findings)
    ? this.results.findings.flatMap((entry) => entry.findings)
    : findings(this);
  assert.deepEqual(
    all.filter((finding) => finding.artifact_ids.includes(artifactId)),
    [],
  );
});

Given('{string} has no accepted verification scenario', function (artifactId) {
  const { links } = this.call('links', { baseline: 'baseline-a' });
  assert.deepEqual(
    links.filter(
      (link) =>
        link.review_state === 'accepted' &&
        link.source_id === artifactId &&
        link.relation_type === 'verified_by',
    ),
    [],
  );
});

Given('{string} has no accepted implementation', function (artifactId) {
  const { links } = this.call('links', { baseline: 'baseline-a' });
  assert.deepEqual(
    links.filter(
      (link) =>
        link.review_state === 'accepted' &&
        link.source_id === artifactId &&
        link.relation_type === 'implemented_by',
    ),
    [],
  );
});

Then(/^a "([^"]+)" finding references (.*)$/, function (findingType, text) {
  const ids = quoted(text);
  const all = Array.isArray(this.results.findings)
    ? this.results.findings.flatMap((entry) => entry.findings)
    : findings(this);
  const match = all.filter(
    (finding) =>
      finding.finding_type === findingType && ids.every((id) => finding.artifact_ids.includes(id)),
  );
  assert.ok(match.length >= 1, `no ${findingType} finding references ${ids.join(', ')}`);
});

Given(
  /^"([^"]+)" verification passed at baseline "([^"]+)" \(evidence "([^"]+)"\)$/,
  function (scenarioId, baseline, evidenceId) {
    const { evidence } = this.call('ingest', { revision: baseline });
    const row = evidence.find((item) => item.evidence_id === evidenceId);
    assert.ok(row);
    assert.equal(row.scenario_id, scenarioId);
    assert.equal(row.result, 'passed');
  },
);

Given(
  'the file backing {string} changed between baseline {string} and {string}',
  function (artifactId, previous, baseline) {
    const { changed } = this.call('changed', { baseline, previous });
    assert.ok(changed.includes(artifactId), `${artifactId} did not change`);
  },
);

Given('no later evidence exists for {string}', function (scenarioId) {
  const { evidence } = this.call('ingest', { revision: 'baseline-b' });
  const rows = evidence.filter((item) => item.scenario_id === scenarioId);
  assert.equal(rows.filter((item) => item.result === 'passed').length, 1);
});

Then('that finding references evidence {string}', function (evidenceId) {
  const all = Array.isArray(this.results.findings)
    ? this.results.findings.flatMap((entry) => entry.findings)
    : findings(this);
  assert.ok(all.some((finding) => finding.evidence_ids.includes(evidenceId)));
});

Then('no {string} finding references {string}', function (findingType, artifactId) {
  const all = Array.isArray(this.results.findings)
    ? this.results.findings.flatMap((entry) => entry.findings)
    : findings(this);
  assert.deepEqual(
    all.filter((finding) => finding.finding_type === findingType && finding.artifact_ids.includes(artifactId)),
    [],
  );
});

Then('evidence {string} recorded a failing run for {string} at baseline {string}', function (
  evidenceId,
  testId,
  baseline,
) {
  const { evidence } = this.call('ingest', { revision: baseline });
  const row = evidence.find((item) => item.evidence_id === evidenceId);
  assert.ok(row);
  assert.equal(row.test_id, testId);
  assert.equal(row.result, 'failed');
});

Given('{string} is marked {string} in its requirement front matter', function (artifactId, status) {
  const { artifact } = this.call('artifact', { id: artifactId, baseline: 'baseline-a' });
  assert.equal(artifact.metadata.status, status);
});

Given('{string} still has accepted links', function (artifactId) {
  const { links } = this.call('links', { baseline: 'baseline-a' });
  assert.ok(links.some((link) => link.source_id === artifactId));
});

Given('the fixture records {string} as a proposed link from {string} to {string}', function (
  linkId,
  sourceId,
  targetId,
) {
  const { link } = this.call('link', { id: linkId, baseline: 'baseline-a' });
  assert.ok(link);
  assert.equal(link.review_state, 'proposed');
  assert.equal(link.source_id, sourceId);
  assert.equal(link.target_id, targetId);
});

Then('{string} has review state {string}', function (linkId, state) {
  const { link } = this.call('link', { id: linkId, baseline: 'baseline-a' });
  assert.equal(link.review_state, state);
});

Then('no accepted link exists between {string} and {string}', function (sourceId, targetId) {
  const { links } = this.call('links', { baseline: 'baseline-a' });
  assert.deepEqual(
    links.filter(
      (link) =>
        link.review_state === 'accepted' && link.source_id === sourceId && link.target_id === targetId,
    ),
    [],
  );
});

Given('a checkout of tag {string}', function (tag) {
  this.results.tag = tag;
});

When('the fixture test suite runs', function () {
  this.results.fixtureRun = this.call('fixture_tests', { tag: this.results.tag });
});

Then('it passes', function () {
  assert.equal(this.results.fixtureRun.exit_code, 0, this.results.fixtureRun.stdout);
});

Then('it fails exactly in {string}', function (selector) {
  // The scenario names each expected failure in its own step, so the exact set is asserted at
  // scenario teardown (see world.js) once every named selector has been collected.
  const run = this.results.fixtureRun;
  assert.notEqual(run.exit_code, 0);
  assert.ok(run.failed.includes(selector), `${selector} did not fail`);
  this.results.expectedFailures = [...(this.results.expectedFailures || []), selector];
});
