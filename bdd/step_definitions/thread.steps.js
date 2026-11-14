import assert from 'node:assert/strict';
import { Given, Then, When } from '@cucumber/cucumber';

function quoted(text) {
  return [...text.matchAll(/"([^"]+)"/g)].map((match) => match[1]);
}

Given('the fixture repository is ingested at {string}', function (baseline) {
  const result = this.call('ingest', { revision: baseline });
  this.results.ingest = result;
  this.results.baseline = baseline;
});

When('the thread for {string} is requested', function (artifactId) {
  if (this.results.withoutExamples) {
    const result = this.call('thread_without_examples', {
      id: artifactId,
      baseline: this.results.baseline,
    });
    this.results.thread = result.thread;
    this.results.withoutExamplesSchema = result.schema_version;
    return;
  }
  const { thread } = this.call('thread', { id: artifactId, baseline: this.results.baseline });
  this.results.thread = thread;
});

Then(/^the response contains (.*)$/, function (text) {
  const ids = quoted(text);
  const present = new Set([
    this.results.thread.root_id,
    ...this.results.thread.accepted_links.flatMap((link) => [link.source_id, link.target_id]),
    ...this.results.thread.artifacts.map((artifact) => artifact.artifact_id),
  ]);
  for (const id of ids) {
    assert.ok(present.has(id), `thread does not contain ${id}`);
  }
});

Then(/^the accepted links ("[^"]+"(?:, "[^"]+")*(?:, and "[^"]+")?)$/, function (text) {
  assert.deepEqual(
    this.results.thread.accepted_links.map((link) => link.link_id),
    quoted(text).sort(),
  );
});

Then('the evidence recorded for {string}', function (artifactId) {
  const evidence = this.results.thread.evidence;
  assert.ok(
    evidence.some((run) => run.scenario_id === artifactId || run.test_id === artifactId),
    `no evidence recorded for ${artifactId}`,
  );
});

Then('the response is identical whether the baseline is given as the tag or the commit SHA', function () {
  const commit = this.results.thread.artifacts[0].revision;
  const bySha = this.call('thread', { id: this.results.thread.root_id, baseline: commit }).thread;
  assert.deepEqual(bySha, this.results.thread);
});

Given('{string} has no accepted links', function (artifactId) {
  const { thread } = this.call('thread', { id: artifactId, baseline: 'baseline-a' });
  assert.deepEqual(thread.accepted_links, []);
});

Then('{string} is empty', function (field) {
  assert.deepEqual(this.results.thread[field], []);
});

Then('{string} appears only in {string}', function (linkId, field) {
  const ids = this.results.thread[field].map((link) => link.link_id);
  assert.ok(ids.includes(linkId), `${linkId} missing from ${field}`);
  const other = field === 'proposed_links' ? 'accepted_links' : 'proposed_links';
  assert.ok(!this.results.thread[other].some((link) => link.link_id === linkId));
});

Given('the committed thread example files are unavailable', function () {
  this.results.withoutExamples = true;
});

Then('the same thread is served from parsed repository data', function () {
  assert.ok(this.results.thread, 'no thread was retrieved');
  assert.ok(this.results.thread.artifacts.length > 0);
  assert.ok(this.results.thread.accepted_links.length > 0);
});

Then('its schema_version matches the running contract', function () {
  assert.equal(this.results.thread.schema_version, this.results.withoutExamplesSchema);
});

Given('{string} does not exist', function (artifactId) {
  const response = this.call('api', { path: `/api/artifacts/${artifactId}` });
  assert.equal(response.status, 404);
  this.results.missingArtifact = response;
});

Then(
  'a thread for an existing source artifact {string} is 404 {string}',
  function (artifactId, code) {
    const response = this.call('api', { path: `/api/threads/${artifactId}?baseline=baseline-a` });
    assert.equal(response.status, 404);
    assert.equal(response.body.code, code);
  },
);

Given('the fixture repository at {string}', function (baseline) {
  this.results.baseline = baseline;
  this.call('ingest', { revision: baseline });
});

When('an ingestion run is requested', function () {
  this.results.lastApi = this.call('api', {
    method: 'POST',
    path: '/api/ingestion/run',
    json: { repository: 'banking-demo', revision: this.results.baseline },
  });
  assert.equal(this.results.lastApi.status, 200);
});

Then('it reports the artifact, accepted-link, proposed-link, and evidence counts', function () {
  const body = this.results.lastApi.body;
  const { commit } = this.call('ingest', { revision: this.results.baseline });
  const state = this.call('ingest', { revision: this.results.baseline });
  assert.equal(body.artifact_count, state.artifacts.length);
  assert.equal(body.accepted_link_count, state.accepted_links.length);
  assert.equal(body.proposed_link_count, state.proposed_links.length);
  assert.equal(body.evidence_count, state.evidence.length);
  assert.ok(body.baseline);
  assert.equal(commit.length, 40);
});

Then('its run id is deterministically derived from the resolved commit', function () {
  const body = this.results.lastApi.body;
  const { commit } = this.call('ingest', { revision: this.results.baseline });
  assert.equal(body.run_id, `ing-${commit.slice(0, 12)}`);
});

When('artifacts are listed for that baseline', function () {
  const result = this.call('api', { path: `/api/artifacts?baseline=${this.results.baseline}` });
  assert.equal(result.status, 200);
  this.results.artifacts = result.body.artifacts;
});

Then('every requirement, scenario, source, and test artifact is returned', function () {
  const types = new Set(this.results.artifacts.map((artifact) => artifact.artifact_type));
  for (const expected of ['requirement', 'scenario', 'source', 'test']) {
    assert.ok(types.has(expected), `missing artifact type ${expected}`);
  }
  assert.deepEqual(
    this.results.artifacts.map((artifact) => artifact.artifact_id).sort(),
    ['CODE-001', 'CODE-002', 'REQ-001', 'REQ-002', 'REQ-003', 'SCN-001', 'SCN-002', 'SCN-003', 'TEST-001', 'TEST-002'],
  );
});

Then('filtering by artifact type returns only that type', function () {
  const result = this.call('api', {
    path: `/api/artifacts?baseline=${this.results.baseline}&artifact_type=scenario`,
  });
  assert.equal(result.status, 200);
  assert.ok(result.body.artifacts.length > 0);
  assert.deepEqual(
    [...new Set(result.body.artifacts.map((artifact) => artifact.artifact_type))],
    ['scenario'],
  );
});

When('its thread is requested', function () {
  this.results.lastApi = this.call('api', { path: '/api/threads/REQ-999?baseline=baseline-a' });
});
