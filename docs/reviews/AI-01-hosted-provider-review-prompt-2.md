# PR 1 implementation review — submission 2 of 7 (repair round 1)

## 1. Scope and prior verdict

**Slice:** PR 1 — hosted LLM capability and provider integration (RAG mission).
**Workstream:** A, with the shared integration owner for settings/docs.
**Base / branch:** `60dcc1fc5d0383b6011e7a97a3bf2a110984ff07` (`main`) /
`feat/30-hosted-ai-provider`. **GitHub authority:** local-only; no issue creation, push, PR, or
merge. **Proposed commit:** `feat(ai): [issue #30] add optional hosted AI provider boundary`
(body `Refs #30`).

**Prior verdict:** `docs/reviews/AI-01-hosted-provider-review.md` (sha256
`ea9119565b0b0d00922de19dba528d3d224d7362c0f278feadf94a14528f3308`) — **REQUEST_CHANGES**,
submission 1 of 7, session `01a1d3d2-52f6-78b3-861b-5c22926f382c`. The prior packet is
`docs/reviews/AI-01-hosted-provider-review-prompt.md` (sha256
`26733dbd222c71ce55ac250bb93449cca29650f367c373e135467734b89f047b`). The reviewer's full verdict,
including PR1-AC-1–3/7/8 support and the PR1-AC-4/5 failures, is retained there and not rewritten.

The served issue and premise correction are unchanged from submission 1: AI-01 #30 is closed; this
is a follow-up on its real-provider boundary, not a claim of its CandidateDiscovery scenarios or of
AI-02/AI-03/AI-05. M1's engineering gate is currently satisfied at `M1-review-2.md`; PR 1 does not
consume M1 graph semantics. PR 3 still needs PR 2 and a new story issue/feature; Test D waits for M2.

## 2. Repairs for PR1-R1…R4

| Finding | Severity | Repair | Regression / recheck |
| --- | --- | --- | --- |
| PR1-R1 | Major | `capabilities._sanitize_text` now replaces URL credentials/query and configured secrets in **every report string**, not only `_url` keys. `sanitize_url` handles malformed URLs. | `test_probe_sanitizes_urls_in_model_metadata` runs the complete probe with a credentialed `models.deployment_metadata.root` and a configured key; no password/query token/key remains. |
| PR1-R2 | Major | Embedding parsing distinguishes an absent `index` key from an invalid one. Supplied string, float, boolean, duplicate, or out-of-range indices raise `ProviderResponseError`; only a wholly unindexed response uses order. | `test_embedding_rejects_invalid_index_types` covers `"1"`/`"0"` and `True`/`False`. |
| PR1-R3 | Major | `deployment_identifiable` now requires the configured model to be found with catalogue metadata; unrelated catalogue entries do not identify the deployment. Chat/schema/embedding `observed_model` fields honor `model_observed` and stay `None` when the endpoint omitted the model. | `test_probe_does_not_claim_identity_from_an_unrelated_catalogue` asserts `configured_model_found=false`, `deployment_identifiable=false`, and both observed-model fields `null`. |
| PR1-R4 | Minor | Embedding numeric conversion rejects non-numeric, unrepresentable (`10**400`), and non-finite values as `ProviderResponseError` within the sanitized taxonomy. | `test_embedding_rejects_unrepresentable_numbers`. |

No acceptance criterion was weakened, no oracle changed, and no later-milestone behavior was added.

### Repair source excerpts

`backend/app/discovery/capabilities.py` (sanitizer):

```python
def sanitize_capability_report(value: Any, *, secrets: tuple[str | None, ...] = ()) -> Any:
    """Recursively remove credentials and URL credentials/query strings from a report."""
    if isinstance(value, dict):
        sanitized: dict[str, Any] = {}
        for key, item in value.items():
            lowered = str(key).lower()
            sensitive = lowered in {
                "api_key", "authorization", "password", "secret", "token", "access_token",
            } or lowered.endswith(("_api_key", "_secret", "_password"))
            if sensitive:
                sanitized[key] = "<redacted>" if item else item
            else:
                sanitized[key] = sanitize_capability_report(item, secrets=secrets)
        return sanitized
    if isinstance(value, list):
        return [sanitize_capability_report(item, secrets=secrets) for item in value]
    if isinstance(value, tuple):
        return tuple(sanitize_capability_report(item, secrets=secrets) for item in value)
    if isinstance(value, str):
        return _sanitize_text(value, secrets)
    return value


def _sanitize_text(value: str, secrets: tuple[str | None, ...]) -> str:
    """Remove URL credentials/query and known secret values from any report string."""
    without_credentials = _URL_PATTERN.sub(lambda match: sanitize_url(match.group(0)), value)
    return redact_secrets(without_credentials, secrets)
```

`backend/app/discovery/capabilities.py` (identity/provenance):

```python
report["deployment_identifiable"] = bool(
    observation["configured_model_found"] and observation["deployment_metadata"]
)
...
report["json_schema"] = {
    "supported": True,
    "http_status": structured.http_status,
    "observed_model": structured.model if structured.model_observed else None,
    "model_observed": structured.model_observed,
    "usage": _usage(structured),
    "parsed": structured.parsed,
}
```

`backend/app/discovery/ai_http.py` (embedding index and numeric validation):

