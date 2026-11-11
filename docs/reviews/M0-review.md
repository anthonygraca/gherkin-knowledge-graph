# M0 independent review

## 1. Verdict

**M0 not verified** — the fixture store does not implement the shared `ArtifactRepository` contract required for independent workstream development.

Reviewed commit: `acf0738aa1ae91327bba433a80238d776a952343`. Environment: macOS arm64, Python 3.12.13, Git 2.54.0, uv 0.12.6. Findings below are **observed**, not suspected. Temporary checkouts and fixture copies were used for destructive probes; implementation changes were confined to a disposable clone for the mutation test. Output excerpts omit temporary absolute paths and the existing Starlette deprecation warning.

## 2. Findings

### R1 — Major: the mock repository cannot serve consumers of the shared port

Locations: `backend/app/domain/ports.py:53`, `backend/app/persistence/store.py:50`, `backend/app/persistence/store.py:62`, `backend/app/persistence/store.py:73`, `backend/app/persistence/store.py:76`, `backend/app/persistence/store.py:85`, `backend/app/persistence/store.py:88`, `backend/app/api/deps.py:23`.

Command executed:

```bash
uv run --project backend python - <<'PY'
from app.persistence.store import FixtureStore
from app.settings import load_settings
from app.domain.ports import ArtifactRepository
store = FixtureStore.from_settings(load_settings())
print('is ArtifactRepository:', isinstance(store, ArtifactRepository))
for method, args in [('get_artifact', ('REQ-001',)),
                     ('list_links', ('baseline-a',)),
                     ('changed_artifacts', ('baseline-b', 'baseline-a'))]:
    try:
        print(method, getattr(store, method)(*args))
    except AttributeError as e:
        print(type(e).__name__ + ': ' + str(e))
PY
```

Observed output:

```text
is ArtifactRepository: False
AttributeError: 'FixtureStore' object has no attribute 'get_artifact'
AttributeError: 'FixtureStore' object has no attribute 'list_links'
AttributeError: 'FixtureStore' object has no attribute 'changed_artifacts'
```

The port declares `resolve_baseline`, `get_artifact`, `list_artifacts`, `list_links`, `list_evidence`, and `changed_artifacts`. The store instead exposes `resolve`, `artifact`, `artifacts`, `links`, `evidence`, and `changed_artifact_ids`; its resolver also returns a snapshot rather than the port's declared string. Routes depend on the concrete store. Thus a C implementation written against the agreed port cannot use B's mock, despite `docs/architecture.md:23` saying implementations can be replaced without changing routes or contracts. This blocks the M0 independent-development exit condition.

Smallest acceptable fix: choose one repository method/signature contract, make `FixtureStore` satisfy it, and have consumers use it. Retain explicit fixture-only thread/sample interfaces where necessary; no real ingestion or database is required. Verify a consumer can fetch artifacts, links, evidence, and changed IDs through the port.

### R2 — Major: the thread response contract permits proposals inside `accepted_links`

Locations: `backend/app/domain/api.py:42`, `backend/app/persistence/store.py:101`. The snapshot has state checks in `backend/app/domain/oracle.py`'s `BaselineSnapshot`; the separately loaded `ThreadResponse` does not.

The following probe was executed together with R4's version probe, using a copied response directory:

