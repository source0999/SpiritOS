# Campaign 2 Goal — Resume Here

This is the first file to read when resuming Campaign 2. Full scope, gate anchors, and rules are in [campaign-2-plan.md](campaign-2-plan.md). Machine-readable state is in [campaign-2-state.json](campaign-2-state.json).

## Canonical goal

The single canonical Campaign 2 goal is the evidence-grounded **"Campaign goal and terminal verdict"** section in [campaign-2-plan.md](campaign-2-plan.md). This resume artifact deliberately links to that statement instead of restating an abbreviated mechanism. It defines the operator-visible reliability gap, measurable end state, gate traceability, and the sole terminal condition: `CAMPAIGN_2_CORE_CODING_OS_STABLE` only after the clean-baseline proving task, controlled failure injection-and-recovery, and a clean rerun all pass.

## Where things stand

- Worktree: `/home/source/SpiritOS-campaign-2-20260716`
- Branch: `codex/spiritos-campaign-2-core-coding-os-20260716`
- Base: `8a20473c` (Campaign 1 terminal tip — do not mutate the Campaign 1 worktree)
- Next gate: `gate_2_1_versioned_lane_registry_and_contracts`
- Completed gates: none yet
- Check completion anytime: `python3 scripts/campaign2-autoloop-completion.py --state docs/architecture/campaign-2-state.json --ledger docs/architecture/campaign-2-ledger.md`

## The gates, in order (do not skip ahead)

1. **Gate 2.1** Versioned canonical lane registry and contracts (EXTEND + BUILD)
2. **Gate 2.2** Canonical orchestrator and lane-state machine (BUILD)
3. **Gate 2.3** Canonical context broker and consumption acknowledgement (ADOPT)
4. **Gate 2.4** Source Proxy routing, health, fallback truthfulness (EXTEND)
5. **Gate 2.5** TypeScript and Python target-plugin adapter reconciliation (ADOPT + reconcile)
6. **Gate 2.6** Canonical executor and lane-scoped authority (ADOPT + BUILD)
7. **Gate 2.7** Reviewer, verifier, anti-cheat, evidence identity binding (ADOPT)
8. **Gate 2.8** Cartographer core discovery/proposal integration (ADOPT + BUILD)
9. **Gate 2.9** Task lifecycle reliability and recovery (EXTEND)
10. **Gate 2.10** Canonical shell observability (EXTEND)
11. **Gate 2.11** Core proving task and final acceptance (BUILD execution; ADOPT battery)

Do not begin a later gate while an earlier foundational dependency remains structurally incomplete. No later gate may be accepted based on a stub, mock, or future promise in an earlier gate. Each gate's adopt/extend/build verdict and file anchors are in the plan.

## Critical: do not rebuild what already exists

Most of the core coding OS is already built and authoritative. Before writing new code for a gate, read its verdict in the plan. The context broker, executor, approval authority, reviewer, verifier, anti-cheat, evidence envelope, target-plugin identity binding, Cartographer discovery/proposals, and the LumaCart 10-prompt battery all already exist — adopt them. Only the orchestrator, lane-state machine, lane-scoped authority, lane contract schema, fallback layer, Cartographer-executor wiring, and proving-task execution are genuinely net-new.

Naming-collision hazards are documented in the plan (read before naming anything "lane").

## Execution rules for every turn

1. If the worktree has owned uncommitted files that pass their focused tests, commit them as a coherent slice with a scoped message before doing anything else.
2. Implement the next coherent slice toward the current gate.
3. Run focused tests + typecheck. If green, commit with a scoped message. If red, repair within this turn and re-run; do not stop on an ordinary test failure.
4. When a gate is genuinely complete, update `campaign-2-state.json` (move the gate into `completed_gate_ids`, advance `next_gate_id`), append a row to the ledger's gate-status table, and record the commit.
5. Continue to the next slice in the same turn. Do not end the turn after one commit. Keep going until you hit a REAL critical blocker or Campaign 2 reaches GO.
6. When you discover something not in the plan, classify it (`mandatory-c2` / `deferred-c3` / `deferred-c4-repair` / `deferred-later-coding` / `obsolete-removable`) in the ledger's discovery log. Do not absorb it into Campaign 2 silently.
7. Do not touch protected product branches (Source Proxy, SpiritFlix, architecture-audit, Campaign 1 worktree). Do not push. Do not use `git add -A`.

## When to stop

Stop only for a REAL critical blocker: SSH down, irreconcilable product intent, missing unique data, hardware failure, or a credential genuinely unavailable after checking. Ordinary test failures, ordinary commits, and ordinary "another slice remains" are NOT stop conditions — repair and continue.

When you must stop on a real critical blocker, end with a single line:

```
TURN_ENDED_CAMPAIGN_2_BLOCKED - reason: <reason>
```

Otherwise, keep working until the completion evaluator prints `CAMPAIGN_2_COMPLETE`.
