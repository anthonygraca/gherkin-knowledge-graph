# PR 1 capability evidence

**Live capability status: NOT RUN.** At invocation, none of `CTA_AI_MODE`, `CTA_LLM_BASE_URL`,
`CTA_LLM_MODEL`, `CTA_LLM_API_KEY`, `CTA_EMBED_BASE_URL`, `CTA_EMBED_MODEL`,
`CTA_EMBED_API_KEY`, or `CTA_VECTOR_BACKEND` was present in the process environment. No endpoint
was contacted, and no hosted capability matrix is claimed. A missing configuration is **NOT RUN**,
not failed and not passed.

The committed `offline-summary.json` is the sanitized output of:

```bash
uv run --project backend python tools/probe_ai_capabilities.py
```

It reports `mode: fake`, `probed: false`, no base URLs, no key values, and no endpoint observations.
The CLI's `--live` path was also invoked in fake mode and correctly exited 2 with a configuration
error; that stderr is retained at
[`../evidence/check-repair-3-probe-live-fake.stderr`](../evidence/check-repair-3-probe-live-fake.stderr).

If a live probe is run later, its report may contain local endpoint details. Write it outside the
repository; the CLI refuses a repository path unless `--allow-repo-report` is explicit. The report
is sanitized for URL userinfo/query, dynamic keys, configured secrets, and credential-like fields.
Commit only a sanitized capability summary with owner approval. The probe uses synthetic canary text
only; repository artifacts require a separate owner-approved data-handling decision (ADR 0007).
