# SpiritOS Foundation Remediation R1 Goal

## Objective

Repair the shared SpiritOS coding foundation from Campaign 2 engineering commit
`2b8ead66578d7f7053c01cb987e011b763c1c03d`. Restore production-valid Campaign 1
authority guarantees, make the Campaign 2 coding orchestrator the live backend owner,
and close only after a clean, source-bound production proving run is immutably anchored.

The only valid terminal verdict is `SPIRITOS_FOUNDATION_REMEDIATION_COMPLETE`.

## Product scope

- Source Proxy: coding task creation, orchestration, context, lane contracts, model
  routing, approval, execution, review, verification, anti-cheat, evidence, recovery,
  undo/reset, and authoritative task state.
- SpiritFlix: complete administrative mutation bindings and transactional authority.
- Cartographer: persisted proposal selection/review and downstream transfer without
  filesystem, Git, command, queue, or coding authority.
- Design: security preservation only. No new lane or feature expansion.
- Shared architecture: portable authority configuration, immutable evidence,
  validators, recovery anchors, and roadmap correction.

## Explicit exclusions

- Do not implement Scout, Mac, Obsidian, retained coding sub-agents, conflict
  resolution, extended coding lanes, or Campaign 4.
- Do not expand Designer functionality.
- Do not relabel the historical design Campaign 3 as the intended coding campaign.
- Do not create or adopt the pre-existing Campaign 4 goal.
- Do not push.

## Historical claim disposition

- Campaign 1 terminal history is preserved but its production authority claim is not
  accepted by R1 until the replacement gates pass.
- Campaign 2 terminal history is preserved but its production-orchestrator claim is
  not accepted by R1 until the live importer, state machine, contracts, participants,
  and proving task pass.
- Campaign 3 terminal `4aec510409e8bb82386190af9fa8f666efcbc63e` is classified
  `CAMPAIGN_3_SCOPE_DIVERGED_TO_DESIGN`. It is historical work, not a prerequisite.

## Terminal invariants

R1 may close only when all of the following are true:

1. Protected refs still resolve to their recorded commits.
2. No production writer bypasses canonical authority.
3. Mutation bindings cover every material input and expected/resulting state hash.
4. Success finalization occurs only after independent review, verification,
   anti-cheat, and evidence invocations pass against one immutable artifact identity.
5. The live HTTP task route is owned by the persisted CodingOrchestrator.
6. Runtime producer/consumer contract compatibility and output consumption are
   enforced, not merely catalogued.
7. Source Proxy task state is authoritative; any frontend store is a bounded view.
8. Prompts 1-10 each have executable, target-owned Python behavior and specifications.
9. A fresh isolated production run proves Cartographer transfer, model-authored diff,
   approval/apply, participants, recovery, undo/reset, clean rerun, and revocation.
10. The terminal receipt is content-addressed, source/build bound, redaction checked,
    claim-ceiling limited, and reachable from the verified recovery bundle.

Self-declared GO fields, test-only imports, callback labels, and mutable ignored
receipts are never sufficient proof.
