# Post-approval changes (recorded, not re-reviewed)

Review 7 approved the slice at commit `37980aa`; the task review budget is exhausted (7 of 7).
Two operational commits follow the approval and are **not** covered by that verdict:

| Commit | Change | Reason | Local verification |
| --- | --- | --- | --- |
| _this commit_ | `bdd/support/ui.js` creates `bdd/.cache` before `mkdtempSync` | Hosted CI checkout had no `bdd/.cache`; `BeforeAll` failed with ENOENT and the bdd job failed before running any scenario. | `cucumber-js --tags "@AS-04 or @AS-05"`: 7 scenarios / 58 steps passed. |
| `4aebcce`, `a85c9cc`, `_this commit_` | approval/status records and manifest preservation | Documentation only; the reviewed manifest remains pinned to the approved snapshot. | `commitlint` passes; no product change. |

The product code, canonical features, fixtures, and verifier logic remain as reviewed. If the owner
requires a fresh independent review of the CI-only fix, it must be obtained outside the exhausted
seven-submission budget and recorded before merge or immediately after.
