import assert from 'node:assert/strict';
import { Given, Then, When } from '@cucumber/cucumber';

import { getUI, startReviewUI } from '../support/ui.js';

function review(world, action, args = {}) {
  return world.call('review', { action, ...args });
}

function capture(world, args = {}) {
  const result = review(world, 'capture', args);
  world.results.capture = result;
  return result;
}

function decide(world, args = {}) {
  let result;
  if (world.results.failingJournal) {
    result = review(world, 'failing_decide', {
      mode: world.results.failingJournal,
      ...args,
    });
  } else {
    result = review(world, 'decide', args);
  }
  world.results.decision = result;
  return result;
}

function proposals(world, baseline = 'baseline-a') {
  return review(world, 'workspace', { kind: 'proposals', baseline }).body;
}

function history(world, baseline = 'baseline-a') {
  return review(world, 'workspace', { kind: 'history', baseline }).body;
}

function thread(world, root = 'REQ-002', baseline = 'baseline-a') {
  return review(world, 'workspace', { kind: 'thread', artifact_id: root, baseline }).body;
}

function journal(world) {
  return review(world, 'journal');
}

function assertLastProblem(world, status, code) {
  const result = world.results.problem ?? world.results.decision ?? world.results.capture;
  assert.ok(result, 'no review response was recorded');
  assert.equal(result.status, status, JSON.stringify(result.body));
  if (code !== undefined) {
    assert.equal(result.body.code, code, JSON.stringify(result.body));
  }
}

function captureLinkId(world) {
  const body =
    world.results.originalCapture?.body ??
    world.results.capture?.body ??
    {};
  const linkId = body.link?.link_id;
  assert.ok(linkId, 'no captured link id');
  return linkId;
}

function capturedProposals(world) {
  return world.results.captured ?? [];
}

Given('banking-demo baseline-a is loaded', async function () {
  if (this.page) {
    await startReviewUI();
    return;
  }
  this.results.review = review(this, 'init', { operator: 'rv-ana' });
});

Given('the review journal is empty and outside the fixture repository', async function () {
  if (this.page) {
    const history = await getUI().api('/api/workspace/history?baseline=baseline-a');
    assert.deepEqual(history.events, []);
    return;
  }
  this.results.review = review(this, 'init', { operator: 'rv-ana' });
  assert.equal(this.results.review.outside_fixture, true);
  assert.deepEqual(this.results.review.events, []);
});

Given('trusted-local-operator mode identifies the operator as {string}', async function (operator) {
  if (this.page) {
    const config = await getUI().api('/api/review/config');
    assert.equal(config.enabled, true);
    assert.equal(config.operator, operator);
    return;
  }
  this.results.review = review(this, 'init', { operator });
  assert.equal(this.results.review.config.operator, operator);
});

Given('the review journal is empty', async function () {
  if (this.page) {
    const history = await getUI().api('/api/workspace/history?baseline=baseline-a');
    assert.deepEqual(history.events, []);
    return;
  }
  this.results.review = review(this, 'init', { operator: 'rv-ana' });
  assert.deepEqual(this.results.review.events, []);
});

Given('the application has no configured operator identity', function () {
  this.results.review = review(this, 'init', { operator: null });
  assert.equal(this.results.review.config.enabled, false);
});

// ------------------------------------------------------------------ capture

Given('fake discovery returned SCN-002 implemented_by CODE-001', function () {
  this.results.candidate = true;
});

When(
  'the operator submits that candidate and its baseline-a endpoint hashes to POST {string}',
  function (_path) {
    capture(this, { candidate: true });
  },
);

Then('a new link is returned with review_state {string}', function (state) {
  assert.equal(this.results.capture.body.link.review_state, state);
});

Then(
  'its snapshot retains the submitted provider, model version, and index revision',
  function () {
    const snapshot = this.results.capture.body.snapshot;
    assert.equal(snapshot.provider, 'fake');
    assert.equal(snapshot.model_version, 'fake-fixture-v1');
    assert.match(snapshot.index_revision, /^sha256:/);
  },
);

Then('its snapshot identifies baseline-a and both endpoint content hashes', function () {
  const snapshot = this.results.capture.body.snapshot;
  assert.equal(snapshot.baseline, 'baseline-a');
  assert.match(snapshot.source_content_hash, /^sha256:/);
  assert.match(snapshot.target_content_hash, /^sha256:/);
});

Then('its snapshot digest is the canonical hash of the snapshot identity fields', function () {
  assert.equal(this.results.capture.digest_valid, true);
});

Then(
  'no accepted link, verification evidence, or assurance finding is created',
  function () {
    const compared = review(this, 'compare_baseline', { baseline: 'baseline-a' });
    assert.equal(compared.findings_equal, true);
    assert.equal(compared.evidence_equal, true);
    const linkId = captureLinkId(this);
    assert.deepEqual(
      thread(this).accepted_links.filter((link) => link.link_id === linkId),
      [],
    );
  },
);

