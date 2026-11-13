# PR 1 hosted-provider implementation review — submission 2 of 7

| Field | Value |
| --- | --- |
| Reviewer | Codex `gpt-6.1-sol`, reasoning effort `high`, read-only |
| Session | `01a1d3de-2e54-7b01-8a65-4d70e5ec6ef0` |
| Packet | [AI-01-hosted-provider-review-prompt-2.md](AI-01-hosted-provider-review-prompt-2.md), sha256 `02f3c22076216cc8d0dcff74d9daa03936fb07a18ec44edf8980c4db61135dee` |
| Snapshot | base `60dcc1fc5d0383b6011e7a97a3bf2a110984ff07`; branch `feat/30-hosted-ai-provider`; 18-file repair manifest in the packet |
| Prior verdict | [AI-01-hosted-provider-review.md](AI-01-hosted-provider-review.md) — submission 1 **REQUEST_CHANGES** |
| Window | 2026-11-13T07:45:15Z → 07:47:08Z (113 s) |
| Process exit | 0 |
| CLI-reported tokens | 92,552 |
| Verdict | **REQUEST_CHANGES** — PR1-R1 remains open (dynamic keys and offline CLI output); PR1-R2/R3/R4 closed |

The verdict below is copied verbatim from the reviewer's final message; only absolute repository
paths are substituted with `<task_repo>`.

---

**REQUEST_CHANGES — submission 2 of 7.**

All 18 manifest hashes and both prior-review hashes match. One major finding remains open.

**PR1-R1 — Major; partially repaired, still open.** Credential redaction has two remaining bypasses:

- [capabilities.py:443](<task_repo>/backend/app/discovery/capabilities.py:443) preserves dictionary keys. In a complete mocked probe, a catalogue model ID of `https://account:password@example.test/model?access_token=hidden&key=review-key`, with `max_model_len=4096`, became a `models.context_lengths` key unchanged. The serialized report retained the password, query token and configured API key.
- [probe_ai_capabilities.py:26](<task_repo>/tools/probe_ai_capabilities.py:26) bypasses sanitization for offline summaries. With that URL as `CTA_LLM_MODEL`, the CLI returned exit 0 and `probed=false` while printing it unchanged.

Apply sanitization to dynamic report keys and every report-output path. Add complete-probe and offline-CLI regressions asserting that serialized output contains neither URL credentials/query tokens nor configured secrets. PR1-AC-5 remains unmet.

| Prior finding | Disposition |
|---|---|
| PR1-R2 | **Closed** — invalid indices are rejected; additional float, null, duplicate and range checks passed. |
| PR1-R3 | **Closed** — unrelated catalogues no longer establish identity; omitted response models remain unknown. |
| PR1-R4 | **Closed** — unrepresentable numeric embeddings raise `ProviderResponseError`. |

PR1-AC-1–4, 7 and 8 are supported within this slice. PR1-AC-6 has passing evidence but lacks regression coverage for the remaining redaction bypasses. SCN-901/902 remain contextual and unclaimed.

Independent checks: **30 tests passed, 2 live tests skipped**; all four supplied regression selectors passed, with probe regressions invoked directly without temporary-file creation. Ruff lint, formatting and `git diff --check` passed. I inspected the retained **277 passed, 2 skipped**, network-denial and fixture-verification records; those broader runs were not repeated in this read-only environment. Hosted compatibility remains **NOT RUN**.

Proposal/accepted/evidence separation, deterministic-assurance isolation and existing revision/hash provenance remain preserved. Retrieval, citation validation and index isolation belong to later slices. No files were changed, fixtures regenerated, endpoints contacted, commits made or work delegated.

---

## Finding dispositions (post-verdict repair)

| Finding | Severity | Repair | Recheck |
| --- | --- | --- | --- |
| PR1-R1 | Major | Report sanitization moved to `app/discovery/ai.py` (no `httpx`); dynamic dictionary keys and values are sanitized, with collision suffixes; every CLI output path (offline/live, stdout/`--report`) applies it. | `test_probe_sanitizes_dynamic_model_id_keys`, `test_probe_cli_offline_sanitizes_model_credentials`, `test_sanitizer_redacts_dynamic_dictionary_keys`, `test_probe_cli_offline_import_does_not_import_the_transport`. |
| PR1-R2 | Major | Closed by reviewer in round 2; no further change. | Invalid index and overflow regressions remain. |
| PR1-R3 | Major | Closed by reviewer in round 2; no further change. | Unrelated-catalogue identity regression remains. |
| PR1-R4 | Minor | Closed by reviewer in round 2; no further change. | Unrepresentable-number regression remains. |

Post-repair gates: 281 backend passed, 2 skipped (normal and network-denied); fixture verify, Ruff
lint/format, and `git diff --check` clean. Submission 3 is pending; this record does not approve the
repaired snapshot.

## Snapshot integrity

`git status` before/after the review call is retained in the external run directory; no task file
changed during review. The reviewer was read-only and instructed not to edit files, implement
repairs, regenerate fixtures, commit, or delegate. This record covers only the reviewed snapshot
and scope; it does not attest stakeholder validation, human link decisions, or release
authorization.
