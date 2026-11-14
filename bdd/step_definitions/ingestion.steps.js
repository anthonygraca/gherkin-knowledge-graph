import assert from 'node:assert/strict';
import { Given, Then, When } from '@cucumber/cucumber';

function ingest(world, baseline) {
  const result = world.call('ingest', { revision: baseline });
  world.results.ingests = world.results.ingests || {};
  world.results.ingests[baseline] = result;
  return result;
}

function artifact(world, artifactId, baseline) {
  return world.call('artifact', { id: artifactId, baseline }).artifact;
}

Given('the fixture repository checked out at {string}', function (baseline) {
  this.results.baseline = baseline;
  ingest(this, baseline);
});

When('the requirements are ingested', function () {
  this.results.ingest = ingest(this, this.results.baseline || 'baseline-b');
});

When('the scenarios are ingested', function () {
  if (this.results.probeRepo) {
    this.results.attempt = this.attempt('ingest', {
      name: this.results.probeRepo,
      revision: 'HEAD',
    });
    this.results.ingest = this.results.attempt.result;
    return;
  }
  this.results.ingest = ingest(this, this.results.baseline || 'baseline-b');
});

Then(
  'an artifact {string} of type {string} exists with title {string}',
  function (artifactId, artifactType, title) {
    const result =
      this.results.ingest || this.results.ingests?.[this.results.baseline] || null;
    assert.ok(result, 'no ingestion has run');
    const found = result.artifacts.find((item) => item.artifact_id === artifactId);
    assert.ok(found, `artifact ${artifactId} missing`);
    assert.equal(found.artifact_type, artifactType);
    assert.equal(found.title, title);
    this.results.artifact = found;
  },
);

Then('its locator is {string}', function (locator) {
  assert.equal(this.results.artifact.locator, locator);
});

Then('its content_hash is the sha256 of the file bytes at that revision', function () {
  const artifact = this.results.artifact;
  const path = artifact.locator.split('#')[0];
  const { content_hash } = this.call('blob_hash', {
    revision: artifact.revision,
    path,
  });
  assert.equal(artifact.content_hash, content_hash);
});

Then('its metadata records status {string}', function (status) {
  assert.equal(this.results.artifact.metadata.status, status);
});

Given('{string} contains the tag {string}', function (path, tag) {
  const { text } = this.call('blob_text', { revision: 'baseline-b', path });
  assert.ok(text.includes(tag), `${path} does not contain ${tag}`);
});

Then(
  'an artifact {string} of type {string} exists with locator {string}',
  function (artifactId, artifactType, locator) {
    const found = this.results.ingest.artifacts.find((item) => item.artifact_id === artifactId);
    assert.ok(found, `artifact ${artifactId} missing`);
    assert.equal(found.artifact_type, artifactType);
    assert.equal(found.locator, locator);
    this.results.artifact = found;
  },
);

Then('its title is the scenario name from the feature file', function () {
  assert.ok(this.results.artifact.title.length > 0);
  const scenarioId = this.results.artifact.artifact_id;
  const { text } = this.call('blob_text', {
    revision: this.results.artifact.revision,
    path: this.results.artifact.locator.split('#')[0],
  });
  const lines = text.split('\n');
  const index = lines.findIndex((line) => line.includes(`@${scenarioId}`));
  assert.ok(index >= 0);
  const declaration = lines.slice(index + 1).find((line) => line.trim().startsWith('Scenario:'));
  assert.ok(declaration);
  assert.equal(declaration.trim().slice('Scenario:'.length).trim(), this.results.artifact.title);
});

Then('unannotated files produce no artifacts', function () {
  const locators = this.results.ingest.artifacts.map((artifact) => artifact.locator);
  assert.ok(!locators.some((locator) => locator.startsWith('src/__init__.py')));
  assert.ok(locators.every((locator) => !locator.startsWith('README')));
});

Given('a repository revision where {string} has no front matter block', function (path) {
  this.call('repo', {
    name: 'broken-front-matter',
    files: {
      [path]: '# Plain markdown with no front matter\n\nNo identity declaration here.\n',
    },
  });
  this.results.probeRepo = 'broken-front-matter';
});