Then('every file in the fixture repository retains its original content hash', function () {
  assert.equal(this.results.capture.fixture_unchanged, true);
});

When('the operator submits a capture with {string}', function (defect) {
  this.results.problem = capture(this, { defect });
});

Then('the response is a {int} problem with code {string}', function (status, code) {
  assertLastProblem(this, status, code);
});

Then('no proposal or decision is appended', function () {
  assert.deepEqual(journal(this).events, []);
});

Given('a captured proposal for SCN-002 implemented_by CODE-001 at baseline-a', function () {
  const result = capture(this, { candidate: true });
  this.results.captured = [result.body.link.link_id];
});

Given('a captured proposal for SCN-002 exercised_by TEST-002 at baseline-a', function () {
  const first = this.results.captured?.[0];
  const result = capture(this, {
    source_id: 'SCN-002',
    target_id: 'TEST-002',
    relation_type: 'exercised_by',
  });
  this.results.captured = [first, result.body.link.link_id];
});

Given('a captured proposal connects SCN-002 to CODE-001 at baseline-a', function () {
  const result = capture(this, { candidate: true });
  this.results.captured = [result.body.link.link_id];
});

Given('a valid capture for SCN-002 implemented_by CODE-001 at baseline-a', function () {
  capture(this, { candidate: true, dry_run: true });
});

When('the operator submits the identical snapshot again', function () {
  this.results.originalCapture = this.results.capture;
  this.results.problem = capture(this, { stored: true });
});

Then('the response is 200 with the existing link and snapshot', function () {
  assert.equal(this.results.problem.status, 200);
  assert.equal(this.results.problem.body.created, false);
  assert.equal(
    this.results.problem.body.link.link_id,
    this.results.capture.body.link.link_id,
  );
});

When('the operator submits {string}', function (submission) {
  this.results.originalCapture = this.results.capture;
  this.results.problem = capture(this, { submission });
});

Then('the journal still contains exactly one capture event for that proposal', function () {
  const linkId = captureLinkId(this);
  const captures = journal(this).events.filter(
    (event) => event.event === 'proposal_captured' && event.link.link_id === linkId,
  );
  assert.equal(captures.length, 1);
});

Given(
  'an evidence-only revision exists whose endpoint content hashes equal baseline-a',
  function () {
    this.results.evidenceOnly = review(this, 'evidence_only');
  },
);

When('the operator accepts that proposal against that evidence-only revision', function () {
  decide(this, {
    link_id: captureLinkId(this),
    baseline: this.results.evidenceOnly.commit,
  });
});

Then('the response contains the proposal with review_state {string}', function (state) {
  assert.equal(this.results.decision.body.review_state, state);
});

Then('the decision identifies the selected commit and the unchanged endpoint hashes', function () {
  const decision = this.results.decision;
  assert.equal(decision.body.provenance.baseline_commit, this.results.evidenceOnly.commit);
  const event = decision.journal_events.find(
    (item) => item.event === 'decision_recorded' && item.link.link_id === decision.link_id,
  );
  assert.ok(event);
  assert.equal(event.snapshot.source_content_hash, this.results.capture.body.snapshot.source_content_hash);
  assert.equal(event.snapshot.target_content_hash, this.results.capture.body.snapshot.target_content_hash);
});

Then('no source change or verification failure is inferred from the different commit', function () {
  const findings = review(this, 'findings', {
    baseline: this.results.evidenceOnly.commit,
  }).body.findings;
  const relevant = findings.filter(
    (finding) =>
      finding.finding_type === 'verification_failed' &&
      (finding.artifact_ids.includes('SCN-002') || finding.artifact_ids.includes('CODE-001')),
  );
  assert.deepEqual(relevant, []);
});

// ---------------------------------------------------------------- decisions

Given('LNK-007 is proposed at baseline-a', function () {
  const pending = proposals(this).proposals.map((record) => record.link.link_id);
  assert.ok(pending.includes('LNK-007'), `pending proposals: ${pending}`);
});

Given('baseline findings and evidence have been recorded for comparison', function () {
  this.results.baselineComparison = review(this, 'baseline', { baseline: 'baseline-a' });
});

When('{string} posts decision {string} for LNK-007 at baseline-a', function (reviewer, decision) {
  decide(this, {
    link_id: 'LNK-007',
    reviewer,
    decision,
    baseline: 'baseline-a',
  });
});

When(
  '{string} posts decision {string} for LNK-007 at baseline-a without an Origin header',
  function (reviewer, decision) {
    decide(this, {
      link_id: 'LNK-007',
      reviewer,
      decision,
      baseline: 'baseline-a',
    });
  },
);

Then('the response contains LNK-007 with review_state {string}', function (state) {
  assert.equal(this.results.decision.body.review_state, state);
});

