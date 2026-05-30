# Cartographer Full Auto Plan 1 Operator Review: Read-Only /map Wiring Acceptance And Step 2 Permission Gate

status: operator-review-permission-gate

Status date: 2026-05-22

Current HEAD: `40141f34d27d915503f265efba119673a412354a`

## Review Result

Plan 1 Step 1 is accepted for operator review as a display-only read-only `/map` wiring increment.

The implemented lane is limited to:

- GET-only allowlist reads.
- 1500ms per-endpoint timeout.
- Static fallback display state.
- Display-only recommendation packet.
- Display-only blocked endpoint/action classifier.
- Visible authority denials.

This review does not grant write authority, command execution authority, queue execution authority, approval authority, self-approval, limited unattended operation, or full auto.

Full auto is not granted. Limited unattended operation is not granted.

## Files Accepted For This Increment

The accepted Plan 1 Step 1 files are:

- `src/app/map/page.tsx`
- `src/app/map/read-only-map-data.ts`
- `docs/cartographer-full-auto-plan-1-implementation-decision-read-only-map-wiring.md`
- `docs/cartographer-full-auto-plan-1-read-only-map-wiring-implementation-closeout.md`
- `docs/cartographer-full-auto-plan-1-operator-review-read-only-map-wiring-acceptance-and-step-2-permission-gate.md`

No other file is accepted into Plan 1 Step 1 scope by this packet.

## Current Repo State

The repo remains dirty and ahead of origin. Existing unrelated dirty and untracked files are not part of this Plan 1 lane.

Known unrelated tracked dirty files include:

- `docs/plan-index.md`
- `package.json`
- `src/app/coding/page.tsx`
- `src/app/v1/decisions/prompt-packet/route.ts`
- `src/components/dashboard/demo-v4/DashboardDemoV4FloatingNav.tsx`

Those files must not be cleaned, staged, committed, reverted, checked out, stashed, deleted, or absorbed into this lane without separate explicit instruction.

## Acceptance Criteria

Plan 1 Step 1 is acceptable only if all of these remain true:

- `/map` renders with display-only GET state or static fallback state.
- `/map` uses only the exact GET-only endpoint allowlist.
- Timeout behavior is bounded.
- Failed reads keep fallback display state.
- Recommendation packets are display-only.
- Blocked endpoint/action findings are display-only.
- No active approval, apply, execute, commit, push, branch, queue, command, or self-approval controls exist.
- No write authority is introduced.
- No command execution authority is introduced.
- No queue execution authority is introduced.
- No approval authority is introduced.
- No durable queue storage is introduced.
- No event storage is introduced.
- No approval-token runtime is introduced.
- Full auto is not granted.
- Limited unattended operation is not granted.

## Step 2 Permission Gate

Step 2 is not approved by this packet.

Step 2 may be proposed only as a narrow display-only hardening pass. Candidate title:

Plan 1 Step 2: Read-Only /map Packet Shape Hardening And Fallback Proof

Step 2 may request permission to:

- Refine display-only packet field labels.
- Add clearer fallback-state wording.
- Add more explicit stale/unavailable display states.
- Add docs-only proof that the GET-only allowlist remains bounded.
- Add a closeout doc for Step 2.

Step 2 must not request:

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
- Approval, apply, execute, commit, push, branch, worktree, stash, checkout, clean, delete, or command controls.
- Limited unattended operation.
- Full auto.

## Exact Files Allowed If Step 2 Is Later Approved

If the operator explicitly approves Step 2 after this gate, the allowed files should be exactly:

- `src/app/map/page.tsx`
- `src/app/map/read-only-map-data.ts`
- `docs/cartographer-full-auto-plan-1-step-2-read-only-map-packet-shape-hardening-and-fallback-proof.md`

No other files are allowed without a new decision packet.

## Forbidden Files For Step 2

Step 2 must not touch:

- `/coding` files.
- `src/app/coding/**`
- `src/components/coding/**`
- `src/lib/coding/**`
- Dashboard files.
- `src/components/dashboard/**`
- `src/app/v1/**`
- `src/app/api/**`
- `source_proxy/**`
- tests.
- package files.
- config files.
- env files.
- generated files.
- Scout files.
- runtime files.
- data files.
- approval, evidence, receipt, queue, or event-storage files.
- unrelated dirty files.

## Manual Checks

```bash
cd /home/source/SpiritOS

git diff --check

npx eslint src/app/map/page.tsx src/app/map/read-only-map-data.ts

grep -nE "Review Result|Step 2 Permission Gate|not approved|Full auto is not granted|Limited unattended operation is not granted|GET-only|display-only|Forbidden Files For Step 2|Next Recommended Increment Title" \
  docs/cartographer-full-auto-plan-1-operator-review-read-only-map-wiring-acceptance-and-step-2-permission-gate.md

grep -nE "GET-only|display-only|Static fallback|blocked endpoint|blocked action|full auto is not granted|limited unattended operation is not granted" \
  src/app/map/page.tsx \
  src/app/map/read-only-map-data.ts \
  docs/cartographer-full-auto-plan-1-read-only-map-wiring-implementation-closeout.md

grep -nE "onClick|<button|approval token|self-approval|queue execution controls|command controls" \
  src/app/map/page.tsx \
  src/app/map/read-only-map-data.ts || true

git status --short -- \
  src/app/map/page.tsx \
  src/app/map/read-only-map-data.ts \
  docs/cartographer-full-auto-plan-1-implementation-decision-read-only-map-wiring.md \
  docs/cartographer-full-auto-plan-1-read-only-map-wiring-implementation-closeout.md \
  docs/cartographer-full-auto-plan-1-operator-review-read-only-map-wiring-acceptance-and-step-2-permission-gate.md \
  docs/plan-index.md

git status --branch --short

git diff --stat
```

## Expected Output

```text
git diff --check prints nothing.

Focused ESLint prints nothing.

The gate doc grep shows Review Result, Step 2 Permission Gate, not-approved language, full-auto denial, limited-unattended denial, GET-only/display-only language, forbidden files, and the next increment title.

The /map grep shows GET-only, display-only, Static fallback, blocked endpoint/action, full auto denial, and limited unattended operation denial matches.

The control grep may show inert copy only. It must not show active click handlers, buttons, command controls, queue execution controls, approval-token runtime, or self-approval implementation.

Focused status shows only the Plan 1 docs and /map files in this lane, plus unrelated docs/plan-index.md drift if it remains dirty.

Repo status still shows the broader pre-existing dirty/untracked worktree.
```

## Stop Conditions

Stop before Step 2 if:

- The operator does not explicitly approve Step 2.
- Any Step 2 file would fall outside the exact allowed file list.
- Any forbidden file must be edited.
- Any new endpoint is needed.
- Any mutation endpoint is needed.
- Any write, command, queue execution, approval, self-approval, durable storage, event storage, or approval-token runtime is requested.
- Any limited unattended operation or full auto is implied.

## Next Recommended Increment Title

Plan 1 Step 2: Read-Only /map Packet Shape Hardening And Fallback Proof
