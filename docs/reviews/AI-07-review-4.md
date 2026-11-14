**REQUEST_CHANGES — submission 4 of 7.** The separator repair works, but AI07-R1 retains a medium-severity defect.

| ID | Verdict | Result |
|---|---|---|
| AI07-R1 | **FAIL** | CRLF and U+2028 are preserved, but trailing-LF comparison remains incorrect. |
| AI07-R2 | **PASS** | Actual provider returns correct empty-result bindings through `/api/discovery` across baseline-a → baseline-b → baseline-a. |
| AI07-R5 | **PASS** | Same-store audits pass for normal, injection, and rejection paths. Mutation probes detect changes to links, artifacts, evidence, and findings. |
| AI07-N2 | **PASS** | Explicit lexical requests skip live-client construction and model settings, including with live configuration enabled. Five malformed embedding shapes report unavailable. |

**AI07-R1 — Medium residual:** [code_index.py:247](</home/anthonygraca/CSU Fullerton Dropbox/Anthony Graca/cpsc-583-knowledge-representation/project/gherkin-knowledge-graph/backend/app/discovery/code_index.py:247>) uses `hit.content.rstrip("\n")`, removing every trailing LF.

Independent probes reproduced both consequences:

- A hit for line 1 containing the correct text plus **three trailing LFs** returned `ok`, CODE-001, canonical provenance, and no unresolved result.
- For committed bytes `A\n\nB\n`, a correct hit containing `A\n\n` for lines **1–2** was rejected.

Compare the exact committed range while applying only the documented single-trailing-LF normalization. Add acceptance coverage for ranges ending in blank lines and rejection coverage for excess trailing LFs.

Independent verification passed 17 existing retrieval checks, additional probes, targeted Ruff/format checks, and `git diff --check`. Packet and live-manifest hashes match; the retained Cucumber gate passes **101 cases / 834 results**.

**NOT VERIFIED:** full backend suite, fixture verification, fresh Cucumber execution, and live CocoIndex execution were not rerun. No files were edited, installed, regenerated, or committed; no work was delegated.