Then(
  'the journal contains one decision identifying {string} and a server UTC timestamp',
  function (operator) {
    const decisions = journal(this).events.filter((event) => event.event === 'decision_recorded');
    assert.equal(decisions.length, 1);
    assert.equal(decisions[0].operator, operator);
    assert.match(decisions[0].recorded_at, /Z|[+]00:00$/);
  },
);

Then('that decision identifies the proposal snapshot and baseline-a endpoint hashes', function () {
  const event = journal(this).events.find((item) => item.event === 'decision_recorded');
  assert.ok(event);
  assert.equal(event.snapshot.baseline, 'baseline-a');
  assert.match(event.snapshot.source_content_hash, /^sha256:/);
  assert.match(event.snapshot.target_content_hash, /^sha256:/);
});

Then('the workspace thread contains LNK-007 only in accepted_links', function () {
  const body = thread(this);
  assert.deepEqual(
    body.accepted_links.filter((link) => link.link_id === 'LNK-007').map((link) => link.review_state),
    ['accepted'],
  );
  assert.deepEqual(body.proposed_links.filter((link) => link.link_id === 'LNK-007'), []);
});

Then('the workspace pending queue excludes LNK-007', function () {
  assert.deepEqual(
    proposals(this).proposals.filter((record) => record.link.link_id === 'LNK-007'),
    [],
  );
});

Then('workspace history returns that acceptance', function () {
  const decisions = history(this).events.filter((event) => event.event === 'decision_recorded');
  assert.equal(decisions.length, 1);
  assert.equal(decisions[0].decision, 'accept');
});

Then('baseline findings and evidence equal the recorded values', function () {
  const compared = review(this, 'compare_baseline', { baseline: 'baseline-a' });
  assert.equal(compared.findings_equal, true);
  assert.equal(compared.evidence_equal, true);
});

Then('default baseline thread reads equal their values before the decision', function () {
  const compared = review(this, 'compare_baseline', { baseline: 'baseline-a' });
  assert.equal(compared.thread_equal, true);
});

When('{string} rejects LNK-007 at baseline-a with reason {string}', function (reviewer, reason) {
  decide(this, {
    link_id: 'LNK-007',
    reviewer,
    decision: 'reject',
    baseline: 'baseline-a',
    reason,
  });
});

Then('the journal contains one rejection with that reason', function () {
  const decisions = journal(this).events.filter((event) => event.event === 'decision_recorded');
  assert.equal(decisions.length, 1);
  assert.equal(decisions[0].decision, 'reject');
  assert.ok(decisions[0].reason);
});

Then('the workspace history returns that rejection', function () {
  const decisions = history(this).events.filter((event) => event.event === 'decision_recorded');
  assert.equal(decisions[0].decision, 'reject');
  assert.ok(decisions[0].reason);
});

Then('LNK-007 is absent from the workspace accepted links and pending queue', function () {
  assert.deepEqual(
    thread(this).accepted_links.filter((link) => link.link_id === 'LNK-007'),
    [],
  );
  assert.deepEqual(
    proposals(this).proposals.filter((record) => record.link.link_id === 'LNK-007'),
    [],
  );
});

Then('LNK-007 is labelled as rejected for that baseline', function () {
  const decision = history(this).events.find((event) => event.event === 'decision_recorded');
  assert.ok(decision);
  assert.equal(decision.decision, 'reject');
});

Then('baseline findings, evidence, and fixture file hashes are unchanged', function () {
  const compared = review(this, 'compare_baseline', { baseline: 'baseline-a' });
  assert.equal(compared.findings_equal, true);
  assert.equal(compared.evidence_equal, true);
  assert.equal(compared.fixture_equal, true);
});

Then('no decision is appended', function () {
  assert.deepEqual(
    journal(this).events.filter((event) => event.event === 'decision_recorded'),
    [],
  );
});

Then('the workspace still shows LNK-007 as proposed', function () {
  const record = proposals(this).proposals.find((item) => item.link.link_id === 'LNK-007');
  assert.ok(record);
  assert.equal(record.link.review_state, 'proposed');
});

When(/^"([^"]+)" rejects LNK-007 at baseline-a with (?!reason ")(.+)$/, function (reviewer, input) {
  decide(this, {
    link_id: 'LNK-007',
    reviewer,
    decision: 'reject',
    baseline: 'baseline-a',
    reason: input,
  });
});

Given('a durable acceptance decision already exists for LNK-007 at baseline-a', function () {
  decide(this, { link_id: 'LNK-007', decision: 'accept', baseline: 'baseline-a' });
  assert.equal(this.results.decision.status, 200);
  this.results.firstDecision = journal(this);
});

When(
  '{string} posts decision {string} for LNK-007 at baseline-a with reason {string}',
  function (reviewer, decision, reason) {
    decide(this, {
      link_id: 'LNK-007',
      reviewer,
      decision,
      baseline: 'baseline-a',
      reason,
    });
  },
);

