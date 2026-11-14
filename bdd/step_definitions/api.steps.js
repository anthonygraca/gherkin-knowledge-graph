import assert from 'node:assert/strict';
import { Given, Then, When } from '@cucumber/cucumber';

function callPath(world, verb, path) {
  world.results.lastApi = world.call('api', { method: verb, path });
  return world.results.lastApi;
}

const REQUIRED = {
  Artifact: [
    'artifact_id',
    'artifact_type',
    'title',
    'source_uri',
    'repository',
    'revision',
    'content_hash',
    'locator',
    'metadata',
  ],
  FindingsResponse: ['schema_version', 'baseline', 'findings'],
  ThreadResponse: [
    'schema_version',
    'root_id',
    'baseline',
    'artifacts',
    'accepted_links',
    'proposed_links',
    'evidence',
  ],
};

When(/^(GET|POST) (\/\S+) is called$/, function (verb, path) {
  callPath(this, verb, path);
});

When('{string} is called', function (request) {
  const [, verb, path] = request.match(/^(GET|POST) (\/\S+)$/);
  callPath(this, verb, path);
});

Then('the response validates against the {string} contract', function (contract) {
  const body = this.results.lastApi.body;
  for (const field of REQUIRED[contract]) {
    assert.ok(field in body, `${contract} response is missing ${field}`);
  }
  if (contract === 'FindingsResponse') {
    for (const finding of body.findings) {
      assert.match(finding.finding_id, /^FND-[0-9a-f]{16}$/);
      assert.ok(finding.rule_id);
    }
  }
});

Then('its {string} equals the commit SHA tagged {string}', function (field, tag) {
  const { commit } = this.call('ingest', { revision: tag });
  assert.equal(this.results.lastApi.body[field], commit);
});

Then('{string} returns the accepted chain plus evidence', function (path) {
  const [, verb, target] = path.match(/^(GET|POST) (\/\S+)$/);
  const response = callPath(this, verb, target);
  assert.equal(response.status, 200);
  assert.ok(response.body.accepted_links.length >= 3);
  assert.ok(response.body.evidence.length >= 1);
  this.results.threadResponse = response.body;
});

Then('{string} validates against the {string} contract', function (path, contract) {
  const [, verb, target] = path.match(/^(GET|POST) (\/\S+)$/);
  const response = callPath(this, verb, target);
  assert.equal(response.status, 200);
  for (const field of REQUIRED[contract]) {
    assert.ok(field in response.body, `${contract} response is missing ${field}`);
  }
});

Given('the backend runs with no network and no embedding or LLM service', function () {
  const settings = this.call('settings', {});
  assert.equal(settings.ai_mode, 'fake');
  assert.equal(settings.discovery_provider, 'fake');
  const health = this.call('api', { path: '/health' });
  assert.equal(health.status, 200);
  assert.deepEqual(health.body.discovery_providers, ['fake']);
});

Given('{string} resolves to a commit SHA in the fixture manifest', function (baseline) {
  const { commit } = this.call('ingest', { revision: baseline });
  this.results.baseline = baseline;
  this.results.commit = commit;
  assert.equal(commit.length, 40);
});

When('the same endpoint is called with the tag and with that SHA', function () {
  this.results.byTag = this.call('api', {
    path: `/api/artifacts/REQ-001?baseline=${this.results.baseline}`,
  });
  this.results.bySha = this.call('api', {
    path: `/api/artifacts/REQ-001?baseline=${this.results.commit}`,
  });
});

Then('both responses are identical', function () {
  assert.deepEqual(this.results.bySha, this.results.byTag);
});

Then('the status is {int}', function (status) {
  assert.equal(this.results.lastApi.status, status);
});

Then('the body is an RFC 9457 problem document with a {string} type', function (type) {
  const body = this.results.lastApi.body;
  assert.equal(body.type, type);
  assert.equal(body.status, Number(type.split(':').pop() === '' ? 0 : body.status));
  assert.ok(body.title);
  assert.ok(body.detail);
  assert.ok(body.instance);
});

