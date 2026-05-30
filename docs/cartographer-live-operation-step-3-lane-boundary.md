# Cartographer Live Operation Step 3: Lane Boundary

status: documentation-only

Status date: 2026-05-22

Current HEAD: `40141f34d27d915503f265efba119673a412354a`

## Purpose

This document keeps Cartographer Step 3 separate from `/coding` shell work.

Step 3 is a read-only live mode planning lane. It may define observation and recommendation boundaries for Cartographer, but it must not touch `/coding` shell files, `/coding` UI implementation files, Cartographer runtime modules, tests, durable storage, approval tokens, or any live autonomy path.

## Cartographer Lane Allowed Files

For this session, the Cartographer Step 3 lane is limited to:

- `docs/cartographer-live-operation-step-3-read-only-live-mode-plan.md`
- `docs/cartographer-live-operation-step-3-lane-boundary.md`
- `docs/cartographer-live-operation-package-a-step-3-to-5-sequencing.md`
- `docs/cartographer-live-operation-step-3-1-read-only-live-observation-contract.md`
- `docs/cartographer-live-operation-step-3-2-read-only-recommendation-packet-schema.md`
- `docs/cartographer-live-operation-step-3-3-blocked-action-classifier-plan.md`
- `docs/cartographer-live-operation-step-3-4-operator-review-packet-plan.md`
- `docs/cartographer-live-operation-step-3-5-read-only-live-mode-closeout-and-step-4-gate.md`

Optional only if already clearly indexed and tiny:

- `docs/plan-index.md`

No other files are allowed in the Step 3 diff for this session.

## /coding Shell Lane Forbidden Files

The `/coding` shell lane is protected from this Step 3 work.

Forbidden files and paths include:

- `src/app/coding/page.tsx`
- `src/components/coding/`
- `src/lib/coding/`
- `/coding` shell implementation files.
- `/coding` UI implementation files.
- `/coding` tests.
- `/coding` docs that belong to the UI makeover lane.

Any `/coding` file appearing in a Step 3 diff means the lane boundary has been crossed.

## Other Forbidden Lanes

Step 3 must also avoid:

- `source_proxy/cartographer` runtime modules.
- `source_proxy/tests`.
- `source_proxy/api`.
- Package files.
- Config files.
- Environment files.
- Generated files.
- Scout files.
- Dashboard components.
- Existing dirty files unless one is an allowed Step 3 docs file.

Step 3 must not stage, commit, push, merge, stash, checkout, clean, delete, create branches, or create worktrees.

## How To Work In Parallel Safely

Britton can continue working on the `/coding` shell while the Cartographer Step 3 lane stays docs-only.

Safe parallel work requires:

- Step 3 edits only the allowed Step 3 docs.
- `/coding` edits remain in the `/coding` lane and are not modified by Step 3.
- Existing dirty `/coding` files are treated as pre-existing and intentionally untouched.
- Existing `source_proxy/cartographer` runtime and `source_proxy/tests` files are treated as pre-existing proof-stack material and intentionally untouched.
- Verification checks focus on whether Step 3 introduced only the allowed docs.

## How To Tell If Codex Accidentally Crossed Lanes

Codex crossed lanes if `git diff --name-only` or `git status --branch --short` shows Step 3 changes in:

- Any `/coding` shell or UI file.
- Any `src/app/coding/` file.
- Any `src/components/coding/` file.
- Any `src/lib/coding/` file.
- Any `source_proxy/cartographer` runtime file.
- Any `source_proxy/tests` file.
- Any package, config, env, generated, Scout, dashboard, or API file.

Crossing lanes also includes enabling live operation, implementing queue execution, creating durable queue or event storage, generating approvals, self-approval, or performing git mutation.

## Dirty Tree Expectations

The tree may already contain unrelated dirty or untracked files from other lanes.

Step 3 should not normalize, clean, stage, delete, move, or edit those files. Step 3 should only add the allowed docs listed in this boundary.

Known pre-existing dirty work includes a `/coding` lane modification and multiple untracked Cartographer proof-stack runtime/test/docs files. They are intentionally not touched by Step 3.

## Stop Conditions If /coding Files Show Up In Step 3 Diff

Stop immediately if Step 3 creates or modifies:

- `src/app/coding/page.tsx`
- `src/components/coding/`
- `src/lib/coding/`
- Any `/coding` shell implementation file.
- Any `/coding` UI implementation file.

The expected recovery is to halt and report the lane crossing for operator review. Do not stash, checkout, clean, delete, or otherwise mutate the `/coding` lane.

## Stop Conditions If source_proxy/cartographer Runtime Files Show Up In Step 3 Diff

Stop immediately if Step 3 creates or modifies any `source_proxy/cartographer` runtime module.

This session is docs-first and planning-only. Runtime shape may be proposed in docs, but source_proxy/cartographer runtime files must not be edited.

## Stop Conditions If Tests/Runtime Modules Are Edited

Stop immediately if Step 3 creates or modifies:

- `source_proxy/tests`.
- `source_proxy/api`.
- Any Cartographer runtime module.
- Any dashboard component.
- Any package, config, env, generated, Scout, or protected file.

Do not repair by reverting, stashing, checking out, cleaning, or deleting. Halt and report the unexpected diff.

## Manual Checks

Before closing Step 3 planning, manually verify:

- `git diff --check` passes.
- The Step 3 diff contains only allowed Step 3 docs.
- `/coding` shell and UI files were not touched by Step 3.
- `source_proxy/cartographer` runtime files were not touched by Step 3.
- `source_proxy/tests` files were not touched by Step 3.
- No queue execution, command execution, durable storage, approval token flow, self-approval, limited unattended operation, or full auto was enabled.

## Expected Output

Expected output is a lane boundary document that allows Cartographer Step 3 planning to proceed separately from `/coding` shell work.

No `/coding` shell file, `/coding` UI file, runtime module, test file, package file, config file, env file, generated file, Scout file, dashboard component, branch, worktree, commit, push, merge, stash, checkout, clean, or delete operation is expected.

## Rollback Notes

Rollback for this document is limited to removing:

- `docs/cartographer-live-operation-step-3-lane-boundary.md`

Rollback must not touch `/coding` shell work, source_proxy/cartographer runtime files, tests, branches, worktrees, commits, stashes, or generated files.

## Stop Conditions

Stop immediately if:

- Any `/coding` path appears in the Step 3 diff.
- Any `source_proxy/cartographer` runtime path appears in the Step 3 diff.
- Any `source_proxy/tests` path appears in the Step 3 diff.
- Any live autonomy, limited unattended operation, full auto, queue execution, command execution through Cartographer, approval generation, or self-approval appears.
- Any git mutation would be required to continue.