Then('the original decision bytes are unchanged', function () {
  assert.equal(
    this.results.decision.journal_hashes.bytes_sha256,
    this.results.decision.journal_hashes_before.bytes_sha256,
  );
});

Then('no second decision is appended', function () {
  assert.equal(
    journal(this).events.filter((event) => event.event === 'decision_recorded').length,
    1,
  );
});

Then('CODE-001 has different content at baseline-b', function () {
  const atA = this.call('artifact', { id: 'CODE-001', baseline: 'baseline-a' }).artifact;
  const atB = this.call('artifact', { id: 'CODE-001', baseline: 'baseline-b' }).artifact;
  assert.notEqual(atA.content_hash, atB.content_hash);
});

When('the operator accepts that proposal against baseline-b', function () {
  decide(this, { link_id: captureLinkId(this), baseline: 'baseline-b' });
});

Then('no verification failure is recorded', function () {
  const compared = review(this, 'compare_baseline', { baseline: 'baseline-a' });
  assert.equal(compared.findings_equal, true);
});

Given(
  'the journal cannot durably append a record and can roll back to its prior committed length',
  function () {
    this.results.failingJournal = 'rollback';
  },
);

Given(
  'the journal fails and rolls back to its prior committed length',
  function () {
    this.results.failingJournal = 'rollback';
  },
);

Given(
  'the journal writes a complete commit pair but cannot confirm its durability or roll it back',
  function () {
    this.results.failingJournal = 'indeterminate';
  },
);

Given(
  'the journal writes a complete pair but cannot confirm durability or roll it back',
  function () {
    this.results.failingJournal = 'indeterminate';
  },
);

Then('its durability is {string}', function (expected) {
  assertLastProblem(this, 503, 'review-storage-unavailable');
  assert.equal(this.results.decision.body.durability, expected);
});

Then('the application does not report the decision as successful', function () {
  assert.equal(this.results.decision.status, 503);
});

Then('further journal mutations are refused with {string}', function (code) {
  const result = review(this, 'decide', {
    link_id: 'LNK-007',
    decision: 'reject',
    baseline: 'baseline-a',
    reason: 'after the indeterminate write',
  });
  assert.equal(result.status, 503);
  assert.equal(result.body.code, code);
});

Then('no partial or malformed record is replayed', function () {
  const restarted = review(this, 'restart', { baseline: 'baseline-a' });
  assert.ok(restarted.history.events.every((event) => event.event && event.link));
});

Then('restarting with the same journal does not expose an accepted decision', function () {
  const restarted = review(this, 'restart', { baseline: 'baseline-a' });
  assert.deepEqual(
    restarted.history.events.filter((event) => event.event === 'decision_recorded'),
    [],
  );
});

When('{string} posts decision {string} for LNK-999 at baseline-a', function (reviewer, decision) {
  decide(this, { link_id: 'LNK-999', reviewer, decision, baseline: 'baseline-a' });
});

// ------------------------------------------------------------------ restart

Given('the proposal is accepted at baseline-a', function () {
  decide(this, { link_id: captureLinkId(this), decision: 'accept', baseline: 'baseline-a' });
  assert.equal(this.results.decision.status, 200);
});

When('{string} accepts that proposal at baseline-a', function (_reviewer) {
  decide(this, { link_id: captureLinkId(this), decision: 'accept', baseline: 'baseline-a' });
});

When('the application restarts with the same journal', function () {
  this.results.restart = review(this, 'restart', { baseline: 'baseline-a' });
});

Then('the workspace thread contains that proposal only in accepted_links', function () {
  const linkId = captureLinkId(this);
  const body = thread(this);
  assert.deepEqual(
    body.accepted_links.filter((link) => link.link_id === linkId).map((link) => link.review_state),
    ['accepted'],
  );
  assert.deepEqual(body.proposed_links.filter((link) => link.link_id === linkId), []);
});

Then('the workspace pending queue excludes that proposal', function () {
  const linkId = captureLinkId(this);
  assert.deepEqual(
    proposals(this).proposals.filter((record) => record.link.link_id === linkId),
    [],
  );
});

Then('the workspace pending queue still lists the unrelated pending proposal LNK-007', function () {
  const pending = proposals(this).proposals.map((record) => record.link.link_id);
  assert.ok(pending.includes('LNK-007'));
});

Then('the workspace history returns the capture and the acceptance', function () {
  const kinds = history(this).events.map((event) => event.event);
  assert.deepEqual(kinds.sort(), ['decision_recorded', 'proposal_captured']);
});

Then('the decision identifies the same snapshot and operator', function () {
  const decision = history(this).events.find((event) => event.event === 'decision_recorded');
  assert.ok(decision);
  assert.equal(decision.operator, 'rv-ana');
  assert.ok(decision.snapshot.snapshot_digest.startsWith('sha256:'));
});

