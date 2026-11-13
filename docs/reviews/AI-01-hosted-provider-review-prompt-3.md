# PR 1 implementation review — submission 3 of 7 (repair round 2)

## 1. Scope and prior verdicts

**Slice:** PR 1 — hosted LLM capability and provider integration (RAG mission).
**Base / branch:** `60dcc1fc5d0383b6011e7a97a3bf2a110984ff07` (`main`) /
`feat/30-hosted-ai-provider`. **GitHub authority:** local-only; no issue creation, push, PR, or
merge. **Proposed commit:** `feat(ai): [issue #30] add optional hosted AI provider boundary`
(body `Refs #30`).

**Prior verdicts:**

* Submission 1: `docs/reviews/AI-01-hosted-provider-review.md` (sha256
  `ea9119565b0b0d00922de19dba528d3d224d7362c0f278feadf94a14528f3308`) — **REQUEST_CHANGES**,
  PR1-R1…R4. Packet 1 sha256 `26733dbd222c71ce55ac250bb93449cca29650f367c373e135467734b89f047b`.
* Submission 2: `docs/reviews/AI-01-hosted-provider-review-2.md` (sha256
  `364df29aa08c076a23dd8f51159a0b4094f02518a7b59c2ce471f4d8f27d22c8`) — **REQUEST_CHANGES**,
  PR1-R1 remains open; PR1-R2/R3/R4 closed. Packet 2
  sha256 `02f3c22076216cc8d0dcff74d9daa03936fb07a18ec44edf8980c4db61135dee`.

The served issue, premise correction, and non-goals are unchanged: AI-01 #30 is closed; this is a
follow-up on its real-provider boundary, not a claim of its CandidateDiscovery scenarios or of
AI-02/AI-03/AI-05. M1's engineering gate is satisfied at `M1-review-2.md`; PR 1 does not consume M1
graph semantics. PR 3 still needs PR 2 and a new story issue/feature; Test D waits for M2.

## 2. Repair for the remaining PR1-R1 finding

The reviewer found two credential-redaction bypasses in submission 2:

1. Dynamic dictionary keys were not sanitized: a model URL used as a `models.context_lengths` key
   retained userinfo/query/configured key.
2. The offline CLI summary was printed without sanitization, so a credentialed `CTA_LLM_MODEL`
   appeared unchanged even though `probed=false`.

Repair:

* The report sanitizer now lives in `backend/app/discovery/ai.py`, which imports no `httpx`. It
  sanitizes **keys and values** recursively, with collision suffixes, and applies URL credential/
  query removal plus configured-secret replacement.
* `backend/app/discovery/capabilities.py` imports the sanitizer and applies it to the live report.
* `tools/probe_ai_capabilities.py` imports the same sanitizer and applies it to every output path
  (offline summary, live probe, stdout, and `--report`) before printing or writing.
* The fake-mode import path remains transport-free; a subprocess regression adds the CLI module to
  the existing registry import-isolation check.

### Repair source excerpts

`backend/app/discovery/ai.py`:

```python
def sanitize_capability_report(value: Any, *, secrets: Sequence[str | None] = ()) -> Any:
    """Recursively sanitize report values **and dynamic keys**."""
    if isinstance(value, dict):
        sanitized: dict[str, Any] = {}
        for key, item in value.items():
            sanitized_key = _sanitize_text(str(key), secrets)
            if sanitized_key in sanitized:
                suffix = 2
                candidate = f"{sanitized_key}#{suffix}"
                while candidate in sanitized:
                    suffix += 1
                    candidate = f"{sanitized_key}#{suffix}"
                sanitized_key = candidate
            lowered = str(key).lower()
            sensitive = lowered in {
                "api_key", "authorization", "password", "secret", "token", "access_token",
            } or lowered.endswith(("_api_key", "_secret", "_password"))
            if sensitive:
                sanitized[sanitized_key] = "<redacted>" if item else item
            else:
                sanitized[sanitized_key] = sanitize_capability_report(item, secrets=secrets)
        return sanitized
    if isinstance(value, list):
        return [sanitize_capability_report(item, secrets=secrets) for item in value]
    if isinstance(value, tuple):
        return tuple(sanitize_capability_report(item, secrets=secrets) for item in value)
    if isinstance(value, str):
        return _sanitize_text(value, secrets)
    return value
```

`tools/probe_ai_capabilities.py`:

```python
from app.discovery.ai import sanitize_capability_report
...
# Apply the same sanitizer to every output path, including the offline summary.
report = sanitize_capability_report(
    report, secrets=(settings.llm_api_key, settings.embed_api_key)
)
```

`backend/app/discovery/capabilities.py` now imports `sanitize_capability_report` from
`app.discovery.ai` and returns the sanitized live report; the local duplicate sanitizer was removed.

### Regression selectors

```text
backend/tests/test_ai_providers.py::test_probe_sanitizes_dynamic_model_id_keys
backend/tests/test_ai_providers.py::test_probe_cli_offline_sanitizes_model_credentials
backend/tests/test_ai_providers.py::test_sanitizer_redacts_dynamic_dictionary_keys
backend/tests/test_ai_providers.py::test_probe_cli_offline_import_does_not_import_the_transport
```

The first test runs the complete probe with a model ID of
`https://account:password@example.test/model?access_token=hidden&key=review-key` and
`max_model_len=4096`; it asserts the serialized report contains no password, query token, or
configured key. The second sets that URL as `CTA_LLM_MODEL` with the configured key and asserts the
offline CLI output is sanitized. The third exercises nested dynamic keys directly. The fourth
proves the offline CLI still imports no transport.