Given('the candidate-discovery provider is {string}', function (provider) {
  this.results.provider = provider;
  const result = this.call('discover', {
    artifact_id: 'SCN-001',
    provider,
    assert_known: true,
  });
  this.results.discovery = result;
});

When('candidates are requested for {string}', function (artifactId) {
  this.results.linksBefore = this.call('links', { baseline: 'baseline-a' }).links;
  this.results.discovery = this.call('discover', {
    artifact_id: artifactId,
    provider: this.results.provider,
  });
});

Then(
  '{string} is returned as a proposed {string} candidate at rank {int}',
  function (targetId, relationType, rank) {
    const candidate = this.results.discovery.candidates.find(
      (item) => item.target_id === targetId && item.proposed_relation_type === relationType,
    );
    assert.ok(candidate, `no ${relationType} candidate for ${targetId}`);
    assert.equal(candidate.rank, rank);
  },
);

Then('the response includes the provider name, model version, and index revision', function () {
  const response = this.results.discovery;
  assert.ok(response.provider);
  assert.ok(response.model_version);
  assert.match(response.index_revision, /^sha256:[0-9a-f]{64}$/);
});

Then('the candidate carries no link identifier or review state', function () {
  for (const candidate of this.results.discovery.candidates) {
    assert.ok(!('link_id' in candidate));
    assert.ok(!('review_state' in candidate));
  }
});

Then('no accepted link is created or modified', function () {
  const after = this.call('links', { baseline: 'baseline-a' }).links;
  assert.deepEqual(after, this.results.linksBefore);
});

// ---------------------------------------------------------------- AI-01 contract

Given('the {string} provider and any future local provider', function (provider) {
  this.results.provider = provider;
  const result = this.call('discover', { artifact_id: 'SCN-001', provider });
  this.results.discovery = result;
});

When('the shared contract tests run against a provider', function () {
  const probes = ['SCN-001', 'SCN-002'].map((artifactId) =>
    this.call('discover', { artifact_id: artifactId, provider: this.results.provider }),
  );
  for (const probe of probes) {
    assert.deepEqual(
      probe.candidates.map((candidate) => candidate.rank),
      probe.candidates.map((_, index) => index + 1),
    );
    for (const candidate of probe.candidates) {
      assert.equal(candidate.discovery_provider, this.results.provider);
    }
  }
  this.results.probes = probes;
});

Then('it returns ranked candidates whose source_id is the requested artifact', function () {
  for (const probe of this.results.probes) {
    assert.ok(probe.candidates.length > 0);
    for (const candidate of probe.candidates) {
      assert.equal(candidate.source_id, probe.candidates[0].source_id);
    }
  }
});

Then('it reports the provider name, model version, and index revision', function () {
  for (const probe of this.results.probes) {
    assert.ok(probe.provider);
    assert.ok(probe.model_version);
    assert.ok(probe.index_revision);
  }
});

Then('it exposes no way to accept, store, or verify a link', function () {
  for (const probe of this.results.probes) {
    for (const candidate of probe.candidates) {
      assert.deepEqual(
        Object.keys(candidate).sort(),
        [
          'discovery_provider',
          'index_revision',
          'model_version',
          'proposed_relation_type',
          'rank',
          'rationale',
          'score',
          'source_id',
          'target_id',
        ].sort(),
      );
    }
  }
});

Given('an unknown provider name', function () {
  this.results.provider = 'not-a-provider';
});

When('candidates are requested', function () {
  this.results.lastApi = this.call('api', {
    method: 'POST',
    path: '/api/discovery',
    json: { artifact_id: 'SCN-001', provider: this.results.provider },
  });
});

Then('the request fails with {string}', function (code) {
  assert.equal(this.results.lastApi.status, 400);
  assert.equal(this.results.lastApi.body.code, code);
});

Then('the response lists the registered providers', function () {
  assert.match(this.results.lastApi.body.detail, /fake/);
});