Then('the journal bytes are identical to their bytes before restart', function () {
  assert.equal(
    this.results.restart.journal_hashes_before.bytes_sha256,
    this.results.restart.journal_hashes_after.bytes_sha256,
  );
});

Then('the workspace pending queue lists that proposal with its snapshot and provenance', function () {
  const linkId = captureLinkId(this);
  const record = proposals(this).proposals.find((item) => item.link.link_id === linkId);
  assert.ok(record);
  assert.equal(record.binding, 'captured');
  assert.equal(record.snapshot.provider, 'fake');
});

Then('the workspace history returns its capture event', function () {
  assert.deepEqual(
    history(this).events.map((event) => event.event),
    ['proposal_captured'],
  );
});

Then('no accepted link or decision exists for it', function () {
  const linkId = captureLinkId(this);
  assert.deepEqual(
    thread(this).accepted_links.filter((link) => link.link_id === linkId),
    [],
  );
  assert.deepEqual(
    journal(this).events.filter((event) => event.event === 'decision_recorded'),
    [],
  );
});

Given(
  '{string} rejects that proposal at baseline-a with reason {string}',
  function (reviewer, reason) {
    decide(this, {
      link_id: captureLinkId(this),
      reviewer,
      decision: 'reject',
      baseline: 'baseline-a',
      reason,
    });
  },
);

Then('the workspace history returns the rejection with its reason and operator', function () {
  const decision = history(this).events.find((event) => event.event === 'decision_recorded');
  assert.ok(decision);
  assert.equal(decision.decision, 'reject');
  assert.ok(decision.reason);
  assert.equal(decision.operator, 'rv-ana');
});

Then('the proposal is absent from accepted links and the pending queue', function () {
  const linkId = captureLinkId(this);
  assert.deepEqual(
    thread(this).accepted_links.filter((link) => link.link_id === linkId),
    [],
  );
  assert.deepEqual(
    proposals(this).proposals.filter((record) => record.link.link_id === linkId),
    [],
  );
});

Given('the first proposal is rejected with reason {string}', function (reason) {
  decide(this, {
    link_id: capturedProposals(this)[0],
    decision: 'reject',
    baseline: 'baseline-a',
    reason,
  });
  this.results.firstDecision = journal(this);
});

When('{string} accepts the second proposal at baseline-a', function (reviewer) {
  decide(this, {
    link_id: capturedProposals(this)[1],
    reviewer,
    decision: 'accept',
    baseline: 'baseline-a',
  });
});

Then("the first decision's journal bytes are unchanged", function () {
  const after = review(this, 'journal', {
    prefix_bytes: this.results.firstDecision.bytes,
  });
  assert.equal(after.prefix_sha256, this.results.firstDecision.bytes_sha256);
});

Then('the workspace history returns both decisions', function () {
  assert.equal(
    history(this).events.filter((event) => event.event === 'decision_recorded').length,
    2,
  );
});

Then('the first proposal remains absent from accepted links and pending', function () {
  const linkId = capturedProposals(this)[0];
  assert.deepEqual(
    thread(this).accepted_links.filter((link) => link.link_id === linkId),
    [],
  );
  assert.deepEqual(
    proposals(this).proposals.filter((record) => record.link.link_id === linkId),
    [],
  );
});

When(
  '{string} submits an acceptance and a rejection for LNK-007 at baseline-a concurrently',
  function (_reviewer) {
    this.results.concurrent = review(this, 'concurrent', { link_id: 'LNK-007' });
  },
);

Then('exactly one request returns a successful decision', function () {
  assert.equal(
    this.results.concurrent.outcomes.filter((outcome) => outcome.status === 200).length,
    1,
  );
});

Then('the other request returns a 409 problem with code {string}', function (code) {
  const conflict = this.results.concurrent.outcomes.find((outcome) => outcome.status === 409);
  assert.ok(conflict);
  assert.equal(conflict.body.code, code);
});

Then('exactly one terminal decision event is appended', function () {
  assert.equal(
    this.results.concurrent.events.filter((event) => event.event === 'decision_recorded').length,
    1,
  );
});

Then('the workspace thread and pending queue agree with that decision', function () {
  const decision = history(this).events.find((event) => event.event === 'decision_recorded');
  assert.ok(decision);
  const accepted = thread(this).accepted_links.some((link) => link.link_id === 'LNK-007');
  const pending = proposals(this).proposals.some((record) => record.link.link_id === 'LNK-007');
  if (decision.decision === 'accept') {
    assert.equal(accepted, true);
    assert.equal(pending, false);
  } else {
    assert.equal(accepted, false);
    assert.equal(pending, false);
  }
});

// ------------------------------------------------------------------ boundary

