# Source Proxy Codex-Class New Chat Handoff v1.0

status: active handoff

Status date: 2026-05-22
Owner: Britton

## Current Objective

Continue the Source Proxy `/coding` production roadmap from the active master plan:

`docs/source-proxy-codex-class-production-master-plan-v1.0.md`

The objective is to take Source Proxy `/coding` from its current state to a fully functional, polished Codex-class coding cockpit through Britton's phase/increment workflow.

Functional proof first. Workflow and provider features second. Visual polish last.

## Current Phase

If this prompt has not been completed, start at Phase 0: Master plan consolidation and authority reset.

If this prompt has been completed and Britton approves the Phase 0 closeout, start at Phase 1: Plain-English Coding Intake and Self-Scoping.

Do not infer approval from the existence of the files. Britton must approve moving from Phase 0 to Phase 1 after the Phase 0 big terminal check passes.

## Files To Read First

Read these before doing any work:

1. `docs/source-proxy-codex-class-production-master-plan-v1.0.md`
2. `docs/source-proxy-codex-class-new-chat-handoff-v1.0.md`
3. `docs/plan-index.md`
4. `docs/source-proxy-production-hardening-plan.md`
5. `docs/source-proxy-coding-agent-a-plus-stress-gauntlet.md`
6. `docs/coding-command-center-voidcore-foundation-closeout-v0.1.md`
7. `docs/source-proxy-regression-matrix.md`
8. `docs/source-proxy-daily-use-runbook.md`
9. `src/app/coding/page.tsx`
10. `src/components/coding/CodingCommandCenterShell.tsx`
11. `src/lib/coding/`
12. `source_proxy/tests/`

Read runtime files for context only unless the active phase and increment explicitly authorize editing them.

## Exact First Thing The New Chat Should Do

Run baseline status and state the active phase/increment before making any edits:

```bash
cd /home/source/SpiritOS
git status --branch --short
```

Then say which phase and increment are active and list the allowed files or lane before changing anything.

## Workflow Rules

Use Britton's required workflow:

1. Run baseline status.
2. Implement exactly one small increment.
3. Run that increment's check yourself.
4. Record result.
5. If PASS and no authority boundary was crossed, move to the next increment in the same phase.
6. If FAIL, repair within scope, rerun checks, then stop with blocker if still failing.
7. If an approval/apply/commit/push/worktree/package/server/auth/config/env boundary appears, stop and ask Britton.
8. At phase end, produce phase closeout.
9. Ask Britton to run the big terminal check.
10. Ask permission before the next phase.

Do not ask Britton to verify every small increment unless a human boundary is hit. Codex should run the increment checks. Britton gets the big phase closeout check.

## Forbidden Actions

Do not run or perform these unless a later explicit phase/increment approval allows the exact action:

- apply
- execute-approved
- commit
- push
- stash
- reset
- clean
- package install
- server restart
- worktree creation
- branch mutation
- external network or API cost
- auth, config, or env changes
- edits outside the approved lane
- protected path edits
- secret, token, certificate, credential, or `.env*` edits

For this handoff, also preserve these start rules:

Do not jump into feature work.

Do not start UI polish.

Do not start model switching.

Do not start live previews.

Start with the active phase and use the phase/increment workflow.

## Expected Output Style After Each Increment

Use this compact format:

```text
Increment:
Files changed:
Checks run:
Result:
Evidence:
Blockers:
Next increment:
```

If the result is `FAIL`, repair within the approved lane and rerun checks. If still failing, stop with a blocker.

If the result is `BLOCKED`, do not continue to the next increment until Britton resolves or approves the boundary.

## Expected Output Style After Each Phase

Use this closeout format:

```text
Phase:
Files changed:
What was added:
What was intentionally not changed:
Verification results:
Current phase status:
Recommended next phase:
Big manual check for Britton:
Permission question:
```

At the end of every phase, provide one big manual check block for Britton to run in terminal, then ask permission before the next phase.

## Phase 0 Completion Marker

Phase 0 is complete only when:

- `docs/source-proxy-codex-class-production-master-plan-v1.0.md` exists.
- `docs/source-proxy-codex-class-new-chat-handoff-v1.0.md` exists.
- `docs/plan-index.md` references both files.
- Required Phase 0 verification passes.
- Codex has asked Britton for permission before Phase 1.

## Phase 1 Start Rule

Phase 1 starts only after Britton approves:

`Phase 1: Plain-English Coding Intake and Self-Scoping`

Do not begin Phase 1 by editing UI polish, provider routing, live previews, parallel workers, workspaces, or release hardening. Start with the Phase 1 active increment from the master plan.
