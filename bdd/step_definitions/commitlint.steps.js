import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { Given, Then, When } from '@cucumber/cucumber';

const ROOT = path.resolve(import.meta.dirname, '../..');
const ISSUE_MAP = fs.readFileSync(path.join(ROOT, 'docs/traceability-issue-map.md'), 'utf8');
const ISSUE_MAP_PATH = path.join(ROOT, 'docs/traceability-issue-map.md');

function lint(world, message) {
  world.results.lint = world.call('commitlint', { mode: 'message', message });
  return world.results.lint;
}

function range(world, args) {
  world.results.lint = world.call('commitlint', { mode: 'range', ...args });
  return world.results.lint;
}

Given('issue 8 is registered as a story in the issue map', function () {
  const result = this.call('commitlint', { mode: 'known' });
  assert.ok(result.known_issues.includes(8));
  this.results.knownIssues = result.known_issues;
});

When('a commit message is {string}', function (message) {
  lint(this, message);
});

Then('commit lint succeeds', function () {
  assert.equal(this.results.lint.exit_code, 0, JSON.stringify(this.results.lint.errors));
});

Then('the same message without the optional scope also succeeds', function () {
  const result = lint(this, 'ci: [issue #8] enforce commit references');
  assert.equal(result.exit_code, 0, JSON.stringify(result.errors));
});

Given('a commit subject is {string}', function (subject) {
  this.results.subject = subject;
});

Given('its body contains {string}', function (body) {
  this.results.message = `${this.results.subject}\n\n${body}\n`;
});

When('commit lint checks the message', function () {
  lint(this, this.results.message);
});

Then('it fails and describes the required subject format', function () {
  assert.equal(this.results.lint.exit_code, 1);
  assert.ok(
    this.results.lint.errors.some((error) => error.includes('<type>[optional scope]: [issue #N]')),
    this.results.lint.errors.join('\n'),
  );
});

Given('issue 999 is absent from the story and task tables', function () {
  const result = this.call('commitlint', { mode: 'known' });
  assert.ok(!result.known_issues.includes(999));
});

When('issue 999 appears in the required subject reference or a body reference line', function () {
  this.results.lint = this.call('commitlint', {
    mode: 'message',
    message: 'feat: [issue #999] invent a work item\n\nRefs #999\n',
  });
});

Then('commit lint fails', function () {
  assert.equal(this.results.lint.exit_code, 1);
});

Then('feature rows and duplicate numbers mentioned only in prose are not valid work items', function () {
  assert.ok(this.results.lint.errors.some((error) => error.includes('#999')));
  const result = this.call('commitlint', { mode: 'known' });
  assert.ok(!result.known_issues.includes(1), 'feature #1 must not be a work item');
  assert.ok(!result.known_issues.includes(7), 'feature #7 must not be a work item');
  const attempt = this.call('commitlint', {
    mode: 'message',
    message: 'feat: [issue #1] use a feature row\n',
  });
  assert.equal(attempt.exit_code, 1);
});

Given('a legacy commit without an issue reference is the fixed adoption baseline', function () {
  this.call('repo', {
    name: 'lint-history',
    files: { 'docs/traceability-issue-map.md': ISSUE_MAP, 'README.md': 'probe\n' },
    message: 'legacy message without a reference',
  });
  const head = this.call('git', { name: 'lint-history', args: ['rev-parse', 'HEAD'] }).output;
  this.results.legacy = head;
});

Given('an invalid new commit follows it', function () {
  this.call('commit', {
    name: 'lint-history',
    files: { 'README.md': 'probe 2\n' },
    message: 'not a conventional message',
  });
  this.results.invalid = this.call('git', { name: 'lint-history', args: ['rev-parse', 'HEAD'] }).output;
});

Given('a valid new commit follows the invalid commit', function () {
  this.call('commit', {
    name: 'lint-history',
    files: { 'README.md': 'probe 3\n' },
    message: 'feat: [issue #8] add a valid commit',
  });
  this.results.valid = this.call('git', { name: 'lint-history', args: ['rev-parse', 'HEAD'] }).output;
});

When('commit lint checks the new history', function () {
  range(this, {
    name: 'lint-history',
    head: 'HEAD',
    legacy_baseline: this.results.legacy,
  });
});

Then('it reports the invalid new commit', function () {
  assert.equal(this.results.lint.exit_code, 1);
  assert.ok(this.results.lint.errors.some((error) => error.startsWith(this.results.invalid.slice(0, 12))));
});

Then('it does not report the legacy commit', function () {
  assert.ok(!this.results.lint.errors.some((error) => error.includes(this.results.legacy.slice(0, 12))));
});

Given('a topic branch and its target both contain the adoption baseline', function () {
  this.call('repo', {
    name: 'lint-branches',
    files: { 'docs/traceability-issue-map.md': ISSUE_MAP, 'README.md': 'base\n' },
    message: 'legacy message without a reference',
  });
  this.results.legacy = this.call('git', { name: 'lint-branches', args: ['rev-parse', 'HEAD'] }).output;
});

Given('both branches contain independent later commits', function () {
  this.call('git', { name: 'lint-branches', args: ['checkout', '-b', 'topic'] });
  this.call('commit', {
    name: 'lint-branches',
    files: { 'topic.txt': 'one\n' },
    message: 'feat: [issue #8] topic one',
  });
  this.results.topicCommit = this.call('git', { name: 'lint-branches', args: ['rev-parse', 'HEAD'] }).output;
  this.call('git', { name: 'lint-branches', args: ['checkout', 'main'] });
  this.call('commit', {
    name: 'lint-branches',
    files: { 'main.txt': 'one\n' },
    message: 'feat: [issue #8] main only',
  });
});