When(/^a decision request arrives with (.+)$/, function (condition) {
  if (condition === 'a non-loopback client address') {
    decide(this, {
      link_id: 'LNK-007',
      decision: 'accept',
      baseline: 'baseline-a',
      client_host: '192.0.2.10',
    });
  } else if (condition === 'a browser Origin of https://example.invalid') {
    decide(this, {
      link_id: 'LNK-007',
      decision: 'accept',
      baseline: 'baseline-a',
      origin: 'https://example.invalid',
    });
  } else {
    throw new Error(`unknown boundary condition ${condition}`);
  }
});

Then('the response is 200 with LNK-007 accepted', function () {
  assert.equal(this.results.decision.status, 200);
  assert.equal(this.results.decision.body.review_state, 'accepted');
});

Then('the journal contains one decision', function () {
  assert.equal(
    journal(this).events.filter((event) => event.event === 'decision_recorded').length,
    1,
  );
});

When('the workspace is read at baseline-a and at baseline-b', function () {
  this.results.workspaceA = thread(this, 'REQ-002', 'baseline-a');
  this.results.workspaceB = thread(this, 'REQ-002', 'baseline-b');
});

Then('baseline-a shows the proposal as accepted', function () {
  const linkId = captureLinkId(this);
  assert.ok(this.results.workspaceA.accepted_links.some((link) => link.link_id === linkId));
});

Then('baseline-b shows the same acceptance only if both endpoint hashes are unchanged', function () {
  const linkId = captureLinkId(this);
  const snapshot = this.results.capture.body.snapshot;
  const atB = this.call('artifacts', { baseline: 'baseline-b' }).artifacts;
  const byId = Object.fromEntries(atB.map((artifact) => [artifact.artifact_id, artifact]));
  const unchanged =
    byId[snapshot.source_id].content_hash === snapshot.source_content_hash &&
    byId[snapshot.target_id].content_hash === snapshot.target_content_hash;
  const shown = this.results.workspaceB.accepted_links.some((link) => link.link_id === linkId);
  assert.equal(shown, unchanged);
});

Then('neither workspace shows an acceptance whose endpoint content differs from the snapshot', function () {
  const linkId = captureLinkId(this);
  const snapshot = this.results.capture.body.snapshot;
  for (const workspace of [this.results.workspaceA, this.results.workspaceB]) {
    for (const link of workspace.accepted_links.filter((item) => item.link_id === linkId)) {
      assert.equal(link.provenance.snapshot_digest, snapshot.snapshot_digest);
    }
  }
});

Then('default baseline reads remain unchanged', function () {
  const compared = review(this, 'compare_baseline', { baseline: 'baseline-a' });
  assert.equal(compared.thread_equal, true);
  const baselineThread = this.call('thread', { id: 'REQ-002', baseline: 'baseline-a' }).thread;
  const linkId = captureLinkId(this);
  assert.deepEqual(
    baselineThread.accepted_links.filter((link) => link.link_id === linkId),
    [],
  );
});

// ------------------------------------------------------------ journal tails

Given('the journal ends with a complete payload record lacking a commit marker', function () {
  review(this, 'tail');
});

Then('the uncommitted record is not replayed', function () {
  const restarted = review(this, 'restart', { baseline: 'baseline-a' });
  assert.deepEqual(
    restarted.history.events.filter((event) => event.event === 'decision_recorded'),
    [],
  );
});

Then(
  'a new review mutation is refused with a 503 problem and code {string}',
  function (code) {
    const result = review(this, 'decide', {
      link_id: 'LNK-007',
      decision: 'accept',
      baseline: 'baseline-a',
    });
    assert.equal(result.status, 503);
    assert.equal(result.body.code, code);
    this.results.problem = result;
  },
);

Then('no new journal record is appended', function () {
  const before = journal(this).line_count;
  const result = review(this, 'decide', {
    link_id: 'LNK-007',
    decision: 'accept',
    baseline: 'baseline-a',
  });
  assert.equal(result.status, 503);
  assert.equal(journal(this).line_count, before);
});

// ------------------------------------------------ capture persistence failure

When('the operator submits that capture', function () {
  if (this.results.failingJournal) {
    this.results.decision = review(this, 'failing_capture', {
      mode: this.results.failingJournal,
    });
  } else {
    this.results.decision = capture(this, { stored: true });
  }
});

Then(/^the live workspace (.+)$/, function (condition) {
  const payload = this.results.capture.payload;
  const live = this.results.decision.live_pending ?? proposals(this);
  const pending = live.proposals.filter(
    (record) =>
      record.link.source_id === payload.source_id &&
      record.link.target_id === payload.target_id &&
      record.link.relation_type === payload.relation_type,
  );
  const accepted = thread(this).accepted_links.filter(
    (link) =>
      link.source_id === payload.source_id &&
      link.target_id === payload.target_id &&
      link.relation_type === payload.relation_type,
  );
  if (condition === 'does not list the proposal or an accepted link') {
    assert.deepEqual(pending, []);
    assert.deepEqual(accepted, []);
  } else if (condition === 'does not list the proposal optimistically') {
    assert.deepEqual(pending, []);
  } else {
    throw new Error(`unknown workspace condition ${condition}`);
  }
});

