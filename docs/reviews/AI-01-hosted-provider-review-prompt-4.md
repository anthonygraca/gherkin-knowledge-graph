# PR 1 implementation review — submission 4 of 7 (repair round 3)

## 1. Scope and prior verdicts

**Slice:** PR 1 — hosted LLM capability and provider integration (RAG mission).
**Base / branch:** `60dcc1fc5d0383b6011e7a97a3bf2a110984ff07` (`main`) /
`feat/30-hosted-ai-provider`. **GitHub authority:** local-only; no issue creation, push, PR, or
merge. **Proposed commit:** `feat(ai): [issue #30] add optional hosted AI provider boundary`
(body `Refs #30`).

**Prior verdicts:**

* Submission 1: `AI-01-hosted-provider-review.md` (sha256 `ea9119565b0b0d00922de19dba528d3d224d7362c0f278feadf94a14528f3308`) — **REQUEST_CHANGES**, PR1-R1…R4.
* Submission 2: `AI-01-hosted-provider-review-2.md` (sha256 `364df29aa08c076a23dd8f51159a0b4094f02518a7b59c2ce471f4d8f27d22c8`) — **REQUEST_CHANGES**, PR1-R1 open; R2/R3/R4 closed.
* Submission 3: `AI-01-hosted-provider-review-3.md` (sha256 `207348a8aacae2a035cb73ee80e31149aa9084dc0fb0c7eefa2a730640b5c174`) — **REQUEST_CHANGES**, PR1-R1 open (fake-mode/report returns); PR1-R5 new (logging credentials); R2/R3/R4 remain closed.

The served issue, premise correction, and non-goals are unchanged: AI-01 #30 is closed; this is a
follow-up on its real-provider boundary, not a claim of its CandidateDiscovery scenarios or of
AI-02/AI-03/AI-05. M1's engineering gate is satisfied at `M1-review-2.md`; PR 1 does not consume M1
graph semantics. PR 3 still needs PR 2 and a new story issue/feature; Test D waits for M2.

## 2. Repairs for PR1-R1 and PR1-R5

**PR1-R1 — report-return paths.** The fake-mode return of `probe_capabilities` and the public
`offline_summary` helper bypassed sanitization. Repair:

* `_base_summary` sanitizes at construction.
* The fake-mode `probe_capabilities` return sanitizes.
* `offline_summary` sanitizes before returning.
* The CLI's `_offline_summary` sanitizes at construction; the CLI also sanitizes every output path
  (offline/live, stdout/`--report`).

**PR1-R5 — logging URLs.** `_log` replaced configured secrets but kept URL userinfo/query. Repair:

* `ai_http._log` applies `sanitize_text` (URL credential/query removal + configured-secret
  replacement) to every logged field.
* Upstream error codes use the same sanitizer.
* The URL-safe sanitizer lives in `app/discovery/ai.py` (no `httpx` import) and is shared by the
  report, CLI, and logging paths.

### Repair source excerpts

`backend/app/discovery/ai.py`:

```python
def sanitize_text(value: str, secrets: Sequence[str | None] = ()) -> str:
    """Remove URL credentials/query and known secret values from arbitrary text."""
    without_credentials = _URL_PATTERN.sub(lambda match: sanitize_url(match.group(0)), value)
    return redact_secrets(without_credentials, secrets)
```

`backend/app/discovery/ai_http.py`:

```python
safe = {key: sanitize_text(str(value), self._secrets) for key, value in fields.items()}
...
upstream = parse_upstream_code(payload)
upstream = sanitize_text(upstream, self._secrets) if upstream else None
```

`backend/app/discovery/capabilities.py`:

```python
def _base_summary(settings: Settings) -> dict[str, Any]:
    summary = {...}
    return sanitize_capability_report(
        summary, secrets=(settings.llm_api_key, settings.embed_api_key)
    )

def offline_summary(settings: Settings, *, reason: str) -> dict[str, Any]:
    ...
    return sanitize_capability_report(
        summary, secrets=(settings.llm_api_key, settings.embed_api_key)
    )

if settings.ai_mode != "live":
    ...
    return sanitize_capability_report(
        report, secrets=(settings.llm_api_key, settings.embed_api_key)
    )
```

`tools/probe_ai_capabilities.py` also sanitizes `_offline_summary` at construction and the final
report before every print/write.

### Regression selectors

```text
backend/tests/test_ai_providers.py::test_fake_mode_probe_report_is_sanitized
backend/tests/test_ai_providers.py::test_offline_summary_is_sanitized
backend/tests/test_ai_providers.py::test_logs_sanitize_url_credentials  # 200 and 401
```

The fake-mode tests use a configured model URL containing `account:password` and
`access_token=hidden&key=review-key` with `ai_mode="fake"`; the serialized report must contain none of
them. The logging tests inject a logger on both a successful completion and a 401; the captured log
must contain no password, query token, or configured key.

## 3. Snapshot manifest

