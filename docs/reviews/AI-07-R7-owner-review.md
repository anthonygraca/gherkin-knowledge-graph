# AI-07 — R7 owner review of retrieval labels (draft; not an attestation)

**Finding under review (AI07-R7):** the new hand-labeled retrieval oracle declares
`hand_labeled: true` without a recorded human disposition. Agent inspection cannot satisfy this.

**Artifact:** `fixtures/banking-demo/expected/code-retrieval.json`
**Current sha256:** `694bba1aafe74d7cc9c50ec71f97a89d3b2dc27ade4d3cd0d94abf37f772a344`
**Why this hash changed during review:** CR-002's label is a semantic relevance judgment, not an
accepted-link fact. The fixture oracle has no accepted implementation link for SCN-002. The file now
records `basis` per case and states that distinction explicitly; the retriever never produced a
label.

## Labels to review

| Case | Baseline | Scenario | Relevant artifacts | Basis |
| --- | --- | --- | --- | --- |
| CR-001 | baseline-a | SCN-001 | CODE-001, TEST-001 | accepted links LNK-002, LNK-003 |
| CR-002 | baseline-a | SCN-002 | CODE-002 | **semantic relevance only** (no accepted implementation link; oracle reports `missing_implementation_link`) |
| CR-003 | baseline-a | SCN-003 | CODE-002, TEST-002 | accepted links LNK-005, LNK-006 |
| CR-004 | baseline-b | SCN-001 | CODE-001, TEST-001 | accepted links LNK-002, LNK-003 |
| CR-005 | baseline-b | SCN-003 | CODE-002, TEST-002 | accepted links LNK-005, LNK-006 |

Accepted links at both baselines (only LNK-001..006 are accepted):
`REQ-001→SCN-001`, `SCN-001→CODE-001`, `SCN-001→TEST-001`, `REQ-003→SCN-003`,
`SCN-003→CODE-002`, `SCN-003→TEST-002`.

## Owner disposition

**Attested.** The repository owner reviewed the five labels and the basis note above.

* **Owner statement (verbatim):** “i attest that the labels and hash are correct”
* **Recorded:** 2026-11-14T02:55Z, transcribed from the session message.
* **Reviewed hash:** `694bba1aafe74d7cc9c50ec71f97a89d3b2dc27ade4d3cd0d94abf37f772a344`.
* **Scope:** the five cases in `fixtures/banking-demo/expected/code-retrieval.json`, including the
  CR-002 semantic-relevance basis. This attests label correctness, not retrieval quality.
* If the file changes, this hash no longer identifies the reviewed content and the attestation must
  be repeated.
