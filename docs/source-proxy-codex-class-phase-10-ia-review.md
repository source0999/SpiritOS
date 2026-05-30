# Source Proxy Codex-Class Phase 10 IA Review

Status date: 2026-05-22
Phase: 10.1 Codex-Class IA Review
Status: closed, ready for 10.2 visual density polish

## Scope

This is a planning receipt only. No backend authority, apply logic, model/provider routing, package
configuration, server state, branch state, or worktree state changed for this increment.

## Current IA Findings

- The `/coding` shell already presents the required zones: workspace/chat rail, active task area,
  composer, preview evidence, approval/apply/verify gates, timeline evidence, receipt, and mobile
  command composer.
- The proven workflow states are now stronger than the visual hierarchy. The next polish should
  reduce scanning cost around preview evidence, changed files, approval preflight, blockers, and
  receipt readiness.
- The right safety pane and central active task area should stay operationally dense. Avoid hero
  copy, marketing layout, decorative cards, or visual changes that obscure gate state.
- Mobile polish should keep preview/review controls readable without adding mobile-only execution
  authority.

## Phase 10 Polish Boundaries

- Keep `/coding` UI-only over existing Source Proxy contracts.
- Keep apply, commit, push, branch, worktree, provider, package, auth/config/env, and server restart
  authority unchanged.
- Prefer copy/layout/class changes in `src/components/coding/CodingCommandCenterShell.tsx` and
  focused assertions in `src/components/coding/__tests__/coding-command-center-shell.test.tsx`.
- Do not touch backend authority code during Phase 10 unless a regression check exposes a blocker.

## 10.2 Candidate Work

- Make preview evidence and changed-file state easier to scan.
- Tighten blocked/error/no-diff panels so the next safe action is visually obvious.
- Preserve all existing approval, apply, verify, no-op, and unexpected-file lock copy.

## 10.3 Candidate Work

- Improve mobile review density and accessibility labels around composer, preview, and receipt
  controls.
- Keep mobile controls as review/preview surfaces unless existing approval gates explicitly allow
  an action.

## Verification

Baseline UI checks passed before polish:

```bash
git diff --check
npm run typecheck
npm run test:coding-frontend-regression
```