Then(/^restarting (?!with the same journal)(.+)$/, function (condition) {
  const restarted = review(this, 'restart', { baseline: 'baseline-a' });
  const captures = restarted.history.events.filter(
    (event) => event.event === 'proposal_captured',
  );
  if (condition === 'exposes no captured proposal') {
    assert.deepEqual(captures, []);
  } else if (
    condition ===
    'exposes either no proposal or one complete pending captured proposal, never an accepted link'
  ) {
    assert.ok(captures.length <= 1);
    for (const event of captures) {
      assert.equal(event.link.review_state, 'proposed');
    }
  } else if (condition === 'exposes either no decision or exactly one complete committed decision') {
    const decisions = restarted.history.events.filter(
      (event) => event.event === 'decision_recorded',
    );
    assert.ok(decisions.length <= 1);
    for (const event of decisions) {
      assert.ok(event.snapshot.snapshot_digest.startsWith('sha256:'));
    }
  } else {
    throw new Error(`unknown restart condition ${condition}`);
  }
});

// ------------------------------------------------------------------- browser

function browserProposal(world) {
  const linkId = world.results.browserCapture.body.link.link_id;
  return world.page.locator(`article.proposal[data-link-id="${linkId}"]`);
}

async function openReviewWorkspace(world, artifactId = 'REQ-002') {
  const ui = getUI();
  await world.page.goto(ui.baseUrl);
  await world.page.locator('#baseline').selectOption('baseline-a');
  await world.page.getByRole('button', { name: artifactId, exact: true }).click();
  await world.page.getByRole('region', { name: 'Review proposals' }).waitFor();
}

When(
  'the reviewer captures the fake candidate for SCN-002 implemented_by CODE-001 at baseline-a',
  async function () {
    const ui = getUI();
    const artifacts = await ui.api('/api/artifacts?baseline=baseline-a');
    const byId = Object.fromEntries(
      artifacts.artifacts.map((artifact) => [artifact.artifact_id, artifact]),
    );
    const discovered = await ui.request('/api/discovery', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        artifact_id: 'SCN-002',
        provider: 'fake',
        relation_types: ['implemented_by'],
      }),
    });
    const candidate = discovered.body.candidates.find(
      (item) => item.source_id === 'SCN-002' && item.target_id === 'CODE-001',
    );
    assert.ok(candidate, 'fake discovery returned no SCN-002 implemented_by CODE-001 candidate');
    const captured = await ui.request('/api/link-proposals', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        source_id: 'SCN-002',
        target_id: 'CODE-001',
        relation_type: 'implemented_by',
        baseline: 'baseline-a',
        source_content_hash: byId['SCN-002'].content_hash,
        target_content_hash: byId['CODE-001'].content_hash,
        provider: candidate.discovery_provider,
        model_version: candidate.model_version,
        index_revision: candidate.index_revision,
        score: candidate.score,
        rationale: candidate.rationale,
      }),
    });
    assert.equal(captured.status, 201, JSON.stringify(captured.body));
    this.results.browserCapture = captured;
  },
);

When('the reviewer opens the review workspace for REQ-002', async function () {
  await openReviewWorkspace(this, 'REQ-002');
});

Then(
  'the proposal shows provider {string}, model version {string}, and its index revision',
  async function (provider, model) {
    const article = browserProposal(this);
    await article.waitFor();
    const text = await article.innerText();
    assert.ok(text.includes(provider), `missing provider ${provider}: ${text}`);
    assert.ok(text.includes(model), `missing model ${model}: ${text}`);
    assert.ok(
      text.includes(this.results.browserCapture.body.snapshot.index_revision),
      `missing index revision: ${text}`,
    );
  },
);

Then('the proposal is labelled as fixture-generated', async function () {
  assert.ok((await browserProposal(this).innerText()).includes('fixture-generated'));
});

Then('the review controls require a reason for rejection', async function () {
  const article = browserProposal(this);
  const reject = article.getByRole('button', {
    name: `Reject ${this.results.browserCapture.body.link.link_id}`,
  });
  assert.equal(await reject.isDisabled(), true);
  await article.getByLabel(`Reason for rejecting ${this.results.browserCapture.body.link.link_id}`).fill('a reason');
  assert.equal(await reject.isDisabled(), false);
  await article.getByLabel(`Reason for rejecting ${this.results.browserCapture.body.link.link_id}`).fill('');
});

When('the reviewer accepts the proposal', async function () {
  const linkId = this.results.browserCapture.body.link.link_id;
  await this.page.getByRole('button', { name: `Accept ${linkId}` }).click();
  await this.page.getByRole('list', { name: 'Review history' }).getByText('accept').waitFor();
});

