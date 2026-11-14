# M2 external oracle — owner attestation

**Reviewer:** repository owner (anthonygraca)
**Recorded:** 2026-11-14T00:24Z, from a session message; transcribed by the coordinator.
**Owner statement (verbatim):** “i attest that the inventory and commit hashes are correct”

## Attested inputs

| Artifact | sha256 / commit |
| --- | --- |
| `fixtures/external-recipes/expected/inventory.json` | `652de56b4ebe421a517827bad43829d14e9337dfe5cef0c46bee04183058e214` |
| `fixtures/external-twin/expected/inventory.json` | `870056361277005d82b97a94e604ab39920c8c53ee5beda2db563ecabd7f387f` |
| `external-recipes` v1 commit | `55d3d74a8359acf3b271abd830e0d1e531921cb8` |
| `external-recipes` v2 commit | `d8e5903ee11533d30cf472e618a4b0fa00c52324` |
| `external-twin` v1 commit | `36c27b8f5f0467d7b4b4f81fd58bb95261d97560` |

The commit values are the deterministic outputs of `tools/external_fixture.py` for the committed
trees and match `docs/reports/omp-m2-portability/evidence/report-manifest.json`.

## Disposition

The repository owner attests that the two external inventory files and the external fixture commit
hashes above are correct. This satisfies invariant 6 for the M2 external oracles (R12).

**Scope note.** The owner's earlier message referred to `external-recipes` specifically; this
attestation is recorded for both M2 external inventories because the statement covers “the inventory
and commit hashes” and R12 names both files. If the owner intended only `external-recipes`, this
record must be corrected before milestone approval. If an inventory file or fixture tree changes,
these hashes no longer identify the reviewed content and the attestation must be repeated.
