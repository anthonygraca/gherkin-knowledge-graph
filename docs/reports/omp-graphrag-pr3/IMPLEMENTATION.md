# AI-08 PR 3 — GraphRAG evidence retrieval

**Story:** AI-08 [#69] (parent F-09 #15). **Milestone:** M3.
**Snapshot:** `3ece0f9` plus this uncommitted slice; schema `0.5.0`.
**Review:** pending at this record.

## Delivered

* `app/domain/answers.py` — typed request/response/path/reference contracts; no model field can
  create a graph fact.
* `app/graphrag/context.py` — requirement identification (explicit ID or lexical title fallback),
  accepted-only thread traversal, graph paths, evidence-state precedence, M2 findings, citation
  whitelist, optional semantic candidates.
* `POST /api/answers` — additive deterministic answer endpoint; no chat model.
* Canonical `docs/stories/AI-08.feature` (7 scenarios) with Cucumber bindings.

## Behaviour

| Requirement state | Answer |
| --- | --- |
| REQ-001 at baseline-b | accepted LNK-001..003, EV-001, `reverification_required`, "not a verification failure" |
| REQ-002 | `abstained`, no accepted links, LNK-007 proposed only, `missing_verification_link` |
| REQ-003 at baseline-b | `verification_failed`, EV-003, no reverification claim |
| Unknown question | `not_found`, no requirement invented |
| Semantic candidates | separate field; graph paths remain accepted-only |
| Injection text | cannot add cited IDs |

## Verification

* `backend/tests/test_answers.py` — 9 passed.
* Backend suite — 478 passed, 3 opt-in skips.
* Cucumber `AI-08` — 7 scenarios passed (full-suite counts recorded after the run).
* Schema `0.5.0`; fixtures regenerated and drift-checked.

## Limits

* No chat/LLM explanation; `chat_model=null`.
* Requirement identification is ID or lexical title; not semantic requirement retrieval.
* GraphRAG answers do not prove requirement satisfaction and do not close M3.