When('commit lint checks the topic head excluding the target history', function () {
  range(this, {
    name: 'lint-branches',
    head: 'topic',
    base: 'main',
    legacy_baseline: this.results.legacy,
  });
});

Then('it checks every topic commit absent from the target', function () {
  assert.deepEqual(this.results.lint.commits, [this.results.topicCommit]);
});

Then('it excludes commits already reachable from the target', function () {
  assert.equal(this.results.lint.exit_code, 0, JSON.stringify(this.results.lint.errors));
});

Given('a new merge commit integrates a topic branch', function () {
  this.call('repo', {
    name: 'lint-merge',
    files: { 'docs/traceability-issue-map.md': ISSUE_MAP, 'README.md': 'base\n' },
    message: 'legacy message without a reference',
  });
  this.results.legacy = this.call('git', { name: 'lint-merge', args: ['rev-parse', 'HEAD'] }).output;
  this.call('git', { name: 'lint-merge', args: ['checkout', '-b', 'topic'] });
  this.call('commit', {
    name: 'lint-merge',
    files: { 'topic.txt': 'bad\n' },
    message: 'bad topic commit',
  });
  this.call('git', { name: 'lint-merge', args: ['checkout', 'main'] });
  this.call('commit', {
    name: 'lint-merge',
    files: { 'main.txt': 'ok\n' },
    message: 'feat: [issue #8] main work',
  });
  this.call('git', {
    name: 'lint-merge',
    args: ['merge', '--no-ff', '--no-edit', 'topic'],
  });
});

When('either the merge message or a topic commit lacks the required issue reference', function () {
  range(this, {
    name: 'lint-merge',
    head: 'HEAD',
    legacy_baseline: this.results.legacy,
  });
});

Then('a conforming merge with conforming topic commits succeeds', function () {
  this.call('repo', {
    name: 'lint-merge-ok',
    files: { 'docs/traceability-issue-map.md': ISSUE_MAP, 'README.md': 'base\n' },
    message: 'legacy message without a reference',
  });
  const legacy = this.call('git', { name: 'lint-merge-ok', args: ['rev-parse', 'HEAD'] }).output;
  this.call('git', { name: 'lint-merge-ok', args: ['checkout', '-b', 'topic'] });
  this.call('commit', {
    name: 'lint-merge-ok',
    files: { 'topic.txt': 'good\n' },
    message: 'feat: [issue #8] topic work',
  });
  this.call('git', { name: 'lint-merge-ok', args: ['checkout', 'main'] });
  this.call('commit', {
    name: 'lint-merge-ok',
    files: { 'main.txt': 'ok\n' },
    message: 'feat: [issue #8] main work',
  });
  this.call('git', {
    name: 'lint-merge-ok',
    args: ['merge', '--no-ff', '--no-edit', '-m', 'feat: [issue #8] merge topic', 'topic'],
  });
  const result = range(this, { name: 'lint-merge-ok', head: 'HEAD', legacy_baseline: legacy });
  assert.equal(result.exit_code, 0, JSON.stringify(result.errors));
});

Given('a new commit references an issue absent from its own issue map', function () {
  const mapWithout = ISSUE_MAP.replace(/\| SETUP-01 \| \[#8\].*\n/, '');
  this.call('repo', {
    name: 'lint-historical',
    files: { 'docs/traceability-issue-map.md': mapWithout, 'README.md': 'base\n' },
    message: 'legacy message without a reference',
  });
  this.results.legacy = this.call('git', { name: 'lint-historical', args: ['rev-parse', 'HEAD'] }).output;
  this.call('commit', {
    name: 'lint-historical',
    files: { 'README.md': 'next\n' },
    message: 'feat: [issue #8] use an issue added later',
  });
  this.results.historical = this.call('git', { name: 'lint-historical', args: ['rev-parse', 'HEAD'] }).output;
});

Given('the working tree later adds that issue', function () {
  this.call('write', {
    name: 'lint-historical',
    files: { 'docs/traceability-issue-map.md': ISSUE_MAP },
  });
});

When('commit lint checks the commit', function () {
  range(this, {
    name: 'lint-historical',
    head: 'HEAD',
    legacy_baseline: this.results.legacy,
  });
});

Then('it fails using the map at that commit', function () {
  assert.equal(this.results.lint.exit_code, 1);
  assert.ok(this.results.lint.errors.some((error) => error.includes('#8')));
});

Given('a selected revision is unavailable or the repository is shallow', function () {
  this.call('repo', {
    name: 'lint-missing',
    files: { 'docs/traceability-issue-map.md': ISSUE_MAP, 'README.md': 'base\n' },
    message: 'legacy message without a reference',
  });
  this.results.legacy = this.call('git', { name: 'lint-missing', args: ['rev-parse', 'HEAD'] }).output;
});

When('commit lint checks the history', function () {
  range(this, {
    name: 'lint-missing',
    head: 'does-not-exist',
    legacy_baseline: this.results.legacy,
  });
});

Then('it fails with an operational error', function () {
  assert.equal(this.results.lint.exit_code, 2);
  assert.ok(this.results.lint.errors.length > 0);
});

Then('it does not claim the selected commits passed', function () {
  assert.deepEqual(this.results.lint.commits, []);
});
