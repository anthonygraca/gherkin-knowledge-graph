# M0 — stories, acceptance criteria, and exit evidence

Milestone **M0 (Contract + fixture foundation)** is defined in `CONTINUOUS_TRACEABILITY_ROADMAP.md` §7.
This file records what M0 includes, who owns it, and which command proves each exit criterion.

**Backlog mapping.** M0 reuses the roadmap's own foundation stories — **FT-01** and **FT-02**
(owner: B lead, priority P0). Parts of the milestone that the backlog does not cover
(repository layout, developer setup guide, initial CI workflow) are tracked as platform tasks
**M0-P1…M0-P3** instead of inventing parallel story IDs, so the roadmap remains the single
source of story numbers. Any change to this file is a contract change: A, B, and C all review it.

---

## FT-01 — labeled fixture repository and baseline oracle (owner: B lead)

> As a developer, I want labeled fixture repos and baseline oracles so I can test without external systems.

### AC-1.1 Deterministic Git history

```gherkin
Scenario: Fixture history is reproducible
  Given the fixture generator builds "banking-demo" twice in different directories
  When each generated repository is asked for the tags "baseline-a" and "baseline-b"
  Then both repositories report the same commit SHA for each tag
  And those SHAs match the committed manifest "fixtures/banking-demo/expected/baselines.json"
```

### AC-1.2 Healthy chain has no findings

```gherkin
Scenario: Requirement with a complete accepted chain
  Given "REQ-001" has accepted links to "SCN-001", "CODE-001", and "TEST-001"
  And evidence "EV-001" recorded a passing run for "TEST-001" at baseline "baseline-a"
  When findings for baseline "baseline-a" are inspected
  Then no finding references "REQ-001"
```

### AC-1.3 Missing links are reported

```gherkin
Scenario: Coverage gaps at baseline "baseline-a"
  Given "REQ-002" has no accepted verification scenario
  And "SCN-002" has no accepted implementation
  When findings for baseline "baseline-a" are inspected
  Then a "missing_verification_link" finding references "REQ-002"
  And a "missing_implementation_link" finding references "SCN-002"
```

### AC-1.4 Change after verification is reverification, not failure

```gherkin
Scenario: Implementation changed since verification
  Given "SCN-001" verification passed at baseline "baseline-a" (evidence "EV-001")
  And the file backing "CODE-001" changed between baseline "baseline-a" and "baseline-b"
  And no later evidence exists for "SCN-001"
  When findings for baseline "baseline-b" are inspected
  Then a "reverification_required" finding references "REQ-001", "SCN-001", and "CODE-001"
  And that finding references evidence "EV-001"
  And no "verification_failed" finding references "REQ-001"
```

### AC-1.5 Confirmed failure stays distinct from staleness

```gherkin
Scenario: Failing test at the evaluated baseline
  Given evidence "EV-003" recorded a failing run for "TEST-002" at baseline "baseline-b"
  When findings for baseline "baseline-b" are inspected
  Then a "verification_failed" finding references "REQ-003", "SCN-003", and "TEST-002"
  And that finding references evidence "EV-003"
  And no "reverification_required" finding references "SCN-003"
```

### AC-1.6 Superseded lifecycle

```gherkin
Scenario: Superseded requirement with live relationships
  Given "REQ-003" is marked "superseded" in its requirement front matter
  And "REQ-003" still has accepted links
  When findings for baseline "baseline-a" or "baseline-b" are inspected
  Then a "lifecycle_review_required" finding references "REQ-003"
```

### AC-1.7 Unreviewed proposal is never an accepted link

```gherkin
Scenario: Semantically plausible proposal stays pending
  Given the fixture records "LNK-007" as a proposed link from "REQ-002" to "SCN-002"
  When findings for baseline "baseline-a" are inspected
  Then a "candidate_pending_review" finding references "REQ-002" and "SCN-002"
  And "LNK-007" has review state "proposed"
  And no accepted link exists between "REQ-002" and "SCN-002"
```

### AC-1.8 Fixture evidence labels are real

```gherkin
Scenario: The fixture test suite reproduces the labeled evidence
  Given a checkout of tag "baseline-a"
  When the fixture test suite runs
  Then it passes
  Given a checkout of tag "baseline-b"
  When the fixture test suite runs
  Then it fails exactly in "tests/test_accounts.py::test_withdraw_allows_fractional_amounts"
  And it fails exactly in "tests/test_transfers.py::test_transfer_exactly_at_limit_is_permitted"
```

> AC-1.8 is what makes the labels honest: the "passed" evidence at baseline-a and the
> "failed" evidence at baseline-b are reproducible outcomes of the fixture code, not assertions
> we invented. It also shows that re-running "TEST-001" at baseline-b would fail — which is why
> AC-1.4 must report *reverification*, not failure, when no such run has been recorded.

