import { After, Before, setWorldConstructor } from '@cucumber/cucumber';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

const ROOT = path.resolve(import.meta.dirname, '../..');
const PYTHON =
  process.env.CTA_BDD_PYTHON || path.join(ROOT, 'backend', '.venv', 'bin', 'python');
const BRIDGE = path.join(ROOT, 'bdd', 'support', 'cta_bridge.py');

export class CtaWorld {
  constructor() {
    this.stateDir = fs.mkdtempSync(path.join(os.tmpdir(), 'cta-bdd-'));
    this.results = {};
  }

  invoke(op, args = {}) {
    const stdout = execFileSync(PYTHON, [BRIDGE], {
      input: JSON.stringify({ op, args }),
      env: {
        ...process.env,
        CTA_BDD_STATE: this.stateDir,
        CTA_REPO_ROOT: ROOT,
        CTA_FIXTURES_DIR: path.join(ROOT, 'fixtures'),
      },
      encoding: 'utf8',
      maxBuffer: 128 * 1024 * 1024,
    });
    return JSON.parse(stdout);
  }

  call(op, args = {}) {
    const response = this.invoke(op, args);
    if (!response.ok) {
      throw new Error(`${response.error.type || 'Error'}: ${response.error.detail}`);
    }
    return response.result;
  }

  attempt(op, args = {}) {
    return this.invoke(op, args);
  }
}

setWorldConstructor(CtaWorld);

Before(function () {
  this.results = {};
});

After(function () {
  try {
    if (this.results.expectedFailures) {
      assert.deepEqual(
        [...this.results.fixtureRun.failed].sort(),
        [...this.results.expectedFailures].sort(),
        'fixture suite failed in a different set of tests than the scenario named',
      );
    }
  } finally {
    fs.rmSync(this.stateDir, { recursive: true, force: true });
  }
});
