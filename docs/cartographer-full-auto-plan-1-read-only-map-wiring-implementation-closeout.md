# Cartographer Full Auto Plan 1 Read-Only /map Wiring Implementation Closeout

status: implementation-closeout

Status date: 2026-05-22

Current HEAD: `40141f34d27d915503f265efba119673a412354a`

## Implementation Result

Plan 1 read-only `/map` wiring is implemented for display-only GET allowlist reads with static fallback.

This closeout does not grant write authority, command execution authority, queue execution authority, approval authority, self-approval, limited unattended operation, or full auto.

Full auto is not granted. Limited unattended operation is not granted.

## Files Changed

- `src/app/map/page.tsx`
- `src/app/map/read-only-map-data.ts`
- `docs/cartographer-full-auto-plan-1-read-only-map-wiring-implementation-closeout.md`

## What Changed

- Added a narrow `/map` read-only data adapter.
- Added an exact GET-only endpoint allowlist.
- Added a 1500ms per-endpoint timeout.
- Added static fallback behavior when any read is unavailable.
- Added a display-only recommendation packet shape.
- Added display-only blocked endpoint/action classifier content.
- Updated `/map` copy from inert pre-approval state to Plan 1 display-only wiring state.

## GET-only Allowlist

The implemented allowlist is:

- `/v1/cartographer/status`
- `/v1/cartographer/repo-map`
- `/v1/cartographer/blueprints`
- `/v1/cartographer/proposals`
- `/v1/cartographer/v1-evidence`
- `/v1/cartographer/audit-trail`
- `/v1/cartographer/v1-readiness`
- `/v1/cartographer/trust-score`

No endpoint outside this list is part of Plan 1 implementation.

## Blocked Endpoint Classes

The implementation keeps these endpoint classes blocked:

- Any `POST`, `PUT`, `PATCH`, or `DELETE` endpoint.
- Any approve, review, apply, commit, push, branch, or autonomy-promotion path.
- Any endpoint that mutates files, queues, events, approvals, evidence, receipts, audit ledgers, branches, worktrees, runtime, tests, dashboard, `/coding`, package, config, env, generated, Scout, API, or Source Proxy state.

Blocked endpoint classes are displayed as inert findings only.

## Display-only Requirements Preserved

The `/map` route remains display-only:

- No write controls.
- No approval controls.
- No apply controls.
- No command controls.
- No queue execution controls.
- No commit, push, merge, branch, worktree, stash, checkout, clean, or delete controls.
- No approval-token runtime.
- No durable queue storage.
- No event storage.
- No dashboard mutation.
- No `/coding` mutation.
- No Source Proxy mutation.
- No tests edited.

## Timeout And Fallback

Every allowlisted GET read uses a 1500ms timeout.

If any endpoint fails, times out, or returns a non-OK status, `/map` renders fallback display state and keeps all action classes blocked. Fallback does not create evidence, receipts, queue entries, event records, approval requests, alerts, monitors, jobs, or follow-ups.

## Recommendation Packet

The implemented packet is display-only and includes:

- `packet_id`
- `status_date`
- `source_endpoints_observed`
- `source_endpoints_blocked`
- `protected_lane_findings`
- `blocked_action_classes`
- `recommendation_summary`
- `manual_next_step`
- `authority_denials`

The packet does not include approval token material, secrets, environment values, executable commands, durable queue state, event ledger writes, evidence write instructions, receipt write instructions, apply instructions, git mutation instructions, self-approval fields, or autonomous task selection.

## Manual Checks

```bash
cd /home/source/SpiritOS

git diff --check

npx eslint src/app/map/page.tsx src/app/map/read-only-map-data.ts

grep -nE "GET-only|display-only|Static fallback|blocked endpoint|blocked action|full auto is not granted|limited unattended operation is not granted" \
  src/app/map/page.tsx src/app/map/read-only-map-data.ts docs/cartographer-full-auto-plan-1-read-only-map-wiring-implementation-closeout.md

grep -nE "onClick|<button|approval token|self-approval|queue execution controls|command controls" \
  src/app/map/page.tsx src/app/map/read-only-map-data.ts || true

grep -RInE "export async function (GET|POST|PUT|PATCH|DELETE)" \
  src/app/v1/cartographer/status \
  src/app/v1/cartographer/repo-map \
  src/app/v1/cartographer/blueprints \
  src/app/v1/cartographer/proposals \
  src/app/v1/cartographer/v1-evidence \
  src/app/v1/cartographer/audit-trail \
  src/app/v1/cartographer/v1-readiness \
  src/app/v1/cartographer/trust-score \
  --include='route.ts'

git status --branch --short

git diff --stat
```

## Expected Output

```text
git diff --check prints nothing.

Focused ESLint prints no errors.

The first grep shows GET-only, display-only, Static fallback, blocked endpoint/action, full auto denial, and limited unattended operation denial matches.

The second grep may show inert blocked copy only; it must not show active controls or executable handlers.

Route grep shows GET handlers for the allowlisted endpoint routes. Nested proposal action routes may show POST handlers and must remain blocked display-only boundaries.

git status shows only the approved Plan 1 files added/modified plus pre-existing dirty/untracked work.

git diff --stat includes:
- src/app/map/page.tsx
- src/app/map/read-only-map-data.ts
- docs/cartographer-full-auto-plan-1-read-only-map-wiring-implementation-closeout.md
- pre-existing tracked dirty files
```

## Rollback Notes

Rollback for this increment is limited to:

- Remove Plan 1 read-only display wiring from `src/app/map/page.tsx`.
- Remove `src/app/map/read-only-map-data.ts`.
- Remove this closeout document.

Rollback must not touch unrelated dirty files. Rollback must not use checkout, clean, stash, reset, branch, worktree, commit, push, or merge without a separate explicit operator instruction.

## Stop Conditions

Stop immediately if:

- Any forbidden file must be edited.
- Any endpoint outside the allowlist is required.
- Any mutation endpoint is required.
- Any active button or click handler is required.
- Any write authority is requested.
- Any command execution authority is requested.
- Any queue execution authority is requested.
- Any approval authority or self-approval is requested.
- Any approval-token runtime is requested.
- Any durable queue or event storage is requested.
- Any dashboard, `/coding`, `src/app/v1/**`, Source Proxy, test, package, config, env, generated, or Scout mutation is required.
- Any limited unattended operation or full auto authority is implied.

## Next Recommended Increment Title

Plan 1 Operator Review: Read-Only /map Wiring Acceptance And Step 2 Permission Gate