Then('ingestion fails with an error naming {string}', function (token) {
  assert.equal(this.results.attempt.ok, false, 'ingestion should have failed');
  assert.ok(
    this.results.attempt.error.detail.includes(token),
    `error does not name ${token}: ${this.results.attempt.error.detail}`,
  );
});

Then('no partial artifact set is returned', function () {
  assert.equal(this.results.attempt.result, undefined);
});

Given(
  'a feature file containing a scenario without an {string} tag',
  function (tag) {
    this.call('repo', {
      name: 'untagged',
      files: {
        'features/plain.feature': 'Feature: Plain\n  Scenario: Ordinary\n    Given a step\n',
      },
    });
    this.results.probeRepo = 'untagged';
  },
);

Then('no artifact is created for that scenario', function () {
  assert.equal(this.results.attempt.ok, true);
  assert.deepEqual(this.results.attempt.result.artifact_ids, []);
});

Given(
  'a feature file where {string} is not followed by a {string} line',
  function (tag, anchor) {
    this.call('repo', {
      name: 'dangling-tag',
      files: {
        'features/dangling.feature': `Feature: Dangling\n  ${tag}\n  Rule: not a scenario\n    Scenario: real\n      Given a step\n`,
      },
    });
    this.results.probeRepo = 'dangling-tag';
  },
);

Given('two requirement documents declare the same id {string}', function (artifactId) {
  const frontMatter = (title) =>
    `---\nid: ${artifactId}\ntitle: ${title}\nstatus: active\n---\n\nBody.\n`;
  this.call('repo', {
    name: 'duplicate-ids',
    files: {
      'requirements/one.md': frontMatter('First'),
      'requirements/two.md': frontMatter('Second'),
    },
  });
  this.results.probeRepo = 'duplicate-ids';
});

Given('the fixture repository has tag {string} at a full commit SHA', function (tag) {
  const result = ingest(this, tag);
  assert.equal(result.commit.length, 40);
  this.results.tagCommit = result.commit;
});

When('the revision is ingested by tag name', function () {
  this.results.byTag = ingest(this, 'baseline-a');
});

Then('every artifact revision is that full commit SHA', function () {
  assert.equal(this.results.byTag.commit, this.results.tagCommit);
  for (const artifact of this.results.byTag.artifacts) {
    assert.equal(artifact.revision, this.results.tagCommit);
  }
});

Then('ingesting the same revision by its SHA returns identical artifacts', function () {
  const bySha = ingest(this, this.results.tagCommit);
  assert.deepEqual(bySha.artifacts, this.results.byTag.artifacts);
});

Given(
  'a tagged scenario whose step contains a doc string with {string} and {string}',
  function (tag, text) {
    this.call('repo', {
      name: 'doc-string',
      files: {
        'features/doc.feature': `Feature: Doc strings\n  @SCN-901\n  Scenario: Real scenario\n    Given a step\n      """\n      ${tag}\n      ${text}\n      """\n`,
      },
    });
    this.results.probeRepo = 'doc-string';
  },
);

Then('only the real tagged scenario becomes an artifact', function () {
  assert.equal(this.results.attempt.ok, true);
  assert.deepEqual(this.results.attempt.result.artifact_ids, ['SCN-901']);
});

Then('an opening delimiter line never also closes the same doc string', function () {
  const artifact = this.results.attempt.result.artifacts[0];
  assert.equal(artifact.artifact_id, 'SCN-901');
  const { output } = this.call('git', {
    name: this.results.probeRepo,
    args: ['show', `${artifact.revision}:features/doc.feature`],
  });
  assert.equal(output.split('"""').length, 3, 'exactly one doc string should be present');
});

Then('an unterminated doc string is an error', function () {
  const repo = this.call('repo', {
    name: 'unterminated',
    files: {
      'features/bad.feature': 'Feature: Bad\n  @SCN-902\n  Scenario: Broken\n    Given a step\n      """\n      never closed\n',
    },
  });
  const attempt = this.attempt('ingest', { name: 'unterminated', revision: repo.commit });
  assert.equal(attempt.ok, false);
  assert.ok(attempt.error.detail.includes('features/bad.feature'));
});

