import assert from 'node:assert/strict';
import { Given, Then, When } from '@cucumber/cucumber';

import { getUI, startReviewUI } from '../support/ui.js';

const MODEL = 'embeddinggemma-2-text-270m-q8_0@sha256:278a7ff1248c';
const INDEX = 'snapshot:bdd-recorded-baseline-a';

async function openDashboard(world, baseline = 'baseline-a') {
  const ui = getUI();
  await world.page.goto(ui.baseUrl);
  await world.page.locator('#baseline').selectOption(baseline);
  await world.page.getByRole('region', { name: 'Findings summary' }).waitFor();
  await world.page.getByLabel('Finding counts by type').waitFor();
}

async function selectBaseline(world, baseline) {
  const response = world.page.waitForResponse(
    (candidate) =>
      candidate.url().includes('/api/findings') && candidate.url().includes(baseline),
    { timeout: 20_000 },
  );
  await world.page.locator('#baseline').selectOption(baseline);
  await response;
  await world.page.getByLabel('Finding counts by type').waitFor();
}

function candidateRegion(world) {
  return world.page.getByRole('region', { name: 'Discovery candidates' });
}

async function requestCandidates(world, source, provider, custom = '') {
  const region = candidateRegion(world);
  try {
    await region.getByLabel('Source artifact', { exact: true }).waitFor({ timeout: 10_000 });
  } catch (error) {
    process.stderr.write(
      `[candidate panel missing] errors=${JSON.stringify(world.pageErrors)}\n` +
        `${await world.page.locator('main').innerHTML()}\n`,
    );
    throw error;
  }
  await region.getByLabel('Source artifact', { exact: true }).selectOption(source);
  if (provider !== null) {
    await region.getByLabel('Provider', { exact: true }).selectOption(provider);
  }
  await region.getByLabel('Custom provider name', { exact: true }).fill(custom);
  await new Promise((resolve) => setTimeout(resolve, 150));
  await region.getByRole('button', { name: 'Find candidates' }).click();
}

async function captureViaApi(world, overrides = {}) {
  const ui = getUI();
  const artifacts = await ui.api('/api/artifacts?baseline=baseline-a');
  const byId = Object.fromEntries(
    artifacts.artifacts.map((artifact) => [artifact.artifact_id, artifact]),
  );
  const payload = {
    source_id: 'SCN-002',
    target_id: 'CODE-001',
    relation_type: 'implemented_by',
    baseline: 'baseline-a',
    source_content_hash: byId['SCN-002'].content_hash,
    target_content_hash: byId['CODE-001'].content_hash,
    provider: 'fake',
    model_version: 'fake-fixture-v1',
    index_revision: `sha256:${'a'.repeat(64)}`,
    score: 0.71,
    ...overrides,
  };
  for (const [key, value] of Object.entries(payload)) {
    if (value === '__absent__') delete payload[key];
    else if (value === '__null__') payload[key] = null;
  }
  const response = await ui.request('/api/link-proposals', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  assert.equal(response.status, 201, JSON.stringify(response.body));
  world.results.apiCapture = response;
  return response.body;
}

Given('the effective discovery registry contains only "fake"', async function () {
  if (!this.results.registryAlreadyFakeOnly) {
    await startReviewUI({ providerMode: 'fake-only' });
  }
  const catalog = await getUI().api('/api/discovery/providers');
  assert.deepEqual(
    catalog.providers.map((provider) => provider.name),
    ['fake'],
  );
});

Given('the dashboard displays REQ-001 at baseline-a', async function () {
  await openDashboard(this, 'baseline-a');
  this.results.findingsBefore = await getUI().api('/api/findings?baseline=baseline-a');
  await this.page.getByRole('button', { name: 'REQ-001', exact: true }).click();
  await this.page.getByRole('region', { name: /Thread for REQ-001/ }).waitFor();
});

When('discovery is requested with provider "missing-provider"', async function () {
  await requestCandidates(this, 'REQ-001', 'fake', 'missing-provider');
  await this.page.getByRole('alert').waitFor();
});

Then('the API returns a 400 problem with code "provider-not-registered"', async function () {
  const response = await getUI().request('/api/discovery', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ artifact_id: 'REQ-001', provider: 'missing-provider' }),
  });
  assert.equal(response.status, 400);
  assert.equal(response.body.code, 'provider-not-registered');
  this.results.problem = response.body;
});

