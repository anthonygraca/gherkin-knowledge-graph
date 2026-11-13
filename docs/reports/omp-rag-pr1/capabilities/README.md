# PR 1 capability evidence

**Live capability status: RUN (partial, post-approval).** The endpoint variables were supplied after
the submission-4 approval. With process-only `CTA_AI_MODE=live` and the observed catalogue model
`deepseek-ai/DeepSeek-V4.1-Flash-1017`, the synthetic-canary probe observed:

* chat: HTTP 200, `finish_reason=stop`, 54 tokens, 553.3 ms, text `canary`;
* schema-constrained JSON: HTTP 200, parsed `{"ok": true, "label": "canary"}`, 92 tokens;
* `/models`: HTTP 200, one model, context length 1,048,576 (metadata, not a tested capacity);
* embeddings: **unavailable** (configured local endpoint refused the connection);
* timeout: 5 ms probe deadline observed as timeout; configured timeout 10 s;
* error format: an empty `messages` request returned HTTP 200 with no error object.

The configured model `deepseek-ai/DeepSeek-V4.1-Flash` was **not** in the catalogue and returned
HTTP 404; the final smoke used the observed catalogue model as a process-only override. The user's
environment was not changed. The live chat test passed; the live embeddings test is **NOT RUN**
because the endpoint was unavailable. These are observations at one configuration, not a general
compatibility or capacity guarantee. See [`live-observation.md`](live-observation.md) and
[`live-summary.json`](live-summary.json).

The committed `offline-summary.json` is the sanitized output of:

```bash
uv run --project backend python tools/probe_ai_capabilities.py
```

It reports `mode: fake`, `probed: false`, no base URLs, no key values, and no endpoint observations.
The CLI's `--live` path was also invoked in fake mode and correctly exited 2 with a configuration
error; that stderr is retained at
[`../evidence/check-repair-3-probe-live-fake.stderr`](../evidence/check-repair-3-probe-live-fake.stderr).

A live report may contain local endpoint details. Write it outside the repository; the CLI refuses a
repository path unless `--allow-repo-report` is explicit. The report is sanitized for URL
userinfo/query, dynamic keys, configured secrets, and credential-like fields. Commit only a sanitized
capability summary with owner approval. The probe uses synthetic canary text only; repository
artifacts require a separate owner-approved data-handling decision (ADR 0007).
