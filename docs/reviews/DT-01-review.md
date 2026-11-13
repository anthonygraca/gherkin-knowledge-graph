# DT-01 — independent review, round 1

**Task:** DT-01 (#20), M1, owner B. **Submission 1 of 7.**
**Reviewer:** Codex, model `gpt-6.1-sol`, reasoning effort `xhigh`, read-only sandbox — session
`01a1d25d-1906-72e1-bc4a-d40fc65f12f7`, 2026-11-13T01:01:52Z → 01:06:39Z (287.0 s), exit 0;
usage 16,289 input (CLI-reported total; output not separately exposed).
**Reviewed snapshot:** branch `feat/20-dt-01-ingestion`, base
`e18cdcfafe058e2f1d99c3c0b4bc2e155e9b16c9`, captured 2026-11-13T00:58:20Z; the reviewer confirmed
all 14 supplied hashes matched before and after review.
**Packet:** `docs/reviews/DT-01-review-prompt.md`, sha256
`c1d4860795b3104c71a3c8b511512e4e12303e853d7cc9ba7ba3f3f6a50282e2` (55,839 bytes).
**Verdict:** REQUEST_CHANGES — four blocking defects (R1–R4) plus one nonblocking documentation
issue (N1). Repairs and rechecks are recorded in
`docs/reports/omp-dt-01-ingestion/IMPLEMENTATION.md`; submission 2 is
`docs/reviews/DT-01-review-2.md`.

The verdict below is copied verbatim from the reviewer's final message (raw file sha256
`5fcc851d297d5869319fd68696529f9d6c0b4bf38c8caac103e06a37d40cbc88` before path sanitization);
only the absolute repository path is substituted with `<task_repo>`.

---

**REQUEST_CHANGES**

Reviewed submission 1 on `feat/20-dt-01-ingestion`, base `e18cdcfafe058e2f1d99c3c0b4bc2e155e9b16c9`, captured **2026-11-13T00:58:20Z**. All 14 supplied file hashes matched before and after review. Reviewer launch metadata reports `gpt-6.1-sol`, effort `xhigh`. No files were changed.

Four blocking defects remain.

1. **DT01-R1 — Major; blocking — Scans do not enforce immutable revision pinning.**

   **Location:** [scan.py:42](<task_repo>/backend/app/ingestion/scan.py:42>) and artifact construction at line 126.

   **Contract:** Revision-pinned ingestion; `docs/domain-contracts.md` requires `Artifact.revision` to carry the resolved commit SHA.

   **Observed:** On the retained fixture repository, scanning `"baseline-a"` returned six artifacts whose revision was `"baseline-a"`. Scanning `"67109fac"` stored that abbreviation. The resolved commit is `67109fac965377629c9ab5835541aa64461db785`. The scanner passes the original expression into every Git read, so symbolic references also remain exposed to movement between reads.

   **Expected:** Every artifact and every read belongs to one immutable commit.

   **Smallest correction/recheck:** Resolve once at the scan boundary and use that SHA throughout, or explicitly reject noncanonical revision inputs. Check tag/SHA equivalence, full SHA output, and preservation of the selected baseline across working-tree or reference changes.

2. **DT01-R2 — Major; blocking — Scenario identities escape their declaration context.**

   **Location:** [parsers.py:73](<task_repo>/backend/app/ingestion/parsers.py:73>).

   **Criteria:** SCN-502, SCN-504, SCN-505; documented assumption that the identity tag immediately precedes its `Scenario:` line.

   **Observed:** This input returns `SCN-999` with title `Untagged`:

   ```gherkin
   Feature: Demo
     @SCN-999
     Rule: Group
       Scenario: Untagged
         Given a thing
   ```

   A `Scenario Outline:` between the tag and a later scenario produces the same misassociation. Separately, literal `@SCN-999` and `Scenario: This is data` lines inside a Gherkin doc string create a scenario artifact.

   **Expected:** An intervening unsupported declaration must reject the pending identity; doc-string contents must remain data.

   **Smallest correction/recheck:** Track enough lexical context to distinguish declarations from doc strings and prevent pending tags crossing declaration boundaries. Recheck both cases alongside valid tagged scenarios, blank-line separation, and additional nonidentity tags. Supporting outlines or adding a Gherkin runner is unnecessary.