Given('a scenario tagged {string}', function (tag) {
  this.call('repo', {
    name: 'malformed-tag',
    files: {
      'features/bad.feature': `Feature: Bad\n  ${tag}\n  Scenario: Bad identity\n    Given a step\n`,
    },
  });
  this.results.probeRepo = 'malformed-tag';
});

Given(
  'a requirement whose id and status are quoted YAML strings with a trailing comment',
  function () {
    this.call('repo', {
      name: 'quoted-front-matter',
      files: {
        'requirements/REQ-900.md':
          '---\nid: "REQ-900"\nstatus: superseded  # lifecycle note\ntitle: "Quoted title"\n---\n\nBody.\n',
      },
    });
    this.results.probeRepo = 'quoted-front-matter';
  },
);

Then('the id is {string} without quotation marks', function (artifactId) {
  assert.equal(this.results.attempt.result.artifacts[0].artifact_id, artifactId);
});

Then('the status is {string} without the comment', function (status) {
  assert.equal(this.results.attempt.result.artifacts[0].metadata.status, status);
});

Then('a quoted title is stored without quotation marks', function () {
  assert.equal(this.results.attempt.result.artifacts[0].title, 'Quoted title');
});

Given('a requirement whose front matter has an unterminated quoted title', function () {
  this.call('repo', {
    name: 'bad-yaml',
    files: {
      'requirements/BROKEN.md': '---\nid: REQ-901\ntitle: "unterminated\n---\n\nBody.\n',
    },
  });
  this.results.probeRepo = 'bad-yaml';
});

Then('ingestion fails with an error naming the file and the YAML problem', function () {
  assert.equal(this.results.attempt.ok, false);
  assert.ok(this.results.attempt.error.detail.includes('requirements/BROKEN.md'));
  assert.match(this.results.attempt.error.detail, /YAML/);
});

// ---------------------------------------------------------------- DT-02 artifacts

Given('{string} begins with the annotation {string}', function (path, annotation) {
  const { text } = this.call('blob_text', { revision: 'baseline-b', path });
  assert.equal(text.split('\n')[0], annotation);
});

When('the repository is ingested at {string}', function (baseline) {
  this.results.baseline = baseline;
  this.results.ingest = ingest(this, baseline);
});

Then(
  'artifact {string} has type {string} and locator {string}',
  function (artifactId, artifactType, locator) {
    const found = this.results.ingest.artifacts.find((item) => item.artifact_id === artifactId);
    assert.ok(found, `artifact ${artifactId} missing`);
    assert.equal(found.artifact_type, artifactType);
    assert.equal(found.locator, locator);
    this.results.artifact = found;
  },
);

Then('its revision is the commit tagged {string}', function (tag) {
  const result = this.results.ingests[tag];
  assert.equal(this.results.artifact.revision, result.commit);
});

Then('its content_hash differs from the same artifact at {string}', function (baseline) {
  this.results.ingests[baseline] = this.results.ingests[baseline] || ingest(this, baseline);
  const other = this.results.ingests[baseline].artifacts.find(
    (item) => item.artifact_id === this.results.artifact.artifact_id,
  );
  assert.ok(other);
  assert.notEqual(other.content_hash, this.results.artifact.content_hash);
});

Given('{string} has no cta:artifact annotation', function (path) {
  const { text } = this.call('blob_text', { revision: 'baseline-b', path });
  assert.ok(!text.includes('cta:artifact'));
});

Then('no artifact references {string}', function (path) {
  const locators = this.results.ingest.artifacts.map((artifact) => artifact.locator.split('#')[0]);
  assert.ok(!locators.includes(path));
});

Then('its content_hash is the sha256 of the committed blob', function () {
  const artifact = this.results.artifact;
  const { content_hash } = this.call('blob_hash', {
    revision: artifact.revision,
    path: artifact.locator,
  });
  assert.equal(artifact.content_hash, content_hash);
});

Given('a Python file whose annotation appears after its first line', function () {
  this.call('repo', {
    name: 'late-annotation',
    files: {
      'src/late.py': '"""Doc."""\n# cta:artifact CODE-900\n\nVALUE = 1\n',
    },
  });
  this.results.probeRepo = 'late-annotation';
});

