# AI-05 retrospective

**Outcome.** Candidate retrieval is now measured against the existing hand-labeled index rather than
assumed. The harness is offline, records provenance and dataset hashes, and keeps reports separate
from rule-test expectations.

**Limits.** Five labeled pairs are a harness check, not a general retrieval benchmark; the PR 4
four-arm benchmark covers code/graph arms separately. No model-quality claim is made.
