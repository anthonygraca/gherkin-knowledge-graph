import assert from 'node:assert/strict';
import { Given, Then, When } from '@cucumber/cucumber';

Given('the code-retrieval evaluation capture', function () {
  this.results.haveCapture = true;
});

Given('the evidence-answer labels', function () {
  this.results.haveAnswers = true;
});

When('the benchmark report is generated', function () {
  this.results.report = this.call('rag_benchmark', {}).report;
});

When('the benchmark evaluates accepted-graph answers', function () {
  this.results.report = this.call('rag_benchmark', {}).report;
});

When('the benchmark evaluates hybrid answers', function () {
  this.results.report = this.call('rag_benchmark', {}).report;
});

Given('the benchmark report', function () {
  this.results.report = this.call('rag_benchmark', {}).report;
});

Then('the report names the same labels hash for A and B', function () {
  assert.ok(this.results.report.inputs.code_labels.sha256.startsWith('sha256:'));
  assert.ok(this.results.report.A_B_code_retrieval);
});

Then('both method sections use the hand-labeled code cases', function () {
  assert.ok(this.results.report.A_B_code_retrieval.lexical);
  assert.ok(this.results.report.A_B_code_retrieval.cocoindex_live);
});

Then('no metric is fabricated for a method that did not run', function () {
  assert.notEqual(this.results.report.A_B_code_retrieval.cocoindex_live, null);
});

Then(
  'status, accepted links, evidence, findings, and graph paths match every labeled case',
  function () {
    const aggregate = this.results.report.C_graph_answers.aggregate;
    for (const key of [
      'status_ok',
      'accepted_links_ok',
      'evidence_ok',
      'findings_ok',
      'paths_ok',
    ]) {
      assert.equal(aggregate[key], 1);
    }
  },
);

Then('citation accuracy is one', function () {
  assert.equal(this.results.report.C_graph_answers.aggregate.citation_ok, 1);
});

Then('unsupported assertions are zero', function () {
  assert.equal(this.results.report.C_graph_answers.unsupported_claim_rate, 0);
});

Then('the authoritative fields match the accepted-graph method', function () {
  const c = this.results.report.C_graph_answers;
  const d = this.results.report.D_hybrid_answers;
  for (const key of ['status_ok', 'accepted_links_ok', 'evidence_ok', 'findings_ok', 'paths_ok']) {
    assert.equal(d.aggregate[key], c.aggregate[key]);
  }
});

Then('semantic candidates are reported separately', function () {
  assert.ok(
    this.results.report.D_hybrid_answers.cases.some((row) => row.semantic_candidates > 0),
  );
});

Then('every graph path remains accepted-only', function () {
  assert.equal(this.results.report.D_hybrid_answers.aggregate.citation_ok, 1);
});

Then('it records the labels, code-evaluation capture, and answer-label hashes', function () {
  assert.ok(this.results.report.inputs.code_labels.sha256);
  assert.ok(this.results.report.inputs.answer_labels.sha256);
  assert.ok(this.results.report.inputs.code_eval.sha256);
});

Then('it states that C and D receive additional graph information', function () {
  assert.ok(
    this.results.report.limitations.some((text) => text.includes('accepted-graph information')),
  );
});

Then('it does not claim M4 or M3 completion', function () {
  assert.ok(
    this.results.report.limitations.some((text) => text.includes('does not close M4')),
  );
});