Then('ingestion fails with an error naming that file', function () {
  assert.equal(this.results.attempt.ok, false);
  assert.ok(this.results.attempt.error.detail.includes('src/late.py'));
});

Given('a Python file containing two different cta:artifact annotations', function () {
  this.call('repo', {
    name: 'double-annotation',
    files: {
      'src/double.py': '# cta:artifact CODE-901\n# cta:artifact TEST-901\n\nVALUE = 1\n',
    },
  });
  this.results.probeRepo = 'double-annotation';
});

Then('ingestion fails with an error naming the conflicting identities', function () {
  assert.equal(this.results.attempt.ok, false);
  assert.match(this.results.attempt.error.detail, /CODE-901/);
  assert.match(this.results.attempt.error.detail, /TEST-901/);
});

Given('an ingested revision with a clean working tree', function () {
  const repo = this.call('repo_from_fixture', { name: 'dirty-worktree', tag: 'baseline-a' });
  this.results.probeRepo = 'dirty-worktree';
  this.results.cleanCommit = repo.commit;
});

When('a file is modified in the working tree without committing', function () {
  this.call('write', {
    name: this.results.probeRepo,
    files: { 'src/accounts.py': '# cta:artifact CODE-001\nVALUE = "uncommitted"\n' },
  });
});

Then('re-ingesting the same revision returns the committed content_hash', function () {
  const first = this.call('ingest', {
    name: this.results.probeRepo,
    revision: this.results.cleanCommit,
  });
  const second = this.call('ingest', {
    name: this.results.probeRepo,
    revision: this.results.cleanCommit,
  });
  assert.deepEqual(second.artifacts, first.artifacts);
  const artifact = first.artifacts.find((item) => item.artifact_id === 'CODE-001');
  assert.ok(artifact);
  const { output } = this.call('git', {
    name: this.results.probeRepo,
    args: ['show', `${this.results.cleanCommit}:src/accounts.py`],
  });
  assert.ok(!output.includes('uncommitted'));
});

Then('the artifact revision is unchanged', function () {
  const again = this.call('ingest', {
    name: this.results.probeRepo,
    revision: this.results.cleanCommit,
  });
  for (const artifact of again.artifacts) {
    assert.equal(artifact.revision, this.results.cleanCommit);
  }
});

Given('the fixture repository built from its declarative history', function () {
  this.results.baseline = 'baseline-a';
});

When('each tagged baseline is ingested', function () {
  this.results.ingests = {
    'baseline-a': ingest(this, 'baseline-a'),
    'baseline-b': ingest(this, 'baseline-b'),
  };
});

Then(
  'the artifact ids, types, titles, locators, revisions, and content hashes equal {string} for that baseline',
  function (snapshotPath) {
    const snapshot = JSON.parse(
      JSON.stringify(this.call('snapshot', {}).snapshot),
    );
    const baselines = snapshot.baselines || [snapshot];
    for (const [baseline, review] of Object.entries(this.results.ingests)) {
      const expected = baselines.find((item) => item.baseline === baseline);
      assert.ok(expected, `no snapshot for ${baseline} in ${snapshotPath}`);
      const project = (artifact) => ({
        artifact_id: artifact.artifact_id,
        artifact_type: artifact.artifact_type,
        title: artifact.title,
        locator: artifact.locator,
        revision: artifact.revision,
        content_hash: artifact.content_hash,
      });
      assert.deepEqual(review.artifacts.map(project), expected.artifacts.map(project));
    }
  },
);


function ingestProbe(world) {
  world.results.attempt = world.attempt('ingest', {
    name: world.results.probeRepo,
    revision: 'HEAD',
  });
  if (world.results.attempt.ok) {
    world.results.ingest = world.results.attempt.result;
  }
}

When('the requirement is ingested', function () {
  ingestProbe(this);
});

When('the repository is ingested', function () {
  ingestProbe(this);
});

Given('{string} begins with {string}', function (path, annotation) {
  const { text } = this.call('blob_text', { revision: 'baseline-a', path });
  const firstLine = text.split('\n')[0];
  assert.ok(
    firstLine.includes(annotation),
    `${path} first line is ${JSON.stringify(firstLine)}`,
  );
});
