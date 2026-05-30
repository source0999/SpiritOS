# Agent Factory Plan 1 New Chat Start Prompt v0.1

## copy-paste prompt

Use this in a new Codex chat.

```text
You are taking over Agent Factory planning work in /home/source/SpiritOS.

Start in:
/home/source/SpiritOS

Read these docs first:
- docs/agent-factory-roadmap-v0.1.md
- docs/agent-factory-new-chat-handoff-v0.1.md
- docs/agent-factory-phase-1-docs-only-agent-contracts-v0.1.md
- docs/agent-factory-planning-package-closeout-v0.1.md
- docs/agent-factory-plan-1-new-chat-start-prompt-v0.1.md

Important correction:
Plan 1 Phase 1 docs-only contracts and operating rules were already written in docs/agent-factory-phase-1-docs-only-agent-contracts-v0.1.md during planning-package consolidation.

Do not pretend Plan 1 Phase 1 has not started.
Do not rewrite the existing Plan 1 Phase 1 contracts unless something is missing, contradictory, or unsafe.

Your first task is to review and ratify the existing Plan 1 Phase 1 docs-only contracts and operating rules.

Active work:
Agent Factory Plan 1 review and ratification.

Before editing anything, state:
- active plan
- active phase
- active increment
- allowed files
- forbidden files/actions
- whether the current step is review-only or edit-authorized

Baseline:
cd /home/source/SpiritOS
git status --branch --short
git diff --check -- docs/agent-factory-*.md

Review target:
- Confirm docs/agent-factory-roadmap-v0.1.md has the Plan 1 through Plan 9 sequence.
- Confirm docs/agent-factory-phase-1-docs-only-agent-contracts-v0.1.md already contains Plan 1 Phase 1 docs-only contracts and operating rules.
- Confirm the existing contracts do not grant approval, apply, write, command execution, workflow execution, queue execution, commit, push, branch/worktree, self-approval, or background autonomy.
- Confirm the operating rules include dirty worktree handling, one-lane planning, authority crossings, allowed files, forbidden actions, stop conditions, and short planning-check style.

If the review passes:
- Ratify the existing Plan 1 Phase 1 docs in a short docs-only note if the roadmap or closeout says such a note is allowed.
- Then proceed only to the next valid Plan 1 phase if the roadmap says it is allowed and Britton explicitly approves it in this new chat.

If the review finds a gap:
- Fix only the missing or unsafe Agent Factory planning doc content.
- Stay within the allowed files.
- Rerun the focused check once.
- If it still fails, stop with a blocker.

Workflow rules:
- Work one phase at a time.
- Work one increment at a time.
- Codex runs its own checks after each increment.
- Britton gets only a short manual spot-check at phase end for planning docs.
- Ask permission before the next phase.
- Never infer permission.
- Never start Plan 2 unless Britton explicitly approves Plan 2 and the roadmap dependency gates are satisfied.
- Never touch runtime/source files unless the phase explicitly allows it.

Allowed files:
- docs/agent-factory-roadmap-v0.1.md
- docs/agent-factory-new-chat-handoff-v0.1.md
- docs/agent-factory-phase-1-docs-only-agent-contracts-v0.1.md
- docs/agent-factory-planning-package-closeout-v0.1.md
- docs/agent-factory-plan-1-new-chat-start-prompt-v0.1.md

Forbidden:
- source_proxy/**
- src/**
- scout/**
- backend/**
- scripts/**
- config/**
- package.json
- package-lock.json
- tests/**
- existing Source Proxy docs
- existing Cartographer docs
- existing Design docs
- existing Scout docs
- commits
- pushes
- branches
- worktrees
- stash/reset/clean
- runtime helpers
- implementation work
- package installs
- server restarts
- external API calls
- auth/config/env changes

Manual check style:
For planning docs, do not give Britton a huge terminal block. Give only a short spot-check.

Stop conditions:
- Any request to start Plan 2 before dependency gates are satisfied.
- Any request to write runtime helpers.
- Any request to touch source, tests, package, config, auth, environment, or implementation files.
- Any lane-caused dirty file outside the allowed Agent Factory docs.
- Any attempted self-approval or inferred permission.

Final review output format:
1. Active Plan/Phase Reviewed
2. Existing Plan 1 Phase 1 Ratified?
3. Files Changed
4. Codex Self-Checks Run
5. Short Spot Check For Britton
6. Blockers
7. Next Valid Handoff Target

Do not continue to the next phase until Britton explicitly approves it.
```
