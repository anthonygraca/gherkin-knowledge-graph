# PR 1 hosted-provider implementation review — submission 3 of 7

| Field | Value |
| --- | --- |
| Reviewer | Codex `gpt-6.1-sol`, reasoning effort `high`, read-only |
| Session | `01a1d3e6-7dca-78c3-a371-a17262f82609` |
| Packet | [AI-01-hosted-provider-review-prompt-3.md](AI-01-hosted-provider-review-prompt-3.md), sha256 `b8233550b3807dc61505a7f73ec69dd053c76477782336184775c75b112ffd97` |
| Snapshot | base `60dcc1fc5d0383b6011e7a97a3bf2a110984ff07`; branch `feat/30-hosted-ai-provider`; 18-file manifest in the packet |
| Prior verdicts | submission 1 **REQUEST_CHANGES** (`AI-01-hosted-provider-review.md`); submission 2 **REQUEST_CHANGES** (`AI-01-hosted-provider-review-2.md`) |
| Window | 2026-11-13T07:54:20Z → 07:57:09Z (169 s) |
| Process exit | 0 |
| CLI-reported tokens | 79,113 |
| Verdict | **REQUEST_CHANGES** — PR1-R1 remains open (report returns); PR1-R5 new (logging credentials); PR1-R2/R3/R4 remain closed |

The verdict below is copied verbatim from the reviewer's final message; only absolute repository
paths are substituted with `<task_repo>`.

---

**REQUEST_CHANGES — submission 3 of 7.**

All 18 snapshot hashes and the supplied prior-review/packet hashes match. The two submission-2 bypasses are repaired, but credential redaction remains incomplete.

1. **PR1-R1 — Major; remains open.**
   [capabilities.py:211](<task_repo>/backend/app/discovery/capabilities.py:211) returns the fake-mode report before sanitization. Using the supplied credentialed model URL with `ai_mode="fake"`, I observed `probed=false` while the serialized report retained `password`, `hidden`, and `review-key`. The public `offline_summary()` helper also retains them. The CLI now sanitizes correctly, but these report-return paths bypass it.

   Sanitize both returns and add direct fake-mode report regressions. PR1-AC-5 remains unmet.

2. **PR1-R5 — Major; new: provider logging retains URL credentials.**
   [ai_http.py:134](<task_repo>/backend/app/discovery/ai_http.py:134) replaces configured secrets without removing URL credentials/query parameters. With the supplied URL as the model and an injected logger, both mocked successful and HTTP-401 completions logged `password` and the query token `hidden`. The configured key was redacted.

   Apply URL sanitization to logged fields alongside configured-secret replacement; cover success and failure logs. PR1-AC-3’s safe-logging requirement remains unmet.

| Prior finding | Disposition |
|---|---|
| PR1-R2 | **Remains closed** — invalid embedding indices are rejected. |
| PR1-R3 | **Remains closed** — unobserved model identity stays unknown. |
| PR1-R4 | **Remains closed** — unrepresentable numbers use `ProviderResponseError`. |

Independent verification: **32 pytest tests passed, 2 live tests skipped**, plus nine existing checks passed by direct invocation. All four repair regressions passed. Collision preservation and sanitized CLI stdout/report-writer inputs also passed. Ruff lint, formatting and `git diff --check` passed. I inspected the retained **281 passed, 2 skipped**, network-denial and fixture-verification evidence; those broader runs were not repeated.

PR1-AC-1/2/4/7/8 remain supported. Proposal/accepted/evidence separation, deterministic-assurance isolation, existing revision/hash provenance and generated-file discipline remain preserved. SCN-901/902 are contextual and unclaimed; retrieval, citation validation and index isolation remain later-slice work.

Hosted compatibility remains **NOT RUN**. No files were changed, endpoints contacted, fixtures regenerated, commits made or work delegated.

---

## Finding dispositions (post-verdict repair)

| Finding | Severity | Repair | Recheck |
| --- | --- | --- | --- |
| PR1-R1 | Major | `_base_summary`, the fake-mode `probe_capabilities` return, `offline_summary`, and the CLI `_offline_summary` now sanitize at construction; every report-return/output path is covered. | `test_fake_mode_probe_report_is_sanitized`, `test_offline_summary_is_sanitized`. |
| PR1-R5 | Major | `ai_http._log` and upstream-error-code construction use `sanitize_text` (URL credentials/query + configured secrets), not configured-secret replacement alone. | `test_logs_sanitize_url_credentials` (success and 401). |
| PR1-R2 | Major | Remains closed; no further change. | Invalid-index regressions remain. |
| PR1-R3 | Major | Remains closed; no further change. | Unrelated-catalogue identity regression remains. |
| PR1-R4 | Minor | Remains closed; no further change. | Unrepresentable-number regression remains. |

Post-repair gates: 285 backend passed, 2 skipped (normal and network-denied); fixture verify, Ruff
lint/format, and `git diff --check` clean. Submission 4 is pending; this record does not approve the
repaired snapshot.

## Snapshot integrity

`git status` before/after the review call is retained in the external run directory; no task file
changed during review. The reviewer was read-only and instructed not to edit files, implement
repairs, regenerate fixtures, commit, or delegate. This record covers only the reviewed snapshot
and scope; it does not attest stakeholder validation, human link decisions, or release
authorization.