Then(
  'the workspace shows the proposal as accepted and excludes it from the pending queue',
  async function () {
    const linkId = this.results.browserCapture.body.link.link_id;
    assert.equal(await this.page.locator(`article.proposal[data-link-id="${linkId}"]`).count(), 0);
    const historyText = await this.page.getByRole('list', { name: 'Review history' }).innerText();
    assert.ok(historyText.includes(linkId));
    assert.ok(historyText.includes('accept'));
  },
);

Then('the history shows one acceptance by {string} with a server timestamp', async function (operator) {
  const historyText = await this.page.getByRole('list', { name: 'Review history' }).innerText();
  assert.ok(historyText.includes(operator));
  assert.match(historyText, /\d{4}-\d{2}-\d{2}T/);
});

When('the reviewer rejects the proposal with reason {string}', async function (reason) {
  const linkId = this.results.browserCapture.body.link.link_id;
  await this.page
    .getByLabel(`Reason for rejecting ${linkId}`)
    .fill(reason);
  await this.page.getByRole('button', { name: `Reject ${linkId}` }).click();
  await this.page.getByRole('list', { name: 'Review history' }).getByText('reject').waitFor();
});

Then(
  'the workspace excludes the proposal from accepted links and the pending queue',
  async function () {
    const linkId = this.results.browserCapture.body.link.link_id;
    assert.equal(await this.page.locator(`article.proposal[data-link-id="${linkId}"]`).count(), 0);
    const thread = await getUI().api('/api/workspace/threads/REQ-002?baseline=baseline-a');
    assert.deepEqual(thread.accepted_links.filter((link) => link.link_id === linkId), []);
  },
);

Then(
  'the history shows one rejection by {string} with that reason and a server timestamp',
  async function (operator) {
    const historyText = await this.page.getByRole('list', { name: 'Review history' }).innerText();
    assert.ok(historyText.includes(operator));
    assert.ok(historyText.includes('Not the right implementation'));
    assert.match(historyText, /\d{4}-\d{2}-\d{2}T/);
  },
);

Then('the proposal remains absent from default baseline accepted links', async function () {
  const linkId = this.results.browserCapture.body.link.link_id;
  const thread = await getUI().api('/api/threads/REQ-002?baseline=baseline-a');
  assert.deepEqual(thread.accepted_links.filter((link) => link.link_id === linkId), []);
});

When(
  'the reviewer opens the review workspace for REQ-002 and displays the pending acceptance control',
  async function () {
    await openReviewWorkspace(this, 'REQ-002');
    const linkId = this.results.browserCapture.body.link.link_id;
    await this.page.getByRole('button', { name: `Accept ${linkId}` }).waitFor();
  },
);

When('the proposal is accepted through the API in another local request', async function () {
  const linkId = this.results.browserCapture.body.link.link_id;
  const response = await getUI().request(`/api/links/${linkId}/review`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      decision: 'accept',
      reviewer_id: 'rv-ana',
      baseline: 'baseline-a',
    }),
  });
  assert.equal(response.status, 200, JSON.stringify(response.body));
});

When(
  'the reviewer submits the already displayed acceptance control without refreshing',
  async function () {
    const linkId = this.results.browserCapture.body.link.link_id;
    await this.page.getByRole('button', { name: `Accept ${linkId}` }).click();
  },
);

Then('the dashboard displays the typed review conflict', async function () {
  const alert = this.page.getByRole('alert');
  await alert.waitFor();
  assert.match(await alert.innerText(), /review-conflict/);
});

Then('it does not display the proposal as newly accepted', async function () {
  const linkId = this.results.browserCapture.body.link.link_id;
  const article = this.page.locator(`article.proposal[data-link-id="${linkId}"]`);
  assert.equal(await article.count(), 1);
  assert.equal(await article.getAttribute('data-state'), 'proposed');
  const historyText = await this.page.getByRole('list', { name: 'Review history' }).innerText();
  assert.ok(!/\baccept\b/.test(historyText), historyText);
});

Then(
  'refreshing the workspace shows the proposal as accepted by the earlier decision',
  async function () {
    await openReviewWorkspace(this, 'REQ-002');
    const linkId = this.results.browserCapture.body.link.link_id;
    assert.equal(await this.page.locator(`article.proposal[data-link-id="${linkId}"]`).count(), 0);
    const historyText = await this.page.getByRole('list', { name: 'Review history' }).innerText();
    assert.ok(historyText.includes('accept'));
  },
);

Then('the journal contains exactly one terminal decision', async function () {
  const history = await getUI().api('/api/workspace/history?baseline=baseline-a');
  assert.equal(
    history.events.filter((event) => event.event === 'decision_recorded').length,
    1,
  );
});