```text
e4c4246eedd363f76299bedec9e49ecaf6b1ecaa47a028293a1829796547d0d8  backend/app/discovery/ai.py
abf4170c82603cd819df12f8fc7786aefaac9b7f551ddbc9b9ccca2098d09191  backend/app/discovery/ai_fake.py
3ad0e0c62085de0ae084074f2e291f41f9d85b61bde902d015d820dbac8a818b  backend/app/discovery/ai_http.py
2207cd5e4a025e858c32d543f006c274342bfcf73d9afc641b0415a1b30f2ab3  backend/app/discovery/capabilities.py
bc2d1cf6d75f74e52651b9679e1c41bb68d9a76843bb52135cf0a61a4802a997  backend/app/discovery/__init__.py
7b4fa24de134806590a8cd8626df1a91c6a6b9b381fa85eee6138fefcfb9c57b  backend/app/discovery/registry.py
93a293342a93be9974b91ae40b1b02bf2b9c6f3a55fd871151961ff9aaf880f1  backend/app/settings.py
805b2fa79111e2b62c7f72b9eb1bd022dc0891f10ca4e9c4419d45b49af0b63d  backend/pyproject.toml
d2acd9c9398df945cde02915fc4bd284e21f76ca5d5a51d0ebb1b6922c19994d  backend/tests/test_ai_providers.py
54fdfbce2c5a88a6d60dc21df0b58d4e0da6c0f81d498bee1d127e9bde3df2a5  backend/tests/test_live_provider_integration.py
02106d33af5d3c4de0549f9fc20ef8466ef19fd256a7cd7b7439b9c03c9d8e0e  backend/uv.lock
6ea728a0c4a49239d994d974992c879ab8ab8bfe724df2236b5d61642f128fba  docs/adr/0006-deferred-decisions.md
5d0fe19b897ae735b773798126ff78a662579c9a29924f4a81990b3ab625b9bb  docs/adr/0007-ai-provider-boundary.md
1901b10cab487887f258c6183cc9a7fed1b76314c6b9506fbfff70793029600d  docs/architecture.md
a1528bc342c142e9716771777d0fe1c81a3a6da363e7e38891683cacf1a195d7  docs/setup.md
7db53a935889aa68d8659ee8310fb8dde44eea0eac538f1a4f4e73bcd84db7e6  docs/stories/AI-01.feature
4ffc7b56168558fa0156e41a99c2290d09652813d2df0927f91e5b02357d60cc  docs/stories/AI-01.md
5e29bbc004de6110f13339b87e8dfc7b94ab31a5a42ccc4f2093b294b0039e58  tools/probe_ai_capabilities.py
```

Compared with submission 3, only `ai.py`, `ai_http.py`, `capabilities.py`, `test_ai_providers.py`,
and the CLI changed; all other hashes are unchanged. The cumulative diff remains
`git diff 60dcc1f -- . ':(exclude).gitignore'`. `.gitignore` is unrelated and unmodified by this
task. Prior review records are included by reference and hash; their verdicts are not rewritten.

## 4. Evidence at the repair snapshot

```text
uv sync --project backend --frozen                       exit 0  (25 packages checked)
uv run --project backend pytest backend/tests -q         exit 0  285 passed, 2 skipped
unshare -rn backend/.venv/bin/python -m pytest -q        exit 0  285 passed, 2 skipped
  socket probe under the same namespace                  DENIED  OSError: [Errno 101] Network is unreachable
uv run --project backend python tools/fixturectl.py verify  exit 0  reproducible and current
uv run --project backend ruff check .                    exit 0
uv run --project backend ruff format --check .           exit 0  (57 files)
git diff --check                                         exit 0
probe_ai_capabilities.py (offline)                       exit 0  probed=false, mode=fake, sanitized
probe_ai_capabilities.py --live (fake mode)              exit 2  expected refusal
```

Logs: `docs/reports/omp-rag-pr1/evidence/check-repair-3-*` and
`capabilities/offline-summary.json`. The two skipped tests are the opt-in live integration tests.
Hosted compatibility remains **NOT RUN**: no `CTA_AI_MODE`/`CTA_LLM_*`/`CTA_EMBED_*` configuration
was present, and no endpoint was contacted.

## 5. Reviewer instructions

You are the independent CTA implementation reviewer using GPT-6.1 Sol high. Decide whether this exact
repaired snapshot satisfies the supplied mission slice, every applicable Gherkin criterion, and the
repository invariants. Treat OMP summaries and test results as claims to check against the packet and
targeted source inspection. Check proposal/accepted/evidence separation, no LLM authority in
deterministic assurance, revision and content-hash provenance, baseline and model isolation, offline
defaults, bounded retry/timeout and redaction behavior, untrusted-retrieved-text handling, citation
validation, honest 501/error behavior, independent oracle expectations, and generated-file
discipline. Do not demand implementation of a later milestone. Do not edit files, implement repairs,
regenerate fixtures, commit, or delegate. Ask OMP for missing runtime evidence; distinguish observed
defects from hypotheses. Return APPROVE, REQUEST_CHANGES, or NEEDS_INPUT with findings stable by ID.
PR1-R1 and PR1-R5 must be checked as closed; PR1-R2/R3/R4 remain closed and must not be renumbered.
