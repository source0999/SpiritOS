# Source Proxy Plan 10/24 /coding Active Task Cockpit And Operator Clarity

Date: 2026-05-27
Mode: SOURCE PROXY UI ONLY
Plan: Plan 10/24, /coding Active Task Cockpit And Operator Clarity
Repository HEAD: caeccea45b18d39f94c463a3376a6eb911256ea8

## Entry Evidence

Plan 9/24 closed with GO for blocker map, receipt semantics, safety metrics, and focused regression proof. It did not authorize a Run 300 rerun or Plan 10 start by itself. The operator then requested continuing if good under the same workflow. Plan 9 mechanical verification passed before this packet started.

## Scope Boundary

Allowed scope:

- UI truth surfaces.
- Evidence visibility.
- Approval boundary display.
- Route/UI proof and grep for authority copy.

Forbidden scope avoided:

- Hidden route calls.
- Backend mutation.
- Provider calls.
- Apply.
- Commit.
- Push.
- Queue or worker start.
- Cartographer activation.
- Final CSS.
- Runtime start.
- Browser proof.
- Branch, worktree, stash, reset, clean, or checkout.

This packet records Plan 10 only. It does not start Plan 11/24.

## Phase 10.1 UI Truth Surfaces

### 10.1.1 Show Task Target

Evidence reviewed:

- `src/components/coding/CodingCommandCenterShell.tsx`
- `src/components/coding/__tests__/coding-command-center-shell.test.tsx`
- `docs/source-proxy-codex-like-active-task-ui-revamp-plan-v0.1.md`
- `docs/codingUI.md`

Evidence recorded:

- The component has task target fields and receipt target text, including `previewTarget`, `receiptTargetScopeText`, `Target scope`, and task-backed fallback evidence.
- Tests assert target display for plain-English browser intake, preview evidence, receipt proof, evidence drawer switching, and selected trial target display.
- Tests assert preview remains locked when target is missing or ambiguous.

GO / NO-GO:

- GO for task target visibility.
- NO-GO for hidden target inference that enables preview without bounded task data.

Next authorized increment: 10.1.2 Show allowed and forbidden files.

### 10.1.2 Show Allowed And Forbidden Files

Evidence reviewed:

- `src/components/coding/CodingCommandCenterShell.tsx`
- `src/components/coding/__tests__/coding-command-center-shell.test.tsx`

Evidence recorded:

- The component has `allowedFiles`, `allowed_files_mismatch`, `Allowed files`, `changed_files`, `unexpected_files`, protected-path handling, and receipt changed-file fields.
- Tests assert allowed files are visible for preview evidence.
- Tests assert preview locks when allowed files are missing.
- Tests assert apply remains locked when changed files are outside allowed files.
- Tests assert protected-path blockers and false authority fields remain visible.

GO / NO-GO:

- GO for allowed/forbidden file truth visibility.
- NO-GO for any preview/apply path that hides unexpected files or protected-path scope.

Next authorized increment: 10.1.3 Show provider/model status.

### 10.1.3 Show Provider/Model Status

Evidence reviewed:

- `src/components/coding/CodingCommandCenterShell.tsx`
- `src/components/coding/__tests__/coding-command-center-shell.test.tsx`

Evidence recorded:

- Provider/model state is displayed through provider chips, model status, backend truth, usage/time receipt, and lifecycle receipt lines.
- Tests assert local default is preview-available, GPT/cloud is unavailable unless configured, Codex worker is proposal-only, and future providers are unavailable.
- Tests assert provider intent changes do not claim provider calls.
- Tests assert `provider_call_made: false` remains visible in receipts and copied diagnostics.

GO / NO-GO:

- GO for provider/model status visibility.
- NO-GO for fake provider availability or provider call authority.

Next authorized increment: Phase 10.1 review.

### Phase 10.1 Review

Completed increments:

- 10.1.1 GO.
- 10.1.2 GO.
- 10.1.3 GO.

Evidence exists:

- Source grep and focused tests cover task target, allowed/forbidden files, provider/model status, and lock behavior.

Forbidden scope avoided:

- No code edits, hidden route calls, backend mutation, provider call, apply, commit, push, queue, worker, runtime start, browser proof, Cartographer activation, or final CSS occurred.

Phase result: GO to Phase 10.2.

Next authorized increment: 10.2.1 Show dirty-tree state.

## Phase 10.2 Evidence Visibility

### 10.2.1 Show Dirty-Tree State

Evidence reviewed:

- `src/components/coding/CodingCommandCenterShell.tsx`
- `src/components/coding/__tests__/coding-command-center-shell.test.tsx`

Evidence recorded:

- Evidence drawer and receipt fields include workspace dirty state, workspace authority, dirty-tree proof, changed files, unexpected files, diff check result, rollback hint, and receipt readiness.
- Tests assert evidence drawer visibility, task-scoped evidence switching, progress/evidence receipts, and current page audit evidence.
- Current repository status for this plan shows only untracked roadmap/evidence docs; no source/test/CSS changes were made by Plan 10.

