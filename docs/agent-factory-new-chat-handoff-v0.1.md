# Agent Factory New Chat Handoff v0.1

## Current objective

Continue from the completed Agent Factory planning package in `docs/agent-factory-roadmap-v0.1.md`.

## Current status

The planning package is docs-only. Plan 1 Phase 1 docs-only contracts and operating rules were already written during planning-package consolidation in `docs/agent-factory-phase-1-docs-only-agent-contracts-v0.1.md`. No runtime helpers are authorized yet.

The next eligible work is a new Codex chat that reviews and ratifies the existing Plan 1 Phase 1 docs. That chat must not pretend Phase 1 was unwritten. It may proceed only to the next valid Plan 1 phase if the roadmap allows it and Britton explicitly approves.

## Files to read first

- `docs/agent-factory-roadmap-v0.1.md`
- `docs/agent-factory-new-chat-handoff-v0.1.md`
- `docs/agent-factory-phase-1-docs-only-agent-contracts-v0.1.md`
- `docs/agent-factory-planning-package-closeout-v0.1.md`
- `docs/agent-factory-plan-1-new-chat-start-prompt-v0.1.md`

## Workflow

- Run baseline git status.
- State active plan/phase/increment.
- Name allowed files.
- Treat existing Plan 1 Phase 1 docs as already written.
- First review and ratify the existing contracts and operating rules.
- Do not rewrite them unless something is missing.
- Complete one small increment at a time only after the ratification step.
- Run that increment check.
- Continue within the same plan phase if clean.
- Use short docs-only spot-checks for planning-only docs.
- Use larger manual checks only when source code, tests, runtime helpers, or authority boundaries are touched.
- At plan end, output a short closeout and next handoff target.
- Ask permission before the next phase or next plan.
- Never infer permission.

## Stop conditions

- Any request to edit `source_proxy`, `src`, `scout`, package/config/env, tests, or existing active Proxy/Cartographer docs without explicit approval.
- Any request to implement runtime helpers before the dependency gate.
- Any request to grant apply, commit, push, command execution, branch, worktree, queue execution, self-approval, or background autonomy.
- Any unexpected dirty file caused by this lane.
- Any attempt to treat roadmap-writing as Phase 2 or implementation work.
- Any attempt to write the next handoff prompt before Britton explicitly asks for it.

## Next recommended permission phrase

Use the copy-paste prompt in `docs/agent-factory-plan-1-new-chat-start-prompt-v0.1.md`.

## Short planning spot-check

```bash
cd /home/source/SpiritOS

git status --branch --short
test -f docs/agent-factory-roadmap-v0.1.md && echo "roadmap exists"
test -f docs/agent-factory-new-chat-handoff-v0.1.md && echo "handoff exists"
git diff --check -- docs/agent-factory-*.md
grep -nE "Plan 1:|Plan 2:|Plan 3:|Plan 4:|Plan 5:|Plan 6:|Plan 7:|Plan 8:|Plan 9:|READY FOR HANDOFF PROMPT" docs/agent-factory-roadmap-v0.1.md
```

Expected final result:

- Both docs exist.
- `git diff --check` passes for both docs.
- The roadmap clearly names Plan 1 through Plan 9.
- Existing unrelated dirty work may remain, but no unrelated file is changed by this task.
- No runtime, test, UI, package, config, Scout, Source Proxy, or Cartographer implementation files are touched.

Final planning-package line:

READY FOR HANDOFF PROMPT:
Agent Factory Plan 1 Phase 1 can start in a new chat.
