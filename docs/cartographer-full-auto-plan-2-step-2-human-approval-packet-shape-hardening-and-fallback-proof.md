# Cartographer Full Auto Plan 2 Step 2: Human Approval Packet Shape Hardening And Fallback Proof

status: implementation-closeout

Status date: 2026-05-22

Current HEAD: `40141f34d27d915503f265efba119673a412354a`

## Implementation Result

Plan 2 Step 2 is complete as a display-only `/map` packet-shape hardening increment.

This increment hardens the Plan 2 Human-Approved Operator display packet with explicit packet shape, approval state enum, required packet fields, forbidden packet fields, field-level fallback labels, blocked reasons, and fallback proof bullets.

This closeout does not add backend endpoints, call backend mutation endpoints, create approval-token runtime, create approval-token storage, record approvals, create durable queue/event storage, execute queues, run commands through Cartographer, write evidence, write receipts, grant limited unattended operation, or grant full auto.

Full auto is not granted. Limited unattended operation is not granted. Command execution is not granted. Queue execution is not granted.

## Files Changed

The exact Step 2 files changed are:

- `src/app/map/page.tsx`
- `src/app/map/human-approved-operator-data.ts`
- `docs/cartographer-full-auto-plan-2-step-2-human-approval-packet-shape-hardening-and-fallback-proof.md`

No other file is part of this Plan 2 Step 2 increment.

## Current Repo State

Implementation commands were run from `/home/source/SpiritOS`.

- Branch state: `main...origin/main [ahead 34]`.
- Current HEAD: `40141f34d27d915503f265efba119673a412354a`.
- Tracked dirty files already present outside this lane:
  - `docs/plan-index.md`
  - `package.json`
  - `src/app/coding/page.tsx`
  - `src/app/proxy-backend/page.tsx`
  - `src/app/v1/decisions/prompt-packet/route.ts`
  - `src/components/dashboard/demo-v4/DashboardDemoV4FloatingNav.tsx`

Those tracked dirty files and the broader untracked tree remain outside Plan 2 authority. They must not be cleaned, stashed, checked out, staged, committed, overwritten, deleted, or absorbed into this lane.

## What Changed

- Converted the Plan 2 required approval fields from plain labels into display-only objects with:
  - field label.
  - fallback label.
  - blocked reason.
- Added explicit packet shape display data:
  - packet kind.
  - allowed approval states.
  - required top-level fields.
  - forbidden top-level fields.
- Added explicit fallback reason to the display-only recommendation packet.
- Added fallback proof bullets to show how missing or unavailable approval data remains blocked and display-only.
- Rendered the hardened packet shape and fallback proof on `/map`.

## Packet Shape Requirements Met

The display-only Plan 2 packet now includes:

- `packet_id`
- `status_date`
- `packet_kind`
- `approval_state`
- `fallback_reason`
- `required_fields`
- `blocked_states`
- `forbidden_actions`
- `recommendation_summary`
- `manual_next_step`
- `authority_denials`

Allowed approval states are display-only:

- `blocked-until-explicit-human-approval`
- `missing-required-field`
- `fallback-display-only`
- `not-approved`

Forbidden packet fields are explicitly shown:

- `approval_token`
- `approval_secret`
- `bearer_token`
- `queue_execution_state`
- `command`
- `shell`
- `apply_instruction`
- `write_instruction`
- `commit_instruction`
- `push_instruction`

## Fallback Proof Requirements Met

The `/map` display now proves fallback behavior by showing:

- Missing or incomplete approval packet data renders as blocked display state.
- Required fields include explicit fallback labels and blocked reasons.
- Packet shape lists allowed approval states and forbidden executable fields.
- Authority denials remain visible when approval data is unavailable.
- No approval token, queue execution, command execution, write instruction, or self-approval field is present.

## What Remains Forbidden

- Backend endpoint creation.
- Backend mutation endpoint calls.
- `src/app/v1/**` edits.
- `src/app/api/**` edits.
- `src/app/proxy-backend/page.tsx` edits.
- Source Proxy edits.
- Test edits.
- Dashboard edits.
- `/coding` edits.
- Package, config, env, generated, or Scout edits.
- Approval-token runtime.
- Approval-token storage.
- Approval recording.
- Durable queue storage.
- Durable event storage.
- Queue execution.
- Command execution.
- Evidence writes.
- Receipt writes.
- Branch/worktree creation.
- Commit, push, merge, stash, checkout, clean, or delete.
- Limited unattended operation.
- Full auto.

## Manual Checks

