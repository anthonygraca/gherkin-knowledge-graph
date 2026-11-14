# Independent acceptance review — AI-08/PR 3 and AI-09/PR 4 (combined submission 1)

## Snapshot

* Base `3ece0f9`; working tree uncommitted.
* AI-08 [#69], canonical `docs/stories/AI-08.feature`
  sha256 `3f78b5da2eafbf9f3ee85b1084c12996659109755339b8dfd101ed711d6ceda5`.
* AI-09 [#70], canonical `docs/stories/AI-09.feature`
  sha256 `f97f2996333605f43c131d42300e055837178d8d6e2a703aeb0c30b6b0ac5594`.
* Answer labels `fixtures/banking-demo/expected/evidence-answers.json`
  sha256 `cae8be443fdd5ee594e09bd39c896261bd742933c279e53706677506a56ab522`.
* Benchmark `docs/reports/omp-cocoindex-pr4/evidence/rag-benchmark.json`
  sha256 `d5b97a2f49bcef5aee59b1dc2133d1b46afe10011c6a1059956a540cccaf5f71`.
* Schema `0.5.0`; fixtures regenerated.

## PR 3 (AI-08)

`app/domain/answers.py`, `app/graphrag/context.py`, `POST /api/answers`. Accepted links are the only
traversable graph; proposed links and semantic candidates are separate; graph paths carry accepted
link IDs; evidence-state precedence reports failure vs reverification vs missing; references are a
context whitelist; deterministic answer text; `chat_model=null`.

## PR 4 (AI-09)

`tools/evaluate_rag.py` combines the AI-07 A/B code capture with C (accepted graph) and D (hybrid
graph + lexical candidates) answer scoring. Labels are hand-derived from the M1/M2 fixtures. Report
records input hashes and limitations; it does not close M3/M4.

## Evidence

| Check | Result |
| --- | --- |
| Backend suite | 475 passed, 3 opt-in skips |
| AI-08 tests | 9 passed |
| Cucumber + gate | 112 scenarios / 933 results passed; strict gate ok (112 cases); report sha256 4fa44816… |
| C/D benchmark | all 1.0 agreement; unsupported assertions 0.0 |
| A/B | lexical vs live CocoIndex on identical four-file snapshots; CocoIndex no Recall@1 gain, more false candidates (~1 s/query) |
| Fixture/ruff/format/diff | clean |

## Reviewer mandate

You are the independent CTA implementation reviewer using GPT-6.1 Sol high. Verify that accepted
links alone define graph paths; proposals/semantic candidates stay separate; evidence states and M2
findings are reported correctly and not re-derived; citations cannot be created by question or
repository text; no chat model is claimed; and the benchmark uses identical inputs for A/B, scores
C/D against independent labels, reports its limitations, and does not claim M3/M4 completion.
Do not edit, install, regenerate, commit, or delegate. Return PASS/FAIL/NOT VERIFIED per criterion
with stable IDs and APPROVE / REQUEST_CHANGES / NEEDS_INPUT. A separate human label attestation is
required for the answer labels; agent review cannot supply it.
