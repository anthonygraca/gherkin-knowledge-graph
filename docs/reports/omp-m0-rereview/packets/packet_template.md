# CTA M0 re-review — submission 1 (verification of the R1–R7 repairs)

Reviewer: **GPT-6.1 Sol, reasoning effort `xhigh`** (this call). Independence: the implementation and
repairs were committed by the project developer (Anthony Graca); this is a fresh session that has
not been part of the repair work. OMP (the coordinator) produced §7's runtime evidence on the exact
snapshot in §5; treat OMP's summaries as claims to check against the artifacts and the repository.

## 0. How this packet is organized

| § | Content |
|---|---|
| 1 | Scope, milestone ceiling, and the concrete decision this review must make |
| 2 | Repository invariants and quality gates the snapshot must uphold |
| 3 | The frozen M0 acceptance criteria (AC-1.1…AC-1.8, AC-2.1…AC-2.5) |
| 4 | The seven first-review findings (R1–R7): original claim, original probe, claimed repair, regression tests |
| 5 | Exact snapshot identity: revisions, manifest, content hashes, full cumulative diff |
| 6 | Implementation context: which files to read, and what is hand-labeled vs generated |
| 7 | Runtime evidence produced on this snapshot (commands, exits, outputs) and its limits |
| 8 | What this review must decide and report |
| 9 | Appended reviewer instructions (authoritative for the verdict format) |

---

## 1. Scope