```bash
uv run --project backend python - <<'PY'
import json, tempfile, shutil
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import create_app
from app.settings import Settings
from app.domain.api import ThreadResponse

root = Path.cwd()
client = TestClient(create_app())
thread = client.get('/api/threads/REQ-002?baseline=baseline-a').json()
thread['accepted_links'] = thread.pop('proposed_links')
thread['proposed_links'] = []
print('ThreadResponse accepts proposed LNK-007 in accepted_links:',
      ThreadResponse.model_validate(thread).accepted_links[0].review_state)
with tempfile.TemporaryDirectory(prefix='cta-m0-contract-') as d:
    fixtures = Path(d) / 'fixtures'
    shutil.copytree(root/'fixtures/api-responses', fixtures/'api-responses')
    shutil.copytree(root/'fixtures/banking-demo/expected',
                    fixtures/'banking-demo/expected')
    app = create_app(Settings(repo_root=root, fixtures_dir=fixtures))
    path = fixtures/'api-responses/threads/REQ-002.baseline-a.json'
    path.write_text(json.dumps(thread))
    c = TestClient(app)
    r = c.get('/api/threads/REQ-002?baseline=baseline-a')
    print('served proposed link through accepted_links:', r.status_code,
          r.json()['accepted_links'][0]['link_id'],
          r.json()['accepted_links'][0]['review_state'])
    for relative, url in [
        ('threads/REQ-001.baseline-a.json', '/api/threads/REQ-001?baseline=baseline-a'),
        ('findings.baseline-a.json', '/api/findings?baseline=baseline-a')]:
        path = fixtures/'api-responses'/relative
        data = json.loads(path.read_text())
        data['schema_version'] = '999.0.0'
        path.write_text(json.dumps(data))
        r = c.get(url)
        print('mismatched version', relative, '->',
              r.status_code, r.json().get('schema_version'))
PY
```

Observed output relevant to R2:

```text
ThreadResponse accepts proposed LNK-007 in accepted_links: proposed
served proposed link through accepted_links: 200 LNK-007 proposed
```

This does **not** demonstrate automatic approval by discovery: that attack failed, and the normal committed fixture keeps the arrays separate. It demonstrates that the public response model and HTTP loader accept a mispartitioned proposal. A consumer following the documented rule to traverse only `accepted_links` would treat it as an accepted edge. The normal drift check catches this file edit, but runtime schema validation does not enforce the advertised invariant.

Smallest acceptable fix: validate link states in `ThreadResponse` (or use appropriately constrained link types), rejecting any nonaccepted entry in `accepted_links` and accepted entry in `proposed_links`. Add a negative contract check at the loading boundary.

### R3 — Major: `verify` ignores a corrupted or deleted baseline manifest

Locations: `tools/fixturectl.py:573`, `tools/fixturectl.py:577`, `tools/fixturectl.py:643`; `backend/tests/test_fixture_drift.py:29`.

Command executed, using a copied tool and fixture tree so the real manifest remained unchanged:

```bash
uv run --project backend python - <<'PY'
from pathlib import Path
import tempfile, shutil, json, subprocess, sys
with tempfile.TemporaryDirectory(prefix='cta-m0-manifest-cli-') as d:
    root = Path(d)
    (root/'tools').mkdir()
    shutil.copy2('tools/fixturectl.py', root/'tools/fixturectl.py')
    shutil.copytree('fixtures', root/'fixtures',
                    ignore=shutil.ignore_patterns('.build', '__pycache__'))
    p = root/'fixtures/banking-demo/expected/baselines.json'
    data = json.loads(p.read_text())
    data['tags']['baseline-a'] = '0'*40
    p.write_text(json.dumps(data))
    for mode in ['tampered', 'deleted']:
        if mode == 'deleted':
            p.unlink()
        r = subprocess.run([sys.executable, str(root/'tools/fixturectl.py'), 'verify'],
                           text=True, capture_output=True)
        print(f'CLI manifest {mode}: exit={r.returncode}\n{r.stdout}{r.stderr}')
PY
```

Observed output:

```text
CLI manifest tampered: exit=0
fixture generation is reproducible and committed files are current (banking-demo)

CLI manifest deleted: exit=0
fixture generation is reproducible and committed files are current (banking-demo)
```

`compare_tree` enumerates `root.rglob('*.json')`, but `command_verify` passes two **file paths** for this comparison. Both enumerations are empty. Consequently the verification command gives a false success for a generated provenance file it claims to check. The full pytest suite has a separate manifest comparison and can catch this corruption; this finding concerns the independently documented/CI-invoked `verify` guard and its drift test's incomplete coverage.

Smallest acceptable fix: compare the manifest as a file, including explicit absence handling, and add tamper/delete probes for that manifest alongside the API-directory probes. Both should exit nonzero and name `baselines.json`.

### R4 — Minor: thread and findings loaders serve unsupported contract versions

