# Backend Console Reset Phase 7: Read-Only Data Wiring Decision Gate

- status: planning-only
- implementation: not started
- decision: no-go by default
- parent plan: `docs/backend-console-usability-reset-plan-v0.1.md`
- previous increment: `docs/backend-console-reset-phase-6-safe-navigation-links.md`
- target page: `/proxy-backend`
- current HEAD: `40141f34d27d915503f265efba119673a412354a`

## Purpose

This document defines the future decision gate for possible read-only data wiring on `/proxy-backend`.

The goal is to decide later whether safe GET-only health data can be wired. This increment does not approve wiring, does not list any endpoint as approved, and does not change backend runtime behavior.

This is a docs-only increment. It does not edit `src/app/proxy-backend/page.tsx`, `/coding`, `/map`, dashboard files, Scout runtime files, backend runtime files, `source_proxy`, package/config/env/generated/test files, or Cartographer full-auto roadmap implementation files.

## Decision State

Current decision:

```text
No-go by default.
```

Meaning:

- Keep `/proxy-backend` static.
- Mark live values `Planned, not wired`.
- Do not wire read-only data yet.
- Do not create or call backend endpoints.
- Do not alter backend runtime.
- Do not bundle execution controls with status display.

Read-only wiring requires a later explicit go decision.

## Candidate Read-Only Data Classes

Potential future data classes may include:

- backend API health
- source proxy reachability
- local model availability
- Scout/intelligence status

These are data classes only, not approved endpoints.

No endpoint path is approved by Phase 7.

## Endpoint Approval Requirements

Any future endpoint proposed for `/proxy-backend` must prove:

- method is `GET`
- response is read-only
- handler has no mutation side effects
- handler does not start, stop, restart, apply, commit, push, merge, branch, worktree, stash, checkout, clean, or delete anything
- handler does not trigger jobs
- handler does not write files
- handler does not change runtime state
- handler does not require package/config/env changes
- failure state is visible and harmless
- timeout or unavailable state is visible and harmless

If any item is unclear, the decision remains no-go.

## Forbidden Endpoint Classes

Forbidden:

- mutation endpoints
- action endpoints
- command endpoints
- job-trigger endpoints
- approval endpoints
- execution endpoints
- autonomy endpoints
- write endpoints
- start/stop/restart endpoints
- apply/commit/push/merge/branch/worktree/stash/checkout/clean/delete endpoints

If a future endpoint uses a mutation verb or changes state, it is out of scope for this reset.

## Display Requirements If Later Approved

If a later decision explicitly approves read-only wiring, the UI must display failure states safely.

Allowed display states:

- `Healthy`
- `Degraded`
- `Blocked`
- `Offline`
- `Not wired`
- `Unavailable`
- `Timed out`

Failure-state copy should be plain:

```text
Status unavailable. No action was run.
```

The page must not hide failure states behind decorative language.

## Static Fallback

If read-only wiring is not approved, the page should remain static:

```text
Planned, not wired
```

Static fallback is acceptable and preferred over unclear wiring.

## Separation From Static Usability Reset

The static usability reset and read-only wiring are separate decisions.

Static usability reset may proceed later with:

- static status labels
- plain page flow
- safe navigation links
- no-wiring banner
- blocked/not-wired explanations

Read-only wiring may proceed only after:

- endpoint inventory
- GET-only proof
- harmless failure-state proof
- explicit go decision

## Non-Goals

Phase 7 does not:

- approve implementation
- wire data
- inspect backend runtime internals
- create endpoint names
- add endpoint handlers
- add polling
- add refresh buttons
- add execution controls
- add autonomy controls
- change package/config/env files

## Future Go/No-Go Packet Shape

A future decision packet should include:

- proposed endpoint path
- method
- source file
- owner lane
- exact data returned
- proof of no mutation
- failure behavior
- timeout behavior
- UI display mapping
- rollback plan
- manual checks
- final go/no-go decision

Decision rule:

```text
No explicit go means no wiring.
```

## Allowed Future Implementation Surface

After explicit implementation approval, static page work may still prefer:

```text
src/app/proxy-backend/page.tsx
```

Read-only wiring may require a separate approved wiring plan before any runtime or endpoint file is touched.

Phase 7 does not approve either implementation or wiring.

## Forbidden Files And Actions

Forbidden files and directories:

- `src/app/proxy-backend/page.tsx` during this docs-only increment
- backend runtime files
- mutation endpoint files
- package files
- config files
- env files
- generated files
- `/coding` implementation files
- `/map` implementation files
- dashboard implementation files
- Scout runtime files
- `src/app/coding/page.tsx`
- `src/app/coding/**`
- `src/app/map/page.tsx`
- `src/app/map/**`
- `src/components/coding/**`
- `src/components/dashboard/**`
- `source_proxy/**`
- test files
- Cartographer full-auto roadmap implementation files

Forbidden actions:

- Implementing read-only wiring in this increment.
- Proposing mutation endpoints.
- Creating endpoint handlers.
- Calling backend action endpoints.
- Adding executable controls.
- Adding refresh buttons that imply live execution.
- Adding autonomy controls.
- Staging, committing, pushing, merging, stashing, checking out, cleaning, branching, or using worktrees.

## Stop Conditions

Stop immediately if:

- This decision gate turns into implementation.
- Any forbidden file changes.
- Any mutation endpoint is proposed.
- Any action endpoint is proposed.
- Any start/stop/restart or apply-style action is bundled into wiring.
- Any endpoint approval is unclear.
- Any execution control is introduced.
- Any autonomy control is introduced.
- The current dirty worktree can no longer be distinguished from this docs-only increment.

## Manual Verification Commands

```bash
git diff --check
grep -n "Backend Console Reset Phase 7\|planning-only\|no-go by default\|/proxy-backend\|GET\|read-only\|mutation endpoint\|Planned, not wired\|No explicit go means no wiring\|/coding\|/map\|Stop" docs/backend-console-reset-phase-7-read-only-data-wiring-decision-gate.md
git status --branch --short
git diff --stat
git diff --name-only
```

Expected output:

- `git diff --check` has no output.
- `grep` prints matching lines for the Phase 7 title, planning status, no-go default, `/proxy-backend`, GET-only/read-only requirements, mutation endpoint prohibitions, static fallback, protected lanes, and Stop conditions.
- `git status --branch --short` shows this new Phase 7 docs file plus pre-existing dirty files and earlier docs-only increments.
- `git diff --stat` shows no implementation-file changes from this increment.
- `git diff --name-only` still lists only tracked pre-existing dirty files, because the docs-only increment files are untracked.

## Next Recommended Increment

Backend Console Reset Phase 8: Future Implementation Sequence
