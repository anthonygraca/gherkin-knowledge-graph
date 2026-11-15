import assert from 'node:assert/strict';
import { Given, Then, When } from '@cucumber/cucumber';

function retrieval(world, action, args = {}) {
  return world.call('retrieval_lifecycle', { action, ...args });
}

function manifestA(world) {
  return world.results.manifests.baselineA;
}

function candidate(targetId, indexRevision, score) {
  return {
    source_id: 'SCN-001',
    target_id: targetId,
    proposed_relation_type: 'implemented_by',
    rank: 1,
    score,
    discovery_provider: 'fake',
    model_version: 'fake-fixture-v1',
    index_revision: indexRevision,
  };
}

function boundBatch(snapshotBinding, providerIndexRevision, candidates) {
  return {
    snapshot_binding: snapshotBinding,
    provider: 'fake',
    provider_index_revision: providerIndexRevision,
    model_version: 'fake-fixture-v1',
    candidates,
  };
}

Given('a retrieval manifest for banking-demo baseline-a', function () {
  retrieval(this, 'init');
  const response = retrieval(this, 'refresh', { baseline: 'baseline-a' });
  assert.equal(response.status, 200, JSON.stringify(response.body));
  this.results.manifests = { baselineA: response.body };
});

Then('the eligible corpus contains source and test artifacts', function () {
  const artifacts = manifestA(this).artifacts;
  assert.equal(artifacts.length, 4);
  assert.ok(artifacts.every((artifact) => ['source', 'test'].includes(artifact.artifact_type)));
});

When('the refresh planner compares baseline-a with baseline-b', function () {
  this.results.plan = retrieval(this, 'plan', {
    baseline: 'baseline-b',
    previous_baseline: 'baseline-a',
  });
  const refreshed = retrieval(this, 'refresh', {
    baseline: 'baseline-b',
    previous_baseline: 'baseline-a',
  });
  assert.equal(refreshed.status, 200, JSON.stringify(refreshed.body));
  this.results.manifests.baselineB = refreshed.body;
});

Then('changed artifacts are exactly CODE-001 and TEST-002', function () {
  assert.deepEqual(this.results.plan.changed, ['CODE-001', 'TEST-002']);
});

Then('unchanged artifacts are exactly CODE-002 and TEST-001', function () {
  assert.deepEqual(this.results.plan.unchanged, ['CODE-002', 'TEST-001']);
});

Then('the plan records both resolved revisions', function () {
  assert.ok(this.results.plan.commit);
  assert.ok(this.results.plan.previous_commit);
});

Then(
  'the current and referenced previous manifests record their respective artifact content hashes',
  function () {
    const current = this.results.manifests.baselineB;
    const previous = manifestA(this);
    assert.equal(current.previous_snapshot_binding, previous.snapshot_binding);
    assert.notEqual(current.commit, previous.commit);
    for (const artifact of [...current.artifacts, ...previous.artifacts]) {
      assert.match(artifact.content_hash, /^sha256:/);
      assert.ok(artifact.revision);
    }
  },
);

Then('the plan does not claim that CocoIndex embedded exactly two items', function () {
  assert.ok(!('items_embedded' in this.results.plan));
});

// ------------------------------------------------------------------ SCN-3302

Given('two commits have identical eligible artifact IDs, paths, and content hashes', function () {
  retrieval(this, 'init');
  const first = retrieval(this, 'refresh', { baseline: 'baseline-a' });
  assert.equal(first.status, 200, JSON.stringify(first.body));
  this.results.manifests = { baselineA: first.body };
  this.results.evidenceOnly = retrieval(this, 'evidence_only');
  const second = retrieval(this, 'refresh', {
    baseline: this.results.evidenceOnly.commit,
    previous_baseline: 'baseline-a',
  });
  assert.equal(second.status, 200, JSON.stringify(second.body));
  this.results.manifests.evidenceOnly = second.body;
});

Given('their model and retrieval configuration are identical', function () {
  assert.equal(
    this.results.manifests.evidenceOnly.config_digest,
    manifestA(this).config_digest,
  );
});

When('refresh manifests are built for both commits', function () {
  assert.ok(this.results.manifests.evidenceOnly);
});

