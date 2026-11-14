**REQUEST_CHANGES — submission 3 of 7.** R2, R5, and N2 pass. R1 retains a medium-severity defect.

| ID | Verdict | Result |
|---|---|---|
| AI07-R2 | **PASS** | Public `/api/discovery` returned the correct empty-result binding across baseline-a → baseline-b → baseline-a using the actual provider. |
| AI07-R5 | **PASS** | Normal, injection, and rejection paths compare the same store’s links, artifacts, evidence, and deterministic findings. Mutation probes confirmed the audits detect changes. |
| AI07-N2 | **PASS** | Explicit lexical requests skip model settings and live-client construction. Malformed embedding shapes report `embedding=unavailable`. |
| AI07-R1 | **FAIL** | Leading-newline repairs pass, but internal line separators are still normalized before comparison. |

**AI07-R1 — Medium residual: committed bytes and ranges can still be misrepresented.**

At [code_index.py:229](</home/anthonygraca/CSU Fullerton Dropbox/Anthony Graca/cpsc-583-knowledge-representation/project/gherkin-knowledge-graph/backend/app/discovery/code_index.py:229>), `splitlines()` removes line separators; line 242 reconstructs them as LF. This changes committed content before comparison.

Independent in-memory service probes, with matching artifact hashes, returned `ok`, CODE-001, and no unresolved result for:

- A CRLF blob with hit content changed to LF.
- A two-line blob containing U+2028 inside a string, with that character replaced by LF and a declared range of **2–3**.

Preserve committed line bytes and delimiters, applying only the documented trailing-newline normalization. Add rejection coverage for both cases.

Independent verification passed 15 existing retrieval checks, endpoint and audit probes, Ruff, formatting, and `git diff --check`. The retained feature/report hashes match; the strict gate passes **101 cases / 834 results**. Live manifest implementation and evidence hashes also match.

**NOT VERIFIED:** full backend suite, fixture regeneration/verification, fresh Cucumber execution, and live CocoIndex execution were not rerun. No files were edited, installed, regenerated, or committed; no work was delegated.