Locations: `backend/app/persistence/store.py:111`, `backend/app/assurance/sample_findings.py:33`, `backend/app/assurance/sample_findings.py:40`, `docs/domain-contracts.md:6`.

The command in R2 produced:

```text
mismatched version threads/REQ-001.baseline-a.json -> 200 999.0.0
mismatched version findings.baseline-a.json -> 200 999.0.0
```

Only the files in the temporary response tree were changed. The snapshot still declared `0.1.0`. The runtime neither rejected the unsupported version nor reported a configuration error. This contradicts the documented promise that loaders reject version mismatches, and permits mixed-version responses during workstream integration. Snapshot and candidate-index checks do not cover these independent files.

Smallest acceptable fix: apply the same supported-version check to the thread and sample-findings loaders, returning the documented fixture error for mismatches, and exercise both negative paths.

### R5 — Minor: inherited Git object format changes every baseline SHA

Locations: `tools/fixturectl.py:78`, `tools/fixturectl.py:114`, `tools/fixturectl.py:199`.

Command executed:

```bash
uv run --project backend python - <<'PY'
import os, sys, tempfile, subprocess
from pathlib import Path
sys.path.insert(0, 'tools')
import fixturectl as f
with tempfile.TemporaryDirectory(prefix='cta-m0-repro-') as d:
    root = Path(d)
    first = f.build_repo(f.FIXTURE_DIR, root/'one')
    second = f.build_repo(f.FIXTURE_DIR, root/'two')
    print('different directories, all commits equal:', first == second)
    cfg = root/'global.gitconfig'
    subprocess.run(['git', 'config', '--file', str(cfg),
                    'commit.gpgsign', 'true'], check=True)
    os.environ.update({'GIT_CONFIG_GLOBAL': str(cfg), 'TZ': 'Pacific/Honolulu'})
    third = f.build_repo(f.FIXTURE_DIR, root/'signed-tz')
    print('global commit.gpgsign=true + TZ=Pacific/Honolulu, all commits equal:',
          first == third)
    os.environ['GIT_DEFAULT_HASH'] = 'sha256'
    fourth = f.build_repo(f.FIXTURE_DIR, root/'sha256')
    print('GIT_DEFAULT_HASH=sha256, tags equal:', first.tags == fourth.tags)
    print('default tags:', first.tags)
    print('sha256 tags:', fourth.tags)
PY
```

Observed output:

```text
different directories, all commits equal: True
global commit.gpgsign=true + TZ=Pacific/Honolulu, all commits equal: True
GIT_DEFAULT_HASH=sha256, tags equal: False
default tags: {'baseline-a': '67109fac965377629c9ab5835541aa64461db785', 'baseline-b': 'c02064fed61bcfc6ade5ea14ac62f9eb1b5f5c54'}
sha256 tags: {'baseline-a': '44ac9e4c4ee93bcb34e1853ea6620276c23b651d5634eab8128236a8f4ebbfef', 'baseline-b': 'c6af1addfd360e770d2c035ecee78e26f84de3fedb08845eb3a78dc854ce9ba3'}
```

The global signing setting was provided through an isolated global-config file; the user's actual global configuration was not changed. The signing/timezone attack failed. The object-format attack succeeded because the generator inherits this environment variable and does not pin the format at `git init`. Repeated builds in a fixed environment remain deterministic; the stronger cross-environment SHA claim does not hold.

Smallest acceptable fix: explicitly initialize the fixture repository with the chosen object format and cover the alternate environment setting. Continue using the committed SHA-1 manifest unless deliberately migrating its contract.

### R6 — Minor: fingerprint expectations can change with the implementation and still pass

Locations: `backend/tests/test_api_contract.py:192`, `backend/tests/test_domain_contracts.py:206`, `backend/tests/test_domain_contracts.py:227`, `backend/app/domain/models.py:198`.

Command executed in a disposable clone:

