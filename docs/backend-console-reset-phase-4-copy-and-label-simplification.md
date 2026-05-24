# Backend Console Reset Phase 4: Copy And Label Simplification

- status: planning-only
- implementation: not started
- parent plan: `docs/backend-console-usability-reset-plan-v0.1.md`
- previous increment: `docs/backend-console-reset-phase-3-static-usability-shell-plan.md`
- target page: `/proxy-backend`
- current HEAD: `40141f34d27d915503f265efba119673a412354a`

## Purpose

This document defines the copy and label rules for a future `/proxy-backend` usability reset.

The goal is to replace confusing language with simple labels and short explanations. The page should use plain words like `Backend API`, `Source Proxy`, `Healthy`, `Blocked`, `Not wired`, and `Next step`.

This is a docs-only increment. It does not edit `src/app/proxy-backend/page.tsx`, `/coding`, `/map`, dashboard files, backend runtime files, `source_proxy`, package/config/env/generated/test files, or Cartographer full-auto roadmap implementation files.

## Copy Goal

Every section should have one clear job.

Every label should answer one of these questions:

- What service is this?
- What state is it in?
- What can I safely do next?
- Where should I go?
- What is intentionally not wired?

If a label requires backend, coding, dashboard, or Cartographer context to understand, it should be rewritten.

## Approved Plain Labels

Service labels:

- `Backend API`
- `Source Proxy`
- `Ollama/local model`
- `Scout`
- `Coding`
- `Cartographer map`
- `Dashboard`

State labels:

- `Healthy`
- `Degraded`
- `Blocked`
- `Offline`
- `Not wired`
- `Planned, not wired`
- `Out of scope`

Action guidance labels:

- `Next step`
- `Check later`
- `Open coding`
- `Open map`
- `Open dashboard`
- `Review blocked items`

Boundary labels:

- `Execution controls: not added`
- `Autonomy controls: not enabled`
- `Read-only data: requires later decision`
- `Backend runtime: out of scope`

## Labels To Avoid

Avoid abstract or overloaded wording such as:

- `operator runtime`
- `autonomy surface`
- `execution plane`
- `modal state`
- `control authority`
- `intervention layer`
- `workflow orchestration`
- `safety substrate`
- `full-auto readiness`
- `agentic backend`

Avoid button-style labels for static planned checks:

- `Run`
- `Start`
- `Stop`
- `Restart`
- `Apply`
- `Commit`
- `Push`
- `Merge`
- `Branch`
- `Worktree`
- `Stash`
- `Checkout`
- `Clean`
- `Delete`

Avoid decorative labels that hide important states:

- `standing by`
- `warming up`
- `awaiting signal`
- `mission control`
- `command deck`
- `neural bridge`

## Section Copy Rules

### Top Area

Use:

```text
Backend Console
Check backend health, proxy status, and safe next actions.
```

Do not use:

```text
Operator control center for autonomous backend orchestration.
```

Reason:

- The top area should explain the page in one breath.
- It should not imply execution, autonomy, or command authority.

### System Status

Use short row copy:

```text
Backend API
Planned, not wired
Live status requires a later read-only wiring decision.
```

Copy pattern:

- service name
- state label
- one-line explanation

Do not include long safety explanations in each row.

### Safe Checks

Use:

```text
Backend health check
Planned, not wired
```

Do not use:

```text
Run backend health check
```

Reason:

- Phase 4 copy must not make a static planned check look executable.

### Current Workflows

Use:

```text
Open coding
Coding command center for coding agent workflow.

Open map
Cartographer manual control center.

Open dashboard
Overview-only dashboard.
```

Rules:

- Navigation labels may say `Open`.
- Navigation labels must point to normal links only.
- Navigation labels must not imply backend execution.

### Blocked Or Not Wired

Use:

```text
Execution controls: not added
Autonomy controls: not enabled
Read-only data: requires later decision
Backend runtime: out of scope
```

Rules:

- Keep blocked states visible.
- Keep explanations short.
- Do not turn blocked states into a large warning wall.

### Debug Notes

Use plain implementation facts:

```text
Current route delegates to CodingAgentInterface.
Future implementation surface is src/app/proxy-backend/page.tsx.
```

Rules:

- Debug notes belong lower on the page.
- Debug notes should not define the main user experience.

## Five-Second Rewrite Test

For each label, ask:

- Would a tired operator understand this in five seconds?
- Does this label describe a real page state?
- Does this label avoid implying execution?
- Does this label avoid unnecessary autonomy language?
- Does this label keep `/coding`, `/map`, dashboard, and backend runtime responsibilities separate?

If the answer is no, rewrite the label.

## Modal-Like Wording Check

Future implementation should avoid copy that sounds like a modal or emergency interlock unless there is a real modal or emergency state.

Avoid:

- `critical intervention required`
- `operator must acknowledge`
- `control lock engaged`
- `approval gate armed`
- `unsafe operation pending`

Prefer:

- `Blocked`
- `Not wired`
- `Requires later approval`
- `Out of scope`

## Autonomy Language Check

Autonomy should appear only when stating that it is not enabled.

Allowed:

```text
Autonomy controls: not enabled
```

Avoid:

- `autonomous backend console`
- `full-auto controls`
- `unattended operation`
- `autonomy lane`
- `self-running checks`

## Allowed Future Implementation Surface

After explicit implementation approval, the preferred future surface remains:

```text
src/app/proxy-backend/page.tsx
```

Phase 4 does not approve implementation. It only defines copy and label rules.

## Forbidden Files And Actions

Forbidden files and directories:

- `src/app/proxy-backend/page.tsx` during this docs-only increment
- `src/app/coding/page.tsx`
- `src/app/coding/**`
- `src/app/map/page.tsx`
- `src/app/map/**`
- `src/components/coding/**`
- `src/components/dashboard/**`
- `source_proxy/**`
- package files
- config files
- env files
- generated files
- Scout files
- test files
- dashboard files
- backend runtime files
- Cartographer full-auto roadmap implementation files

Forbidden actions:

- Implementing copy changes in this increment.
- Editing React components.
- Adding backend action endpoints.
- Adding executable controls.
- Adding autonomy controls.
- Staging, committing, pushing, merging, stashing, checking out, cleaning, branching, or using worktrees.

## Stop Conditions

Stop immediately if:

- This copy plan turns into implementation.
- Any forbidden file changes.
- Labels become abstract again.
- Safety copy expands into a wall of text.
- The page hides important blocked states behind decorative language.
- Any executable backend control is introduced.
- Any autonomy control is introduced.
- The current dirty worktree can no longer be distinguished from this docs-only increment.

## Manual Verification Commands

```bash
git diff --check
grep -n "Backend Console Reset Phase 4\|planning-only\|/proxy-backend\|Backend API\|Source Proxy\|Healthy\|Blocked\|Not wired\|Next step\|Autonomy controls: not enabled\|/coding\|/map\|Stop" docs/backend-console-reset-phase-4-copy-and-label-simplification.md
git status --branch --short
git diff --stat
git diff --name-only
```

Expected output:

- `git diff --check` has no output.
- `grep` prints matching lines for the Phase 4 title, planning status, `/proxy-backend`, approved plain labels, autonomy-disabled copy, protected lanes, and Stop conditions.
- `git status --branch --short` shows this new Phase 4 docs file plus pre-existing dirty files and earlier docs-only increments.
- `git diff --stat` shows no implementation-file changes from this increment.
- `git diff --name-only` still lists only tracked pre-existing dirty files, because the docs-only increment files are untracked.

## Next Recommended Increment

Backend Console Reset Phase 5: Section Reduction And Scroll Control