Then('both manifests have the same corpus cache key', function () {
  assert.equal(
    this.results.manifests.evidenceOnly.corpus_cache_key,
    manifestA(this).corpus_cache_key,
  );
});

Then('their snapshot bindings identify their respective commits', function () {
  assert.equal(manifestA(this).commit, manifestA(this).commit);
  assert.equal(
    this.results.manifests.evidenceOnly.commit,
    this.results.evidenceOnly.commit,
  );
  assert.notEqual(
    this.results.manifests.evidenceOnly.snapshot_binding,
    manifestA(this).snapshot_binding,
  );
});

Then('the content-change plan is empty', function () {
  const manifest = this.results.manifests.evidenceOnly;
  assert.deepEqual(manifest.changed, []);
  assert.deepEqual(manifest.added, []);
  assert.deepEqual(manifest.removed, []);
});

Then('no source change or verification failure is inferred from the different commits', function () {
  assert.equal(this.results.evidenceOnly.findings_unchanged, true);
  assert.deepEqual(this.results.evidenceOnly.verification_failed, []);
});

// ------------------------------------------------------------------ SCN-3303

Given('an existing manifest and unchanged artifact content', function () {
  retrieval(this, 'init');
  const old = retrieval(this, 'refresh', {
    baseline: 'baseline-a',
    weights_digest: 'sha256:' + 'a'.repeat(64),
  });
  assert.equal(old.status, 200, JSON.stringify(old.body));
  this.results.manifests = { old: old.body };
});

When('a manifest is requested with a different weights digest', function () {
  const current = retrieval(this, 'refresh', {
    baseline: 'baseline-a',
    previous_baseline: 'baseline-a',
    weights_digest: 'sha256:' + 'b'.repeat(64),
  });
  assert.equal(current.status, 200, JSON.stringify(current.body));
  this.results.manifests.current = current.body;
});

Then('the corpus cache key differs', function () {
  assert.notEqual(
    this.results.manifests.current.corpus_cache_key,
    this.results.manifests.old.corpus_cache_key,
  );
});

Then('the old cache is not declared compatible with the new model', function () {
  assert.notEqual(
    this.results.manifests.current.config_digest,
    this.results.manifests.old.config_digest,
  );
  assert.notEqual(
    this.results.manifests.current.config.weights_digest,
    this.results.manifests.old.config.weights_digest,
  );
});

Then('the old manifest remains unchanged', function () {
  const all = retrieval(this, 'manifests').body.manifests;
  const old = all.find(
    (manifest) => manifest.snapshot_binding === this.results.manifests.old.snapshot_binding,
  );
  assert.deepEqual(old, this.results.manifests.old);
});

// ------------------------------------------------------------------ SCN-3304

Given('baseline-a has a published retrieval manifest', function () {
  retrieval(this, 'init');
  const first = retrieval(this, 'refresh', { baseline: 'baseline-a' });
  assert.equal(first.status, 200, JSON.stringify(first.body));
  this.results.manifests = { baselineA: first.body };
});

Given('the deterministic index adapter fails while building baseline-b', function () {
  this.results.failingAdapter = true;
});

When('refresh is requested for baseline-b', function () {
  this.results.failedRefresh = retrieval(this, 'refresh', {
    baseline: 'baseline-b',
    previous_baseline: 'baseline-a',
    adapter: this.results.failingAdapter ? 'failing' : undefined,
  });
});

Then('refresh reports a typed failure', function () {
  assert.equal(this.results.failedRefresh.status, 503);
  assert.equal(this.results.failedRefresh.error, 'RetrievalUnavailable');
});

Then('no baseline-b snapshot is published', function () {
  const response = retrieval(this, 'manifest', { baseline: 'baseline-b' });
  assert.equal(response.status, 404);
});

Then('requests explicitly naming baseline-a still use its original manifest', function () {
  const response = retrieval(this, 'manifest', { baseline: 'baseline-a' });
  assert.equal(response.status, 200);
  assert.deepEqual(response.body, manifestA(this));
});

Then('requests naming baseline-b do not receive baseline-a results as a substitute', function () {
  const response = retrieval(this, 'manifest', { baseline: 'baseline-b' });
  assert.equal(response.status, 404);
  assert.equal(response.body.code, 'retrieval-snapshot-not-found');
});

// ------------------------------------------------------------------ SCN-3305