```bash
uv run --project backend python - <<'PY'
import tempfile, subprocess
from pathlib import Path
with tempfile.TemporaryDirectory(prefix='cta-m0-fingerprint-mutation-') as d:
    clone = Path(d)/'clone'
    subprocess.run(['git', 'clone', '--quiet', '--no-hardlinks', '.', str(clone)],
                   check=True)
    p = clone/'backend/app/domain/models.py'
    text = p.read_text()
    assert 'hashlib.sha256(payload.encode' in text
    p.write_text(text.replace('hashlib.sha256(payload.encode',
                              'hashlib.sha1(payload.encode'))
    for cmd in [
        ['uv', 'sync', '--offline', '--frozen', '--project', 'backend'],
        ['uv', 'run', '--offline', '--project', 'backend', 'python',
         'tools/fixturectl.py', 'all'],
        ['uv', 'run', '--offline', '--project', 'backend', 'pytest',
         'backend/tests', '-q']]:
        r = subprocess.run(cmd, cwd=clone, text=True, capture_output=True)
        print('$ ' + ' '.join(cmd) + '\n' + r.stdout + f'exit={r.returncode}')
        if r.returncode:
            print(r.stderr)
            break
PY
```

Observed output excerpts:

```text
$ uv run --offline --project backend python tools/fixturectl.py all
wrote fixtures/api-responses/findings.baseline-a.json
wrote fixtures/api-responses/findings.baseline-b.json
2 generated file(s) changed
exit=0
$ uv run --offline --project backend pytest backend/tests -q
92 passed, 1 warning in 5.11s
exit=0
```

This mutation violates the documented SHA-256 fingerprint contract without changing the schema version. The test obtains its expected fingerprint from the same production helper that materializes the sample, while the remaining tests check properties that SHA-1 also satisfies. Regeneration is a normal documented workflow, so the drift guard does not provide an independent fingerprint expectation. Current fingerprints were independently recomputed and are correct; the observed defect is the regression protection, not current IDs. Oracle checks for finding types, artifact/evidence membership, and healthy `REQ-001` are separate and were not defeated by this mutation.

Smallest acceptable fix: add at least one independently calculated, fixed fingerprint vector with duplicate/out-of-order IDs. The expected value must not come from `finding_fingerprint` or regenerated responses. The mutation above should then fail.

### R7 — Minor: the committed review instructions' direct fixture-test command fails collection

Location: `docs/reviews/M0-review-prompt.md:64`; fixture import setup: `fixtures/banking-demo/tree/conftest.py:1`.

Executed the prompt's invocation pattern from the outer repository, against detached temporary worktrees:

```bash
backend/.venv/bin/python -m pytest -q <baseline-a-worktree>/tests
backend/.venv/bin/python -m pytest -q <baseline-b-worktree>/tests
```

Both returned exit 2, with these output excerpts:

```text
ERROR collecting test_accounts.py
E   ModuleNotFoundError: No module named 'src'
ERROR collecting test_transfers.py
E   ModuleNotFoundError: No module named 'src'
2 errors during collection
```

Running the same environment's interpreter **with the worktree as cwd**, as the backend helper does, produced:

```text
(cd baseline-a && python -m pytest -q --tb=short) exit=0
5 passed in 0.01s
(cd baseline-b && python -m pytest -q --tb=short) exit=1
FAILED tests/test_accounts.py::test_withdraw_allows_fractional_amounts
FAILED tests/test_transfers.py::test_transfer_exactly_at_limit_is_permitted
2 failed, 4 passed in 0.03s
```

The advertised independent verification command therefore fails before checking its claimed outcomes. This does not invalidate AC-1.8: the corrected invocation reproduces it. Smallest acceptable fix: document execution from each worktree with an absolute backend interpreter path, or otherwise ensure that invocation loads the fixture root's import setup.

## 3. Unverified claims

