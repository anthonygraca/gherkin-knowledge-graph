import assert from 'node:assert/strict';
import { Given, Then, When } from '@cucumber/cucumber';

Given('the labeled candidate index with positive and negative labels', function () {
  this.results.labels = true;
});

When('the evaluation harness runs for the fake provider', function () {
  this.results.report = this.call('candidate_benchmark', {}).report;
});

When('the evaluation harness runs', function () {
  this.results.report = this.call('candidate_benchmark', {}).report;
});

Given('a completed evaluation report', function () {
  this.results.originalReport = this.call('candidate_benchmark', {}).report;
});

Given('no network, model, or vector service', function () {
  this.results.offline = true;
});

When('the labeled dataset changes', function () {
  const variant = this.call('dataset_variant', {});
  this.results.variantHash = variant.sha256;
  this.results.variantReport = this.call('candidate_benchmark', {
    dataset_path: variant.path,
  }).report;
});

Then(
  'it reports recall@1, recall@5, recall@10, precision@k, MRR, and the false-candidate rate',
  function () {
    const aggregate = this.results.report.aggregate;
    for (const key of ['recall_at_1', 'recall_at_5', 'recall_at_10', 'precision_at_5', 'mrr', 'false_candidate_rate']) {
      assert.ok(key in aggregate, `missing ${key}`);
    }
  },
);

Then('the report records the provider, model version, and index revision', function () {
  assert.equal(this.results.report.provider, 'fake');
  assert.ok(this.results.report.model_version);
  assert.ok(this.results.report.index_revision.startsWith('sha256:'));
});

Then('the report records the dataset hash and per-source results', function () {
  assert.ok(this.results.report.dataset_sha256.startsWith('sha256:'));
  assert.ok(this.results.report.sources.length > 0);
});

Then('the previous report remains with its recorded dataset hash', function () {
  assert.ok(this.results.originalReport.dataset_sha256);
  assert.notEqual(this.results.variantReport.dataset_sha256, this.results.originalReport.dataset_sha256);
});

Then('a new report names the new hash', function () {
  assert.equal(this.results.variantReport.dataset_sha256, this.results.variantHash);
});

Then('it completes using only the fixture candidate index', function () {
  assert.equal(this.results.report.provider, 'fake');
});
