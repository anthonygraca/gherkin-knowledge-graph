# PR 1 hosted-provider implementation review — submission 1 of 7

| Field | Value |
| --- | --- |
| Reviewer | Codex `gpt-6.1-sol`, reasoning effort `high`, read-only |
| Session | `01a1d3d2-52f6-78b3-861b-5c22926f382c` |
| Packet | [AI-01-hosted-provider-review-prompt.md](AI-01-hosted-provider-review-prompt.md), sha256 `26733dbd222c71ce55ac250bb93449cca29650f367c373e135467734b89f047b` |
| Snapshot | base `60dcc1fc5d0383b6011e7a97a3bf2a110984ff07`; branch `feat/30-hosted-ai-provider`; 17-file implementation manifest in the packet |
| Window | 2026-11-13T07:32:17Z → 07:35:26Z (189 s) |
| Process exit | 0 |
| CLI-reported tokens | 91,486 |
| Verdict | **REQUEST_CHANGES** — PR1-R1…R4 open; PR1-AC-1–3, 7, 8 supported; PR1-AC-4/5 fail; PR1-AC-6 lacks coverage for the findings |

The verdict below is copied verbatim from the reviewer's final message; only absolute repository
paths are substituted with `<task_repo>`.

---

**REQUEST_CHANGES — submission 1 of 7.**

All 17 supplied manifest hashes match. Four findings remain open; each was reproduced offline with mocked responses.

1. **PR1-R1 — Major: capability reports can retain credentials.**
   [capabilities.py:421](<task_repo>/backend/app/discovery/capabilities.py:421>) sanitizes URLs only beneath keys ending in `_url`. An end-to-end probe retained `https://account:password@example.test/model?access_token=hidden` in `models.deployment_metadata.root`. The `_url` branch also bypasses configured-secret replacement, leaving a known key intact if it occurs in the URL path. This violates PR1-AC-5. Apply URL sanitization and secret replacement together across report strings; add regression coverage through the complete probe.

2. **PR1-R2 — Major: malformed embedding indices silently lose their meaning.**
   [ai_http.py:426](<task_repo>/backend/app/discovery/ai_http.py:426>) treats an invalid index type as an absent index. For inputs `["alpha", "beta"]`, response items with indices `"1"` and `"0"` returned vectors in response order without an error. This can associate vectors with the wrong input and violates PR1-AC-4. Distinguish absent indices from invalid ones; reject supplied non-integer indices, including booleans, with `ProviderResponseError`.

3. **PR1-R3 — Major: the probe claims model identity without observing it.**
   [capabilities.py:265](<task_repo>/backend/app/discovery/capabilities.py:265>) sets `deployment_identifiable=true` whenever the catalogue contains any model. With only an unrelated catalogue entry and completion responses omitting `model`, I observed:
   ```json
   {
     "configured_model_found": false,
     "deployment_identifiable": true,
     "chat_observed_model": null,
     "json_schema_observed_model": "configured-alias"
   }
   ```
   The schema section independently labels the configured fallback as observed at line 311. This violates PR1-AC-5 and the stated provenance contract. Preserve unknown identity, honor `model_observed` consistently, and distinguish catalogue presence from reproducible model/deployment identification.

4. **PR1-R4 — Minor: malformed numeric embeddings escape the error taxonomy.**
   [ai_http.py:450](<task_repo>/backend/app/discovery/ai_http.py:450>) converts JSON integers to floats without handling overflow. A vector containing `10**400` raised raw `OverflowError`, bypassing `ProviderResponseError` and the probe’s failure recording. Reject unrepresentable values through the sanitized provider error contract.

PR1-AC-1–3 are supported by inspection and targeted offline checks. PR1-AC-4 and PR1-AC-5 fail as described. PR1-AC-6 has passing supplied evidence but lacks coverage for these cases. PR1-AC-7’s documentation and unchanged API/schema/assurance scope are confirmed; PR1-AC-8’s local publication and scope records are consistent. SCN-901/902 remain contextual and unclaimed.

I independently ran **27 existing tests**, Ruff lint, formatting checks, and `git diff --check`; all passed. I inspected the retained **272 passed, 2 skipped** and network-denied logs but did not rerun the full suite in this read-only environment. Hosted compatibility remains **NOT RUN**.

Proposal/accepted/evidence separation and deterministic-assurance isolation are preserved. Retrieval, citation validation, and index isolation belong to later slices. No files were changed, fixtures regenerated, commits made, or work delegated.

---

## Finding dispositions (post-verdict repair)

| Finding | Severity | Repair | Recheck |
| --- | --- | --- | --- |
| PR1-R1 | Major | All report strings now pass through URL sanitization and configured-secret replacement; `sanitize_url` handles malformed URLs; the full probe path is covered. | `backend/tests/test_ai_providers.py::test_probe_sanitizes_urls_in_model_metadata` passes; no password/query token/key in the report. |
| PR1-R2 | Major | Supplied non-integer or boolean indices are rejected; absent indices remain the only order-based path. | `::test_embedding_rejects_invalid_index_types` (string and boolean cases) passes. |
| PR1-R3 | Major | `deployment_identifiable` requires the configured model to be found with metadata; chat/schema/embedding observed-model fields honor `model_observed`. | `::test_probe_does_not_claim_identity_from_an_unrelated_catalogue` passes. |
| PR1-R4 | Minor | Unrepresentable/non-finite embedding values raise `ProviderResponseError`. | `::test_embedding_rejects_unrepresentable_numbers` passes. |

Post-repair gates: 277 backend passed, 2 skipped (normal and network-denied); fixture verify, Ruff
lint/format, and `git diff --check` clean. Submission 2 is pending; this record does not approve the
repaired snapshot.

## Snapshot integrity

`git status` before/after the review call is retained in the external run directory; no task file
changed during review. The reviewer was read-only and instructed not to edit files, implement
repairs, regenerate fixtures, commit, or delegate. This record covers only the reviewed snapshot
and scope; it does not attest stakeholder validation, human link decisions, or release
authorization.
