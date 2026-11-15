# Review-tool blocker: Codex workspace credits

At 2026-11-15, the independent M4 milestone review command:

```bash
codex exec -m gpt-6.1-sol -c model_reasoning_effort="high" \
  -s workspace-write -c sandbox_workspace_write.network_access=true \
  - < docs/reviews/M4-review-prompt-1.md > docs/reviews/M4-review-1.md
```

exited 1 with an empty verdict file. The retained stderr
`docs/reviews/M4-review-1.log` ends with:

```text
ERROR: Your workspace is out of credits. Ask your workspace owner to refill in order to continue.
tokens used 132,590
```

The earlier independent story reviews (AS-06, AS-07, AI-02, AI-03, CI-01, CI-02, M3) were completed
with Codex before the credit exhaustion; their verdicts are retained in `docs/reviews/`.

**Compliant alternative used:** the repository's independent `reviewer` agent, with the same
`M4-review-prompt-1.md`, merged snapshot `1731aed`, and hosted run `43716166621`. The agent is a
separate reviewer context and was instructed to remain read-only. Its verdict is recorded as
`docs/reviews/M4-review-1.md`; this file records the tool limit rather than hiding it.
