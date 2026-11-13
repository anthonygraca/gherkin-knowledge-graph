**Criteria readiness: REVISE.** The PR 1 capability boundary is appropriate: a typed, optional code-search adapter and synthetic smoke can stand alone without registering `CandidateDiscovery`, producing `TraceCandidate`s, changing the API, or completing AI-02/AI-03/AI-05. The main gaps concern snapshot attribution, process bounds, and live-result reporting.

1. **Major — SCN-1002/1007: distinguish configured provenance from observed provenance.**  
   The supplied MCP contract exposes neither project identity nor index identity. A configured root and recorded Git revision do not prove which contents produced an indexed hit. Replace the identity wording with:

   > “The result records the configured project root as caller-supplied context, and reports the server-reported index identity as unavailable.”

   In SCN-1007, replace “index snapshot identity” with:

   > “index isolation/configuration details, indexing outcome, and server-reported index identity or explicit unavailability.”

   Keep independently recorded fixture revision/content hashes separate. Do not substitute a root path, Git SHA, or adapter-generated identifier for an observed index identity.

2. **Major — SCN-1005: working directory is not snapshot confinement.**  
   Cwd, lexical path validation, and an environment allow-list are observable, but do not establish “touches only the configured snapshot”: symlinks, ancestor settings, shared daemons, and configuration-supplied environment values can defeat that implication. Narrow the rule to **configured project selection and validated paths**, then explicitly require live-smoke settings/runtime isolation and validation of returned paths against the intended snapshot. Define symlink handling and prohibit silently falling back to an ancestor project.

3. **Major — SCN-1004: “matching typed error” and termination timing are underspecified.**  
   Use an outline mapping each failure to an exact error code. Define a total deadline covering startup, initialization and search, plus a bounded cleanup interval with terminate/kill/reap behavior. State which owned descendants are cleaned up; do not imply an unrelated shared daemon is terminated. Include early process exit, closed pipes, caller cancellation, and a child that ignores termination.

4. **Major — malformed protocol and compatibility outcomes are missing.**  
   Add cases for malformed JSON/MCP envelopes, mismatched response IDs, missing/non-text result content, MCP `isError`, invalid payload types, and incompatible server name/version/tool schema. Explicitly require that `success=false` with partial results raises an error and returns **no successful hit list**. Verify observed version `0.2.43`; document any broader compatibility policy rather than assuming one.

5. **Major — “bounded” needs measurable limits.**  
   Specify query/filter limits, `limit` boundaries **1 and 100**, rejection of **0 and 101**, and nonnegative offset. Add configurable bounds for response bytes, individual hit content, and captured stderr. Require concurrent stderr draining so a noisy child cannot block search; stderr must not become protocol data. Define rejection of non-finite scores, inconsistent counts, and oversized responses. Treat a valid empty result as success.

6. **Major — SCN-1007 mixes incompatible preconditions and leaves unavailable runs ambiguous.**  
   Its `Given` requires live opt-in, while its final step asserts behavior without opt-in. Split into explicit cases:

   - **No opt-in:** `NOT RUN`, with no process, indexing, or endpoint contact.
   - **Opted in, prerequisite unavailable:** explicit unavailable/failed outcome and reason; never PASS.
   - **Opted in, execution fails:** FAIL/error; never silently skip or downgrade to a successful offline result.
   - **Successful live execution:** PASS only after all smoke checks complete.

   State that an offline suite passing with live tests skipped does not satisfy the live criterion.

7. **Minor — tighten path and normalization semantics in SCN-1002/1003/1005.**  
   “Non-glob” is ambiguous: a literal `src/accounts.py` can be a valid glob pattern. Specify accepted syntax, empty filters, separators, absolute/drive/UNC paths, and `..` components. Define line validity as integer `1 ≤ start_line ≤ end_line`. Reject the entire malformed response rather than returning its valid subset. Preserve duplicate chunks and reported order unless deduplication becomes an explicit requirement.

8. **Minor — strengthen smoke attribution and limit its claim.**  
   Path/range existence alone permits stale or unrelated content. Compare returned code content with the recorded snapshot under a declared comparison rule, and require a hand-selected source-code target without fixing semantic rank or score. Record the adapter’s tested revision, relevant artifact/specification hashes, invocation, configuration and raw report digest. This establishes a bounded integration observation, not retrieval quality or requirement verification.

9. **Minor — separate behavioral checks from inspection and lifecycle records.**  
   SCN-1001’s “no index is read” should say **“no CocoIndex index is accessed”**, since fake discovery may read its own fixture index. Cwd/environment constraints are observable through an offline child-process harness; registration and prohibited capabilities can also have explicit inspection mappings. Replace SCN-1006’s undefined “citation” with “verification or coverage claim.” Indexed instruction-like text may remain ordinary content. Add AI-06/#56 to the issue map and reconcile the roadmap’s M3 concurrency allowance with AGENTS’ stricter milestone ordering before implementation; this advisory grants no gate exception.

No scenario directly claims requirement verification or `.feature` coverage. The phrases **“from one pinned project snapshot”** and **“live integration evidence”** need the attribution qualifications above so reviewers cannot infer stronger provenance or assurance than the smoke demonstrates.

Read-only advisory only; no implementation acceptance verdict or review submission consumed.