---

## FT-02 — versioned contracts and mock responses (owner: B lead)

> As a developer, I want versioned API/domain contracts plus mock responses so I can build independently.

### AC-2.1 Mock API returns schema-valid fixture data

```gherkin
Scenario: Fixture-backed read endpoints
  Given the backend runs with no network and no embedding or LLM service
  When "GET /api/artifacts/REQ-001?baseline=baseline-a" is called
  Then the response validates against the "Artifact" contract
  And its "revision" equals the commit SHA tagged "baseline-a"
  And "GET /api/threads/REQ-001?baseline=baseline-b" returns the accepted chain plus evidence
  And "GET /api/findings?baseline=baseline-b" validates against the "FindingsResponse" contract
```

### AC-2.2 Baseline resolution

```gherkin
Scenario: Baselines are addressed by tag or commit
  Given "baseline-a" resolves to a commit SHA in the fixture manifest
  When the same endpoint is called with the tag and with that SHA
  Then both responses are identical
```

### AC-2.3 Unknown identifiers fail loudly

```gherkin
Scenario: Unknown artifact
  When "GET /api/artifacts/REQ-999" is called
  Then the status is 404
  And the body is an RFC 9457 problem document with a "urn:cta:error:artifact-not-found" type
```

### AC-2.4 Discovery proposes, never accepts (contract level of AI-04)

```gherkin
Scenario: Discover likely implementation from a scenario
  Given the candidate-discovery provider is "fake"
  When candidates are requested for "SCN-001"
  Then "CODE-001" is returned as a proposed "implemented_by" candidate at rank 1
  And the response includes the provider name, model version, and index revision
  And the candidate carries no link identifier or review state
  And no accepted link is created or modified
```

### AC-2.5 Unimplemented endpoints are honest

```gherkin
Scenario: Contract-only endpoints in M0
  When "POST /api/assurance/evaluate" is called
  Then the status is 501
  And the problem document names the owning story and milestone
```

---

## Platform tasks (not stories)

| Task | Deliverable | Location |
| --- | --- | --- |
| M0-P1 | Repository layout and module ownership | `docs/architecture.md`, `AGENTS.md` |
| M0-P2 | Developer setup guide and offline test command | `docs/setup.md`, `README.md` |
| M0-P3 | Initial CI workflow (offline job) | `.github/workflows/ci.yml` |

---

## Exit criteria → evidence

| M0 exit criterion (roadmap §7) | Evidence |
| --- | --- |
| Repository layout | `docs/architecture.md`, `AGENTS.md` |
| Setup guide | `docs/setup.md` |
| Fixture generator | `tools/fixturectl.py build` |
| Tagged baselines | `fixtures/banking-demo/expected/baselines.json`, AC-1.1 |
| Labeled expected outputs | `fixtures/banking-demo/expected/baseline-{a,b}.json`, AC-1.2…1.7 |
| Pydantic contracts | `backend/app/domain/`, `docs/domain-contracts.md` |
| OpenAPI stub/examples | `GET /openapi.json`, `fixtures/api-responses/` |
| Fake candidate provider | `backend/app/discovery/fake.py`, AC-2.4 |
| Sample findings response | `fixtures/api-responses/findings.baseline-{a,b}.json` |
| Initial CI workflow | `.github/workflows/ci.yml` |
| Clone → documented command → deterministic offline tests | `uv sync --project backend` then `uv run --project backend pytest backend/tests` |
| Mock APIs return schema-valid fixture data | AC-2.1…2.5, `backend/tests/test_api_contract.py` |
| Everyone can begin independently | A-PR1 / B-PR1 / C-PR1 below |

---

## Follow-on assignments (after M0)

| Assignment | Owner | Stories | Deliverable |
| --- | --- | --- | --- |
| **A-PR1** | Developer A | AI-01 (P0) | `CandidateDiscovery` protocol tests, provider configuration, JSON-fixture provider hardening, retrieval-evaluation dataset notes. No embedding dependency. |
| **B-PR1** | Developer B | DT-01, DT-02, DT-04 (P0) | Requirement + Gherkin parsing into the same `Artifact` contract, SQLite-or-memory persistence, `GET /api/threads/REQ-001` from parsed data replacing the fixture replay. |
| **C-PR1** | Developer C | AS-01, AS-04, AS-05 (P0) | Deterministic `missing_verification_link` / `missing_implementation_link` rules over the fixture store, mock findings API, first React/TypeScript dashboard view of one finding. |

**Integration gate:** all three PRs pass on a clean machine in fake/offline mode. No stream may
depend on another stream's real implementation to merge.

**Owner-of-record per boundary:** B leads schemas and example payloads; C owns UI API
consumption and contract checks; A owns the discovery contract and evaluation methodology.
