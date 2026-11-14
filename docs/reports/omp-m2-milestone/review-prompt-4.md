# Independent acceptance review — expanded M2 (submission 4 of 7)

## Snapshot

* Local working tree at base `4659e011c7adbe56940c71891f857d6225a5df10`; M2 slice uncommitted.
* Schema `0.3.0`; fixtures regenerated. `dirty-tree-manifest.txt` is generated after all
  documentation edits and excludes mutable review logs; feature hashes below.
* Prior verdicts: `review-1.md`, `review-2.md`, `review-3.md` — all REQUEST_CHANGES. This packet
  submits the round-3 repairs; `review-3-disposition.md` maps them.

## Repairs since submission 3

| Finding | Repair |
| --- | --- |
| R07 gate completeness | Eligible pickles are derived from the tag policy; every eligible pickle needs a case, started attempts, a `testCaseFinished`, and one result per expected test step; hooks must be `PASSED`/`FAILED`. Omitted case, skipped hook, and duplicate result are all rejected (reproduced). |
| R09 inventory integrity | Generator and GT-02 reconciliation use eligible pickles, expected-step-id matching, and duplicate/unknown result detection; `passing`/`complete` requires all zero. Counterexamples now produce `incomplete`. |
| R16 baseline cache | Evidence cache keys include the baseline; a stale response cannot satisfy the new baseline; failed lookups retry. New component test reproduces the reviewer's traversal. |
| R01 manifest | Regenerated last, with review logs excluded. |
| R08/R12 | **Still blocking; not repaired.** |

## Checks after the repairs

| Command | Observed |
| --- | --- |
| `uv run --project backend pytest backend/tests -q` | 443 passed, 3 opt-in skips |
| `uv run --project backend python tools/fixturectl.py verify` | exit 0 |
| `ruff check` / `ruff format --check` | clean / 78 files formatted |
| `git diff --check` | exit 0 |
| `(cd frontend && npm run build && npm test)` | built; 13 tests passed |
| `(cd bdd && npm run bdd)` + strict gate | 78 scenarios passed (331 Gherkin steps + 156 hooks, 487 results); gate ok; report sha256 53a15afc3194ee9c6b78b3eb19c676a5b8e25f3171a369af045e7dc4a8e25e58 |
| Gate counterexamples | omitted case, skipped hook, duplicate result: all exit 1 |

## Feature hashes (sha256)

| `docs/stories/DT-05.feature` | `f348df16d5bb28945e6a16bbab116fb40cf5f6cb2ceeb69fe26ef2c4b36ece20` |
| `docs/stories/DT-06.feature` | `8b6630b2408e5ced946ec69fc97a014c45fcdf5e3c31eeb9a8603f007de703cd` |
| `docs/stories/AS-02.feature` | `4ea37ca50432b92113e4272826d7b75555677aaf3ff01cb91a46b1d4c29ede78` |
| `docs/stories/AS-03.feature` | `320cfdc2e32625e9dc4b6da11d6f1594e227eb3971ff17f8974d963b30ed00ee` |
| `docs/stories/AS-05.feature` | `2172b7f437f682753df4479b4329e8e73f7d267dc2776b2a7473c207116ac797` |
| `docs/stories/GT-01.feature` | `aac42c24723aa02166d9f534946750e6d49c74f14db7c7ae8bcfe1790a6ba8bf` |
| `docs/stories/GT-02.feature` | `7706223c5355fccbe3b05c37494b0ea48c2beda3bec0db07367a5d4f3d73af69` |
| `docs/stories/GT-03.feature` | `f81b51c4891e4a98da7bf02956ca9fc1a376f46df0ac4325f925d0a14432a85d` |
| `docs/stories/PG-01.feature` | `4739afda0c627835524126bddd5d8db2abee2565f155b668ee80348a460ad766` |
| `docs/stories/DT-01.feature` | `7c597f70673654a0e048ec923cc04073b9b424fd7c54b7254b635b4936b3b5e8` |
| `docs/stories/DT-02.feature` | `4e9ff5c1891763ea4160ab4bf7b55a86ddacdf0a7765cfa6dcd5b7694ffc3774` |
| `docs/stories/DT-03.feature` | `4c581fc95949e64ece04bfacadb6aa59a61358921ca58c2a9159aad0a1a193dc` |
| `docs/stories/DT-04.feature` | `3d525a0a7bdb2dbfc8a555e3e57e88a28f5574667b6f043b2903361d1c68d64a` |
| `docs/stories/AS-01.feature` | `bb214629f16293b719ce42a23a67ee21735163d5f1ad13861507086cdf6592b2` |
| `docs/stories/FT-01.feature` | `d58eeec05ce2072b81fd656531369ae2d329a9fcc09975688d2750fc044c217a` |
| `docs/stories/FT-02.feature` | `bdf55dafaa3fa498242c5fd5d3e27961281679ea612766dce207542cb7cacae8` |
| `docs/stories/AI-01.feature` | `381663033f88f4915481f292c912e94041774497aa74d22bb41a34b17276ef67` |

## Remaining blockers (unchanged)

1. **R08:** AS-04 (5), AS-05 (2), SETUP-01 (8) scenarios have no Cucumber bindings and are marked
   `not_executed`.
2. **R12:** no owner attestation, tied to hashes, for
   `fixtures/external-recipes/expected/inventory.json` and
   `fixtures/external-twin/expected/inventory.json`.

## Reviewer mandate

You are the independent CTA implementation reviewer using GPT-6.1 Sol high. Verify the R07, R09,
R16, and R01 repairs by reproducing the counterexamples where practical, confirm the current
captured report still passes the hardened gate and that the inventory matches it, and confirm the
baseline-scoped dashboard behavior. Do not edit, install, regenerate, commit, or delegate. Return
criterion-by-criterion PASS/FAIL/NOT VERIFIED with stable finding IDs and exactly one verdict:
APPROVE, REQUEST_CHANGES, or NEEDS_INPUT. R08 and R12 remain blockers unless the canonical exit
criteria accept them (they do not). Agent review does not attest human stakeholder validation or
human acceptance of semantic links.
