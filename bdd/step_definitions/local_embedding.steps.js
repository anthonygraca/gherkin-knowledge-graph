import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { Given, Then, When } from '@cucumber/cucumber';

const LIVE_EVIDENCE = path.resolve(
  import.meta.dirname,
  '../../docs/reports/omp-closeout/evidence/AI-02-live-observations.json',
);

function local(world, action, args = {}) {
  const result = world.call('local_embedding', { action, ...args });
  world.results.local = result;
  return result;
}

Given('no local model runtime is installed', function () {
  local(this, 'default_fake');
});

Given('no local inference opt-in is configured', function () {
  assert.equal(this.results.local.model_dir_configured, false);
  assert.deepEqual(this.results.local.registered, ['fake']);
});

When('discovery is requested with no provider override', function () {
  assert.ok(this.results.local.candidates.length > 0);
  assert.equal(this.results.local.provider, 'fake');
});

Then('discovery succeeds through {string}', function (provider) {
  assert.equal(this.results.local.provider, provider);
});

Then('no model process is started', function () {
  assert.equal(this.results.local.onnxruntime_imported, false);
});

Then('no model weights are downloaded', function () {
  assert.equal(this.results.local.model_dir_configured, false);
});

Then('no network connection is attempted', function () {
  assert.deepEqual(this.results.local.network_attempts, []);
});

// ------------------------------------------------------------------ SCN-3202

Given('local inference mode is configured with endpoint {string}', function (endpoint) {
  this.results.localEndpoint = endpoint;
  this.results.localMode = 'remote';
});

When('that provider is requested for SCN-001', function () {
  if (this.results.localMode === 'remote') {
    local(this, 'remote_endpoint');
  } else if (this.results.localMode === 'missing') {
    local(this, 'missing_weights', { condition: this.results.localCondition });
  } else {
    throw new Error('no local inference mode was configured');
  }
});

Then('the API returns a 400 problem with code "invalid-request"', function () {
  assert.equal(this.results.local.status, 400);
  assert.equal(this.results.local.body.code, 'invalid-request');
});

Then('no connection to that endpoint is attempted', function () {
  assert.deepEqual(this.results.local.network_attempts, []);
  assert.match(this.results.local.body.detail, /no connection was attempted/i);
});

Then('no candidates are returned', function () {
  assert.equal(this.results.local.body.candidates ?? undefined, undefined);
});

// ------------------------------------------------------------------ SCN-3203

Given('local inference mode is explicitly enabled', function () {
  this.results.localExplicit = true;
});

Given('its configured weights digest is absent from local storage', function () {
  assert.ok(this.results.localExplicit);
  this.results.localMode = 'missing';
  this.results.localCondition = 'absent';
});

Given('its installed weights do not match the configured digest', function () {
  assert.ok(this.results.localExplicit);
  this.results.localMode = 'missing';
  this.results.localCondition = 'mismatch';
});

Given('its weights are installed but the runtime package is unavailable', function () {
  assert.ok(this.results.localExplicit);
  this.results.localMode = 'missing';
  this.results.localCondition = 'runtime_missing';
});

Then('the API returns a 503 problem with code "retrieval-unavailable"', function () {
  assert.equal(this.results.local.status, 503);
  assert.equal(this.results.local.body.code, 'retrieval-unavailable');
});

Then('no automatic download or remote fallback occurs', function () {
  assert.match(
    this.results.local.body.detail,
    /no download or remote fallback|no model is downloaded automatically/i,
  );
});

// ------------------------------------------------------------------ SCN-3204

Given(
  'the local provider adapter uses deterministic embedding and search transports',
  function () {
    local(this, 'contract');
  },
);

When('the shared CandidateDiscovery contract cases execute against it', function () {
  assert.ok(this.results.local.candidates.length > 0);
});

Then('returned source IDs equal the requested source IDs', function () {
  assert.ok(this.results.local.candidates.every((item) => item.source_id === 'SCN-001'));
});

Then('candidate counts obey top_k and relation filters', function () {
  assert.equal(this.results.local.trimmed.length, 1);
  assert.ok(
    this.results.local.sources.every(
      (item) => item.proposed_relation_type === 'implemented_by',
    ),
  );
  assert.ok(
    this.results.local.tests.every(
      (item) => item.proposed_relation_type === 'exercised_by',
    ),
  );
});

Then('ranks are contiguous from one', function () {
  assert.deepEqual(
    this.results.local.candidates.map((item) => item.rank),
    this.results.local.candidates.map((_, index) => index + 1),
  );
});

Then('every candidate carries provider, model_version, and index_revision', function () {
  for (const candidate of this.results.local.candidates) {
    assert.ok(candidate.discovery_provider);
    assert.ok(candidate.model_version);
    assert.match(candidate.index_revision, /^sha256:/);
  }
});

Then('no candidate carries a link ID or review state', function () {
  for (const candidate of this.results.local.candidates) {
    assert.ok(!('link_id' in candidate));
    assert.ok(!('review_state' in candidate));
  }
});

Then(
  'a known artifact with no eligible targets returns an empty list with retained provenance',
  function () {
    assert.equal(this.results.local.empty_status, 200);
    assert.deepEqual(this.results.local.empty_response.candidates, []);
    assert.equal(this.results.local.empty_response.provider, 'local-embeddinggemma');
    assert.ok(this.results.local.empty_response.model_version);
    assert.match(this.results.local.empty_response.index_revision, /^sha256:/);
  },
);