```python
has_index_key = [isinstance(item, Mapping) and "index" in item for item in data]
if any(has_index_key) and not all(has_index_key):
    raise ProviderResponseError("embedding response mixes indexed and unindexed items", ...)
indices_present = all(has_index_key)
if indices_present:
    for item in data:
        index = item.get("index")
        if isinstance(index, bool) or not isinstance(index, int):
            raise ProviderResponseError("embedding index must be an integer", ...)
...
numbers: list[float] = []
for value in vector:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ProviderResponseError("embedding contains a non-numeric value", ...)
    try:
        number = float(value)
    except (OverflowError, ValueError):
        raise ProviderResponseError("embedding contains an unrepresentable numeric value", ...) from None
    if not math.isfinite(number):
        raise ProviderResponseError("embedding contains a non-finite value", ...)
    numbers.append(number)
floats = tuple(numbers)
```

`backend/app/discovery/ai.py` (`sanitize_url` now returns `<invalid-url>` for malformed input; the
URL regex is case-insensitive).

## 3. Snapshot manifest

The review checkout is the frozen working tree on the branch above. Hashes at freeze time:

```text
378ad3f6d3f10e17b3328fca0cdcb1cb08b07ca36c5034caf4fe4a17f346409c  backend/app/discovery/ai.py
abf4170c82603cd819df12f8fc7786aefaac9b7f551ddbc9b9ccca2098d09191  backend/app/discovery/ai_fake.py
f8e2586fa63e6dfd30058bcb09803888399911f570777741e19fb22cfa46aa15  backend/app/discovery/ai_http.py
b03f62addd45ef9c234636b45b36210230b9ffb3d207612c5dcca84e9b2e9651  backend/app/discovery/capabilities.py
bc2d1cf6d75f74e52651b9679e1c41bb68d9a76843bb52135cf0a61a4802a997  backend/app/discovery/__init__.py
7b4fa24de134806590a8cd8626df1a91c6a6b9b381fa85eee6138fefcfb9c57b  backend/app/discovery/registry.py
93a293342a93be9974b91ae40b1b02bf2b9c6f3a55fd871151961ff9aaf880f1  backend/app/settings.py
805b2fa79111e2b62c7f72b9eb1bd022dc0891f10ca4e9c4419d45b49af0b63d  backend/pyproject.toml
f772eacd36de7462b72903b33957d3ee0a23a3df75149f7db079281494213285  backend/tests/test_ai_providers.py
54fdfbce2c5a88a6d60dc21df0b58d4e0da6c0f81d498bee1d127e9bde3df2a5  backend/tests/test_live_provider_integration.py
02106d33af5d3c4de0549f9fc20ef8466ef19fd256a7cd7b7439b9c03c9d8e0e  backend/uv.lock
6ea728a0c4a49239d994d974992c879ab8ab8bfe724df2236b5d61642f128fba  docs/adr/0006-deferred-decisions.md
5d0fe19b897ae735b773798126ff78a662579c9a29924f4a81990b3ab625b9bb  docs/adr/0007-ai-provider-boundary.md
1901b10cab487887f258c6183cc9a7fed1b76314c6b9506fbfff70793029600d  docs/architecture.md
a1528bc342c142e9716771777d0fe1c81a3a6da363e7e38891683cacf1a195d7  docs/setup.md
7db53a935889aa68d8659ee8310fb8dde44eea0eac538f1a4f4e73bcd84db7e6  docs/stories/AI-01.feature
4ffc7b56168558fa0156e41a99c2290d09652813d2df0927f91e5b02357d60cc  docs/stories/AI-01.md
629c0ce8ba78446b09fbfcd9163070c730d26ce9e8c4708f66eb57703e22e7b8  tools/probe_ai_capabilities.py
```

Compared with submission 1, the review-relevant hashes changed for `ai.py`, `ai_http.py`,
`capabilities.py`, and `test_ai_providers.py`; `ai_fake.py`, settings, registry, docs, ADRs,
feature/companion, CLI, lockfile, and live test are unchanged. The cumulative diff remains
`git diff 60dcc1f -- . ':(exclude).gitignore'`; the previous packet's manifest remains the baseline
for verifying unchanged files. `.gitignore` is an unrelated pre-existing change and is excluded.

## 4. Evidence at the repair snapshot

```text
uv sync --project backend --frozen                       exit 0  (25 packages checked)
uv run --project backend pytest backend/tests -q         exit 0  277 passed, 2 skipped
unshare -rn backend/.venv/bin/python -m pytest -q        exit 0  277 passed, 2 skipped
  socket probe under the same namespace                  DENIED  OSError: [Errno 101] Network is unreachable
uv run --project backend python tools/fixturectl.py verify  exit 0  reproducible and current
uv run --project backend ruff check .                    exit 0
uv run --project backend ruff format --check .           exit 0  (57 files)
git diff --check                                         exit 0
probe_ai_capabilities.py (offline)                       exit 0  probed=false, mode=fake
probe_ai_capabilities.py --live (fake mode)              exit 2  expected refusal
```

Logs: `docs/reports/omp-rag-pr1/evidence/check-repair-*`. The two skipped tests are the opt-in live
integration tests. Hosted compatibility remains **NOT RUN**: no `CTA_AI_MODE`/`CTA_LLM_*`/
`CTA_EMBED_*` configuration was present. No endpoint was contacted.

The full PR1-AC-to-check map and dispositions are in
`docs/reports/omp-rag-pr1/IMPLEMENTATION.md`; the review-specific dispositions are also in the
round-1 record above. The reviewer may re-run the four regression selectors:

```text
backend/tests/test_ai_providers.py::test_probe_sanitizes_urls_in_model_metadata
backend/tests/test_ai_providers.py::test_probe_does_not_claim_identity_from_an_unrelated_catalogue
backend/tests/test_ai_providers.py::test_embedding_rejects_invalid_index_types
backend/tests/test_ai_providers.py::test_embedding_rejects_unrepresentable_numbers
```

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
findings stable by ID. Prior findings PR1-R1…R4 must be checked as closed, not renumbered.
