import { After, AfterAll, Before, BeforeAll, setDefaultTimeout } from '@cucumber/cucumber';
import { execFileSync, spawn } from 'node:child_process';
import fs from 'node:fs';
import http from 'node:http';
import net from 'node:net';
import path from 'node:path';
import { chromium } from 'playwright-core';


const BDD_ROOT = path.resolve(import.meta.dirname, '..');
const ROOT = path.resolve(BDD_ROOT, '..');
const PYTHON = process.env.CTA_BDD_PYTHON || path.join(ROOT, 'backend/.venv/bin/python');
const BRIDGE = path.join(BDD_ROOT, 'support', 'cta_bridge.py');
const DIST = path.join(ROOT, 'frontend', 'dist');

setDefaultTimeout(60_000);

let ui = null;

function freePort() {
  return new Promise((resolve, reject) => {
    const server = net.createServer();
    server.listen(0, '127.0.0.1', () => {
      const { port } = server.address();
      server.close(() => resolve(port));
    });
    server.on('error', reject);
  });
}

function builtFixturePath() {
  const cache = path.join(ROOT, 'bdd', '.cache');
  fs.mkdirSync(cache, { recursive: true });
  const state = fs.mkdtempSync(path.join(cache, 'ui-state-'));
  const stdout = execFileSync(PYTHON, [BRIDGE], {
    input: JSON.stringify({ op: 'fixture_repo', args: {} }),
    env: { ...process.env, CTA_BDD_STATE: state },
    encoding: 'utf8',
  });
  const parsed = JSON.parse(stdout);
  if (!parsed.ok) throw new Error(parsed.error?.detail || 'fixture_repo failed');
  return parsed.result.path;
}

async function waitFor(url, timeoutMs = 20_000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    try {
      const response = await fetch(url);
      if (response.ok) return response;
    } catch {
      // server not listening yet
    }
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
  throw new Error(`${url} did not become ready`);
}

function proxy(targetPort, req, res) {
  const upstream = http.request(
    {
      host: '127.0.0.1',
      port: targetPort,
      path: req.url,
      method: req.method,
      headers: req.headers,
    },
    (response) => {
      res.writeHead(response.statusCode ?? 502, response.headers);
      response.pipe(res);
    },
  );
  upstream.on('error', (error) => {
    res.writeHead(502, { 'content-type': 'text/plain' });
    res.end(`proxy error: ${error.message}`);
  });
  req.pipe(upstream);
}

function startStatic(port, backendPort) {
  const server = http.createServer((req, res) => {
    if (req.url.startsWith('/api') || req.url.startsWith('/health')) {
      proxy(backendPort, req, res);
      return;
    }
    const urlPath = decodeURIComponent(req.url.split('?')[0]);
    const target = path.join(DIST, urlPath === '/' ? 'index.html' : urlPath);
    if (!target.startsWith(DIST)) {
      res.writeHead(403).end();
      return;
    }
    fs.readFile(target, (error, data) => {
      if (error) {
        fs.readFile(path.join(DIST, 'index.html'), (fallbackError, fallback) => {
          if (fallbackError) {
            res.writeHead(404).end();
          } else {
            res.writeHead(200, { 'content-type': 'text/html' }).end(fallback);
          }
        });
        return;
      }
      const ext = path.extname(target);
      const type =
        ext === '.js'
          ? 'text/javascript'
          : ext === '.css'
            ? 'text/css'
            : ext === '.html'
              ? 'text/html'
              : 'application/octet-stream';
      res.writeHead(200, { 'content-type': type }).end(data);
    });
  });
  return new Promise((resolve) => server.listen(port, '127.0.0.1', () => resolve(server)));
}

function chromePath() {
  const candidates = [
    process.env.CTA_CHROME_PATH,
    '/usr/bin/chromium-browser',
    '/usr/bin/chromium',
    '/usr/bin/google-chrome',
    '/usr/bin/google-chrome-stable',
    '/opt/google/chrome/chrome',
  ].filter(Boolean);
  const found = candidates.find((candidate) => fs.existsSync(candidate));
  if (!found) {
    throw new Error(
      'no Chromium/Chrome executable found for browser acceptance; set CTA_CHROME_PATH',
    );
  }
  return found;
}

export function getUI() {
  if (!ui) throw new Error('the browser UI was not started');
  return ui;
}

BeforeAll(async () => {
  if (process.env.CTA_UI_DISABLED === '1') return;
  const index = path.join(DIST, 'index.html');
  if (!fs.existsSync(index)) {
    throw new Error(`frontend build missing at ${DIST}; run "npm run build" in frontend/ first`);
  }
  const fixture = builtFixturePath();
  const backendPort = await freePort();
  const staticPort = await freePort();
  const backend = spawn(
    PYTHON,
    ['-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', String(backendPort)],
    {
      cwd: path.join(ROOT, 'backend'),
      env: {
        ...process.env,
        PYTHONPATH: path.join(ROOT, 'backend'),
        CTA_REPO_ROOT: ROOT,
        CTA_FIXTURES_DIR: path.join(ROOT, 'fixtures'),
        CTA_FIXTURE_REPO: fixture,
      },
      stdio: ['ignore', 'pipe', 'pipe'],
    },
  );
  backend.stderr.on('data', () => {});
  const server = await startStatic(staticPort, backendPort);
  await waitFor(`http://127.0.0.1:${backendPort}/health`);
  await waitFor(`http://127.0.0.1:${staticPort}/`);
  const browser = await chromium.launch({
    executablePath: chromePath(),
    headless: true,
    args: ['--no-sandbox', '--disable-dev-shm-usage'],
  });
  ui = {
    backend,
    backendPort,
    server,
    staticPort,
    browser,
    baseUrl: `http://127.0.0.1:${staticPort}`,
    async api(pathname) {
      const response = await fetch(`http://127.0.0.1:${backendPort}${pathname}`);
      return response.json();
    },
  };
});

Before(async function (scenario) {
  if (!ui) return;
  const tags = scenario.pickle.tags.map((tag) => tag.name);
  if (!tags.includes('@browser')) return;
  this.page = await ui.browser.newPage({ viewport: { width: 1280, height: 1400 } });
  this.pageErrors = [];
  this.page.on('console', (message) => {
    if (message.type() === 'error') this.pageErrors.push(message.text());
  });
});

After(async function (scenario) {
  if (!this.page) return;
  await this.page.close();
});

AfterAll(async () => {
  if (!ui) return;
  await ui.browser.close();
  await new Promise((resolve) => ui.server.close(resolve));
  ui.backend.kill('SIGTERM');
  await new Promise((resolve) => {
    ui.backend.once('exit', resolve);
    setTimeout(resolve, 2000);
  });
  ui = null;
});