- **Human labeling/review.** `git log --format='%h %an <%ae> %s' -- fixtures/banking-demo/expected` returned `9b21835 Anthony Graca <anthonygraca@protonmail.com> feat(fixtures): reproducible banking-demo baselines with hand-labeled oracle`. That establishes recorded authorship, not that a human independently labeled or reviewed the oracle. The generator reads baseline/candidate labels and writes derived responses, but no authenticated human review was established. A human attestation or linked review of the label files is needed; neither prose nor the Git author field proves it.
- **General staleness/failure classification for new inputs.** The current fixture's `REQ-001` case was verified, including absence of a later recorded failing run. `POST /api/assurance/evaluate` returns 501, so there is no general evaluator to adversarially exercise with new evidence sequences. M2 rule implementation and counterexample tests will be needed. No claim is made here that arbitrary stale evidence is correctly classified.
- **Hosted Linux CI and other machines/Git versions.** A fresh local clone passed installation from the existing dependency cache, verification, tests, and the exact root lint/format commands. GitHub Actions itself, its action downloads, a cold dependency install, and a Linux runner were not executed. Those require a hosted run or equivalent runner. Cross-environment reproducibility is already limited by R5.
- **Arbitrary future providers.** Current fake-provider calls preserved thread bytes and rejected acceptance fields. A Python protocol is not a capability sandbox for future plugins; universal absence of side effects cannot be established from this implementation.

## 4. Falsification attempts that failed

The following are failed attempts to falsify specific behavior, with command/output evidence. Findings above identify the portions of the broader claims that did fail review.