**Task.** Verify the repairs of the eight-finding list in `docs/reviews/M0-review.md` (R1–R7; the
first review's verdict was "M0 not verified") and re-assess the M0 exit gate at the snapshot in §5.

**Milestone ceiling.** M0 only ("Contract + fixture foundation"). Do not demand M1/M2/M3
implementation (ingestion, deterministic rule engine, UI, embedding providers). Contract-only
endpoints returning 501 with the owning story are correct M0 behavior.

**Workstream.** Shared platform / B lead (fixture + contracts). Integration owner: the developer.

**Acceptance condition for this review** (from `docs/STATUS.md`, "Next tasks" row 1): every R1–R7
finding dispositioned as `repaired` with command output that shows it; a regression test exists for
each; no open major finding; no regression elsewhere against the M0 exit criteria.

**Out of scope.** (a) `README.md` and `prompts/omp-codex-agentic-loop.md` have uncommitted edits in
the working tree that are **unrelated** to this task and must not be judged here (§5 lists them);
(b) the content of process documents (the first review record, the loop prompt) is not under review —
only that the product claims match the code; (c) roadmap ambitions beyond M0.

**Reported defect discovered during this task's self-review (in scope, included in the snapshot):**
`docs/architecture.md` still named the removed `FixtureStore.resolve()` helper (renamed to
`resolve_baseline` by the R1 repair). OMP corrected the sentence; it is the single uncommitted
in-scope change, identified by hash in §5. Verify it if you like; it is docs-only.

---

## 2. Repository invariants and gates (`AGENTS.md`, authoritative)

1. **Proposals ≠ accepted links ≠ verification.** `TraceCandidate` has no link id and no review
   state; a discovery provider must never write an accepted link or evidence. API responses keep
   `accepted_links` and `proposed_links` as separate arrays.
2. **Offline by default.** No test, CI job, or default code path may require a GPU, LLM, embedding
   model, vector database, network access, or Docker. Model providers are optional plugins behind
   `app.domain.ports.CandidateDiscovery`.
3. **Version-aware or it is not evidence.** Verification claims carry the executed `tested_commit`
   and artifact content hashes; freshness compares **content hashes**, never commit SHAs.
4. **Change ≠ failure.** A relevant change after verification yields `reverification_required`;
   `verification_failed` requires a recorded failing execution at the evaluated baseline.
5. **Explainability.** Findings name rule id, artifacts, evidence, evaluated baseline, and revisions.
6. **Hand-written labels.** Never derive an expected result from model output or from the code under
   test; fixture oracles are human-authored.
7. **Contract-only means 501.** An endpoint whose implementation belongs to a later milestone
   returns 501 naming the owning story; never fake success.

Gate commands (all run by OMP on this snapshot; outputs in §7):

```bash
uv sync --project backend --frozen
uv run --project backend pytest backend/tests -q
uv run --project backend python tools/fixturectl.py verify
uv run --project backend ruff check .
uv run --project backend ruff format --check .
git diff --check
```

Milestone definition of done (`AGENTS.md`): a milestone closes only when its exit criteria pass and
an independent review of those criteria has no open **major** finding.

---

## 3. Frozen acceptance criteria (source: `docs/stories/M0-foundation.md`)

**FT-01 — labeled fixture repository and baseline oracle (owner: B lead) · issue #18**

```gherkin
@AC-1.1  Scenario: Fixture history is reproducible
  Given the fixture generator builds "banking-demo" twice in different directories
  When each generated repository is asked for the tags "baseline-a" and "baseline-b"
  Then both repositories report the same commit SHA for each tag
  And those SHAs match the committed manifest "fixtures/banking-demo/expected/baselines.json"

@AC-1.2  Scenario: Requirement with a complete accepted chain
  Given "REQ-001" has accepted links to "SCN-001", "CODE-001", and "TEST-001"
  And evidence "EV-001" recorded a passing run for "TEST-001" at baseline "baseline-a"
  When findings for baseline "baseline-a" are inspected
  Then no finding references "REQ-001"

@AC-1.3  Scenario: Coverage gaps at baseline "baseline-a"
  Given "REQ-002" has no accepted verification scenario
  And "SCN-002" has no accepted implementation
  When findings for baseline "baseline-a" are inspected
  Then a "missing_verification_link" finding references "REQ-002"
  And a "missing_implementation_link" finding references "SCN-002"

@AC-1.4  Scenario: Implementation changed since verification
  Given "SCN-001" verification passed at baseline "baseline-a" (evidence "EV-001")
  And the file backing "CODE-001" changed between baseline "baseline-a" and "baseline-b"
  And no later evidence exists for "SCN-001"
  When findings for baseline "baseline-b" are inspected
  Then a "reverification_required" finding references "REQ-001", "SCN-001", and "CODE-001"
  And that finding references evidence "EV-001"
  And no "verification_failed" finding references "REQ-001"

@AC-1.5  Scenario: Failing test at the evaluated baseline
  Given evidence "EV-003" recorded a failing run for "TEST-002" at baseline "baseline-b"
  When findings for baseline "baseline-b" are inspected
  Then a "verification_failed" finding references "REQ-003", "SCN-003", and "TEST-002"
  And that finding references evidence "EV-003"
  And no "reverification_required" finding references "SCN-003"

@AC-1.6  Scenario: Superseded requirement with live relationships
  Given "REQ-003" is marked "superseded" in its requirement front matter
  And "REQ-003" still has accepted links
  When findings for baseline "baseline-a" or "baseline-b" are inspected
  Then a "lifecycle_review_required" finding references "REQ-003"

@AC-1.7  Scenario: Semantically plausible proposal stays pending
  Given the fixture records "LNK-007" as a proposed link from "REQ-002" to "SCN-002"
  When findings for baseline "baseline-a" are inspected
  Then a "candidate_pending_review" finding references "REQ-002" and "SCN-002"
  And "LNK-007" has review state "proposed"
  And no accepted link exists between "REQ-002" and "SCN-002"

@AC-1.8  Scenario: The fixture test suite reproduces the labeled evidence
  Given a checkout of tag "baseline-a"
  When the fixture test suite runs
  Then it passes
  Given a checkout of tag "baseline-b"
  When the fixture test suite runs
  Then it fails exactly in "tests/test_accounts.py::test_withdraw_allows_fractional_amounts"
  And it fails exactly in "tests/test_transfers.py::test_transfer_exactly_at_limit_is_permitted"
```

**FT-02 — versioned contracts and mock responses (owner: B lead) · issue #19**

```gherkin
@AC-2.1  Scenario: Fixture-backed read endpoints
  Given the backend runs with no network and no embedding or LLM service
  When "GET /api/artifacts/REQ-001?baseline=baseline-a" is called
  Then the response validates against the "Artifact" contract
  And its "revision" equals the commit SHA tagged "baseline-a"
  And "GET /api/threads/REQ-001?baseline=baseline-b" returns the accepted chain plus evidence
  And "GET /api/findings?baseline=baseline-b" validates against the "FindingsResponse" contract

@AC-2.2  Scenario: Baselines are addressed by tag or commit
  Given "baseline-a" resolves to a commit SHA in the fixture manifest
  When the same endpoint is called with the tag and with that SHA
  Then both responses are identical

@AC-2.3  Scenario: Unknown artifact
  When "GET /api/artifacts/REQ-999" is called
  Then the status is 404
  And the body is an RFC 9457 problem document with a "urn:cta:error:artifact-not-found" type

@AC-2.4  Scenario: Discover likely implementation from a scenario
  Given the candidate-discovery provider is "fake"
  When candidates are requested for "SCN-001"
  Then "CODE-001" is returned as a proposed "implemented_by" candidate at rank 1
  And the response includes the provider name, model version, and index revision
  And the candidate carries no link identifier or review state
  And no accepted link is created or modified

@AC-2.5  Scenario: Contract-only endpoints in M0
  When "POST /api/assurance/evaluate" is called
  Then the status is 501
  And the problem document names the owning story and milestone
```

**M0 exit criterion (roadmap §7):** a new developer can clone, run a documented command, and execute
deterministic tests with no network or AI services; mock APIs return schema-valid fixture data;
everyone can begin independently.

---

## 4. The first-review findings R1–R7: originals, repairs, regression tests

Full original text with complete commands: `docs/reviews/M0-review.md` §2 (readable in-repo at this
snapshot). Original outputs below are abridged to the decisive lines.

### R1 — Major: the mock repository cannot serve consumers of the shared port
- **Original observation:** `isinstance(FixtureStore.from_settings(...), ArtifactRepository)` →
  `False`; `AttributeError: 'FixtureStore' object has no attribute 'get_artifact'` (same for
  `list_links`, `changed_artifacts`); the store exposed `resolve`/`artifact`/`artifacts`/`links`/
  `evidence`/`changed_artifact_ids` and routes depended on the concrete class.
- **Claimed repair (commit `f3fc265`):** `FixtureStore` implements the declared port —
  `baselines`, `resolve_baseline`, `get_artifact`, `list_artifacts`, `list_links`, `list_evidence`,
  `changed_artifacts`; routes take `RepositoryDep` (`app/api/deps.py:20-30`); the two fixture-only
  surfaces (`FixtureStore.thread`, `SampleFindingsSource`) are named as such in code.
- **Regression tests:** `backend/tests/test_contract_boundaries.py::test_store_satisfies_the_artifact_repository_port`,
  `::test_consumer_can_read_everything_through_the_port_alone`, `::test_port_reads_raise_documented_errors`.
- **Probe to re-run:** §7 `probe_r1`.

### R2 — Major: `ThreadResponse` permitted proposals inside `accepted_links`
- **Original observation:** `ThreadResponse.model_validate(thread_with_swapped_arrays)` accepted a
  link whose `review_state` was `proposed` inside `accepted_links`; the HTTP loader served it with
  status 200 (`served proposed link through accepted_links: 200 LNK-007 proposed`).
- **Claimed repair (commit `f3fc265`):** `validate_link_partition` (`app/domain/models.py`)
  rejects non-accepted entries in `accepted_links` and accepted entries in `proposed_links`; it is
  applied by `ThreadResponse` (`app/domain/api.py`) and by `BaselineSnapshot`
  (`app/domain/oracle.py`); the loader rejects a mispartitioned file (500 `fixture-data-invalid`).
- **Regression tests:** `test_contract_boundaries.py::test_thread_response_rejects_a_proposal_inside_accepted_links`,
  `::test_thread_response_rejects_an_accepted_link_inside_proposals`,
  `::test_loader_rejects_a_mispartitioned_thread_file`.
- **Probe to re-run:** §7 `probe_r2_r4` (model + HTTP).

### R3 — Major: `verify` ignored a corrupted or deleted baseline manifest
- **Original observation:** with a copied tree, `fixturectl.py verify` printed
  "fixture generation is reproducible and committed files are current" and exited 0 for both a
  tampered (`tags.baseline-a = '0'*40`) and a deleted `expected/baselines.json`; `compare_tree`
  enumerated nothing when passed file paths.
- **Claimed repair (commit `ba2fb05`):** `compare_file` compares the manifest as a file with
  explicit absence handling; `verify` gains `--baselines`; tamper/delete both exit 1 and name the
  file.
- **Regression tests:** `backend/tests/test_fixture_drift.py::test_drift_detection_fails_when_the_baseline_manifest_is_tampered`,
  `::test_drift_detection_fails_when_the_baseline_manifest_is_missing`.
- **Probe to re-run:** §7 `probe_r3`.

### R4 — Minor: thread and findings loaders served unsupported contract versions
- **Original observation:** a copied `threads/REQ-001.baseline-a.json` / `findings.baseline-a.json`
  with `schema_version: 999.0.0` were served with **200** and the declared version echoed.
- **Claimed repair (commit `f3fc265`):** shared `require_supported_schema_version`
  (`app/persistence/fixtures.py`) called by the snapshot, thread, findings, and candidate-index
  loaders; mismatches raise `fixture-data-invalid` (500) naming the version.
- **Regression tests:** `test_contract_boundaries.py::test_served_responses_reject_an_unsupported_schema_version`
  (parametrized over threads + findings), `::test_snapshot_and_index_versions_are_enforced`.
- **Probe to re-run:** §7 `probe_r2_r4` (HTTP + snapshot construction).

### R5 — Minor: inherited Git object format changed every baseline SHA
- **Original observation:** with `GIT_DEFAULT_HASH=sha256` exported,
  `build_repo` produced tags `44ac9e4c…`/`c6af1add…` instead of the committed
  `67109fac…`/`c02064fe…`; the signing/timezone attack failed.
- **Claimed repair (commit `ba2fb05`):** `GIT_DEFAULT_HASH=sha1` pinned in the generator's fixed
  environment (`tools/fixturectl.py` `GIT_IDENTITY`), documented.
- **Regression test:** `backend/tests/test_fixture_repo.py::test_generator_pins_the_object_format`.
- **Probe to re-run:** §7 `probe_r5`.

### R6 — Minor: fingerprint expectations could change with the implementation and still pass
- **Original observation:** in a disposable clone, replacing `hashlib.sha256` with `hashlib.sha1`
  in `finding_fingerprint` left `fixturectl.py all` + the suite green (`92 passed`); the fingerprint
  test took its expected value from the production helper.
- **Claimed repair (commit `f3fc265`):** three independently computed fixed vectors with duplicate
  and out-of-order ids (`backend/tests/test_domain_contracts.py::INDEPENDENT_FINGERPRINT_VECTORS`),
  covering three rule/finding-type pairs.
- **Regression test:** `test_domain_contracts.py::test_fingerprint_matches_an_independently_computed_vector`
  (3 parametrized cases).
- **Probe to re-run:** §7 `probe_r6` (the same mutation in a clone; it must now fail).

### R7 — Minor: the review prompt's fixture-test command failed collection
- **Original observation:** running the prompt's command from outside a worktree returned exit 2,
  `ModuleNotFoundError: No module named 'src'` (the fixture `conftest.py` is what adds `src` to
  `sys.path`).
- **Claimed repair (commit `ba2fb05`):** `docs/reviews/M0-review-prompt.md` (and `docs/setup.md`)
  now run pytest **from each worktree root** with an absolute backend interpreter and explain why.
- **Regression test:** none (documentation-only change); exercised by running the documented recipe.
- **Probe to re-run:** §7 `probe_r7`.

---

## 5. Snapshot identity

- **Base revision (first review's reviewed commit):** `acf0738aa1ae91327bba433a80238d776a952343`
  (exists in the object store; the branch was rebased afterwards, so it is not an ancestor of HEAD —
  the delta below is therefore complete relative to what was reviewed).
- **Head revision:** `@@HEAD@@` (branch `@@BRANCH@@`), tree `@@TREE@@`.
- **Uncommitted, in scope (this task):** `docs/architecture.md` — sha256 `@@HASH_ARCH@@`.
- **Uncommitted, unrelated (excluded from review):** `README.md` sha256 `@@HASH_README@@`,
  `prompts/omp-codex-agentic-loop.md` sha256 `@@HASH_PROMPT@@`. Pre-existing working-tree edits by
  the user; do not judge them.
- **Versions at the snapshot:** package `0.1.0`, `SCHEMA_VERSION` `0.1.0`.
- **Fixture tags:** `baseline-a = 67109fac965377629c9ab5835541aa64461db785`,
  `baseline-b = c02064fed61bcfc6ade5ea14ac62f9eb1b5f5c54` (committed manifest).
- **Untracked build state (not part of the snapshot):** `backend/.venv/` (uv-managed),
  `fixtures/banking-demo/.build/` (generated fixture repository; rebuilt identically during
  evidence runs).

### 5a. Working tree at freeze

@@STATUS_TXT@@

### 5b. Cumulative delta since the reviewed commit

@@BASE_STAT@@

### 5c. Full cumulative diff (`git diff acf0738a..HEAD`)

@@CUMULATIVE_DIFF@@

### 5d. Uncommitted in-scope diff (`docs/architecture.md`)

@@SCOPED_DIFF@@

### 5e. Tracked-file manifest (`git ls-files -s`, blob hashes)

@@MANIFEST@@

---

## 6. Implementation context (read these in-repo)

| Path | Why it matters |
|---|---|
| `backend/app/domain/ports.py` | `ArtifactRepository` (7 methods) and `CandidateDiscovery` definitions — the R1 contract |
| `backend/app/persistence/store.py` | `FixtureStore`: port implementation, thread replay, baseline resolution, loader version checks |
| `backend/app/persistence/fixtures.py` | `require_supported_schema_version` + `load_model` — the R4 boundary |
| `backend/app/domain/models.py` | `validate_link_partition`, `finding_fingerprint` (R2, R6), model invariants |
| `backend/app/domain/api.py` | `ThreadResponse` validator (R2); envelopes; `ProblemDetails` |
| `backend/app/domain/oracle.py` | `BaselineSnapshot` partition validator; oracle schemas |
| `backend/app/assurance/sample_findings.py` | Sample-findings replay + version check (R4) |
| `backend/app/api/deps.py`, `backend/app/api/routes.py` | Routes read through `RepositoryDep` (R1); 501 contract-only endpoints |
| `backend/app/discovery/fake.py` | Fixture candidate provider; index revision fingerprint |
| `tools/fixturectl.py` | `GIT_IDENTITY` (R5 pin), `compare_file`/`command_verify` (R3), `--baselines` |
| `backend/tests/test_contract_boundaries.py` | R1/R2/R4 regression tests |
| `backend/tests/test_domain_contracts.py` | R6 independent fingerprint vectors |
| `backend/tests/test_fixture_drift.py`, `test_fixture_repo.py` | R3/R5 regression tests; AC-1.1/1.8 |
| `backend/tests/test_api_contract.py`, `test_fixture_oracle.py` | AC-2.x and oracle consistency |
| `docs/domain-contracts.md`, `docs/architecture.md`, `docs/api-contracts.md`, `docs/setup.md` | Doc claims that must match reality (review claim set #11) |
| `.github/workflows/ci.yml` | CI runs the same gate commands on Python 3.12 |

**Hand-labeled vs generated.** Hand-labeled: `fixtures/banking-demo/expected/baseline-a.json`,
`baseline-b.json`, `candidate-links.json`, `fixtures/banking-demo/history.json`, the fixture
repository's `evidence/*.json`. Generated (never hand-edited): `fixtures/api-responses/*`,
`fixtures/banking-demo/expected/baselines.json`. `verify` fails if any generated file differs from
a fresh build.

---

## 7. Runtime evidence produced on this snapshot

Environment: Fedora Linux x86_64; git 2.56.0; uv 0.13.7 (installed once during this session —
the pre-existing `backend/.venv` was a stale macOS venv and was recreated by
`uv sync --project backend --frozen`); CPython **3.12.16** (uv-managed; CI pins 3.12); fastapi
0.162.4, pydantic 2.14.3, pytest 8.4.2, ruff 0.17.4, uvicorn 0.54.0, httpx 0.28.1.
All commands run from the repository root. Full command outputs are embedded below verbatim.

### 7a. AC → check map

| Criterion | Executable check (node id) | Evidence file |
|---|---|---|
| AC-1.1 | `test_fixture_repo.py::test_generated_history_matches_the_committed_manifest`, `::test_tags_exist_and_resolve_to_those_commits`, `::test_rebuilding_in_another_directory_is_reproducible`, `::test_history_is_linear_and_each_commit_has_one_parent`, `::test_generator_pins_the_object_format` | `gate_build`, `probe_r5`, `gate_pytest` |
| AC-1.2 | `test_fixture_oracle.py::test_healthy_artifacts_have_no_finding`, `test_api_contract.py::test_findings_match_the_oracle_exactly[baseline-a]` | `gate_pytest` |
| AC-1.3 | `test_fixture_oracle.py::test_case_2_and_3_coverage_gaps_are_labeled` | `gate_pytest` |
| AC-1.4 | `test_fixture_oracle.py::test_case_4_reverification_identifies_both_baselines_and_the_change` | `gate_pytest` |
| AC-1.5 | `test_fixture_oracle.py::test_case_5_failure_is_distinct_from_staleness` | `gate_pytest` |
| AC-1.6 | `test_fixture_oracle.py::test_case_7_superseded_requirement_is_flagged_for_lifecycle_review` | `gate_pytest` |
| AC-1.7 | `test_api_contract.py::test_thread_keeps_proposals_out_of_accepted_links`, `test_fixture_oracle.py::test_case_6_proposal_is_pending_and_not_accepted`, `test_contract_boundaries.py` (R2 partition tests) | `gate_pytest`, `probe_r2_r4` |
| AC-1.8 | `test_fixture_repo.py::test_fixture_test_suite_reproduces_the_labeled_evidence` | `probe_r7`, `gate_pytest` |
| AC-2.1 | `test_api_contract.py::test_health_reports_contract_and_fixture_status`, `::test_artifact_is_addressable_by_tag_or_commit`, `::test_thread_carries_the_accepted_chain_with_evidence` | `probe_http_live`, `gate_pytest` |
| AC-2.2 | `test_api_contract.py::test_artifact_is_addressable_by_tag_or_commit`, `::test_findings_by_sha_and_by_tag_are_identical` | `probe_http_live`, `gate_pytest` |
| AC-2.3 | `test_api_contract.py::test_unknown_artifact_returns_a_problem_document`, `::test_malformed_artifact_id_is_a_validation_problem`, `::test_unknown_baseline_returns_a_problem_document` | `probe_http_live`, `gate_pytest` |
| AC-2.4 | `test_api_contract.py::test_discovery_returns_a_proposal_and_never_an_accepted_link`, `::test_discovery_rejects_unknown_provider_and_artifact`, `::test_discovery_top_k_and_relation_filter` | `probe_http_live`, `gate_pytest` |
| AC-2.5 | `test_api_contract.py::test_contract_only_endpoints_are_honest`, `::test_contract_only_endpoints_still_validate_their_payloads` | `probe_http_live`, `gate_pytest` |
| R1 | `test_contract_boundaries.py::test_store_satisfies_the_artifact_repository_port`, `::test_consumer_can_read_everything_through_the_port_alone`, `::test_port_reads_raise_documented_errors` | `probe_r1`, `gate_pytest` |
| R2 | `test_contract_boundaries.py::test_thread_response_rejects_a_proposal_inside_accepted_links`, `::test_thread_response_rejects_an_accepted_link_inside_proposals`, `::test_loader_rejects_a_mispartitioned_thread_file` | `probe_r2_r4`, `gate_pytest` |
| R3 | `test_fixture_drift.py::test_drift_detection_fails_when_the_baseline_manifest_is_tampered`, `::test_drift_detection_fails_when_the_baseline_manifest_is_missing` | `probe_r3`, `gate_pytest` |
| R4 | `test_contract_boundaries.py::test_served_responses_reject_an_unsupported_schema_version`, `::test_snapshot_and_index_versions_are_enforced` | `probe_r2_r4`, `gate_pytest` |
| R5 | `test_fixture_repo.py::test_generator_pins_the_object_format` | `probe_r5`, `probe_r6`, `gate_pytest` |
| R6 | `test_domain_contracts.py::test_fingerprint_matches_an_independently_computed_vector` (3 cases) | `probe_r6` (mutation must fail) |
| R7 | documented recipe (run below) | `probe_r7` |

### 7b. Not run / limits (declare as limits, do not assume)

- **Hosted GitHub Actions** was not executed (no run of `ubuntu-latest`); the CI YAML was read only.
- **macOS arm64 / Git 2.54** (the first review's environment) was not re-run; this snapshot's
  evidence is Linux/Git 2.56. R5's fix is environment pinning, tested by `probe_r5`.
- **`uv run --offline` under OS-level network denial** was not executed; the network-denied suite
  run used the venv interpreter directly under `unshare -rn` (see `net_denied`), with the denial
  proven effective by a refused socket.
- **No browser/UI verification**: M0 has no frontend (created in C-PR1).
- A collection smoke on CPython 3.14.10 (system Python) collected the same 107 tests before the
  environment was re-pinned to 3.12.16; all recorded results are from 3.12.16.

### 7c. Embedded evidence (verbatim)

@@EVIDENCE@@

---

## 8. Assignment for this review

1. For **each** of R1–R7: state `repaired` / `partially repaired` / `not repaired`, with the command
   output (yours or the embedded evidence you accept) that shows it, and confirm the regression test
   that would catch a relapse (or state why a test is unnecessary for a docs-only change).
2. Confirm the repair did not regress anything: proposal/accepted/evidence separation, port
   compatibility, revision/content-hash semantics, honest 501s, oracle independence, offline
   defaults, generated-file discipline.
3. Assess the M0 exit criteria (§3) at this snapshot: AC-by-AC `PASS` / `FAIL` / `NOT VERIFIED`.
4. Report the single most important issue (if any) with a smallest acceptable fix; distinguish
   observed defects from hypotheses; list unverified claims and what you would need.
5. Return **exactly one** verdict: `APPROVE`, `REQUEST_CHANGES`, or `NEEDS_INPUT`.
   `APPROVE` requires: every applicable AC satisfied, all R1–R7 dispositioned as repaired, no open
   major finding, no unaddressed blocker, and this exact snapshot identified.

OMP is not allowed to treat a passing process exit, passing tests, or its own confidence as your
approval: only your verdict counts, and only for this snapshot.

---

## 9. Appended reviewer instructions (authoritative)

You are the independent CTA implementation reviewer using GPT-6.1 Sol xhigh. Decide whether this
exact snapshot satisfies the supplied story, every applicable Gherkin criterion, and repository
invariants. Treat OMP's summaries and test results as claims to check against the supplied artifacts
and targeted source inspection. Check proposal/accepted/evidence separation, real port
compatibility, revision/content-hash semantics, honest errors/501s, independent oracle
expectations, offline defaults, and generated-file discipline where relevant. Do not demand
implementation of a later milestone. Do not edit files, implement repairs, regenerate fixtures,
commit, or delegate. Ask OMP for missing runtime evidence; distinguish observed defects from
hypotheses and unavailable checks. Return an AC-by-AC PASS, FAIL, or NOT VERIFIED assessment and
actionable findings with stable IDs, severity, blocking status, AC/invariant, path/line,
expected/actual behavior, and smallest correction/recheck. Keep optional suggestions and unrelated
pre-existing defects separate. Return exactly one verdict: APPROVE, REQUEST_CHANGES, or NEEDS_INPUT.
APPROVE requires every applicable criterion/check to be satisfied, no unresolved blocker, and the
exact snapshot identified. In later rounds verify prior dispositions and regressions while retaining
the complete acceptance assessment. A passing process, passing tests, or exhausted review limit is
not approval. Agent review cannot attest human labeling or human link decisions.

**OMP addendum (procedural, from the repository's own re-review instructions):** this review round
targets the findings list in `docs/reviews/M0-review.md` against the new revision. The repository's
review prompt says to write the review to `docs/reviews/M0-review.md`; **do not do that** — that
verdict is an immutable record of the first review. Return your review as your final message only;
OMP will copy it into a new recorded file (`docs/reviews/M0-rereview-1.md`) and link the
dispositions. Do not modify the repository in any way. The repository is available read-only at the
working root; you may run read-only commands to inspect it, but do not run anything that writes
files (in particular: do not run `fixturectl.py all/build/materialize`, do not regenerate fixtures,
do not run the fixture test suite through mechanisms that create worktrees — OMP has already
supplied those results in §7).