GO / NO-GO:

- GO for dirty-tree/evidence visibility.
- NO-GO for dirty-tree cleanup or mutation.

Next authorized increment: 10.2.2 Show preview, no-op, and proposal status.

### 10.2.2 Show Preview, No-Op, And Proposal Status

Evidence reviewed:

- `src/components/coding/CodingCommandCenterShell.tsx`
- `src/components/coding/__tests__/coding-command-center-shell.test.tsx`
- `docs/source-proxy-run-300-blocker-reduction-plan-9-24-v0.1.md`

Evidence recorded:

- Preview status exists through `previewStatus`, preview evidence, changed-file summaries, approval gate display, and route-gap reason copy.
- No-op status exists through `already_satisfied_noop`, no diff preview, no-op evidence, `changed_files: []`, no approval needed, no apply needed, and no-op receipt copy.
- Proposal status exists through provider/model proposal-only states, route-gap proposal copy, and design proposal intake evidence without apply.
- Tests assert preview-ready evidence, blocked preview gates, already satisfied no-op, design proposal intake without apply, provider proposal-only state, and Run 300 receipt classes.

GO / NO-GO:

- GO for preview/no-op/proposal status visibility.
- NO-GO for treating route gaps as productive passes or no-op without proof.

Next authorized increment: 10.2.3 Show manual check readiness.

### 10.2.3 Show Manual Check Readiness

Evidence reviewed:

- `src/components/coding/CodingCommandCenterShell.tsx`
- `src/components/coding/__tests__/coding-command-center-shell.test.tsx`
- `docs/source-proxy-codex-like-active-task-ui-revamp-plan-v0.1.md`

Evidence recorded:

- The UI has manual check/copy packet controls, diagnostics drawer, evidence drawer, check duration fields, typecheck/lint/focused-test receipt fields, commands-run receipt field, verification receipt, and manual checklist copy.
- Tests assert manual check copy controls, copy receipt, compact diagnostics, evidence drawers, progress checklist, and verification state.
- Focused test proof for Plan 10: `Test Files  1 passed (1)` and `Tests  71 passed (71)`.

GO / NO-GO:

- GO for manual check readiness visibility.
- NO-GO for claiming browser proof or verification pass when unavailable.

Next authorized increment: Phase 10.2 review.

### Phase 10.2 Review

Completed increments:

- 10.2.1 GO.
- 10.2.2 GO.
- 10.2.3 GO.

Evidence exists:

- Source grep and focused tests cover dirty-tree/evidence visibility, preview/no-op/proposal status, and manual check readiness.

Forbidden scope avoided:

- No code edits, hidden route calls, backend mutation, provider call, apply, commit, push, queue, worker, runtime start, browser proof, Cartographer activation, or final CSS occurred.

Checks passed:

- Focused Vitest passed: 1 file, 71 tests.

Phase result: GO to Phase 10.3.

Next authorized increment: 10.3.1 Ensure approval, apply, commit, and push remain separate.

## Phase 10.3 Approval Boundary

### 10.3.1 Ensure Approval, Apply, Commit, And Push Remain Separate

Evidence reviewed:

- `src/components/coding/CodingCommandCenterShell.tsx`
- `src/components/coding/__tests__/coding-command-center-shell.test.tsx`

Evidence recorded:

- UI copy separates preview, approval, apply, verification, commit, and push.
- Tests assert approval is locked until preview evidence exists.
- Tests assert apply is locked until explicit local approval exists.
- Tests assert verify is separate after apply evidence.
- Tests assert commit and push controls are not available from this lane.
- Tests assert no apply button appears for blocked preview, proposal-only provider states, or no-op preview.

GO / NO-GO:

- GO for separated approval boundary.
- NO-GO for approval implying apply, apply implying verify, or verify implying commit/push.

Next authorized increment: 10.3.2 Ensure no hidden route calls.

### 10.3.2 Ensure No Hidden Route Calls

Evidence reviewed:

- `src/components/coding/CodingCommandCenterShell.tsx`
- `src/components/coding/__tests__/coding-command-center-shell.test.tsx`

Evidence recorded:

- Grep found explicit route calls in the component for user-triggered flows, including prompt packet, bounded diff preview, verification diff preview, execute-approved, and verify routes.
- Plan 10 did not start any route call, app runtime, browser proof, provider, queue, worker, apply, or execute-approved action.
- Tests assert route calls happen only through explicit preview/apply/verify interactions and remain gated by visible UI state.
- Tests assert backend truth panels do not start live backend reads, hidden polling, providers, queues, workers, shell commands, or apply routes.
- Tests assert provider/model switches do not claim provider calls.

Decision:

- No hidden route call was introduced by Plan 10.
- Existing explicit route paths remain gated UI behavior and are not newly authorized by this packet.

GO / NO-GO:

