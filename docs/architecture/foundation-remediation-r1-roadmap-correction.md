# SpiritOS Roadmap Correction After Foundation Remediation R1

## Closeout provenance

Foundation Remediation R1 accepts source commit
`ec204d63e431d10501c67db0264082db6e4d31e4`. Candidate
`d6dd49438ef186c6e28cf33276434b0c609aa471` was rejected and carries no terminal
acceptance. The accepted source includes the terminal-independent completion
regression repair; a clean production reproof and all 22 registered profiles then
passed against that accepted source.

The next campaign must start from terminal commit `E` obtained by dereferencing
annotated tag `foundation-remediation-r1-terminal-20260718T120047Z^{commit}`. Its
first parent must be the accepted source above. It must not start from the rejected
candidate, a mutable branch tip, or pre-remediation history.

## Historical classification

The exact disposition of the prior design-lane work remains
`CAMPAIGN_3_SCOPE_DIVERGED_TO_DESIGN`.

Preserve branch `codex/spiritos-campaign-3-core-design-lane-20260717` and terminal
commit `4aec510409e8bb82386190af9fa8f666efcbc63e` as protected historical design work.
Do not rename or rewrite it, and do not accept it as completion of the intended
coding Campaign 3. Any later reuse requires separately reviewed changes based on its
actual design scope; reuse does not alter the classification.

Foundation Remediation R1 repaired the production coding foundation and proof
boundary. It deliberately did not implement the intended Campaign 3 expansion and
did not begin or adopt Campaign 4. This roadmap correction is planning, not campaign
start.

## Intended coding Campaign 3 sequence

Proceed through explicit, source-bound gates in this order:

1. **Scope and contract baseline.** Freeze the R1 tag-derived base, enumerate every
   new producer, consumer, authority boundary, failure mode, and proof claim, and add
   fail-closed validators before enabling a new lane.
2. **Scout and search.** Integrate Scout and approved search providers as truthful
   research lanes. Persist request, provider, source, filtering, attribution,
   freshness, output, consumption, skip, timeout, and failure evidence. Missing or
   unusable results are skipped or degraded, never synthesized as used.
3. **Obsidian context.** Add bounded, read-only Obsidian retrieval with vault/path
   allowlists, provenance, redaction, snapshot identity, prompt consumption, and
   explicit unavailable or stale outcomes. Retrieved notes remain context, not
   coding or filesystem authority.
4. **Mac worker and frameworks.** Define a mutually authenticated Mac worker
   protocol and versioned framework/toolchain capabilities. Bind dispatch,
   workspace, source, environment, artifact, cancellation, timeout, revocation, and
   result acknowledgement. Remote execution must not bypass canonical approval,
   apply, review, verification, evidence, or recovery ownership.
5. **Retained subagents and conflicts.** Make retained-subagent identity, lease,
   context version, budget, output, acknowledgement, expiry, and revocation durable.
   Detect overlapping edits, stale bases, target-ownership violations, and
   incompatible proposals deterministically. Conflict resolution must be explicit,
   operator-visible, reproducible, and unable to overwrite a newer artifact.
6. **Observability and degradation.** Expose one backend-owned lineage for lane
   selection, queueing, latency, retries, fallback, partial availability, circuit
   state, provider/model replacement, claim-ceiling reduction, and final outcome.
   UI status must project durable truth. Degradation must preserve a declared lower
   claim or fail closed, never masquerade as full-lane success.
7. **Genuine all-lane proof and `/coding` harness readiness.** Before wiring the user
   surface, exercise the production orchestrator with Scout/search, Obsidian, Mac
   execution/frameworks, retained subagents, conflict handling, reviewer, verifier,
   anti-cheat, evidence, recovery, and revocation boundaries. Require real
   process/provider outputs, durable producer-consumer acknowledgements,
   model-authored non-empty work, controlled failures, undo/reset, and a clean
   rerun. Test-only injection, synthesized lane status, or an identity-only
   lifecycle is not proof. The `/coding` harness is ready only when it can observe
   and verify this lineage without becoming a second source of truth.
8. **`/coding` wiring.** Only after all-lane readiness passes, connect the `/coding`
   route and interface to the canonical backend lifecycle. The surface may submit
   intent, approval, cancellation, and operator decisions and render projections;
   it must not own decision-bearing state or bypass runtime contracts.
9. **Coder 10 validation.** Finish with a fresh ten-case Coder battery spanning
   productive edits, truthful no-op, protected-path refusal, research and Obsidian
   context, Mac capability use, retained-agent continuity, edit conflicts, provider
   degradation and recovery, approval/apply, independent verification, undo/reset,
   and clean rerun. Every case must bind exact source, task, context, lane
   invocations, artifact/diff, approvals, participant outputs, result, and claim
   ceiling in immutable evidence.

Each gate requires focused regressions and production evidence. Unit tests,
catalogued lane metadata, callbacks, or UI labels cannot substitute for live output
consumption and durable lineage.

## Campaign boundary

- Campaign 3 was not started by Foundation Remediation R1.
- Campaign 4 was not started or adopted by Foundation Remediation R1.
- The historical design branch remains protected evidence, not the base or terminal
  proof for the intended coding Campaign 3.
- No future campaign may close without its own source-bound all-lane proof,
  validators, immutable receipt, annotated tag, and recovery anchor.