Then('failed_provider is {string}', function (provider) {
  assert.equal(this.results.problem.failed_provider, provider);
});

Then('registered_providers is ["fake"]', function () {
  assert.deepEqual(this.results.problem.registered_providers, ['fake']);
});

Then(
  'the candidate panel displays the selected provider as unavailable and names {string}',
  async function (provider) {
    const text = await candidateRegion(this).getByRole('alert').innerText();
    assert.match(text, /Provider unavailable/);
    assert.ok(text.includes(provider), text);
  },
);

Then(
  'the candidate panel lists the registered providers and keeps "fake" selectable',
  async function () {
    const text = await candidateRegion(this).innerText();
    assert.ok(text.includes('fake'), text);
    await candidateRegion(this).getByLabel('Provider', { exact: true }).selectOption('fake');
  },
);

Then('the accepted thread and EV-001 remain accessible', async function () {
  await this.page.getByRole('button', { name: 'REQ-001', exact: true }).click();
  const thread = this.page.getByRole('region', { name: /Thread for REQ-001/ });
  await thread.waitFor();
  assert.ok((await thread.innerText()).includes('EV-001'));
});

Then('no assurance finding is created', async function () {
  const after = await getUI().api('/api/findings?baseline=baseline-a');
  assert.deepEqual(after, this.results.findingsBefore);
});

// ------------------------------------------------------------------ SCN-3102

Given(
  'the configured provider "cocoindex" previously returned candidates for baseline-a',
  async function () {
    await startReviewUI({ providerMode: 'timeout' });
    await openDashboard(this, 'baseline-a');
    this.results.findingsBefore = await getUI().api('/api/findings?baseline=baseline-a');
    this.results.threadBefore = await getUI().api('/api/threads/REQ-001?baseline=baseline-a');
    await requestCandidates(this, 'SCN-001', 'cocoindex');
    await candidateRegion(this)
      .getByRole('list', { name: 'Discovery candidates' })
      .waitFor();
  },
);

When('that provider now times out through its deterministic recorded transport', async function () {
  await selectBaseline(this, 'baseline-b');
  assert.equal(
    await candidateRegion(this).getByRole('list', { name: 'Discovery candidates' }).count(),
    0,
  );
});

When('discovery is requested for baseline-b', async function () {
  await requestCandidates(this, 'SCN-001', 'cocoindex');
  await candidateRegion(this).getByRole('alert').waitFor();
});

Then('the API returns a 503 problem with code "provider-unavailable"', async function () {
  const response = await getUI().request('/api/discovery', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      artifact_id: 'SCN-001',
      provider: 'cocoindex',
      baseline: 'baseline-b',
    }),
  });
  assert.equal(response.status, 503);
  assert.equal(response.body.code, 'provider-unavailable');
  this.results.problem = response.body;
});

Then('the panel displays the provider failure and names "cocoindex"', async function () {
  const text = await candidateRegion(this).getByRole('alert').innerText();
  assert.match(text, /Provider failed/);
  assert.ok(text.includes('cocoindex'), text);
});

Then(
  'no baseline-a candidate appears as a current baseline-b result',
  async function () {
    assert.equal(
      await candidateRegion(this).getByRole('list', { name: 'Discovery candidates' }).count(),
      0,
    );
    const items = await candidateRegion(this).locator('ol.candidate-list li').allInnerTexts();
    assert.deepEqual(items, []);
  },
);

Then('no successful empty-result state is displayed', async function () {
  const text = await candidateRegion(this).innerText();
  assert.ok(!text.includes('0 candidates'), text);
});

Then('the application does not silently request fake discovery', async function () {
  assert.equal(
    await candidateRegion(this).getByLabel('Provider', { exact: true }).inputValue(),
    'cocoindex',
  );
  assert.equal(
    await candidateRegion(this).getByRole('list', { name: 'Discovery candidates' }).count(),
    0,
  );
  assert.equal(this.results.problem.failed_provider, 'cocoindex');
});

