import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { Given, Then, When } from '@cucumber/cucumber';

const FINDING_ID = /^FND-[0-9a-f]{16}$/;

function fingerprint(ruleId, findingType, artifactIds) {
  const payload = `${ruleId}|${findingType}|${[...new Set(artifactIds)].sort().join(',')}`;
  return `FND-${createHash('sha256').update(payload, 'utf8').digest('hex').slice(0, 16)}`;
}

function findings(world) {
  assert.ok(world.results.findings, 'no assurance evaluation has run in this scenario');
  return world.results.findings.findings;
}

Given('requirement {string} exists', function (artifactId) {
  const { artifact } = this.call('artifact', { id: artifactId, baseline: 'baseline-a' });
  assert.equal(artifact.artifact_type, 'requirement');
  this.results.artifact = artifact;
});

Given('no accepted verification scenario is linked to {string}', function (artifactId) {
  const { thread } = this.call('thread', { id: artifactId, baseline: 'baseline-a' });
  const accepted = thread.accepted_links.filter(
    (link) => link.source_id === artifactId && link.relation_type === 'verified_by',
  );
  assert.deepEqual(accepted, []);
});

When('assurance evaluates baseline {string}', function (baseline) {
  const result = this.call('findings', { baseline });
  this.results.findings = result;
  this.results.baseline = baseline;
});

Then('a {string} finding is produced for {string}', function (findingType, artifactId) {
  const match = findings(this).filter(
    (finding) => finding.finding_type === findingType && finding.artifact_ids.includes(artifactId),
  );
  assert.equal(match.length, 1, `expected exactly one ${findingType} finding for ${artifactId}`);
});

Given(
  '{string} proposes {string} verified_by {string} and is not accepted',
  function (linkId, sourceId, targetId) {
    const { link } = this.call('link', { id: linkId, baseline: 'baseline-a' });
    assert.ok(link, `${linkId} must exist at baseline-a`);
    assert.equal(link.review_state, 'proposed');
    assert.equal(link.source_id, sourceId);
    assert.equal(link.target_id, targetId);
    assert.equal(link.relation_type, 'verified_by');
  },
);

Then('{string} still produces a {string} finding', function (artifactId, findingType) {
  const match = findings(this).filter(
    (finding) => finding.finding_type === findingType && finding.artifact_ids.includes(artifactId),
  );
  assert.ok(match.length >= 1, `expected a ${findingType} finding for ${artifactId}`);
});

Then('the proposal is not counted as an accepted link', function () {
  const { thread } = this.call('thread', { id: 'REQ-002', baseline: 'baseline-a' });
  assert.deepEqual(thread.accepted_links, []);
  assert.deepEqual(
    thread.proposed_links.map((link) => link.link_id),
    ['LNK-007'],
  );
});

Given(
  '{string} has accepted link {string} verified_by {string}',
  function (artifactId, linkId, targetId) {
    const { link } = this.call('link', { id: linkId, baseline: 'baseline-a' });
    assert.equal(link.review_state, 'accepted');
    assert.equal(link.source_id, artifactId);
    assert.equal(link.target_id, targetId);
    assert.equal(link.relation_type, 'verified_by');
  },
);

Then('no {string} finding names {string}', function (findingType, artifactId) {
  const match = findings(this).filter(
    (finding) => finding.finding_type === findingType && finding.artifact_ids.includes(artifactId),
  );
  assert.deepEqual(match, []);
});

Given('assurance evaluated baseline {string}', function (baseline) {
  const result = this.call('findings', { baseline });
  this.results.findings = result;
  this.results.baseline = baseline;
});

Then(
  'each finding names the rule id, severity, artifact revisions, and resolved commit',
  function () {
    const evaluated = findings(this);
    assert.ok(evaluated.length > 0);
    for (const finding of evaluated) {
      assert.match(finding.rule_id, /^RULE-[A-Z-]+$/);
      assert.ok(['low', 'medium', 'high'].includes(finding.severity));
      assert.equal(finding.evaluated_baseline, this.results.findings.commit);
      assert.ok(
        Object.keys(finding.artifact_revisions).length >= 1,
        `finding ${finding.finding_id} must carry artifact revisions`,
      );
      for (const artifactId of finding.artifact_ids) {
        assert.ok(
          finding.artifact_revisions[artifactId],
          `finding ${finding.finding_id} is missing the revision of ${artifactId}`,
        );
      }
    }
  },
);

Then('the finding fingerprint follows the canonical rule-and-artifact inputs', function () {
  for (const finding of findings(this)) {
    assert.match(finding.finding_id, FINDING_ID);
    assert.equal(
      finding.finding_id,
      fingerprint(finding.rule_id, finding.finding_type, finding.artifact_ids),
      `fingerprint of ${finding.finding_id} does not match its canonical inputs`,
    );
  }
});

When('assurance is asked for baseline {string}', function (baseline) {
  this.results.lastApi = this.call('api', {
    method: 'POST',
    path: '/api/assurance/evaluate',
    json: { baseline },
  });
});

Then('the response is {int} {string}', function (status, code) {
  assert.equal(this.results.lastApi.status, status);
  assert.equal(this.results.lastApi.body.code, code);
});

When('assurance is asked for an unknown policy', function () {
  this.results.lastApi = this.call('api', {
    method: 'POST',
    path: '/api/assurance/evaluate',
    json: { baseline: 'baseline-a', policy: 'does-not-exist' },
  });
});
