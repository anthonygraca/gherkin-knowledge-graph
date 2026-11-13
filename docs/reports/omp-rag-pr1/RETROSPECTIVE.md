# PR 1 retrospective

## Outcomes

* Delivered an offline-by-default, typed chat/embedding provider boundary with fake and
  OpenAI-compatible HTTP adapters, construction-time settings validation, bounded retry/timeout and
  redaction, a synthetic-canary capability probe, offline contract tests, an opt-in live test, and
  an ADR.
* Preserved the repository invariants: no accepted-link/evidence writes, no assurance-policy
  changes, no API/schema/fixture change, no model in the default path.
* Recorded the M1 premise correction honestly: the gate was unsatisfied at prompt creation and is
  now independently approved at the M1 engineering level.
* Independent review approved submission 4 of 7 with no open finding. After the endpoint variables
  were supplied, the live probe observed chat and schema-constrained JSON with the catalogue model;
  embeddings were unavailable. Submission 5 approved the post-approval probe/test change and the
  sanitized live evidence.

## Rework

Self-review found five local defects before the first review: a missing `supported=false` field on
JSON-schema probe errors; configured model IDs could appear as observed; mixed indexed/unindexed
embedding responses were accepted; fake embeddings failed above 32 dimensions; and the CLI's
in-repository report refusal returned exit 1 instead of the documented usage error.

Independent review found four more defect classes over three rounds:

* PR1-R1: credential redaction was incomplete across URL-bearing strings, dynamic dictionary keys,
  report-return paths, and the offline CLI. It took three repair rounds because each fix covered the
  named path but not the whole output surface.
* PR1-R2: malformed embedding indices could be treated as absent, silently associating vectors with
  the wrong input.
* PR1-R3: the probe could claim model identity from an unrelated catalogue and label a configured
  fallback as observed.
* PR1-R4: a huge numeric embedding escaped the provider error taxonomy as `OverflowError`.
* PR1-R5: provider logs retained URL credentials/query values even though configured keys were
  redacted.

All were reproduced with failing tests before repair; the final repair covers the shared sanitizer
surface and both report and logging paths.

The live smoke added a probe-design correction: a reasoning model spent the original 16-token
canary budget entirely on reasoning and returned no content; the adapter correctly rejected it.
The probe and live test now ask for a final answer with a 64-token budget. The live smoke then
observed chat (HTTP 200, `finish_reason=stop`, 54 tokens) and schema JSON (92 tokens) with the
catalogue model; the configured model name was not in the catalogue and returned 404, and the
embedding endpoint was unavailable.

## Resources

No OMP delegates or advisory calls. Five independent review calls, 436,661 CLI-reported Codex
tokens total, 757 seconds of review time. The live probe took 11 seconds; the live chat test 0.55
seconds. OMP usage/cost was not exposed. No comparator baseline exists, so no benefit claim is made.

## What went well

* Reading the current records first caught both the M1 gate change and a parallel session's new
  `main` commit; the task branch was based on `60dcc1f` rather than the stale `c8390a6`.
* The existing provider/settings conventions were sufficient; no second configuration framework or
  artifact store was added.
* Offline import isolation, network-denied execution, and mocked-transport tests gave concrete
  evidence for the default-offline invariant.
* The reviewer's concrete reproductions made each repair testable; no finding was dismissed.

## What went poorly

* Credential redaction was repaired path-by-path instead of treating "every report and log output"
  as one defect class from the first round. This caused two extra review submissions.
* The first full-suite capture was taken before the final test additions, so the report/evidence
  needed a new `check-*` capture; earlier logs were retained rather than overwritten.
* The packet manifest initially included the report that is updated after the verdict; later
  manifests exclude the post-verdict report to keep the reviewed snapshot stable.
* The first live probe used a prompt that invited a reasoning model to spend the whole budget
  without producing a final answer. A direct final-answer prompt with an adequate budget fixed the
  probe; the adapter's rejection was correct.

## What to do better

* For a redaction/security finding, enumerate every sink (report returns, CLI output, logs, error
  records, dynamic keys) before repairing, and add one regression per sink.
* Capture the final gate after the last code/test edit, name it by attempt, and cite only that file.
* Freeze the review packet's manifest over code/docs/tests, not over the report section that the
  verdict updates.
* Keep a parallel-session check (`git fetch`, `git log`, `git status`) at every resume; the shared
  checkout can move between planning and implementation.
* Treat "no live configuration" as a first-class `NOT RUN` outcome in the report and packet, not as
  a reason to weaken the offline evidence.
* For reasoning-model probes, ask for a final answer explicitly and budget enough tokens for both
  reasoning and content; do not infer capability from a length-truncated `content: null` response.

## New run rule

**Enumerate the full output surface for any redaction or untrusted-data finding.** When a review
finds credential leakage, fix the shared sanitizer and every sink (report values, dynamic keys,
helper returns, CLI stdout/report, logs, and error records) in one pass, with one regression per
sink. This prevents path-by-path review cycling.

**Give reasoning-model probes a final-answer prompt and budget.** A capability probe must not
mistake a reasoning-only, length-truncated response for a missing chat capability; request a final
answer and reserve tokens for both reasoning and content.
