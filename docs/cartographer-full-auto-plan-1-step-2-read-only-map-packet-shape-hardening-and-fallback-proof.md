# Cartographer Full Auto Plan 1 Step 2: Read-Only /map Packet Shape Hardening And Fallback Proof

status: implementation-closeout

Status date: 2026-05-22

Current HEAD: `40141f34d27d915503f265efba119673a412354a`

## Result

Plan 1 Step 2 is complete as a narrow display-only hardening increment.

This increment hardens the `/map` packet shape and fallback proof wording. It does not add endpoints, edit backend routes, edit tests, edit `/coding`, edit dashboard files, edit Source Proxy files, add durable storage, add approval-token runtime, add execution controls, grant limited unattended operation, or grant full auto.

Full auto is not granted. Limited unattended operation is not granted.

## Files Changed

- `src/app/map/page.tsx`
- `src/app/map/read-only-map-data.ts`
- `docs/cartographer-full-auto-plan-1-step-2-read-only-map-packet-shape-hardening-and-fallback-proof.md`

## What Changed

- Added explicit packet kind: `display-only-read-only-map`.
- Added explicit fallback state: `none`, `partial`, or `active`.
- Added explicit fallback reason.
- Added fallback proof bullets.
- Split packet identity from recommendation summary in the `/map` display.
- Added fallback proof display on `/map`.
- Reworded stale pre-implementation labels so they now describe bounded Plan 1 display-only wiring and wider-authority no-go state.

## What Remains Blocked

- New backend endpoints.
- Edits to `src/app/v1/**`.
- Edits to `source_proxy/**`.
- Edits to tests.
- Edits to dashboard files.
- Edits to `/coding` files.
- Package, config, env, generated, or Scout edits.
- Durable queue storage.
- Event storage.
- Approval-token runtime.
- Approval controls.
- Apply controls.
- Execute controls.
- Commit, push, branch, worktree, stash, checkout, clean, delete, or command controls.
- Limited unattended operation.
- Full auto.

## Fallback Proof

The fallback proof remains display-only:

- Missing origin creates active fallback.
- Failed, timed-out, or non-OK GET reads create partial fallback.
- Successful reads create no fallback but still cannot promote authority.
- Fallback proof text is displayed in `/map`.
- Fallback proof does not create evidence, receipts, queue entries, event records, approval requests, alerts, monitors, jobs, or follow-ups.

## Manual Checks

```bash
cd /home/source/SpiritOS

git diff --check

npx eslint src/app/map/page.tsx src/app/map/read-only-map-data.ts

grep -nE "packet_kind|fallback_state|fallback_reason|fallbackProof|Fallback proof|display-only-read-only-map|full auto is not granted|limited unattended operation is not granted" \
  src/app/map/page.tsx \
  src/app/map/read-only-map-data.ts \
  docs/cartographer-full-auto-plan-1-step-2-read-only-map-packet-shape-hardening-and-fallback-proof.md

grep -nE "No-go until explicit operator approval|Read-only wiring remains denied|Not implemented|Not wired|No backend calls|No endpoint calls" \
  src/app/map/page.tsx \
  src/app/map/read-only-map-data.ts || true

grep -nE "onClick|<button|approval token|self-approval|queue execution controls|command controls" \
  src/app/map/page.tsx \
  src/app/map/read-only-map-data.ts || true

git status --short -- \
  src/app/map/page.tsx \
  src/app/map/read-only-map-data.ts \
  docs/cartographer-full-auto-plan-1-implementation-decision-read-only-map-wiring.md \
  docs/cartographer-full-auto-plan-1-read-only-map-wiring-implementation-closeout.md \
  docs/cartographer-full-auto-plan-1-operator-review-read-only-map-wiring-acceptance-and-step-2-permission-gate.md \
  docs/cartographer-full-auto-plan-1-step-2-read-only-map-packet-shape-hardening-and-fallback-proof.md \
  docs/plan-index.md

git status --branch --short

git diff --stat
```

## Expected Output

```text
git diff --check prints nothing.

Focused ESLint prints nothing.

The packet/fallback grep shows packet_kind, fallback_state, fallback_reason, fallbackProof, Fallback proof, display-only-read-only-map, full-auto denial, and limited-unattended denial matches.

The stale-copy grep prints nothing.

The control grep may show inert copy only. It must not show active click handlers, buttons, command controls, queue execution controls, approval-token runtime, or self-approval implementation.

Focused status shows the Plan 1 docs and /map files in this lane, plus unrelated docs/plan-index.md drift if it remains dirty.

Repo status still shows the broader pre-existing dirty/untracked worktree.
```

## Stop Conditions

Stop if any next increment requires:

- New endpoints.
- Backend/API edits.
- Source Proxy edits.
- Tests.
- Dashboard edits.
- `/coding` edits.
- Package, config, env, generated, or Scout edits.
- Durable storage.
- Approval-token runtime.
- Write authority.
- Command execution authority.
- Queue execution authority.
- Approval authority.
- Self-approval.
- Limited unattended operation.
- Full auto.

## Next Recommended Increment Title

Plan 1 Step 3: Read-Only /map Manual Browser Acceptance And Phase Closeout Gate
