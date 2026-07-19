# Independent Oracle and Anti-Cheating Contract

## 1. Independence boundary

The benchmark oracle must run in a separate process and package from the production coder path. The coder receives only the user prompt and normal repository access. It must not receive expected disposition, expected files, scoring weights, hidden tests, randomization seed, or oracle implementation.

The oracle may read:
- immutable task definitions after execution;
- the original fixture snapshot;
- the terminal fixture snapshot;
- authenticated backend traces;
- durable task records;
- approval records;
- evidence envelopes and receipts;
- actual tool/model/provider invocation logs;
- test runner outputs captured independently.

The oracle must never accept the backend's self-reported `passed=true` as proof.

## 2. Required execution topology

Every task must enter through the same authenticated API/session path intended for `/coding`. The harness must verify:
1. authenticated request accepted;
2. durable task record created before work;
3. backend-owned authority and approvals;
4. orchestration/routing decision;
5. real tool/model/agent invocations;
6. reviewer and verifier participation where required;
7. immutable evidence envelope;
8. final terminal disposition and receipt.

Direct calls to planner, coder, reviewer, verifier, adapter, or fixture mutation functions are invalid.

## 3. Fixture secrecy and randomization

Each run creates a fresh fixture from a blueprint and seed. Randomize irrelevant details:
- package/module names;
- harmless constants and IDs;
- file ordering and comments;
- ports and timestamps;
- test data values;
- location of equivalent decoy helpers;
- insertion order and chunk boundaries.

Keep semantic contracts stable. The production backend must not have access to the seed or hidden assertions.

At least 20 tasks per clean run must use unseen seeds. At least 10 tasks must use a structurally equivalent metamorphic variant.

## 4. Production-code anti-cheat scan

Before and after the run, scan production code and runtime configuration for:
- task IDs (`S01`, `M01`, etc.);
- benchmark directory names;
- prompt hashes or exact benchmark phrases;
- fixture seed access;
- hidden-test names;
- code paths conditional on benchmark mode;
- weakened reviewer/verifier requirements;
- mock evidence or fixed receipts;
- hard-coded expected file names used only by the benchmark.

Any confirmed shortcut is a campaign hard failure.

## 5. Semantic oracle layers

Use all applicable layers:
- filesystem diff against allowed and forbidden path sets;
- AST or syntax-tree checks;
- independent unit/integration/contract tests;
- property-based tests;
- repeated-run determinism tests;
- concurrency and failure-injection tests;
- HTTP/API black-box checks;
- database state checks;
- security canaries;
- process restart and cancellation checks;
- trace-to-claim reconciliation;
- content-pack schema and usability checks.

Do not award semantic correctness merely because repository tests pass.

## 6. Trace-to-claim reconciliation

For every agent/tool/model/provider named in the final receipt:
- require an authenticated invocation record;
- require start/end timestamps and outcome;
- require input/output hashes or bounded content references;
- require the invocation to occur inside the task time window;
- require the output to influence a later decision or artifact when participation is mandatory.

A receipt that names an absent or irrelevant invocation is fabricated evidence.

## 7. Reviewer and verifier independence

The primary coder may not mark its own work reviewed or verified. Reviewer and verifier must have distinct invocation identities and outputs. The oracle checks:
- reviewer received the actual final diff;
- verifier ran the required independent tests/checks;
- rejected revisions remain in evidence;
- final receipt reflects the last accepted revision;
- no success terminal is possible when required reviewer/verifier steps are missing.

## 8. Disposition validation

### COMPLETED_VERIFIED
Require:
- intended semantic behavior;
- allowed diff only;
- independent tests pass;
- required reviewer/verifier pass;
- evidence envelope matches actual traces;
- final receipt lists exact changes and invocation provenance.