Then('accepted links, evidence, and findings are unchanged', async function () {
  if (this.results.local) {
    assert.equal(this.results.local.unchanged, true);
    return;
  }
  assert.deepEqual(
    await getUI().api('/api/findings?baseline=baseline-a'),
    this.results.findingsBefore,
  );
  assert.deepEqual(
    await getUI().api('/api/threads/REQ-001?baseline=baseline-a'),
    this.results.threadBefore,
  );
});

// ------------------------------------------------------------------ SCN-3103

Given('the configured discovery provider is "fake"', async function () {
  await startReviewUI({ providerMode: 'fake-only' });
  await openDashboard(this, 'baseline-a');
});

When('candidates are requested for REQ-003 at baseline-a', async function () {
  await requestCandidates(this, 'REQ-003', 'fake');
  await candidateRegion(this).getByText('0 candidates').waitFor();
});

Then('the API returns 200 with an empty candidates array', async function () {
  const response = await getUI().request('/api/discovery', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ artifact_id: 'REQ-003', provider: 'fake', baseline: 'baseline-a' }),
  });
  assert.equal(response.status, 200);
  assert.deepEqual(response.body.candidates, []);
  this.results.discovery = response.body;
});

Then('the response retains provider, model_version, and index_revision', function () {
  assert.equal(this.results.discovery.provider, 'fake');
  assert.equal(this.results.discovery.model_version, 'fake-fixture-v1');
  assert.match(this.results.discovery.index_revision, /^sha256:/);
});

Then(
  'the panel displays zero candidates without an unavailable-provider state',
  async function () {
    const text = await candidateRegion(this).innerText();
    assert.ok(text.includes('0 candidates'), text);
    assert.ok(!text.includes('Provider unavailable'), text);
    assert.ok(!text.includes('Provider failed'), text);
  },
);

// ------------------------------------------------------------------ SCN-3104

Given('LNK-007 is displayed in the proposal panel at baseline-a', async function () {
  await startReviewUI({ providerMode: 'fake-only' });
  await openDashboard(this, 'baseline-a');
  await this.page.getByRole('button', { name: 'REQ-002', exact: true }).click();
  await this.page.getByRole('region', { name: 'Review proposals' }).waitFor();
  await this.page.locator('article.proposal[data-link-id="LNK-007"]').waitFor();
  const row = this.page
    .getByRole('region', { name: /Thread for REQ-002/ })
    .locator('tr[data-link-id="LNK-007"]');
  await row.waitFor();
  const thread = await getUI().api('/api/workspace/threads/REQ-002?baseline=baseline-a');
  const link = thread.proposed_links.find((item) => item.link_id === 'LNK-007');
  assert.ok(link);
  const text = await row.innerText();
  assert.ok(text.includes('fake'), text);
  assert.ok(text.includes('fake-fixture-v1'), text);
  assert.ok(text.includes(link.provenance.index_revision), text);
  assert.ok(text.includes('fixture-generated'), text);
});

Given(
  'a rejection decision for LNK-007 is recorded with reason {string}',
  async function (reason) {
    const response = await getUI().request('/api/links/LNK-007/review', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        decision: 'reject',
        reviewer_id: 'rv-ana',
        baseline: 'baseline-a',
        reason,
      }),
    });
    assert.equal(response.status, 200, JSON.stringify(response.body));
  },
);

When('its details and review history are opened', async function () {
  await openDashboard(this, 'baseline-a');
  await this.page.getByRole('button', { name: 'REQ-002', exact: true }).click();
  await this.page.getByRole('region', { name: 'Review proposals' }).waitFor();
});

Then('every proposal presentation displays provider {string}', async function (provider) {
  const history = await this.page.getByRole('list', { name: 'Review history' }).innerText();
  assert.ok(history.includes(`provider ${provider}`), history);
});

Then('every proposal presentation displays model_version {string}', async function (model) {
  const history = await this.page.getByRole('list', { name: 'Review history' }).innerText();
  assert.ok(history.includes(`model ${model}`), history);
});