Given("one candidate batch is bound to baseline-a's manifest snapshot binding", function () {
  retrieval(this, 'init');
  const first = retrieval(this, 'refresh', { baseline: 'baseline-a' });
  assert.equal(first.status, 200, JSON.stringify(first.body));
  this.results.manifests = { baselineA: first.body };
  const binding = first.body.snapshot_binding;
  this.results.batchA = boundBatch(binding, 'sha256:provider-a', [
    candidate('CODE-001', binding, 0.9),
  ]);
});

Given("the batch retains the provider's own index revision", function () {
  assert.equal(this.results.batchA.provider_index_revision, 'sha256:provider-a');
});

Given("another candidate batch is bound to baseline-b's manifest snapshot binding", function () {
  const second = retrieval(this, 'refresh', {
    baseline: 'baseline-b',
    previous_baseline: 'baseline-a',
  });
  assert.equal(second.status, 200, JSON.stringify(second.body));
  this.results.manifests.baselineB = second.body;
  const binding = second.body.snapshot_binding;
  this.results.batchB = boundBatch(binding, 'sha256:provider-b', [
    candidate('CODE-002', binding, 0.8),
  ]);
});

When('the batches are submitted to the candidate-combination service', function () {
  this.results.combination = retrieval(this, 'combine', {
    snapshot_binding: manifestA(this).snapshot_binding,
    batches: [this.results.batchA, this.results.batchB],
  });
});

Then('combination fails with code {string}', function (code) {
  assert.equal(this.results.combination.status, 409);
  assert.equal(this.results.combination.body.code, code);
});

Then('no combined ranked list is returned', function () {
  assert.equal(this.results.combination.body.candidates ?? undefined, undefined);
});

When('the baseline-a batch is submitted with the expected binding', function () {
  this.results.combination = retrieval(this, 'combine', {
    snapshot_binding: manifestA(this).snapshot_binding,
    batches: [this.results.batchA],
  });
  assert.equal(this.results.combination.status, 200, JSON.stringify(this.results.combination.body));
});

Then('a ranked list is returned', function () {
  assert.ok(this.results.combination.body.candidates.length > 0);
  assert.deepEqual(
    this.results.combination.body.candidates.map((item) => item.rank),
    this.results.combination.body.candidates.map((_, index) => index + 1),
  );
});

Then('every candidate carries the CTA snapshot binding', function () {
  const binding = manifestA(this).snapshot_binding;
  assert.ok(
    this.results.combination.body.candidates.every(
      (item) => item.index_revision === binding,
    ),
  );
});

Then("the batch provenance retains the provider's own index revision", function () {
  assert.equal(
    this.results.combination.body.provenance[0].provider_index_revision,
    'sha256:provider-a',
  );
});

// ------------------------------------------------------------------ SCN-3306

Given('the deterministic search transport exposes no embedding counter', function () {
  retrieval(this, 'init');
  const first = retrieval(this, 'refresh', { baseline: 'baseline-a' });
  assert.equal(first.status, 200, JSON.stringify(first.body));
  this.results.manifests = { baselineA: first.body };
});

When('a baseline-b refresh completes', function () {
  const second = retrieval(this, 'refresh', {
    baseline: 'baseline-b',
    previous_baseline: 'baseline-a',
  });
  assert.equal(second.status, 200, JSON.stringify(second.body));
  this.results.manifests.baselineB = second.body;
});

Then('its report contains measured non-negative elapsed time', function () {
  const report = this.results.manifests.baselineB;
  assert.ok(report.elapsed_ms >= 0);
});

Then('it contains added, changed, removed, and unchanged artifact counts', function () {
  const report = this.results.manifests.baselineB;
  assert.equal(report.added_count, 0);
  assert.equal(report.changed_count, 2);
  assert.equal(report.removed_count, 0);
  assert.equal(report.unchanged_count, 2);
});

Then('items_embedded is null with availability {string}', function (availability) {
  const report = this.results.manifests.baselineB;
  assert.equal(report.items_embedded, null);
  assert.equal(report.items_embedded_availability, availability);
});

Then('the report identifies the published snapshot binding and configuration digest', function () {
  const report = this.results.manifests.baselineB;
  assert.match(report.snapshot_binding, /^snapshot:sha256:/);
  assert.match(report.config_digest, /^sha256:/);
});