- GO for no hidden route-call evidence.
- NO-GO for any new route call or route call hidden behind display-only UI.

Next authorized increment: 10.3.3 Produce final UI readiness gate.

### 10.3.3 Produce Final UI Readiness Gate

Evidence reviewed:

- Phase 10.1 evidence.
- Phase 10.2 evidence.
- Phase 10.3 evidence.
- Focused Vitest output.

Readiness gate:

- `/coding` task target display: GO.
- Allowed/forbidden file display: GO.
- Provider/model status display: GO.
- Dirty-tree/evidence visibility: GO.
- Preview/no-op/proposal status display: GO.
- Manual check readiness display: GO.
- Approval/apply/commit/push separation: GO.
- No hidden route-call change: GO.
- Source Proxy authority unchanged: GO.
- Browser proof: not run.
- Runtime/backend mutation: not run.
- Final CSS: not started.

GO / NO-GO:

- GO for `/coding` readiness gate as display clarity with Source Proxy authority unchanged.
- NO-GO for Plan 11 start without explicit operator approval.

Next authorized increment: Phase 10.3 review.

### Phase 10.3 Review

Completed increments:

- 10.3.1 GO.
- 10.3.2 GO.
- 10.3.3 GO.

Evidence exists:

- Source grep, authority grep, focused tests, and readiness gate are recorded.

Forbidden scope avoided:

- No hidden route calls, backend mutation, provider calls, apply, commit, push, queue/worker, Cartographer activation, final CSS, runtime start, browser proof, branch/worktree, stash, reset, clean, or checkout occurred.

Checks passed:

- Focused Vitest passed: 1 file, 71 tests.

Phase result: GO to Plan 10 closeout.

Next authorized increment: Plan 10/24 closeout.

## Plan 10/24 Closeout

Phase results:

- Phase 10.1 UI Truth Surfaces: GO.
- Phase 10.2 Evidence Visibility: GO.
- Phase 10.3 Approval Boundary: GO.

Evidence exists:

- Plan 10 evidence packet.
- Source grep for UI truth surfaces and route/authority copy.
- Focused `/coding` Vitest proof.
- Current git status.

Forbidden actions:

- No hidden route call introduced.
- No backend mutation.
- No provider call.
- No apply.
- No commit.
- No push.
- No queue or worker.
- No Cartographer activation.
- No final CSS.
- No runtime start.
- No browser proof.
- No branch, worktree, stash, reset, clean, or checkout.

Final `/coding` readiness gate:

- `/coding` is eligible as a display-clarity cockpit with Source Proxy authority unchanged.
- `/coding` is not promoted to apply, provider, queue, worker, commit, push, final CSS, browser-proof, or runtime authority by this plan.

Final Plan 10/24 result: GO for display clarity with Source Proxy authority unchanged; NO-GO for hidden authority, backend mutation, final CSS, browser proof, or Plan 11 start.

Next roadmap plan only: `Plan 11/24: Source Proxy Production Hardening Consolidation`.

## Terminal Verification

```bash
cd /home/source/SpiritOS
git status --branch --short --untracked-files=normal
grep -nE "Plan 10/24|task target|Allowed|provider/model|dirty-tree|preview/no-op/proposal|manual check|approval|apply|commit|push|no hidden route|readiness gate|Plan 11/24|Tests  71 passed" docs/source-proxy-coding-active-task-cockpit-operator-clarity-plan-10-24-v0.1.md
grep -nE "previewTarget|allowedFiles|receiptTargetScopeText|receiptAllowedFilesText|provider_call_made: false|queue_worker_started: false|shell_command_started: false|hidden_execution_started: false|Approval gate display|Commit and push are not available|No hidden chain-of-thought|No hidden execution guard" src/components/coding/CodingCommandCenterShell.tsx src/components/coding/__tests__/coding-command-center-shell.test.tsx
grep -nE "fetch\\(|/v1/actions/execute-approved|/v1/verification/diff-preview|/v1/decisions/prompt-packet|/v1/tasks/long-running" src/components/coding/CodingCommandCenterShell.tsx src/components/coding/__tests__/coding-command-center-shell.test.tsx
git diff --check -- docs/source-proxy-coding-active-task-cockpit-operator-clarity-plan-10-24-v0.1.md
npx --no-install vitest run src/components/coding/__tests__/coding-command-center-shell.test.tsx
```

Expected:

- `git status` shows this Plan 10 packet as untracked with existing roadmap/evidence docs; no source/test/CSS changes from Plan 10.
- Plan grep prints phase, readiness gate, forbidden-action, focused-test, and Plan 11 title lines.
- UI/authority grep prints target, allowed-file, provider/model, evidence, approval/apply/commit/push separation, and false authority lines.
- Route grep prints existing explicit route paths only; Plan 10 did not add or run hidden route calls.
- `git diff --check` prints no output.
- Focused Vitest prints `Test Files  1 passed (1)` and `Tests  71 passed (71)`.
