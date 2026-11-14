import assert from 'node:assert/strict';
import { Given, Then, When } from '@cucumber/cucumber';

Given(
  'an accepted link between {string} and {string} of type {string}',
  function (sourceId, targetId, relationType) {
    const { thread } = this.call('thread', { id: sourceId, baseline: 'baseline-b' });
    const link = thread.accepted_links.find(
      (item) => item.target_id === targetId && item.relation_type === relationType,
    );
    assert.ok(link, `no accepted ${relationType} link ${sourceId} -> ${targetId}`);
    this.results.link = link;
  },
);

When('the link is read back', function () {
  const { link } = this.call('link', { id: this.results.link.link_id, baseline: 'baseline-b' });
  this.results.link = link;
});

Then('its review_state is {string}', function (state) {
  assert.equal(this.results.link.review_state, state);
});

Then('its provenance records the reviewer and the decision time', function () {
  assert.ok(this.results.link.provenance.reviewer_id, 'reviewer_id missing');
  assert.ok(this.results.link.provenance.decided_at, 'decided_at missing');
  assert.ok(this.results.link.created_at);
  assert.ok(this.results.link.updated_at);
});

When('the links for {string} are listed', function (artifactId) {
  this.results.thread = this.call('thread', { id: artifactId, baseline: 'baseline-a' }).thread;
});

Given(
  'a link from {string} to {string} of type {string}',
  function (sourceId, targetId, relationType) {
    const repo = this.call('repo_from_fixture', { name: 'reversed', tag: 'baseline-b' });
    const accepted = {
      schema_version: this.call('schema_version', {}).version,
      repository: 'probe',
      review_state: 'accepted',
      links: [
        {
          link_id: 'LNK-901',
          source_id: sourceId,
          target_id: targetId,
          relation_type: relationType,
          review_state: 'accepted',
          provenance: { reviewer_id: 'bdd', decision_at: '2026-11-13T00:00:00+00:00' },
          created_at: '2026-11-13T00:00:00+00:00',
          updated_at: '2026-11-13T00:00:00+00:00',
        },
      ],
    };
    this.call('commit', {
      name: 'reversed',
      files: { 'evidence/accepted-links.json': JSON.stringify(accepted, null, 2) },
      message: 'probe reversed direction',
    });
    this.results.probeRepo = 'reversed';
  },
);

When('the revision is ingested', function () {
  this.results.attempt = this.attempt('ingest', {
    name: this.results.probeRepo,
    revision: 'HEAD',
  });
});

Then('ingestion fails with an error naming the link and the expected direction', function () {
  assert.equal(this.results.attempt.ok, false, 'ingestion should have failed');
  assert.match(this.results.attempt.error.detail, /LNK-901/);
  assert.match(this.results.attempt.error.detail, /must connect requirement -> scenario/);
});

Given('a link whose target {string} does not exist at the revision', function (targetId) {
  this.call('repo_from_fixture', { name: 'dangling', tag: 'baseline-b' });
  this.results.probeRepo = 'dangling';
  const accepted = {
    schema_version: this.call('schema_version', {}).version,
    repository: 'probe',
    review_state: 'accepted',
    links: [
      {
        link_id: 'LNK-902',
        source_id: 'REQ-001',
        target_id: targetId,
        relation_type: 'verified_by',
        review_state: 'accepted',
        provenance: { reviewer_id: 'bdd', decision_at: '2026-11-13T00:00:00+00:00' },
        created_at: '2026-11-13T00:00:00+00:00',
        updated_at: '2026-11-13T00:00:00+00:00',
      },
    ],
  };
  this.call('commit', {
    name: 'dangling',
    files: { 'evidence/accepted-links.json': JSON.stringify(accepted, null, 2) },
    message: 'probe unknown target',
  });
});

Given('{string} contains a link with review_state {string}', function (path, state) {
  this.call('repo_from_fixture', { name: 'wrong-state', tag: 'baseline-a' });
  this.results.probeRepo = 'wrong-state';
  const accepted = {
    schema_version: this.call('schema_version', {}).version,
    repository: 'probe',
    review_state: 'accepted',
    links: [
      {
        link_id: 'LNK-903',
        source_id: 'REQ-001',
        target_id: 'SCN-001',
        relation_type: 'verified_by',
        review_state: state,
        provenance: { reviewer_id: 'bdd', decision_at: '2026-11-13T00:00:00+00:00' },
        created_at: '2026-11-13T00:00:00+00:00',
        updated_at: '2026-11-13T00:00:00+00:00',
      },
    ],
  };
  this.call('commit', {
    name: 'wrong-state',
    files: { [path]: JSON.stringify(accepted, null, 2) },
    message: 'probe wrong review state',
  });
});

Then('ingestion fails with an error naming the file and the link', function () {
  assert.equal(this.results.attempt.ok, false);
  assert.match(this.results.attempt.error.detail, /evidence\/accepted-links\.json/);
  assert.match(this.results.attempt.error.detail, /LNK-903/);
});

Given('a revision with accepted and proposed links', function () {
  this.results.baseline = 'baseline-a';
});

When('the revision is ingested twice', function () {
  this.results.ingest1 = this.call('ingest', { revision: 'baseline-a' });
  this.results.ingest2 = this.call('ingest', { revision: 'baseline-a' });
});

Then('the link ids, review states, provenance, and timestamps are identical', function () {
  const pick = (revision) =>
    [...revision.accepted_links, ...revision.proposed_links]
      .map((link) => ({
        link_id: link.link_id,
        review_state: link.review_state,
        provenance: link.provenance,
        created_at: link.created_at,
        updated_at: link.updated_at,
      }))
      .sort((a, b) => a.link_id.localeCompare(b.link_id));
  assert.deepEqual(pick(this.results.ingest1), pick(this.results.ingest2));
});

Then('no decision history is rewritten', function () {
  const history = this.results.ingest2.accepted_links.map((link) => link.provenance.decision_at);
  assert.deepEqual(history, this.results.ingest1.accepted_links.map((link) => link.provenance.decision_at));
});


Given('{string} proposes {string} verified_by {string}', function (linkId, sourceId, targetId) {
  const { link } = this.call('link', { id: linkId, baseline: 'baseline-a' });
  assert.ok(link, `${linkId} must exist at baseline-a`);
  assert.equal(link.review_state, 'proposed');
  assert.equal(link.source_id, sourceId);
  assert.equal(link.target_id, targetId);
  assert.equal(link.relation_type, 'verified_by');
});

Then('{string} appears only in the proposed collection', function (linkId) {
  assert.ok(this.results.thread.proposed_links.some((link) => link.link_id === linkId));
  assert.ok(!this.results.thread.accepted_links.some((link) => link.link_id === linkId));
});

Then('the accepted collection is empty', function () {
  assert.deepEqual(this.results.thread.accepted_links, []);
});