```bash
cd /home/source/SpiritOS

git diff --check

npx eslint src/app/map/page.tsx src/app/map/read-only-map-data.ts src/app/map/human-approved-operator-data.ts

grep -nE "packet_kind|approval_state|fallback_reason|required_top_level_fields|forbidden_top_level_fields|humanApprovalFallbackProof|approval-token runtime is not approved|durable queue storage is not approved|durable event storage is not approved|command execution is not granted|queue execution is not granted|limited unattended operation is not granted|full auto is not granted" \
  src/app/map/human-approved-operator-data.ts \
  src/app/map/page.tsx \
  docs/cartographer-full-auto-plan-2-step-2-human-approval-packet-shape-hardening-and-fallback-proof.md

grep -nE "Packet kind|Approval state enum|Required packet fields|Forbidden packet fields|Human approval fallback proof|Fallback reason|blocked display state|forbidden executable fields" \
  src/app/map/page.tsx \
  docs/cartographer-full-auto-plan-2-step-2-human-approval-packet-shape-hardening-and-fallback-proof.md

grep -nE "onClick|<button|approve control|apply control|execute control|command input|shell controls|queue execution controls|token creation controls|self-approval controls" \
  src/app/map/page.tsx \
  src/app/map/human-approved-operator-data.ts || true

curl -k -sS -D /tmp/cartographer-map-plan2-step2.headers -o /tmp/cartographer-map-plan2-step2.html https://localhost:3000/map
sed -n '1,20p' /tmp/cartographer-map-plan2-step2.headers

grep -nE "Packet kind|Approval state enum|Required packet fields|Forbidden packet fields|Human approval fallback proof|approval-token runtime is not approved|durable queue storage is not approved|command execution is not granted|queue execution is not granted|limited unattended operation is not granted|full auto is not granted" \
  /tmp/cartographer-map-plan2-step2.html

grep -o '<button[^>]*>' /tmp/cartographer-map-plan2-step2.html || true

git status --short -- \
  src/app/map/page.tsx \
  src/app/map/read-only-map-data.ts \
  src/app/map/human-approved-operator-data.ts \
  docs/cartographer-full-auto-plan-2-human-approved-operator-v0-2-decision-packet.md \
  docs/cartographer-full-auto-plan-2-operator-review-human-approved-operator-v0-2-no-go-acceptance-and-implementation-decision-gate.md \
  docs/cartographer-full-auto-plan-2-human-approved-operator-v0-2-implementation-decision.md \
  docs/cartographer-full-auto-plan-2-human-approved-operator-v0-2-implementation-closeout.md \
  docs/cartographer-full-auto-plan-2-operator-review-display-only-human-approval-requirements-acceptance-and-step-2-permission-gate.md \
  docs/cartographer-full-auto-plan-2-step-2-human-approval-packet-shape-hardening-and-fallback-proof.md \
  docs/plan-index.md \
  package.json \
  src/app/coding/page.tsx \
  src/app/proxy-backend/page.tsx \
  src/app/v1/decisions/prompt-packet/route.ts \
  src/components/dashboard/demo-v4/DashboardDemoV4FloatingNav.tsx

git status --branch --short

git diff --stat
```

## Expected Output

```text
git diff --check prints nothing.

Focused ESLint prints no errors.

The packet-shape grep shows packet_kind, approval_state, fallback_reason, required_top_level_fields, forbidden_top_level_fields, fallback proof, and all authority denials.

The display grep shows Packet kind, Approval state enum, Required packet fields, Forbidden packet fields, Human approval fallback proof, fallback reason, blocked display state, and forbidden executable fields.

The control grep prints nothing or inert text only. It must not show active Cartographer approval/apply/execute/command/queue/token/self-approval controls.

The curl header includes HTTP/1.1 200 OK.

The rendered HTML grep shows the hardened Plan 2 packet shape, fallback proof, and authority denials.

The button grep may show only shared SpiritOS theme-picker buttons.

Focused status shows the Plan 2 `/map` files and docs plus pre-existing dirty files.

Repo status still shows the broader pre-existing dirty/untracked worktree.

git diff --stat shows tracked dirty files only unless untracked docs/files are staged by a separate explicit human git operation.
```

## Rollback Notes

Rollback for this increment is limited to:

- Remove Step 2 packet-shape display additions from `src/app/map/page.tsx`.
- Remove Step 2 packet-shape and fallback-proof data additions from `src/app/map/human-approved-operator-data.ts`.
- Remove `docs/cartographer-full-auto-plan-2-step-2-human-approval-packet-shape-hardening-and-fallback-proof.md`.

Rollback must not touch unrelated dirty files. Rollback must not use checkout, clean, stash, reset, branch, worktree, commit, push, or merge unless a separate human operator explicitly authorizes that exact operation.

## Stop Conditions

Stop immediately if any next increment requires:

- Backend/API edits.
- Source Proxy edits.
- Tests.
- Dashboard edits.
- `/coding` edits.
- Package, config, env, generated, or Scout edits.
- New endpoint wiring.
- POST, PUT, PATCH, or DELETE wiring.
- Approval-token runtime.
- Durable queue/event storage.
- Write authority.
- Command execution authority.
- Queue execution authority.
- Approval generation.
- Self-approval.
- Evidence writes.
- Receipt writes.
- Limited unattended operation.
- Full auto.

## Next Recommended Increment Title

Plan 2 Operator Review: Human Approval Packet Shape Hardening And Fallback Proof Acceptance And Step 3 Permission Gate
