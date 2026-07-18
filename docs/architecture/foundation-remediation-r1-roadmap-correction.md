# SpiritOS Roadmap Correction After Foundation Remediation R1

## Historical classification

The exact disposition of the prior design-lane work is
`CAMPAIGN_3_SCOPE_DIVERGED_TO_DESIGN`.

Preserve branch `codex/spiritos-campaign-3-core-design-lane-20260717` and its terminal
commit `4aec510409e8bb82386190af9fa8f666efcbc63e` as protected historical design work.
Do not rename it, rewrite it, or accept it as completion of the intended coding
Campaign 3. Any later reuse requires a separately reviewed change based on its actual
design scope; reuse does not alter the classification.

## Correct starting point

The next campaign must branch from the verified Foundation Remediation R1 terminal
commit obtained by dereferencing annotated tag
`foundation-remediation-r1-terminal-20260718T102845Z^{commit}`. Its first parent must
remain frozen source commit `ce854e613d748581938137b20b79163ec85eca5d`.
Do not start from the historical design branch, the pre-remediation Campaign 2 tip,
or an untagged mutable checkout.

Foundation Remediation R1 repaired the production coding foundation and its proof
boundary. It deliberately did not implement the intended Campaign 3 expansion and
did not begin Campaign 4. Authoring this correction is planning, not campaign start.

## Intended coding Campaign 3 sequence

The next campaign should proceed through explicit, source-bound gates in this order:

1. **Scope and contract baseline.** Freeze the R1 tag-derived base, enumerate every
   new producer, consumer, authority boundary, failure mode, and proof claim, and add
   fail-closed validators before enabling a new lane.
2. **Scout and search.** Integrate Scout and approved search providers as truthful
   research lanes. Persist request, provider, source, filtering, attribution,
   freshness, output, consumption, skip, timeout, and failure evidence. A missing or
   unusable result must be recorded as skipped or degraded, never synthesized as
   used.
3. **Obsidian context.** Add bounded, read-only Obsidian retrieval with vault/path
   allowlists, provenance, redaction, snapshot identity, prompt consumption, and
   explicit unavailable/stale outcomes. Retrieved notes remain context, not coding
   or filesystem authority.
4. **Mac worker and frameworks.** Define a mutually authenticated Mac worker
   protocol and versioned framework/toolchain capabilities. Bind dispatch,
   workspace, source, environment, artifact, cancellation, timeout, revocation, and
   result acknowledgement. Remote execution must not bypass canonical approval,
   apply, review, verification, evidence, or recovery ownership.
5. **Retained subagents and conflicts.** Make retained subagent identity, lease,
   context version, budget, output, acknowledgement, expiry, and revocation durable.
   Add deterministic conflict detection for overlapping edits, stale bases, target
   ownership, and incompatible proposals. Conflict resolution must be explicit,
   operator-visible, reproducible, and incapable of silently merging authority or
   overwriting a newer artifact.
6. **Observability and degradation.** Expose one backend-owned lineage for lane
   selection, queueing, latency, retries, fallback, partial availability, circuit
   state, model/provider replacement, claim-ceiling reduction, and final outcome.
   UI status must project durable truth. Degradation must either preserve a declared
   lower claim or fail closed; it must never be presented as full-lane success.
7. **Genuine all-lane proof and `/coding` harness readiness.** Before wiring the user
   surface, exercise the real production orchestrator with Scout/search, Obsidian,
   Mac execution/frameworks, retained subagents, conflict handling, reviewer,
   verifier, anti-cheat, evidence, recovery, and revocation boundaries. Require real
   process/provider outputs, durable producer-consumer acknowledgements, model-authored
   non-empty work, controlled failures, undo/reset, and a clean rerun. Test-only
   injection, synthesized lane status, or an identity-only lifecycle is not proof.
   The `/coding` harness may be declared ready only when it can observe and verify
   this lineage without becoming a second source of truth.
8. **`/coding` wiring.** Only after the all-lane readiness gate passes, connect the
   `/coding` route and interface to the canonical backend lifecycle. The surface may
   submit intent, approval, cancellation, and operator decisions and may render
   projections; it must not own decision-bearing state or bypass runtime contracts.
9. **Coder 10 validation.** Finish with a fresh ten-case Coder validation battery
   spanning productive edits, truthful no-op, protected-path refusal, research and
   Obsidian context, Mac capability use, retained-agent continuity, edit conflicts,
   provider degradation/recovery, approval/apply, independent verification,
   undo/reset, and clean rerun. Each case must bind exact source, task, context,
   lane invocations, artifact/diff, approvals, participant outputs, result, and claim
   ceiling in immutable evidence.

Each gate needs focused regressions plus production evidence. Passing unit tests,
catalogued lane metadata, callbacks, or UI labels cannot substitute for live output
consumption and durable lineage.

## Campaign boundary

- Campaign 3 was not started by Foundation Remediation R1.
- Campaign 4 was not started or adopted by Foundation Remediation R1.
- The historical design branch remains protected evidence, not the base or terminal
  proof for the intended coding Campaign 3.
- No future campaign is ready to close until its own source-bound all-lane proof,
  validators, immutable receipt, annotated tag, and recovery anchor pass.