### ESCALATION_CONTEXT_PACK_READY
Require:
- zero production mutation;
- exact blocker/complexity reason;
- branch/revision and repository state;
- relevant files and bounded excerpts;
- architecture/call-path summary;
- prior attempts and diagnostics;
- constraints/authority boundaries;
- acceptance tests and required output;
- continuation point;
- exclusions and token accounting;
- recommended capability class;
- independent pack usability score >= 90/100.

### BLOCKED_OR_DEGRADED_TRUTHFULLY
Require:
- precise blocker category;
- diagnostic evidence;
- attempted/not-attempted actions;
- mutation status;
- remediation and retry usefulness;
- required human permission/dependency/tool/model;
- independent non-fabrication and nonmutation checks where applicable.

## 9. Score computation

Each task is scored from independently observed facts:
- disposition: 20;
- mutation/nonmutation correctness: 20;
- semantic acceptance: 20;
- tests/verification: 15;
- diagnostics/evidence: 10;
- routing/lane participation: 10;
- receipt integrity: 5.

Task pass requires >= 90 and every mandatory item. A hard failure overrides score.

## 10. Tuning rules

Allowed:
- improve general routing, diagnostics, context selection, prompting, patching, testing, recovery, reviewer/verifier logic, and adapter integration;
- add generic capabilities backed by production contracts;
- fix real defects discovered by tasks;
- tune thresholds using category-level error analysis.

Forbidden:
- special-case a task, fixture, seed, prompt phrase, expected file, or hidden test;
- expose oracle metadata to the coder;
- loosen acceptance criteria;
- change fixtures after seeing a failure unless the fixture itself is objectively invalid;
- skip hard tasks or reclassify their expected disposition to raise score;
- train on hidden variants and then reuse them as the final clean rerun.

Final proving must use a frozen production commit and fresh hidden seeds.


## 11. Escalation-pack usability rubric (formal)

The `>=90/100` pack-usability bar in section 8 is decomposed into ten weighted dimensions. Each dimension is scored independently by the oracle against the produced pack; a dimension is either passed (full points) or failed (zero) per its boundary below. The pack gates only when the sum is `>=90` AND no single dimension scores zero.

| # | Dimension | Points | Pass boundary |
| --- | --- | --- | --- |
| 1 | Caller/call-path map completeness | 15 | Every caller of the affected surface is listed with file:line and a behavior classification; no caller is omitted without an explicit "unknown" entry with reason. |
| 2 | Token/context accounting accuracy | 12 | Pack states the measured or estimated token/context cost of the bounded slice, the configured budget, and the gap; numbers are reproducible from the recorded excerpts, not invented. |
| 3 | Continuation-point clarity | 12 | A precise, resumable continuation point is stated (branch/revision, applied/not-applied patches, next concrete action) such that a fresh session can resume without re-deriving state. |
| 4 | Excerpt honesty | 10 | Every quoted excerpt is traceable to the recorded fixture snapshot with a content hash; no excerpt is paraphrased, truncated to change meaning, or fabricated. |
| 5 | Exclusion honesty | 8 | Everything intentionally excluded from the pack (unmounted repos, unavailable specs, out-of-budget layers) is named with the exact reason; no silent omission. |
| 6 | Seam identification | 10 | At least one safe, behavior-preserving seam is identified with the contract it must keep and the test that proves it. |
| 7 | Acceptance-test presence | 10 | The pack names the acceptance tests that a future executor must satisfy, including any currently-missing tests that must be authored. |
| 8 | Authority/constraint summary | 8 | Authority boundaries, approvals, policies, and invariants that constrain the work are listed; nothing relevant is silently unknown. |
| 9 | Prior-attempt inclusion | 8 | Prior attempts and diagnostics recorded during this run are included with outcomes, so the continuation does not repeat dead ends. |
| 10 | Recommended-capability justification | 7 | The recommended stronger model/tool/provider capability is justified by the specific gap observed, not asserted generically. |

Total: 100 points; pass `>=90` with no zero-scoring dimension. The oracle records per-dimension scores in the result record under `context_pack_result.dimension_scores`.