- **Default setup/tests:** `uv sync --project backend` → `Resolved 25 packages in 4ms; Checked 24 packages in 5ms`; `uv run --project backend pytest backend/tests -q` → `92 passed, 1 warning in 5.53s`.
- **Network dependency:** `sandbox-exec -p '(version 1) (allow default) (deny network*)' uv run --offline --project backend pytest backend/tests -q` → `92 passed, 1 warning in 6.07s`; under the same profile, `socket.create_connection(('127.0.0.1', 8011), timeout=1)` → `PermissionError: [Errno 1] Operation not permitted`, confirming the network denial was effective.
- **Normal drift verification:** `uv run --project backend python tools/fixturectl.py verify` → exit 0, `fixture generation is reproducible and committed files are current (banking-demo)`; manifest exceptions are R3.
- **Default history nondeterminism:** two consecutive `uv run --project backend python tools/fixturectl.py build` calls printed the same four SHA prefixes and `(unchanged)` manifest; the different-directory/signing/timezone probe in R5 also compared all four full commit records equal.
- **API-file drift bypass:** copied `fixtures/api-responses`, changed `reverification_required` to `verification_failed` in `findings.baseline-b.json`, then ran `uv run --project backend python tools/fixturectl.py verify --api-dir <copy>` → exit 1, `out of date: .../findings.baseline-b.json`, with `fixturectl.py all` instructions; deleting that file instead → exit 1, `missing from the repository: .../findings.baseline-b.json`.
- **Candidate acceptance fields:** `TraceCandidate.model_validate({**candidate, 'review_state':'accepted', 'link_id':'LNK-999'})` → validation errors at `('review_state',)` and `('link_id',)`; five HTTP discovery calls for `REQ-002` left its thread response byte-identical. R2 concerns the separate thread envelope.
- **Hidden success/write endpoints:** live `GET /openapi.json` enumerated just four POST surfaces: discovery and the three `contract-only` routes; valid ingestion/review/evaluation requests returned 501, and their empty bodies returned 422 `request-validation`.
- **False failure for changed withdrawal code:** live `GET /api/findings?baseline=baseline-a` had no `REQ-001` finding; baseline B had only `('reverification_required', ['EV-001'])` for that requirement. `GET /api/threads/REQ-001?baseline=baseline-b` exposed only `EV-001`, `passed`, tested at `81efe21a8ffd25243cb67485ede76d3be3fd7d24` for `SCN-001`.
- **Fabricated transfer failure:** the worktree suites produced the exact outcomes in R7. The transfer traceback reached `src/transfers.py:27`; the `>=` condition is at `fixtures/banking-demo/tree/src/transfers.py:26`. Reading the generated snapshot printed `EV-003: {'test_id':'TEST-002', 'scenario_id':'SCN-003', 'result':'failed', 'tested_commit':'812256f7e959231a53ae1827a126e42a987fa4c2'}`. `git show <tested_commit>:<path>` versus `git show baseline-b:<path>` compared equal for the transfer source, test, feature, and `REQ-003`. Accepted links printed `REQ-003 verified_by SCN-003`, `SCN-003 implemented_by CODE-002`, `SCN-003 exercised_by TEST-002`.
- **Current fingerprint/pinning mismatch:** a standalone HTTP-check script calculated `FND-` plus `hashlib.sha256('|'.join([rule_id, finding_type, ','.join(sorted(set(artifact_ids)))]).encode()).hexdigest()[:16]`, without calling the app helper; every current finding matched, every evaluated baseline matched its manifest SHA, and all four baseline-A IDs persisted at B. Regression-test limitation: R6.
- **Tag/SHA addressing mismatch:** live HTTP byte comparisons for artifacts, threads, and findings, at both tags and their full SHAs, all returned `True`/200. Unknown baseline → `404 baseline-not-found`; malformed artifact → `422 request-validation`; `REQ-999` → `404 artifact-not-found`; known `CODE-001` thread → `404 thread-not-found`.
- **Dishonest contract-only problems:** `curl -s -X POST localhost:8011/api/assurance/evaluate -H 'content-type: application/json' -d '{"baseline":"baseline-a"}' -i` → `HTTP/1.1 501 Not Implemented`, `not-implemented`, story `AS-01, AS-02, AS-03 (C-PR1)`, milestone `M1/M2`; equivalent ingestion/review probes named `DT-01, DT-02, DT-04 (B-PR1)`/`M1` and `AS-06 (C-PR1 onward)`/`M1/M2`.
- **API-example mismatch:** parsed the JSON blocks in `docs/api-contracts.md` and compared the health, baseline-A artifact, discovery's first candidate, and assurance-501 examples with live HTTP JSON → `True` for all four. R1/R4 identify other documentation guarantees that do not hold.
- **Empty packages/hidden remote clients:** scanned `backend/app`, `tools`, and dependencies with `rg -n 'TODO|FIXME|NotImplemented|pass$|\.\.\.$|requests|httpx|urllib|socket|sentence_transformers|torch|vllm|https?://' ...`; hits were declared protocol methods, explicit 501 handling, explanatory text, and the dev-only `httpx` dependency. A Python scan reported `empty Python source files: []`. The unusable shared port is R1; no additional hidden-success stub was observed.
- **Missing recent commit trailers:** ran `git log --format=%B -n 5 | git interpret-trailers --parse`, then parsed each commit separately (the piped multi-message command alone exposes only the last trailer block). `acf0738`, `d2c07fb`, `0afc504`, `8fe3f60`, and `9b21835` each printed `Story present: True` with roadmap/platform IDs.
- **Lint/format failure:** `uv run --project backend ruff check backend/app backend/tests tools` → `All checks passed!`; `uv run --project backend ruff format --check backend/app backend/tests tools` → `32 files already formatted`.
- **Clean-checkout failure:** `git clone --quiet --no-hardlinks . <temporary-clone>`, then within it `uv sync --project backend --frozen --offline` → installed 24 packages/exit 0; `uv run --offline --project backend python tools/fixturectl.py verify` → exit 0; `uv run --offline --project backend pytest backend/tests -q` → `92 passed, 1 warning in 5.83s`; root `ruff check .` → `All checks passed!`; root `ruff format --check .` → `49 files already formatted`. This covers local clean-checkout behavior, not a hosted workflow run.

The four full fixture commit SHAs observed after both default builds (`git -C fixtures/banking-demo/.build/repo log --format='%H %s' --reverse`) were:

```text
81efe21a8ffd25243cb67485ede76d3be3fd7d24 Add banking demo sources for baseline A
67109fac965377629c9ab5835541aa64461db785 Record baseline A verification evidence
812256f7e959231a53ae1827a126e42a987fa4c2 Require whole-dollar withdrawals and cover the at-limit transfer boundary
c02064fed61bcfc6ade5ea14ac62f9eb1b5f5c54 Record baseline B verification evidence
```

## 5. Recommendation

**M1 should not start while the major M0 contract/verification findings remain.** The first single change should reconcile `ArtifactRepository` and `FixtureStore` (R1), proving that an independently written consumer can use the mock through the shared port. Then recheck the remaining major findings before declaring the M0 exit gate satisfied. No implementation fixes were made in this review.
