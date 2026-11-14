import assert from 'node:assert/strict';
import { Given, Then, When } from '@cucumber/cucumber';

import { getUI } from '../support/ui.js';

async function openDashboard(world, baseline) {
  const ui = getUI();
  await world.page.goto(ui.baseUrl);
  await world.page.locator('#baseline').selectOption(baseline);
  await world.page.getByRole('region', { name: 'Findings summary' }).waitFor();
  await world.page.getByLabel('Finding counts by type').waitFor({ timeout: 20_000 });
}

async function selectBaseline(world, baseline) {
  const response = world.page.waitForResponse(
    (candidate) =>
      candidate.url().includes('/api/findings') && candidate.url().includes(baseline),
    { timeout: 20_000 },
  );
  await world.page.locator('#baseline').selectOption(baseline);
  await response;
  await world.page.getByLabel('Finding counts by type').waitFor({ timeout: 20_000 });
}

function summary(world) {
  return world.page.getByRole('region', { name: 'Findings summary' });
}

function requirementRow(world, artifactId) {
  return summary(world).locator('tr', { hasText: artifactId });
}

function findingDetails(world, type, requirement) {
  return world.page
    .locator('details.finding')
    .filter({ hasText: type })
    .filter({ hasText: requirement });
}

Given('the fixture data at {string}', async function (baseline) {
  this.results.baseline = baseline;
  await openDashboard(this, baseline);
});

When('the dashboard loads the summary', async function () {
  await openDashboard(this, this.results.baseline);
});

Then('it shows the finding counts by type for that baseline', async function () {
  const counts = summary(this).getByLabel('Finding counts by type');
  const findings = await getUI().api(
    `/api/findings?baseline=${encodeURIComponent(this.results.baseline)}`,
  );
  const byType = new Map();
  for (const finding of findings.findings) {
    byType.set(finding.finding_type, (byType.get(finding.finding_type) ?? 0) + 1);
  }
  for (const [type, count] of byType) {
    const item = counts.locator('li', { hasText: type });
    assert.equal(await item.locator('strong').innerText(), String(count));
  }
});

Then('it shows {string} as fully covered', async function (artifactId) {
  assert.match(await requirementRow(this, artifactId).innerText(), /Covered/);
});

Then('it shows {string} as missing a verification scenario', async function (artifactId) {
  assert.match(await requirementRow(this, artifactId).innerText(), /Missing verification/);
});

Given('findings for {string} and {string} differ', async function (first, second) {
  const api = getUI().api;
  const one = await api(`/api/findings?baseline=${encodeURIComponent(first)}`);
  const two = await api(`/api/findings?baseline=${encodeURIComponent(second)}`);
  assert.notDeepEqual(
    one.findings.map((finding) => finding.finding_type).sort(),
    two.findings.map((finding) => finding.finding_type).sort(),
  );
  await openDashboard(this, 'baseline-b');
});

When('the baseline selector changes', async function () {
  const current = await this.page.locator('#baseline').inputValue();
  this.results.targetBaseline = current === 'baseline-a' ? 'baseline-b' : 'baseline-a';
  await selectBaseline(this, this.results.targetBaseline);
});

Then('the summary reloads for the selected baseline', async function () {
  const counts = summary(this).getByLabel('Finding counts by type');
  const expected =
    this.results.targetBaseline === 'baseline-b'
      ? 'reverification_required'
      : 'missing_verification_link';
  assert.ok((await counts.innerText()).includes(expected));
});

Then('the selected baseline is displayed with the numbers', async function () {
  assert.ok((await summary(this).innerText()).includes(this.results.targetBaseline));
  assert.match(await summary(this).getByLabel('Finding counts by type').innerText(), /\d/);
});

Given('a findings response containing a different set of findings', async function () {
  const findings = await getUI().api('/api/findings?baseline=baseline-a');
  const template = findings.findings[0];
  this.results.alteredFindings = {
    ...findings,
    findings: [
      {
        ...template,
        finding_id: 'FND-0000000000000001',
        finding_type: 'lifecycle_review_required',
        rule_id: 'RULE-LIFECYCLE-SUPERSEDED',
        artifact_ids: ['REQ-001'],
      },
      {
        ...template,
        finding_id: 'FND-0000000000000002',
        finding_type: 'lifecycle_review_required',
        rule_id: 'RULE-LIFECYCLE-SUPERSEDED',
        artifact_ids: ['REQ-003'],
      },
    ],
  };
  await this.page.route(/\/api\/findings\?baseline=baseline-a$/, async (route) => {
    await route.fulfill({ json: this.results.alteredFindings });
  });
});

When('the dashboard renders it', async function () {
  await this.page.goto(getUI().baseUrl);
  await selectBaseline(this, 'baseline-a');
});

Then('the displayed counts change accordingly', async function () {
  const counts = summary(this).getByLabel('Finding counts by type');
  const text = await counts.innerText();
  assert.match(text, /lifecycle_review_required/);
  const item = counts.locator('li', { hasText: 'lifecycle_review_required' });
  assert.equal(await item.locator('strong').innerText(), '2');
  assert.ok(!text.includes('missing_verification_link'));
});

