# PR 1 hosted-provider implementation review — submission 4 of 7 (approval)

| Field | Value |
| --- | --- |
| Reviewer | Codex `gpt-6.1-sol`, reasoning effort `high`, read-only |
| Session | `01a1d3ef-6d7f-7a70-8f16-25d95fb41265` |
| Packet | [AI-01-hosted-provider-review-prompt-4.md](AI-01-hosted-provider-review-prompt-4.md), sha256 `760b974e4e4b5bf18153e26347026f7815a4c276396ed4593d6f5d59bf2bbf50` |
| Snapshot | base `60dcc1fc5d0383b6011e7a97a3bf2a110984ff07`; branch `feat/30-hosted-ai-provider`; 18-file manifest in the packet |
| Prior verdicts | submission 1 **REQUEST_CHANGES**; submission 2 **REQUEST_CHANGES**; submission 3 **REQUEST_CHANGES** |
| Window | 2026-11-13T08:04:05Z → 08:06:16Z (131 s) |
| Process exit | 0 |
| CLI-reported tokens | 88,098 |
| Verdict | **APPROVE** — PR1-R1/R5 closed; PR1-R2/R3/R4 remain closed; no new findings; PR1-AC-1…8 supported within the offline/mocked scope |

The verdict below is copied verbatim from the reviewer's final message; only absolute repository
paths are substituted with `<task_repo>`.

---

**APPROVE — submission 4 of 7**, for the supplied PR 1 provider-boundary slice.

All 18 snapshot hashes and all three prior-review hashes match.

| Finding | Disposition |
|---|---|
| PR1-R1 | **Closed.** Fake-mode reports, public offline summaries, and CLI stdout/report paths sanitize credentials. |
| PR1-R5 | **Closed.** Success and failure logs remove URL credentials/query values and configured secrets; upstream error codes are sanitized. |
| PR1-R2 | **Remains closed.** Invalid embedding indices are rejected. |
| PR1-R3 | **Remains closed.** Unobserved model identity remains unknown. |
| PR1-R4 | **Remains closed.** Unrepresentable embedding numbers raise `ProviderResponseError`. |

No new findings. PR1-AC-1 through PR1-AC-8 are supported within the documented offline/mocked scope.

Independent verification: **34 pytest checks passed, 2 live tests skipped**, plus **18 direct read-only test invocations passed**. Additional CLI output, upstream-error sanitization, and key-collision checks passed. Ruff lint, formatting, and `git diff --check` passed. I inspected the retained **285 passed, 2 skipped**, network-denial, and fixture-verification evidence; those broader runs were not repeated.

Proposal/accepted/evidence separation, deterministic-assurance isolation, existing revision/hash provenance, honest 501 behavior, and generated-file discipline remain preserved. Citation validation, retrieved-text handling, and baseline/model index isolation belong to later slices. SCN-901/902 remain contextual and unclaimed.

Hosted compatibility remains **NOT RUN**. This approval does not establish live endpoint compatibility or close a later story or milestone.

No files changed, endpoints contacted, fixtures regenerated, commits made, or work delegated.

---

## Approval scope and dispositions

This approval covers the PR 1 provider-boundary slice at the reviewed snapshot: typed
chat/embedding protocols, fake and OpenAI-compatible adapters, settings, capability probe, tests,
ADR, and docs. It does **not** establish live endpoint compatibility, hosted inference, a real
`CandidateDiscovery`, retrieval quality, GraphRAG, or any later story or milestone. AI-01 #30
remains closed and its SCN-901/902 are contextual, not claimed.

| Finding | Severity | Final disposition |
| --- | --- | --- |
| PR1-R1 | Major | Closed: all report-return and output paths sanitize URL credentials/query and configured secrets. |
| PR1-R5 | Major | Closed: success/failure logs and upstream error codes sanitize URLs and configured secrets. |
| PR1-R2 | Major | Remains closed: invalid embedding indices are rejected. |
| PR1-R3 | Major | Remains closed: unobserved model identity remains unknown. |
| PR1-R4 | Minor | Remains closed: unrepresentable embedding numbers use `ProviderResponseError`. |

Post-approval changes are record-only (this record, the implementation report, prompt/metrics/
retrospective records, and `docs/STATUS.md`); the reviewed implementation snapshot is unchanged.

## Snapshot integrity

`git status` before/after the review call is retained in the external run directory; no task file
changed during review. The reviewer was read-only and instructed not to edit files, implement
repairs, regenerate fixtures, commit, or delegate. This record covers only the reviewed snapshot and
scope; it does not attest stakeholder validation, human link decisions, or release authorization.
