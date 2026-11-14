# Canonical acceptance specification for AI-03 (#32), M3 — REFINEMENT DRAFT / RE-SCOPE PROPOSED.
# Applies only if the owner adopts the proposed re-scope from CTA-owned embedding refresh to the
# retrieval snapshot/cache lifecycle. See docs/adr/0012-closeout-scope-decisions.md.
@AI-03 @issue-32 @M3 @refinement-draft
Feature: AI-03: Revision-aware retrieval snapshot and cache lifecycle
  CTA owns content-change planning, manifests, isolated snapshot publication, compatibility, and
  candidate provenance. CocoIndex owns code chunking, embeddings, and its internal index.

  Rule: Refresh planning uses artifact content and explicit configuration

    @SCN-3301
    Scenario: Plan the banking fixture content changes
      Given a retrieval manifest for banking-demo baseline-a
      And the eligible corpus contains source and test artifacts
      When the refresh planner compares baseline-a with baseline-b
      Then changed artifacts are exactly CODE-001 and TEST-002
      And unchanged artifacts are exactly CODE-002 and TEST-001
      And the manifest records both resolved revisions and their artifact content hashes
      And the plan does not claim that CocoIndex embedded exactly two items

    @SCN-3302
    Scenario: An evidence-only commit permits content reuse
      Given two commits have identical eligible artifact IDs, paths, and content hashes
      And their model and retrieval configuration are identical
      When refresh manifests are built for both commits
      Then both manifests have the same corpus cache key
      And their snapshot bindings identify their respective commits
      And the content-change plan is empty
      And no source change or verification failure is inferred from the different commits

    @SCN-3303
    Scenario: A model change invalidates compatibility
      Given an existing manifest and unchanged artifact content
      When a manifest is requested with a different weights digest
      Then the corpus cache key differs
      And the old cache is not declared compatible with the new model
      And the old manifest remains unchanged

  Rule: Snapshot publication and result combination preserve one provenance context

    @SCN-3304
    Scenario: Failed refresh leaves the previous snapshot usable
      Given baseline-a has a published retrieval manifest
      And the deterministic index adapter fails while building baseline-b
      When refresh is requested for baseline-b
      Then refresh reports a typed failure
      And no baseline-b snapshot is published
      And requests explicitly naming baseline-a still use its original manifest
      And requests naming baseline-b do not receive baseline-a results as a substitute

    @SCN-3305
    Scenario: Mixed snapshot candidates cannot form one ranked list
      Given one candidate batch is bound to baseline-a
      And another candidate batch is bound to baseline-b
      When the batches are submitted to the candidate-combination service
      Then combination fails with code "mixed-index-context"
      And no combined ranked list is returned

    @SCN-3306
    Scenario: Refresh cost distinguishes measurements from unavailable backend data
      Given the deterministic search transport exposes no embedding counter
      When a baseline-b refresh completes
      Then its report contains measured non-negative elapsed time
      And it contains added, changed, removed, and unchanged artifact counts
      And items_embedded is null with availability "not_available"
      And the report identifies the published snapshot binding and configuration digest
