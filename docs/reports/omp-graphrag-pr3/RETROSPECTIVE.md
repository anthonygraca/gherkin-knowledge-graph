# AI-08 retrospective

**Outcome.** Requirement answers now traverse only accepted links, cite exact artifacts/evidence,
and abstain when verification evidence is absent. Proposed links and semantic candidates remain
separate; deterministic findings are explained, not recomputed.

**Defects caught during implementation.** The answer composer initially joined a list of path-link
lists, causing a runtime error; fixed by flattening. The REQ-003 label omitted EV-002 (append-only
history), caught by the benchmark's evidence check; the label was corrected from the authoritative
thread, not from the answer.

**Limits.** No chat explanation; lexical requirement identification only. GraphRAG does not prove M1
or requirement satisfaction.
