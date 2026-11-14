import assert from 'node:assert/strict';
import { Given, Then, When } from '@cucumber/cucumber';

function answer(world, request) {
  world.results.response = world.call('answer', { request }).response;
  return world.results.response;
}

When('an evidence answer is requested for {string}', function (requirementId) {
  answer(this, { requirement_id: requirementId, baseline: this.results.baseline });
});

When(
  'an evidence answer is requested for {string} with semantic candidates',
  function (requirementId) {
    answer(this, {
      requirement_id: requirementId,
      baseline: this.results.baseline,
      include_semantic_candidates: true,
    });
  },
);

When('an evidence answer is requested for the question {string}', function (question) {
  answer(this, { question, baseline: this.results.baseline });
});

Then('the status is {string}', function (status) {
  assert.equal(this.results.response.status, status);
});

Then('the accepted links are {string}, {string}, and {string}', function (a, b, c) {
  assert.deepEqual(
    this.results.response.accepted_links.map((link) => link.link_id),
    [a, b, c],
  );
});

Then('the evidence includes {string}', function (evidenceId) {
  assert.ok(
    this.results.response.evidence.some((row) => row.evidence_id === evidenceId),
  );
});

Then('the graph paths use only accepted links', function () {
  const accepted = new Set(this.results.response.accepted_links.map((link) => link.link_id));
  for (const path of this.results.response.graph_paths) {
    for (const linkId of path.link_ids) assert.ok(accepted.has(linkId));
  }
});

Then('the answer requests reverification rather than declaring failure', function () {
  assert.match(this.results.response.answer, /reverification_required/);
  assert.match(this.results.response.answer, /not a verification failure/);
});

Then('the accepted links are empty', function () {
  assert.deepEqual(this.results.response.accepted_links, []);
});

Then('{string} appears only in the proposed links', function (linkId) {
  assert.deepEqual(
    this.results.response.proposed_links.map((link) => link.link_id),
    [linkId],
  );
  assert.ok(!this.results.response.accepted_links.some((link) => link.link_id === linkId));
});

Then('the answer makes no verification claim', function () {
  assert.match(this.results.response.answer, /no verification claim/i);
  assert.equal(this.results.response.status, 'abstained');
});

Then('the evidence state is {string}', function (state) {
  assert.equal(this.results.response.evidence_state, state);
});

Then('a {string} finding is included', function (findingType) {
  assert.ok(
    this.results.response.findings.some((finding) => finding.finding_type === findingType),
  );
});

Then('the answer names {string}', function (token) {
  assert.ok(this.results.response.answer.includes(token));
});

Then('the answer does not describe a reverification request', function () {
  assert.ok(!/reverification_required/.test(this.results.response.answer));
});

Then('semantic candidates are returned separately', function () {
  assert.ok(this.results.response.semantic_candidates.length > 0);
  assert.ok(this.results.response.semantic_method);
});

Then('every graph path link id is an accepted link', function () {
  const accepted = new Set(this.results.response.accepted_links.map((link) => link.link_id));
  for (const path of this.results.response.graph_paths) {
    for (const linkId of path.link_ids) assert.ok(accepted.has(linkId));
  }
});

Then('the response says candidates are proposals', function () {
  assert.ok(
    this.results.response.uncertainties.some((text) => text.includes('proposals')),
  );
});

Then('every referenced link id exists in the retrieved context', function () {
  const known = new Set([
    ...this.results.response.accepted_links.map((link) => link.link_id),
    ...this.results.response.proposed_links.map((link) => link.link_id),
  ]);
  for (const linkId of this.results.response.references.link_ids) {
    assert.ok(known.has(linkId), `unknown citation ${linkId}`);
  }
});

Then('{string} is not cited', function (linkId) {
  assert.ok(!this.results.response.references.link_ids.includes(linkId));
});

Then('no requirement id is returned', function () {
  assert.equal(this.results.response.requirement_id, null);
});

Then('the explanation method is {string}', function (method) {
  assert.equal(this.results.response.explanation_method, method);
});

Then('no chat model is claimed', function () {
  assert.equal(this.results.response.chat_model, null);
});
