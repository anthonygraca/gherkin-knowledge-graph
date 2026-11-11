# M0 hand-labeled oracle — human review attestation

This record supplies the human review required by `AGENTS.md` invariant 6 ("Fixture oracles are
reviewed by a human") for the M0 hand-labeled oracle files. It is the repository owner's
attestation, obtained directly in the coordinating session after the independent M0 re-review
(`docs/reviews/M0-rereview-1.md`, finding R8) established that no such evidence was recorded.

* **Attested by:** Anthony Graca (repository owner)
* **Attested at (UTC):** 2026-11-11T05:43:32Z
* **Statement attested (option selected verbatim in the request):** "Yes — reviewed, correct as
  committed. Record my attestation linked to this revision." The same option stated the label
  substance the attestation covers: findings per baseline, healthy REQ-001 at baseline-a,
  EV-001/EV-003 semantics, and the positive/negative candidate labels.
* **Additional note supplied by the reviewer:** none.
* **Revision of record:** files as committed at `191c8292f0492d34582f6e33db3cb6f29be9a9e0`
  (tree `29e7ac97f5cdde346a09df5f9852c9d4a22a49e9`), unchanged in the working tree at
  attestation time. Content hashes at attestation time:

| File | sha256 |
|---|---|
| `fixtures/banking-demo/expected/baseline-a.json` | `140cf15a9312bda4c763667f4587cebb86636fae182794b33ae63a010696bc3f` |
| `fixtures/banking-demo/expected/baseline-b.json` | `c973f6df5e887ffc82807310c88f132fa274b9b2675f0d0dc3e8b31117044c1e` |
| `fixtures/banking-demo/expected/candidate-links.json` | `606887cf3130444682a86a490947a41836a986af8cf9c857b00a5c34954f9704` |

**Scope limits.** This attestation covers the review of the three files above and their
expectations as content. It does not certify model quality (candidate scores are fixture labels,
never measurements), and it does not attest any execution result. A Git author field, an agent
review verdict, or coordination-workflow state is not this attestation; the statement above is
the human reviewer's own, recorded without paraphrase.
