# Source Proxy PR-8.3 Real Coding Task Gauntlet Receipt PR8.3-REAL-01

Date: 2026-05-25

## Task

Improve `/coding` compact diagnostic receipt clarity by adding an explicit active proof-run identity line so Run 10, Run 25, and Run 100 evidence is less ambiguous.

## Scope

Target files:
- `src/components/coding/CodingCommandCenterShell.tsx`
- `src/components/coding/__tests__/coding-command-center-shell.test.tsx`

Allowed files:
- `src/components/coding/CodingCommandCenterShell.tsx`
- `src/components/coding/__tests__/coding-command-center-shell.test.tsx`
- `docs/source-proxy-pr-8-3-real-coding-task-gauntlet-receipt-pr8-3-real-01-v0.1.md`
- `docs/design-agent-design-system-a-grade-preflight-readiness-source-proxy-pr-8-3-accepted-receipt-reference-v0.1.md`

Forbidden actions observed:
- No Run 10, Run 25, or Run 100 reruns.
- No provider/API call, queue/worker execution, approval-token use, apply/execute-approved path, commit, push, branch, worktree, stash, reset, clean, checkout, wrapper/final CSS, Plan I, or Plan J.
- No edits to provider/API, queue/worker, apply, package/config/env/auth, CSS, wrapper, `/map`, or Cartographer files.

## Dirty Tree Evidence

Before implementation baseline captured for this approved task:

```text
## main...origin/main
```

Post-verification status showed unrelated dirty entries already present outside the task scope; this receipt does not clean or mutate them.

## Implementation

`CodingCommandCenterShell.tsx` now derives `activeProofRunText` from the current trial progress or latest current-session batch summary.

Compact diagnostic copy now includes:

```text
active_proof_run: Run 25
```

when a proof run is active, and:

```text
active_proof_run: none
```

when no proof run is active.

Focused tests assert the active proof-run receipt for an active Run 25 diagnostic and the idle no-proof-run state.

## Verification

```text
npx --no-install vitest run src/components/coding/__tests__/coding-command-center-shell.test.tsx
Test Files  1 passed (1)
Tests  63 passed (63)

git diff --check
passed
```

## Expected After State

The `/coding` compact diagnostic receipt can distinguish whether copied evidence came from an active proof run, a later summary, or no proof run. The UI remains preview-only and does not gain apply, commit, push, provider, queue, worker, shell, or approval-token authority.

## Rollback Expectation

Rollback is a normal source rollback of the two edited component/test files plus removal of this receipt pair. No runtime state, external provider state, or backend queue state was created by this gauntlet.

## Acceptance Use

This one receipt satisfies Source Proxy PR-8.3 acceptance recovery by proving a real low-to-mid implementation task was completed inside the PR-8.3 Source Proxy lane after Run 10, Run 25, and Run 100 were accepted.

It also satisfies the Design Agent pre-Plan-I gate by providing the single source-of-truth PR-8.3 real gauntlet receipt that the Design Agent lane can reference instead of duplicating the gauntlet.

## Stop Condition

Stop after receipt creation and final verification. Do not commit, push, clean, rerun proof batches, start Plan I/J, or proceed into Design Agent runtime work without separate approval.