## 3. Snapshot manifest

```text
d18091c3648a0474ae3bc79c45cec22332f410aca8dbe77c1056f925049da4df  backend/app/discovery/ai.py
abf4170c82603cd819df12f8fc7786aefaac9b7f551ddbc9b9ccca2098d09191  backend/app/discovery/ai_fake.py
f8e2586fa63e6dfd30058bcb09803888399911f570777741e19fb22cfa46aa15  backend/app/discovery/ai_http.py
3f40164376d031b87b2254e51fae3123953aff8555809dc7465998724d4a7bd6  backend/app/discovery/capabilities.py
bc2d1cf6d75f74e52651b9679e1c41bb68d9a76843bb52135cf0a61a4802a997  backend/app/discovery/__init__.py
7b4fa24de134806590a8cd8626df1a91c6a6b9b381fa85eee6138fefcfb9c57b  backend/app/discovery/registry.py
93a293342a93be9974b91ae40b1b02bf2b9c6f3a55fd871151961ff9aaf880f1  backend/app/settings.py
805b2fa79111e2b62c7f72b9eb1bd022dc0891f10ca4e9c4419d45b49af0b63d  backend/pyproject.toml
c780473e37240c07a014bf2345f4e3e05bedae077f69fb362f05a4d7dd6cf71b  backend/tests/test_ai_providers.py
54fdfbce2c5a88a6d60dc21df0b58d4e0da6c0f81d498bee1d127e9bde3df2a5  backend/tests/test_live_provider_integration.py
02106d33af5d3c4de0549f9fc20ef8466ef19fd256a7cd7b7439b9c03c9d8e0e  backend/uv.lock
6ea728a0c4a49239d994d974992c879ab8ab8bfe724df2236b5d61642f128fba  docs/adr/0006-deferred-decisions.md
5d0fe19b897ae735b773798126ff78a662579c9a29924f4a81990b3ab625b9bb  docs/adr/0007-ai-provider-boundary.md
1901b10cab487887f258c6183cc9a7fed1b76314c6b9506fbfff70793029600d  docs/architecture.md
a1528bc342c142e9716771777d0fe1c81a3a6da363e7e38891683cacf1a195d7  docs/setup.md
7db53a935889aa68d8659ee8310fb8dde44eea0eac538f1a4f4e73bcd84db7e6  docs/stories/AI-01.feature
4ffc7b56168558fa0156e41a99c2290d09652813d2df0927f91e5b02357d60cc  docs/stories/AI-01.md
4762f0aaeb7e6189644eb43527bcdf5daba742929efdbd68f4df24218840e539  tools/probe_ai_capabilities.py
```

Compared with submission 2, only `ai.py`, `capabilities.py`, `test_ai_providers.py`, and the CLI
changed; all other hashes are unchanged. The cumulative diff remains
`git diff 60dcc1f -- . ':(exclude).gitignore'`. The prior review record for submission 2 is
included by reference and hash; its verdict is not rewritten. `.gitignore` is unrelated and
unmodified by this task.

## 4. Evidence at the repair snapshot

```text
uv sync --project backend --frozen                       exit 0  (25 packages checked)
uv run --project backend pytest backend/tests -q         exit 0  281 passed, 2 skipped
unshare -rn backend/.venv/bin/python -m pytest -q        exit 0  281 passed, 2 skipped
  socket probe under the same namespace                  DENIED  OSError: [Errno 101] Network is unreachable
uv run --project backend python tools/fixturectl.py verify  exit 0  reproducible and current
uv run --project backend ruff check .                    exit 0
uv run --project backend ruff format --check .           exit 0  (57 files)
git diff --check                                         exit 0
probe_ai_capabilities.py (offline)                       exit 0  probed=false, mode=fake
probe_ai_capabilities.py --live (fake mode)              exit 2  expected refusal
```

Logs: `docs/reports/omp-rag-pr1/evidence/check-repair-2-*` and
`capabilities/offline-summary.json`. The two skipped tests are the opt-in live integration tests.
Hosted compatibility remains **NOT RUN**: no `CTA_AI_MODE`/`CTA_LLM_*`/`CTA_EMBED_*` configuration
was present, and no endpoint was contacted.

## 5. Reviewer instructions

You are the independent CTA implementation reviewer using GPT-6.1 Sol high. Decide whether this
exact repaired snapshot satisfies the supplied mission slice, every applicable Gherkin criterion,
and the repository invariants. Treat OMP summaries and test results as claims to check against the
packet and targeted source inspection. Check proposal/accepted/evidence separation, no LLM authority
in deterministic assurance, revision and content-hash provenance, baseline and model isolation,
offline defaults, bounded retry/timeout and redaction behavior, untrusted-retrieved-text handling,
citation validation, honest 501/error behavior, independent oracle expectations, and generated-file
discipline. Do not demand implementation of a later milestone. Do not edit files, implement
repairs, regenerate fixtures, commit, or delegate. Ask OMP for missing runtime evidence;
distinguish observed defects from hypotheses. Return APPROVE, REQUEST_CHANGES, or NEEDS_INPUT with
findings stable by ID. PR1-R1 must be checked as closed; PR1-R2/R3/R4 remain closed and must not be
renumbered.
