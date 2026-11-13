# PR 1 implementation review — submission 1 of 7

## 1. Scope, story, and traceability

**Slice:** PR 1 — hosted LLM capability and provider integration (RAG mission).
**Workstream:** A (semantic discovery/provider behavior), with the shared integration owner for
settings and docs.
**Milestone ceiling:** M3 for PR 1–PR 3. PR 1 implements no M2 deterministic assurance and does not
close M4.
**Repository:** `anthonygraca/gherkin-knowledge-graph`; `origin` verified
`git@github.com:anthonygraca/gherkin-knowledge-graph.git` at 2026-11-13T07:24:33Z.
**Base / branch:** `60dcc1fc5d0383b6011e7a97a3bf2a110984ff07` (`main`) /
`feat/30-hosted-ai-provider`.
**GitHub authority:** local-only. Read issues/PRs/checks; local branch/commit/publication text.
No issue creation, push, PR, or merge was performed.
**Proposed commit:** `feat(ai): [issue #30] add optional hosted AI provider boundary`
(body: why, then `Refs #30`).

### Served issue and scope disposition

AI-01 ([#30](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/30), **closed**) is the
provider-boundary story. Its closure record in `docs/STATUS.md` says the real `CandidateDiscovery`
adapter is a later story. This slice is a **follow-up on AI-01's real-provider boundary**: one typed
interface with fake and real adapters, explicit configuration, and no model in the default path.
It does **not** deliver a real `CandidateDiscovery`, does **not** claim AI-01's two
CandidateDiscovery scenarios, and does **not** close AI-02 (#31), AI-03 (#32), or AI-05 (#35).

The canonical extraction of AI-01's closed criteria is `docs/stories/AI-01.feature`
(sha256 `7db53a935889aa68d8659ee8310fb8dde44eea0eac538f1a4f4e73bcd84db7e6`); its companion
`docs/stories/AI-01.md` records the scope and the existing-test mapping. The PR 1 acceptance slice
is the mission's PR 1 deliverable, expanded into the `PR1-AC` table below. No new GitHub issue was
created because the run holds local-only authority; the report records the prepared child-task
title if the owner wants one.

### M1 premise correction

The mission brief says M1 "has been completed and independently reviewed." At the prompt's
creation this was not true: `docs/reviews/M1-review-attempt-1.md` records an infrastructure failure
with no verdict (workspace out of credits), and the gate was `NOT SATISFIED`. Current records at
invocation differ: `docs/reviews/M1-review-2.md` (sha256
`14a2442c1ce17279e951301034a50f0aef5cda162e357fa9e262abd8837bc6d2`) records **APPROVE** at
`e1497cf`, submission 2 of 7; all 40 M1 criteria and the engineering exit PASS, no open major
finding. `docs/STATUS.md` records the gate **SATISFIED** and the approval merged through
`c8390a6`; current `main` was `60dcc1f` at invocation. The approval covers the M1 engineering gate
only. PR 1 proceeds under the roadmap's post-M0 parallel allowance and does not consume M1 graph
semantics. PR 3/GraphRAG still needs PR 2 and a new story issue/feature; Test D waits for M2.

## 2. Applicable acceptance

### AI-01 canonical feature (context; not claimed by this slice)

```gherkin
# Canonical acceptance specification for AI-01, extracted unchanged from issue #30.
# AI-01 was closed with the fake-provider slice; the real CandidateDiscovery adapter remains
# a later story. PR 1 serves the provider boundary and does not claim these scenarios.
# They are verified by the mapped pytest checks in AI-01.md; no Gherkin runner is configured.
@AI-01 @issue-30 @M0
Feature: AI-01: Fake and real CandidateDiscovery implementations behind one interface
  As a developer, I want fake and real CandidateDiscovery implementations behind one
  interface, so that domain work never depends on a model being available.

  @SCN-901
  Scenario: One contract, interchangeable adapters
    Given the "fake" provider and any future local provider
    When the shared contract tests run against a provider
    Then it returns ranked candidates whose source_id is the requested artifact
    And it reports the provider name, model version, and index revision
    And it exposes no way to accept, store, or verify a link

  @SCN-902
  Scenario: Provider configuration is explicit
    Given an unknown provider name
    When candidates are requested
    Then the request fails with "provider-not-registered"
    And the response lists the registered providers
```

SCN-901/902 are **not** satisfied or exercised by PR 1: it adds chat/embedding providers, not a
real `CandidateDiscovery`. Their mapped fake-provider checks are recorded in `AI-01.md`.

### PR 1 slice acceptance (`PR1-AC`)

| ID | Observable requirement |
| --- | --- |
| PR1-AC-1 | Existing application and offline suite run with no AI configuration; fake providers are the default; fake mode does not import the HTTP transport. |
| PR1-AC-2 | Settings read the mission environment names, default offline, validate required combinations at construction, and never render keys. |
| PR1-AC-3 | Real chat adapter has explicit timeout, bounded retry, Retry-After handling, schema validation, error taxonomy, and safe logging. |
| PR1-AC-4 | Separate real embedding adapter validates vector shape/dimension, rejects chat-shaped output, and is unavailable when not configured; no substitution. |
| PR1-AC-5 | Probe CLI reports configuration without contact; `--live` is explicit; it reports the required capability fields with synthetic canary text and sanitizes/refuses in-repo reports. |
| PR1-AC-6 | Offline contract tests cover fake/real adapters and provider failure classes; live integration is opt-in and skips by default; the default suite needs no network. |
| PR1-AC-7 | ADR and docs cover interface, configuration, timeout/retry, data handling, redaction, optionality; no API/schema/assurance change. |
| PR1-AC-8 | Traceability and publication state are recorded; the slice does not claim a later story, milestone closure, or hosted inference. |

**Environmental limits.** Live provider configuration was absent at invocation; the hosted path is
`NOT RUN`. The reviewer must not treat mocked transport tests as a live compatibility claim. The
default suite must remain offline; a network-denied run is supplied.

## 3. Snapshot and manifest

The review checkout is the frozen working tree on `feat/30-hosted-ai-provider` above the base
commit. The task files and content hashes at freeze time are:

```text
bc2d1cf6d75f74e52651b9679e1c41bb68d9a76843bb52135cf0a61a4802a997  backend/app/discovery/__init__.py
d5060e74da2b2c84e883994e1db8fb3030c4087c5e5be1b40c29210ee9cf5d61  backend/app/discovery/ai.py
abf4170c82603cd819df12f8fc7786aefaac9b7f551ddbc9b9ccca2098d09191  backend/app/discovery/ai_fake.py
837e64751b117faec303a05ff0bedb014efcc3c65c4553c5beb92d112bdad3fb  backend/app/discovery/ai_http.py
1e5810f8349e57cb5daddbb448510cbd0d573fe681fd3882c4a7a740124dd257  backend/app/discovery/capabilities.py
7b4fa24de134806590a8cd8626df1a91c6a6b9b381fa85eee6138fefcfb9c57b  backend/app/discovery/registry.py
93a293342a93be9974b91ae40b1b02bf2b9c6f3a55fd871151961ff9aaf880f1  backend/app/settings.py
805b2fa79111e2b62c7f72b9eb1bd022dc0891f10ca4e9c4419d45b49af0b63d  backend/pyproject.toml
87b5f9547c80f19bd47775fa18a8cdb4225df4c6b9c4b5bc6f8576d5d0220c14  backend/tests/test_ai_providers.py
54fdfbce2c5a88a6d60dc21df0b58d4e0da6c0f81d498bee1d127e9bde3df2a5  backend/tests/test_live_provider_integration.py
02106d33af5d3c4de0549f9fc20ef8466ef19fd256a7cd7b7439b9c03c9d8e0e  backend/uv.lock
6ea728a0c4a49239d994d974992c879ab8ab8bfe724df2236b5d61642f128fba  docs/adr/0006-deferred-decisions.md
5d0fe19b897ae735b773798126ff78a662579c9a29924f4a81990b3ab625b9bb  docs/adr/0007-ai-provider-boundary.md
1901b10cab487887f258c6183cc9a7fed1b76314c6b9506fbfff70793029600d  docs/architecture.md
a1528bc342c142e9716771777d0fe1c81a3a6da363e7e38891683cacf1a195d7  docs/setup.md
7db53a935889aa68d8659ee8310fb8dde44eea0eac538f1a4f4e73bcd84db7e6  docs/stories/AI-01.feature
4ffc7b56168558fa0156e41a99c2290d09652813d2df0927f91e5b02357d60cc  docs/stories/AI-01.md
```

The report `docs/reports/omp-rag-pr1/IMPLEMENTATION.md` is updated only with the verdict/finding
dispositions after the review; the code/docs/tests manifest above is the reviewed implementation
snapshot. Evidence file hashes are in `docs/reports/omp-rag-pr1/evidence/` and
`capabilities/`; the reviewer may read them directly.

**Cumulative diff:** run `git diff 60dcc1f -- . ':(exclude).gitignore'` in the checkout. Diff stat:

```text
 backend/app/discovery/__init__.py   |  29 ++++++-
 backend/app/discovery/registry.py   |  53 ++++++++++++-
 backend/app/settings.py             | 149 ++++++++++++++++++++++++++++++++++--
 backend/pyproject.toml              |   1 +
 backend/uv.lock                     |   2 +
 docs/adr/0006-deferred-decisions.md |   2 +-
 docs/architecture.md                |   6 ++
 docs/setup.md                       |  54 ++++++++++++-
 8 files changed, 281 insertions(+), 15 deletions(-)
```

The new files are listed in the manifest. `.gitignore` has a pre-existing unrelated working-tree
change (adds `prompts/`) and is **not** part of this task; it is excluded from the diff command and
must not be staged.

### Modification map

* `backend/app/discovery/ai.py` — protocols, Pydantic result/usage types, error taxonomy, redaction
  and validation helpers. No link/review/evidence operation.
* `backend/app/discovery/ai_fake.py` — deterministic fake chat/embedding providers; no write
  surface.
* `backend/app/discovery/ai_http.py` — OpenAI-compatible HTTP adapters. Timeout, bounded retry,
  Retry-After parsing/cap, error mapping, model/usage/latency/rate-limit provenance, schema
  validation, embedding shape validation, safe logging.
* `backend/app/discovery/capabilities.py` — synthetic-canary probe. Reads no repository artifact;
  writes nothing; returns the observed matrix and sanitizes it.
* `backend/app/settings.py` — `CTA_AI_MODE`/`CTA_LLM_*`/`CTA_EMBED_*`/`CTA_VECTOR_BACKEND`/
  `CTA_AI_LIVE_TESTS`; fake default; construction-time validation; secret-safe `repr`.
* `backend/app/discovery/registry.py` — lazy chat/embedding construction; live without embeddings
  returns `None`; no fallback.
* `tools/probe_ai_capabilities.py` — offline summary without network; `--live` opt-in; refuses
  in-repo report paths unless explicitly allowed.
* `backend/tests/test_ai_providers.py` — 39 offline contract tests; mocked transport only.
* `backend/tests/test_live_provider_integration.py` — opt-in live test; skips by default.
* ADR 0007, setup, architecture, AI-01 feature/companion — decisions and operator docs.

### Key invariants to inspect

1. **Proposal/accepted/evidence separation.** The new protocols have no link id, review state,
   evidence id, or writer. `CandidateDiscovery` and `ArtifactRepository` are unchanged.
2. **No assurance authority.** No file under `backend/app/assurance/` changed; no model call is
   reachable from deterministic rules.
3. **Offline default.** `CTA_AI_MODE=fake`; fake providers; no `httpx` import in fake mode; no
   network in tests; live test opt-in.
4. **Provenance.** Results distinguish configured vs observed model; usage absent is `None`; HTTP
   status/request id/rate-limit headers are allow-listed; embedding model/dimension/index are
   validated; no model/index mixing exists yet.
5. **Bounded failure behavior.** Timeout default 10 s; retries capped at 5; retry only
   429/5xx/timeouts/transport; Retry-After capped at 5 s; auth/4xx/malformed/schema rejection not
   retried; error details exclude headers/payloads/keys.
6. **Untrusted data / data handling.** Probe uses synthetic canary text only. ADR 0007 forbids
   repository artifacts to the hosted endpoint until owner-approved data handling. No key in
   fixtures, docs, logs, or the frontend.
7. **Honest contracts.** No API/schema/fixture change; `SCHEMA_VERSION` unchanged; no fake success
   endpoint was added. A live configuration without embeddings reports unavailable, not chat
   substitution.
8. **Independent expectations.** Tests assert protocol-visible behavior and failure classes, not
   implementation prose or incidental defaults. The fake provider is not a retrieval-quality
   oracle.

## 4. Evidence

Captured from the repository root at the final snapshot; raw logs are retained in
`docs/reports/omp-rag-pr1/evidence/` (final files are `check-final-*`; earlier `check-1-*` are
checkpoint captures).

```text
uv sync --project backend --frozen                       exit 0  (25 packages checked)
uv run --project backend pytest backend/tests -q         exit 0  272 passed, 2 skipped
unshare -rn backend/.venv/bin/python -m pytest -q        exit 0  272 passed, 2 skipped
  socket probe under the same namespace                  DENIED  OSError: [Errno 101] Network is unreachable
uv run --project backend python tools/fixturectl.py verify  exit 0  reproducible and current
uv run --project backend ruff check .                    exit 0
uv run --project backend ruff format --check .           exit 0  (57 files)
git diff --check                                         exit 0
probe_ai_capabilities.py (offline)                       exit 0  probed=false, mode=fake
probe_ai_capabilities.py --live (fake mode)              exit 2  expected refusal
```

The two skipped tests are `test_live_provider_integration.py::test_live_chat_completion_returns_an_observed_response`
and `::test_live_embeddings_when_configured`. The live path is **NOT RUN**: none of
`CTA_AI_MODE`, `CTA_LLM_BASE_URL`, `CTA_LLM_MODEL`, `CTA_LLM_API_KEY`, `CTA_EMBED_BASE_URL`,
`CTA_EMBED_MODEL`, `CTA_EMBED_API_KEY`, or `CTA_VECTOR_BACKEND` was present at invocation. No
endpoint was contacted and no hosted capability matrix is claimed.

AC-to-check map: see the `PR1-AC` table in
`docs/reports/omp-rag-pr1/IMPLEMENTATION.md` for the full selector list. The key selectors are:

* `backend/tests/test_ai_providers.py::test_fake_mode_import_does_not_import_the_http_transport`
* `::test_chat_request_uses_configured_model_key_and_observes_response`
* `::test_chat_retries_a_rate_limit_and_honors_retry_after`, `::test_retry_after_is_capped`
* `::test_authentication_failure_is_not_retried_and_does_not_echo_the_key`
* `::test_schema_constrained_completion_sends_and_validates_json_schema`,
  `::test_schema_rejection_is_a_capability_error`
* `::test_embeddings_use_the_embeddings_endpoint_and_report_dimensions`,
  `::test_embedding_rejects_a_chat_shaped_response`,
  `::test_embedding_dimension_mismatch_is_a_response_error`
* `::test_probe_records_observed_capabilities`,
  `::test_probe_reports_embeddings_unavailable_without_substituting_chat`,
  `::test_probe_cli_refuses_a_repository_report`, `::test_sanitizer_redacts_credentials_and_url_query`
* `::test_live_mode_requires_llm_configuration`,
  `::test_embedding_configuration_must_be_complete`, `::test_api_keys_are_excluded_from_repr`

## 5. Self-review and known limits

* The OpenAI-compatible request/response shapes are implemented from the mission's endpoint
  description; **live compatibility is unverified**. The probe reports compatibility rather than
  assuming it. Schema-constrained JSON support and the embedding endpoint are also unverified live.
* No vector index, retrieval pipeline, GraphRAG, answer endpoint, UI, or real `CandidateDiscovery`
  exists. Retrieval quality is unmeasured.
* Only synthetic canary text is allowed to the hosted endpoint in PR 1. Repository artifacts need a
  separate owner-approved data-handling decision.
* The probe records `concurrency_limit: unknown` and does not stress-test a shared endpoint.
* `httpx` is now a runtime dependency; fake mode's import isolation is tested, but the package is
  installed by default.
* The report's review section is pending until the reviewer returns a verdict.

## 6. Reviewer instructions

You are the independent CTA implementation reviewer using GPT-6.1 Sol high. Decide whether this
exact snapshot satisfies the supplied mission slice, every applicable Gherkin criterion, and the
repository invariants. Treat OMP summaries and test results as claims to check against the packet
and targeted source inspection. Check proposal/accepted/evidence separation, no LLM authority in
deterministic assurance, revision and content-hash provenance, baseline and model isolation, offline
defaults, bounded retry/timeout and redaction behavior, untrusted-retrieved-text handling, citation
validation, honest 501/error behavior, independent oracle expectations, and generated-file
discipline. Do not demand implementation of a later milestone. Do not edit files, implement
repairs, regenerate fixtures, commit, or delegate. Ask OMP for missing runtime evidence;
distinguish observed defects from hypotheses. Return APPROVE, REQUEST_CHANGES, or NEEDS_INPUT with
findings stable by ID.
