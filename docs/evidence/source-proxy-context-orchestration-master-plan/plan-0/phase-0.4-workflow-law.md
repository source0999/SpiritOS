# Plan 0 Phase 0.4: Workflow Definitions and Pivot Law

Status: GO

Execution boundary: docs/evidence only. No runtime behavior changes in this phase. No coder trials.

## Increment 0.4.1: Definitions

Preview:

- A route, UI surface, packet draft, fixture, screenshot, model-proof shell, or demo exists.
- Preview is not accepted integration.
- Preview cannot imply production readiness.
- Preview cannot apply, commit, push, enqueue continuation, or run background workers.

Advisory:

- A subsystem can produce visible guidance, critique, test notes, source packets, task packets, or handoff text.
- Advisory output may inform Source Proxy.
- Advisory output does not mutate the repo.
- Advisory output does not become accepted unless Source Proxy records how it was used, skipped, or blocked.

Integrated:

- Source Proxy invokes the subsystem in the real `/coding` hot path.
- The subsystem returns a task-specific packet or a visible skipped/blocked reason.
- The final coder packet includes the subsystem status.
- The durable run receipt stores the packet, route truth, output-contract version, and used/skipped/blocked diagnostics.
- The coder receives the final packet.

Production-ready:

- Integrated behavior is covered by positive tests, negative tests, durable receipts, source-status diagnostics, no-hidden-mutation proof, and A+ gauntlet evidence.
- Production-ready status cannot be granted from route existence, preview success, docs, or Repomix-only context.

Result: PASS. Definitions are explicit.

## Increment 0.4.2: Codex Pivot Workflow Law

Execution law:

1. Complete one increment.
2. Test or check that increment.
3. Write increment evidence.
4. Decide GO/NO-GO.
5. Move to the next increment only if GO.
6. Close each phase before starting the next phase.
7. Close each plan before starting the next plan.
8. Stop and ask Britton before starting the next plan.

Evidence law:

- Every increment must name commands/checks run or explain why no safe command exists.
- Every increment must list files inspected or changed.
- Every increment must record result and next permitted increment.
- Every context source must report `used`, `skipped`, or `blocked`.
- Every model route must report alias, provider, routed model, and actual configured default when checked.
- Every output-contract failure must include a specific diagnostic.

Mutation law:

- No hidden apply.
- No hidden commit.
- No hidden push.
- No hidden background worker.
- No silent queue continuation.
- No hidden Scout memory writes.
- No Coder 50 or Coder 100 until the basic A+ gauntlet passes.
- No 14B default switch until it passes output-contract tests and Britton approves.

Result: PASS. Pivot law is explicit.

## Increment 0.4.3: Stop Gates and Plan 1 Handoff

Plan gate law:

- Plan 0 may close only after baseline, route inventory, model truth, and workflow law are complete.
- Plan 1 may not start in the same turn unless Britton explicitly approves after reviewing Plan 0 closeout.
- If Plan 1 is approved later, it starts with output contract, parser, and repair discipline only.

Exact operator handoff for Plan 1:

> Britton, Plan 0 is closed with GO evidence. Do you approve starting Plan 1: Output Contract, Parser, and Repair Discipline?

Result: PASS. Stop gate and handoff are explicit.

## Phase 0.4 Closeout

Checks passed:

- Preview, advisory, integrated, and production-ready are defined.
- Increment/phase/plan pivot law is written.
- No-preview-only, no-route-exists, no-docs-only, and no-Repomix-only policies are reinforced.
- Plan 1 handoff is exact and requires Britton approval.

GO/NO-GO: GO to Plan 0 closeout.

Next permitted step: Plan 0 closeout only.