Then(
  'a runtime that cannot report its model identity fails explicitly without candidates',
  function () {
    assert.equal(this.results.local.unavailable_provenance, true);
  },
);

// ------------------------------------------------------------------ SCN-3205

Given(
  'the owner-accepted local model manifest identifies installed weights and runtime',
  function () {
    local(this, 'live', {
      model_dir: process.env.CTA_LOCAL_EMBEDDING_MODEL_DIR,
      weights_digest: process.env.CTA_LOCAL_EMBEDDING_WEIGHTS_DIGEST,
      output: LIVE_EVIDENCE,
    });
    assert.match(this.results.local.weights_digest, /^sha256:/);
    assert.ok(this.results.local.runtime.includes('onnxruntime'));
    assert.ok(this.results.local.model_version.includes('embeddinggemma-2-text-270m'));
    assert.equal(this.results.local.baseline, 'baseline-a');
    assert.ok(fs.existsSync(LIVE_EVIDENCE));
    const retained = JSON.parse(fs.readFileSync(LIVE_EVIDENCE, 'utf8'));
    assert.equal(retained.external_egress, false);
    assert.equal(retained.egress_denied_env, true);
    assert.ok(retained.network_namespace);
  },
);

Then('non-loopback egress is denied for the inference process tree', function () {
  assert.equal(this.results.local.external_egress, false);
  assert.equal(this.results.local.egress_denied_env, true);
});

Given('an isolated banking-demo index has not yet been built', function () {
  assert.ok(this.results.local.load_seconds > 0);
});

When('that runtime indexes baseline-a and executes the shared discovery contract cases', function () {
  const result = this.results.local;
  assert.ok(result.results['SCN-001'].length > 0);
  assert.ok(result.candidates.length > 0);
  assert.ok(result.candidates.every((item) => item.source_id === 'SCN-001'));
  assert.ok(
    result.candidates.every((item) => item.index_revision === result.index_revision),
  );
  assert.deepEqual(
    result.candidates.map((item) => item.rank),
    result.candidates.map((_, index) => index + 1),
  );
  assert.equal(result.trimmed.length, 1);
  assert.equal(result.trimmed[0].rank, 1);
  assert.ok(
    result.sources.every((item) => item.proposed_relation_type === 'implemented_by'),
  );
  assert.ok(
    result.tests.every((item) => item.proposed_relation_type === 'exercised_by'),
  );
  assert.deepEqual(result.incompatible, []);
  assert.ok(
    result.requirements.every((item) => item.proposed_relation_type === 'verified_by'),
  );
  assert.deepEqual(result.empty_source, []);
  assert.equal(result.empty_response.status, 200);
  assert.deepEqual(result.empty_response.body.candidates, []);
  assert.equal(result.empty_response.body.provider, 'local-embeddinggemma');
  assert.ok(result.empty_response.body.model_version);
  assert.equal(result.empty_response.body.index_revision, result.index_revision);
  assert.equal(result.no_link_fields, true);
});

Then('the contract cases complete without external network access', function () {
  assert.equal(this.results.local.external_egress, false);
  assert.equal(this.results.local.unchanged, true);
});

Then('the execution record names the weights digest and runtime version', function () {
  assert.match(this.results.local.weights_digest, /^sha256:[0-9a-f]{64}$/);
  assert.match(this.results.local.runtime, /^onnxruntime \d+\./);
});

Then('it records the query and document formatting versions', function () {
  assert.match(this.results.local.formatting, /^ai02-code-query-v1\/document-title-text-v1$/);
});

Then('the live record retains the egress-denial observation', function () {
  assert.equal(this.results.local.external_egress, false);
  assert.equal(this.results.local.egress_denied_env, true);
  assert.ok(this.results.local.network_namespace);
});

Then('the observed weights, runtime, and formatting match the identified manifest', function () {
  assert.equal(this.results.local.weights_digest, this.results.local.manifest_weights_digest);
  assert.match(this.results.local.runtime, /^onnxruntime \d+\./);
  assert.equal(
    this.results.local.formatting,
    'ai02-code-query-v1/document-title-text-v1',
  );
});

Then('every returned candidate identifies that model and its snapshot binding', function () {
  assert.ok(this.results.local.candidates.length > 0);
  for (const candidate of this.results.local.candidates) {
    assert.equal(candidate.model_version, this.results.local.model_version);
    assert.equal(candidate.index_revision, this.results.local.index_revision);
  }
});

// ------------------------------------------------------------------ SCN-3206

Given(
  'the local adapter receives a non-finite embedding through its deterministic transport',
  function () {
    local(this, 'malformed');
  },
);

When('discovery is requested for SCN-001', function () {
  assert.equal(this.results.local.status, 503);
});

Then('a typed retrieval-unavailable problem is returned', function () {
  assert.equal(this.results.local.status, 503);
  assert.equal(this.results.local.body.code, 'retrieval-unavailable');
});

Then('no partial candidate list is returned', function () {
  assert.equal(this.results.local.body.candidates ?? undefined, undefined);
});

Then('no accepted link, evidence, or finding is written', function () {
  assert.equal(this.results.local.unchanged, true);
});
