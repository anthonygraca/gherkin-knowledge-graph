# ADR 0011 — GraphRAG evidence answers over the accepted digital thread

**Status:** Accepted · 2026-11-14 · **Stories:** AI-08 (#69), AI-09 (#70)

## Context

CTA already has authoritative artifacts, accepted/proposed links, evidence, deterministic findings,
and thread assembly. Semantic code candidates exist from AI-07. PR 3 must answer requirement
questions from evidence without letting a model or retrieval score become a graph fact; PR 4 must
measure the value of lexical, CocoIndex, graph, and hybrid retrieval.

## Decision

* **Accepted links are the only traversable graph.** Proposed links and semantic candidates are
  separate response fields and never contribute graph paths or citations.
* **Deterministic answer text.** `POST /api/answers` builds its answer from the retrieved thread,
  evidence records, and M2 findings. No chat model is required; `chat_model=null` and
  `explanation_method="deterministic"` make that explicit.
* **Evidence-state precedence.** A confirmed failing execution is reported as `verification_failed`;
  a stale pass as `reverification_required`; no accepted scenario or no evidence yields an explicit
  abstention. The answer never upgrades a link into verification.
* **Citation whitelist.** References are computed from the response context only. Instruction-like
  question or repository text cannot introduce IDs.
* **Benchmark separation.** A/B code retrieval (lexical/CocoIndex) uses identical snapshots and
  labels; C/D receive accepted-graph information and are analysed separately. PR 4 reports metrics
  and limitations; it does not close M3 or M4.

## Consequences

* The endpoint is additive (schema 0.5.0) and reuses the existing store/thread/findings code.
* Chat explanations remain optional and `NOT RUN`; a future provider must validate citations.
* GraphRAG output is not proof of M1 or requirement satisfaction.