3. **DT01-R3 — Major; blocking — Front matter does not preserve YAML values or reject malformed YAML.**

   **Location:** [parsers.py:53](<task_repo>/backend/app/ingestion/parsers.py:53>).

   **Contract:** Requirement identity comes from YAML front matter; malformed declarations fail loudly.

   **Observed:**

   - `id: "REQ-900"` is rejected because quotation marks become part of the ID.
   - `status: "superseded"` is stored with quotation marks, changing the declared status.
   - `status: superseded # historical` includes the comment in the stored value.
   - An unterminated quoted title is accepted as an artifact.

   **Expected:** Basic YAML string values retain their declared meaning, and invalid syntax raises an error naming the input.

   **Smallest correction/recheck:** Safely parse and validate the supported top-level YAML mapping, retaining duplicate-key rejection. Add independent expectations for quoted identity/title/status, comments, and malformed syntax. Continue hashing the original blob bytes.

4. **DT01-R4 — Major; blocking — Malformed scenario identity tokens disappear silently.**

   **Location:** [parsers.py:20](<task_repo>/backend/app/ingestion/parsers.py:20>) and tag processing at line 75.

   **Contract:** The feature-level requirement to reject malformed declarations instead of silently skipping them.

   **Observed:** A scenario tagged `@SCN-99` returns no artifact and no error. A line containing `@SCN-99 @SCN-900` silently accepts only `SCN-900`.

   **Expected:** A malformed token using the reserved scenario-identity prefix produces an error identifying the token and file.

   **Smallest correction/recheck:** Detect scenario-identity attempts separately from valid identities, then validate their format. Check malformed tokens alone and beside valid identities while preserving ordinary tags such as `@smoke`.

The complete acceptance assessment is:

| Criterion | Result | Basis |
|---|---|---|
| SCN-501 requirement artifact | PASS | Supplied baseline case reproduces the expected artifact, metadata and independently read blob hash. General YAML failures are recorded in R3. |
| SCN-502 scenario identity | FAIL | Reference fixture passes, but declaration context is not respected; doc-string text can create artifacts. R2. |
| SCN-503 missing front matter | PASS | Raises `IngestionError` naming the path; no inventory is returned. |
| SCN-504 untagged scenario | FAIL | Reference case passes, but a misplaced pending identity attaches to an untagged scenario. R2. |
| SCN-505 dangling tag | FAIL | End-of-file case passes; an intervening declaration can redirect the tag to an unrelated scenario. R2. |
| SCN-506 duplicate identities | PASS | Duplicate requirements raise an error naming `REQ-900` and both locators. |
| Immutable revision provenance | FAIL | Symbolic and abbreviated revisions are emitted unchanged. R1. |
| Requirement YAML / malformed declarations | FAIL | Observed semantic corruption, invalid-input acceptance and silent identity omission. R3–R4. |

Other applicable boundaries passed inspection:

| Check | Assessment |
|---|---|
| Proposals, accepted links and verification remain separate | PASS — ingestion produces artifacts only. |
| Existing domain/port compatibility | PASS — output uses the existing Pydantic `Artifact`; storage ports remain untouched. |
| Content hashing | PASS — hashes match exact Git blob bytes for the reference cases. |
| Offline defaults | PASS — local implementation; inspected network-denied run reports 154 passes. |
| Contract-only endpoint honesty | PASS — ingestion endpoint retains its 501 response and owning-story information. |
| Independent expectations and oracle discipline | PASS — expectations are independent of the new scanner; existing human-attestation hashes still match. |
| Generated-file and schema discipline | PASS — generated files and contracts are unchanged; no version bump is required. |

I independently ran the **11 parser tests**, Ruff lint/format checks, and `git diff --check`. I also re-executed the snapshot/hash acceptance functions and failure/boundary checks using retained committed test repositories without rebuilding them.

The raw OMP logs support **154 passing tests**, successful fixture verification, and **154 passes under demonstrated network denial**. Those complete runs were not independently repeated in this read-only review. No human labeling or product-owner approval is inferred from this review.

One separate, nonblocking documentation issue remains: [STATUS.md:18](<task_repo>/docs/STATUS.md:18>) still says “Active task: none,” and the following “Current tree” results describe the older SETUP-01 snapshot. Label those entries as historical so they do not contradict the new DT-01 status.