Then(
  'every proposal presentation displays its recorded index_revision',
  async function () {
    const body = await getUI().api('/api/workspace/history?baseline=baseline-a');
    const rejection = body.events.find((event) => event.event === 'decision_recorded');
    assert.ok(rejection);
    const history = await this.page.getByRole('list', { name: 'Review history' }).innerText();
    assert.ok(history.includes(rejection.snapshot.index_revision), history);
  },
);

Then('it is labelled as fixture-generated', async function () {
  const history = await this.page.getByRole('list', { name: 'Review history' }).innerText();
  assert.ok(history.includes('fixture-generated'), history);
});

Then(
  'the review history retains that provenance with the rejection',
  async function () {
    const body = await getUI().api('/api/workspace/history?baseline=baseline-a');
    const rejection = body.events.find((event) => event.event === 'decision_recorded');
    assert.ok(rejection);
    assert.equal(rejection.decision, 'reject');
    assert.ok(rejection.snapshot.snapshot_digest.startsWith('sha256:'));
    const history = await this.page.getByRole('list', { name: 'Review history' }).innerText();
    assert.ok(history.includes('reject'), history);
    assert.ok(history.includes('Not this scenario'), history);
  },
);

Then('it is absent from accepted_links', async function () {
  const thread = await getUI().api('/api/workspace/threads/REQ-002?baseline=baseline-a');
  assert.deepEqual(
    thread.accepted_links.filter((link) => link.link_id === 'LNK-007'),
    [],
  );
});

// ------------------------------------------------------------------ SCN-3105

Given(
  'the CocoIndex provider adapter uses a deterministic recorded search transport',
  async function () {
    await startReviewUI({ providerMode: 'recorded' });
    await openDashboard(this, 'baseline-a');
  },
);

Given('the real discovery route and problem mapping are exercised', async function () {
  const catalog = await getUI().api('/api/discovery/providers');
  assert.ok(catalog.providers.some((provider) => provider.name === 'cocoindex'));
});

When('its mapped proposal is displayed', async function () {
  await requestCandidates(this, 'SCN-001', 'cocoindex');
  await candidateRegion(this)
    .getByRole('list', { name: 'Discovery candidates' })
    .waitFor();
});

Then('the panel identifies the provider as "cocoindex"', async function () {
  const text =
    this.results.providerScope === 'history'
      ? await this.page.getByRole('list', { name: 'Review history' }).innerText()
      : await candidateRegion(this).innerText();
  assert.ok(text.includes('cocoindex'), text);
});

Then('it displays the recorded model identity', async function () {
  const text =
    this.results.providerScope === 'history'
      ? await this.page.getByRole('list', { name: 'Review history' }).innerText()
      : await candidateRegion(this).innerText();
  assert.ok(text.includes(MODEL), text);
});

Then('it labels the snapshot value as a CTA snapshot binding', async function () {
  const text = await candidateRegion(this).innerText();
  assert.ok(text.includes('CTA snapshot binding'), text);
});

Then('it does not label the proposal as fixture-generated or accepted', async function () {
  const items = await candidateRegion(this)
    .getByRole('list', { name: 'Discovery candidates' })
    .locator('li')
    .allInnerTexts();
  assert.ok(items.length > 0);
  for (const item of items) {
    assert.ok(!item.includes('fixture-generated'), item);
    assert.ok(!item.includes('accepted'), item);
  }
});

Then(
  /^this check establishes adapter\/API\/UI behaviour, not live inference or retrieval quality$/,
  async function () {
    const items = await candidateRegion(this)
      .getByRole('list', { name: 'Discovery candidates' })
      .locator('li')
      .allInnerTexts();
    assert.ok(items.length > 0);
    assert.ok(items[0].includes('CTA snapshot binding'));
  },
);

// ------------------------------------------------------------------ SCN-3106

Given(
  /^a historical proposed link whose (\w+) is (absent|null)$/,
  async function (field, value) {
    await startReviewUI({ providerMode: 'fake-only' });
    await openDashboard(this, 'baseline-a');
    const overrides = {};
    overrides[field] = value === 'null' ? '__null__' : '__absent__';
    this.results.missingField = field;
    this.results.missingValue = value;
    await captureViaApi(this, overrides);
  },
);

