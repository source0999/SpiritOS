# Cartographer Full Auto Plan 1: Limited Operator v0.1

status: full-plan-only

Status date: 2026-05-22

Current HEAD: `40141f34d27d915503f265efba119673a412354a`

## Purpose

Plan 1 defines the first future Limited Operator mode for Cartographer: read-only `/map` wiring and inert recommendation packets.

This is a planning document only. It does not implement read-only wiring, edit `/map`, add fetch calls, call backend endpoints, expose executable controls, create durable queue storage, create approval tokens, run commands through Cartographer, write files through Cartographer, grant limited unattended operation, or grant full auto.

## Authority Summary

- current state: inert manual-control lane passed
- current `/map` state: static, unwired, no executable controls
- Plan 1 target: future read-only display and recommendation mode only
- full auto: not granted
- limited unattended operation: not granted
- write authority: not granted
- command execution authority: not granted
- queue execution authority: not granted
- approval authority: not granted
- self-approval: forbidden
- implementation: not started by this plan

## Baseline

The current `/map` lane is navbar-accessible, static, inert, and unwired. Phase 13 final review passed. There are no `/map` fetch calls, no backend endpoint calls, no executable controls, and no real read-only data wiring.

The repo is already dirty outside this Plan 1 lane. Those files are not part of Plan 1 authority and must not be cleaned, staged, overwritten, checked out, stashed, deleted, committed, or absorbed into Plan 1 scope.

## Relationship To Master Roadmap

This plan implements the planning work requested by:

- `docs/cartographer-full-auto-master-roadmap-v0.1.md`
- Plan 1: Limited Operator v0.1

Plan 1 may later become the first implementation package for read-only `/map` wiring only after explicit operator approval. This document is not that implementation approval.

## Plan 1 Goal

The future Plan 1 implementation should let `/map` display live read-only Cartographer state and recommendation packets for a human operator.

The future implementation must remain display-only:

- It may show read-only state.
- It may show blocked-action findings.
- It may show recommendation packets.
- It may show operator review packets.
- It may show fallback/static states when live reads fail.
- It must not execute, approve, write, queue, branch, commit, push, merge, stash, checkout, clean, delete, or self-promote.

## Non-Goals

Plan 1 does not authorize:

- Backend endpoint implementation.
- Runtime module edits.
- Test edits.
- Durable queue storage.
- Event ledger storage.
- Approval token runtime.
- Approval queue actions.
- Writes to docs, evidence, receipts, source, tests, package, config, env, generated, Scout, dashboard, or Source Proxy files.
- Command execution through Cartographer.
- Queue execution.
- Local shell execution through Cartographer.
- Apply, commit, push, merge, branch, worktree, stash, checkout, clean, delete, or package controls.
- Limited unattended operation.
- Full auto.

## Future Allowed Files For A Separately Approved Implementation

This section describes likely future files only. It does not authorize editing them now.

A later implementation package may request exact edits to:

- `src/app/map/page.tsx`
- A future narrow `/map` data adapter under an explicitly approved path.
- Focused `/map` display tests only if separately approved.

Any future file list must be exact. Broad patterns are not enough for implementation approval.

## Files Forbidden For Plan 1 By Default

Plan 1 must not touch:

- `src/app/coding/page.tsx`
- `src/components/coding/**`
- `src/lib/coding/**`
- `src/components/dashboard/**`
- `src/app/(dashboard)/**`
- `src/app/v1/**`
- `source_proxy/**`
- `source_proxy/cartographer/**`
- `source_proxy/tests/**`
- package files
- config files
- env files
- generated files
- Scout files
- existing dirty files unless an explicit future approval names them

## Safe GET-Only Endpoint Candidate List

The future read-only implementation may consider only a small GET-only candidate set. Every candidate must be verified again immediately before implementation because route behavior can change.

Initial candidate endpoints:

| Candidate | Future display purpose | Notes |
| --- | --- | --- |
| `/v1/cartographer/status` | Cartographer status card | Read-only candidate only. |
| `/v1/cartographer/repo-map` | Repo map summary | Read-only candidate only. |
| `/v1/cartographer/proposals` | Recommendation/proposal summary | Display-only; no review or apply actions. |
| `/v1/cartographer/audit-trail` | Recent audit summary | Display-only; no ledger mutation. |
| `/v1/cartographer/v1-readiness` | Readiness signal | Display-only; cannot promote authority. |
| `/v1/cartographer/trust-score` | Trust score signal | Display-only; cannot promote authority. |