Given(
  '{string} has proposed link {string} and no accepted verification link',
  async function (artifactId, linkId) {
    const thread = await getUI().api(
      `/api/threads/${encodeURIComponent(artifactId)}?baseline=baseline-a`,
    );
    assert.deepEqual(thread.accepted_links, []);
    assert.deepEqual(
      thread.proposed_links.map((link) => link.link_id),
      [linkId],
    );
  },
);

When('its thread is displayed', async function () {
  await openDashboard(this, 'baseline-a');
  await summary(this).getByRole('button', { name: 'REQ-002' }).click();
  await this.page.getByRole('region', { name: /Thread for REQ-002/ }).waitFor();
});

Then('{string} is labelled as a proposal', async function (linkId) {
  const region = this.page.getByRole('region', { name: /Thread for REQ-002/ });
  assert.ok((await region.innerText()).includes(linkId));
  assert.ok((await region.innerText()).includes('not accepted'));
});

Then('{string} is not shown as covered', async function (artifactId) {
  assert.ok(!(await requirementRow(this, artifactId).innerText()).includes('Covered'));
});

When('the thread for {string} is displayed', async function (artifactId) {
  await openDashboard(this, 'baseline-b');
  await summary(this).getByRole('button', { name: artifactId }).click();
  await this.page.getByRole('region', { name: new RegExp(`Thread for ${artifactId}`) }).waitFor();
});

Then('the accepted links and their relation types are shown', async function () {
  const region = this.page.getByRole('region', { name: /Thread for REQ-001/ });
  const text = await region.innerText();
  for (const expected of ['LNK-001', 'LNK-002', 'LNK-003', 'verified_by', 'implemented_by', 'exercised_by']) {
    assert.ok(text.includes(expected), `thread is missing ${expected}`);
  }
});

Then('the evidence for {string} is shown', async function (artifactId) {
  const region = this.page.getByRole('region', { name: /Thread for REQ-001/ });
  const text = await region.innerText();
  assert.ok(text.includes('EV-001'));
  assert.ok(text.includes(artifactId));
});

Then('the baseline is shown with the thread', async function () {
  const heading = await this.page
    .getByRole('region', { name: /Thread for REQ-001/ })
    .locator('h2')
    .innerText();
  assert.match(heading, /baseline-b/);
});

// ---------------------------------------------------------------- AS-05

Given(
  'the {string} finding for {string} at {string}',
  async function (findingType, requirement, baseline) {
    await openDashboard(this, baseline);
    const response = await getUI().api(`/api/findings?baseline=${encodeURIComponent(baseline)}`);
    const finding = response.findings.find(
      (item) => item.finding_type === findingType && item.artifact_ids.includes(requirement),
    );
    assert.ok(finding, `no ${findingType} finding for ${requirement}`);
    this.results.finding = finding;
    this.results.details = findingDetails(this, findingType, requirement);
    await this.results.details.waitFor();
  },
);

When('the finding is opened in the dashboard', async function () {
  await this.results.details.locator('summary span.badge').first().click();
  await this.results.details.locator('dl.finding-detail').waitFor();
});

When('the finding is opened', async function () {
  await this.results.details.locator('summary span.badge').first().click();
  await this.results.details.locator('dl.finding-detail').waitFor();
});

Then('it names the rule, the evaluated baseline, and the changed artifact', async function () {
  const text = await this.results.details.innerText();
  assert.ok(text.includes(this.results.finding.rule_id));
  assert.ok(text.includes(this.results.finding.evaluated_baseline));
  assert.ok(text.includes('CODE-001'));
});

Then('it shows the evidence {string} with the revision it was executed at', async function (evidenceId) {
  const thread = await getUI().api('/api/threads/REQ-001?baseline=baseline-b');
  const row = thread.evidence.find((item) => item.evidence_id === evidenceId);
  assert.ok(row);
  await this.results.details.getByText(evidenceId).first().waitFor({ timeout: 10_000 });
  await this.results.details.getByText(row.tested_commit).first().waitFor({ timeout: 10_000 });
  const text = await this.results.details.innerText();
  assert.ok(text.includes(evidenceId));
  assert.ok(text.includes(row.tested_commit));
});

Then('it does not present the requirement as failed', async function () {
  const text = await this.results.details.innerText();
  assert.match(text, /not a verification failure/i);
  assert.ok(!/Verification failed:/i.test(text));
});

Then('the failing evidence {string} and its revision are shown', async function (evidenceId) {
  const thread = await getUI().api('/api/threads/REQ-003?baseline=baseline-b');
  const row = thread.evidence.find((item) => item.evidence_id === evidenceId);
  assert.ok(row);
  await this.results.details.getByText(evidenceId).first().waitFor({ timeout: 10_000 });
  await this.results.details.getByText(row.tested_commit).first().waitFor({ timeout: 10_000 });
  const text = await this.results.details.innerText();
  assert.ok(text.includes(evidenceId));
  assert.ok(text.includes(row.tested_commit));
});

Then('the wording states a failed verification, not a reverification request', async function () {
  const text = await this.results.details.innerText();
  assert.match(text, /Verification failed:/i);
  assert.ok(!/not a verification failure/i.test(text));
});