When('the proposal is displayed', async function () {
  await openDashboard(this, 'baseline-a');
  await this.page.getByRole('button', { name: 'REQ-002', exact: true }).click();
  await this.page.getByRole('region', { name: 'Review proposals' }).waitFor();
  const linkId = this.results.apiCapture.body.link.link_id;
  await this.page.locator(`article.proposal[data-link-id="${linkId}"]`).waitFor();
});

const FIELD_LABELS = {
  provider: 'Provider',
  model_version: 'Model version',
  index_revision: 'Fixture index revision',
};

Then('{word} is shown as {string}', async function (field, expected) {
  const linkId = this.results.apiCapture.body.link.link_id;
  const article = this.page.locator(`article.proposal[data-link-id="${linkId}"]`);
  const dt = article.locator('dt', { hasText: FIELD_LABELS[field] }).first();
  const dd = dt.locator('xpath=following-sibling::dd[1]');
  assert.equal(await dd.innerText(), expected);
  const row = this.page
    .getByRole('region', { name: /Thread for REQ-002/ })
    .locator(`tr[data-link-id="${linkId}"]`);
  await row.waitFor();
  assert.ok((await row.innerText()).includes(expected), await row.innerText());
});

Then('no current {word} is substituted', async function (field) {
  const linkId = this.results.apiCapture.body.link.link_id;
  const article = this.page.locator(`article.proposal[data-link-id="${linkId}"]`);
  const dt = article.locator('dt', { hasText: FIELD_LABELS[field] }).first();
  const dd = dt.locator('xpath=following-sibling::dd[1]');
  const text = await dd.innerText();
  assert.equal(text, 'not recorded');
  assert.ok(!text.includes('fake-fixture-v1'));
  assert.ok(!text.includes('sha256:'));
  assert.notEqual(text, 'fake');
});

Then('the proposal remains outside accepted_links', async function () {
  const linkId = this.results.apiCapture.body.link.link_id;
  const thread = await getUI().api('/api/workspace/threads/REQ-002?baseline=baseline-a');
  assert.deepEqual(
    thread.accepted_links.filter((link) => link.link_id === linkId),
    [],
  );
});

// ------------------------------------------------------------------ SCN-3107

Given(
  'a recorded proposal whose provider is "cocoindex" and whose model and index identity are recorded',
  async function () {
    await startReviewUI({ providerMode: 'fake-only' });
    await openDashboard(this, 'baseline-a');
    const captured = await captureViaApi(this, {
      provider: 'cocoindex',
      model_version: MODEL,
      index_revision: INDEX,
    });
    const response = await getUI().request(
      `/api/links/${captured.link.link_id}/review`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          decision: 'reject',
          reviewer_id: 'rv-ana',
          baseline: 'baseline-a',
          reason: 'Historical provider disabled',
        }),
      },
    );
    assert.equal(response.status, 200, JSON.stringify(response.body));
    this.results.registryAlreadyFakeOnly = true;
  },
);

When('the proposal is displayed in history', async function () {
  this.results.providerScope = 'history';
  await openDashboard(this, 'baseline-a');
  await this.page.getByRole('button', { name: 'REQ-002', exact: true }).click();
  await this.page.getByRole('region', { name: 'Review proposals' }).waitFor();
  await this.page.getByRole('list', { name: 'Review history' }).waitFor();
});

Then('it labels the recorded index value as a CTA snapshot binding', async function () {
  const text = await this.page.getByRole('list', { name: 'Review history' }).innerText();
  assert.ok(text.includes('CTA snapshot binding'), text);
  assert.ok(text.includes(INDEX), text);
});

Then('it does not label the proposal as fixture-generated', async function () {
  const text = await this.page.getByRole('list', { name: 'Review history' }).innerText();
  assert.ok(!text.includes('fixture-generated'), text);
});

Then(
  'it reports the provider as currently unavailable without hiding the recorded provenance',
  async function () {
    const text = await this.page.getByRole('list', { name: 'Review history' }).innerText();
    assert.ok(text.includes('not in the current registry'), text);
    assert.ok(text.includes('cocoindex'), text);
    assert.ok(text.includes(MODEL), text);
  },
);