Routes with approval, apply, commit, push, branch, promotion, or mutation semantics are not Plan 1 candidates even if a route also has a GET surface.

## Explicitly Blocked Endpoint Classes

The future implementation must block:

- Any `POST`, `PUT`, `PATCH`, or `DELETE` route.
- Any route path containing `approve`.
- Any route path containing `apply-approved`.
- Any route path containing `docs-autopilot/apply`.
- Any route path containing `commit`.
- Any route path containing `push`.
- Any route path containing `autonomy-promotion`.
- Any route that mutates backend state, writes files, creates evidence, creates receipts, changes queue state, or implies approval.

Blocked endpoint classes may be displayed as unavailable future capabilities only if the UI copy is inert and cannot be activated.

## Static-To-Live Data Transition

The future implementation must transition `/map` from static placeholder data to live read-only data in a controlled way:

1. Keep the current static model as the fallback baseline.
2. Add one read-only data adapter behind a clear Plan 1 boundary.
3. Fetch only approved GET endpoints.
4. Normalize responses into display-only view data.
5. Render live state only when all required reads succeed safely.
6. Fall back to static/inert state when any read fails, times out, returns unexpected shape, or attempts to cross the allowed endpoint list.
7. Show a blocked/fallback state rather than retrying aggressively or escalating authority.

The fallback state must not offer repair buttons, apply buttons, approval buttons, command buttons, or hidden execution paths.

## Timeout Behavior

Every future read must have bounded timeout behavior.

Required behavior:

- Use a short explicit timeout per endpoint.
- Treat timeout as a display-only unavailable state.
- Do not retry indefinitely.
- Do not switch to a broader endpoint after timeout.
- Do not call mutation endpoints as fallback.
- Do not write timeout evidence or receipts in Plan 1.
- Do not trigger alerts, scheduled jobs, monitors, or autonomous follow-up.

The operator-facing message should say that live read-only data is unavailable and that `/map` is showing fallback display state.

## Fallback Behavior

Fallback must be conservative:

- Keep `/map` usable as an inert manual-control surface.
- Preserve static placeholder summaries.
- Mark live sections as unavailable or stale.
- Preserve blocked-action copy.
- Preserve full-auto and limited unattended denial copy.
- Do not hide the fact that live data failed.
- Do not create queue items, events, evidence, receipts, or approval requests.

Fallback is a stop-safe display state, not a recovery workflow.

## Recommendation Packet Shape

Future Plan 1 recommendation packets are conceptual display data only.

A recommendation packet may contain:

- `packet_id` as display-only identifier.
- `status_date`.
- `source_endpoints_observed`.
- `source_endpoints_blocked`.
- `head` if provided by an approved read-only source.
- `branch_summary` if provided by an approved read-only source.
- `dirty_tree_summary` if provided by an approved read-only source.
- `protected_lane_findings`.
- `blocked_action_classes`.
- `recommendation_summary`.
- `manual_next_step`.
- `authority_denials`.

The packet must not contain:

- Approval token material.
- Secrets.
- Environment values.
- Executable commands.
- Durable queue state.
- Event ledger writes.
- Evidence write instructions.
- Receipt write instructions.
- Apply, commit, push, merge, branch, worktree, stash, checkout, clean, or delete instructions.
- Self-approval fields.
- Autonomous task selection.

## Blocked Action Classifier

Plan 1 must include an inert blocked-action classifier for display purposes.

The classifier must label the following as blocked:

- File writes.
- Evidence writes.
- Receipt writes.
- Durable queue writes.
- Event storage writes.
- Queue execution.
- Local command execution through Cartographer.
- Automatic task selection.
- Approval generation.
- Self-approval.
- Branch creation.
- Worktree creation.
- Commit, push, or merge.
- Stash, checkout, clean, or delete.
- `/coding` shell or UI mutation.
- `source_proxy/cartographer` runtime mutation.
- `source_proxy/tests` mutation.
- Package, config, environment, generated, Scout, dashboard, or API mutation.
- Full auto.
- Limited unattended operation.

The classifier output must be a human-readable blocked reason only. It must not execute a block, write an audit event, or create durable state in Plan 1.

## Operator Review Packet

The future `/map` display should present an operator review packet that helps a human decide what to do next.

Packet sections:

- Live read status.
- Endpoint source summary.
- Current authority summary.
- Recommendation summary.
- Blocked action findings.
- Protected lane findings.
- Manual checks.
- Stop conditions.
- Next recommended manual increment.

The packet must not make the decision automatically. It must not approve, queue, execute, schedule, write, or promote.

## UI Display-Only Requirements

The future `/map` implementation must remain display-only:

- No `<button>` for dangerous actions.
- No click handler for apply, approve, execute, commit, push, merge, branch, worktree, stash, checkout, clean, delete, or promote.
- No hidden form submission for action routes.
- No automatic polling unless separately approved with explicit cadence and stop rules.
- No dashboard mutation.
- No route outside `/map` without separate approval.
- No UI state that implies authority has been granted.

Links to external or internal read-only views may be considered later only if they cannot mutate state.

## Manual Checks For Future Implementation

A future implementation package must include manual checks that prove:

- `/map` remains navbar-accessible.
- `/map` uses only approved GET endpoints.
- `/map` contains no mutation endpoint references.
- `/map` contains no executable action controls.
- Timeout paths render fallback state.
- Unexpected response shapes render fallback state.
- Recommendation packets are inert.
- Blocked action findings are display-only.
- Full auto is not granted.
- Limited unattended operation is not granted.
- No `/coding`, dashboard, runtime, test, package, config, env, generated, Scout, or Source Proxy files are touched unless explicitly approved.

## Verification Commands For This Plan

Plan 1 documentation should be verified with:

```bash
cd /home/source/SpiritOS

git diff --check

grep -n "Limited Operator v0.1\|full auto: not granted\|limited unattended operation: not granted\|write authority: not granted\|command execution authority: not granted\|implementation: not started" \
  docs/cartographer-full-auto-plan-1-limited-operator-v0.1.md

grep -n "Safe GET-Only Endpoint Candidate List\|Explicitly Blocked Endpoint Classes\|Recommendation Packet Shape\|Blocked Action Classifier\|UI Display-Only Requirements\|Do not implement" \
  docs/cartographer-full-auto-plan-1-limited-operator-v0.1.md

git status --branch --short
git diff --stat
```

## Future Implementation Verification Commands

A separately approved implementation package should define focused checks before any code changes. Candidate checks may include:

```bash
cd /home/source/SpiritOS

git diff --check

grep -n "fetch(\|sourceProxyFetch\|proxyCartographer" src/app/map/page.tsx

grep -n "POST\|approve\|apply-approved\|commit\|push\|autonomy-promotion" src/app/map/page.tsx && exit 1 || true

grep -n "onClick\|<button" src/app/map/page.tsx && exit 1 || true
```

These are candidate checks only. A future implementation plan must refine them before code changes begin.

## Rollback Notes

Rollback for this planning document is limited to removing:

- `docs/cartographer-full-auto-plan-1-limited-operator-v0.1.md`

Rollback must not touch `/map`, `/coding`, dashboard, runtime, tests, Source Proxy, package, config, env, generated, Scout, branch, worktree, commit, stash, or unrelated dirty files.

## Stop Conditions

Stop immediately if:

- Any implementation file must be edited.
- Any `/map` wiring is attempted without a separate implementation approval.
- Any backend endpoint is called.
- Any fetch call is added.
- Any executable control is exposed.
- Any approval, apply, commit, push, merge, branch, worktree, stash, checkout, clean, or delete control is exposed.
- Any write authority is granted.
- Any command execution authority is granted.
- Any queue execution authority is granted.
- Any approval token runtime is created.
- Any durable queue or event storage is created.
- Any limited unattended operation is granted.
- Any full auto authority is granted.
- Any protected lane file must be touched.
- Any git staging, commit, push, merge, stash, checkout, clean, branch, or worktree operation is requested.

## Plan 1 Closeout Requirements

Before Plan 1 can be considered complete in a future implementation lane, it must produce:

- Plan 1 implementation closeout doc.
- Verification command results.
- Manual check results.
- Endpoint allowlist proof.
- Mutation endpoint block proof.
- Timeout/fallback proof.
- Recommendation packet inertness proof.
- Protected lane proof.
- No-go/go decision for Plan 2.
- Explicit operator permission gate for Plan 2.

Plan 1 cannot promote itself to Plan 2.

## Stop Point

Stop here. Do not implement Plan 1. Do not wire `/map` without explicit operator approval for a separate implementation package.

## Next Recommended Increment

Plan 1 Implementation Decision: Read-Only `/map` Wiring Approval Or No-Go
