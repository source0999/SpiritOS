# Cartographer Full Auto Plan 1 Implementation Decision: Read-Only /map Wiring

status: implementation-decision-packet

Status date: 2026-05-22

Current HEAD: `40141f34d27d915503f265efba119673a412354a`

## Decision Result

Plan 1 read-only `/map` wiring is GO only as a later, explicitly approved, tightly scoped implementation package.

Implementation remains NO-GO in this chat. This packet does not wire `/map`, add fetch calls, call backend endpoints, edit `src/app/map/page.tsx`, edit tests, edit runtime files, edit dashboard files, stage changes, commit changes, grant limited unattended operation, or grant full auto.

The implementation approval must be reviewed after this packet. Until that explicit approval exists, read-only wiring remains unimplemented.

Full auto is not granted. Limited unattended operation is not granted.

## Current Repo State

Initial takeover commands were run from `/home/source/SpiritOS`.

- Branch state: `main...origin/main [ahead 34]`.
- Current HEAD: `40141f34d27d915503f265efba119673a412354a`.
- Tracked dirty files already present before this packet:
  - `package.json`
  - `src/app/coding/page.tsx`
  - `src/app/v1/decisions/prompt-packet/route.ts`
  - `src/components/dashboard/demo-v4/DashboardDemoV4FloatingNav.tsx`
- Initial tracked diff stat:
  - 4 files changed.
  - 190 insertions.
  - 34 deletions.
- Many untracked Cartographer docs, `source_proxy` files, tests, `/coding` files, and `/map` files already exist in the working tree.

Those pre-existing changes are not Plan 1 implementation authority. They must not be cleaned, stashed, checked out, staged, committed, overwritten, deleted, or absorbed into the read-only `/map` wiring lane.

## Current /map State

Current `/map` state is static, inert, and unwired.

Verified from `src/app/map/page.tsx` and the Phase 13 closeouts:

- `/map` is a single route file: `src/app/map/page.tsx`.
- It imports the existing dashboard floating nav and dashboard stylesheet.
- It renders static manual-control sections, static candidate endpoint text, static mutation-boundary text, static no-go decision text, and static final-review text.
- It has no `fetch(` usage.
- It has no `sourceProxyFetch` usage.
- It has no `proxyCartographer` usage.
- It has no `onClick` usage.
- It has no `<button` usage.
- It does not call backend endpoints.
- It does not expose executable controls.
- It states full auto is not granted and limited unattended operation is not granted.

## Exact Allowed Implementation Files If GO

If, and only if, the operator explicitly approves implementation after reviewing this packet, the allowed implementation files are exactly:

- `src/app/map/page.tsx`
- `src/app/map/read-only-map-data.ts`
- `docs/cartographer-full-auto-plan-1-read-only-map-wiring-implementation-closeout.md`

No other implementation files are allowed by this decision packet.

The implementation may add display-only read wiring in those files only. It must not add write authority, command authority, queue execution authority, approval authority, self-approval, durable storage, event storage, approval-token runtime, limited unattended operation, or full auto.

## Exact Forbidden Files

The following remain forbidden for Plan 1 read-only `/map` wiring:

- `/coding` files.
- `src/app/coding/page.tsx`
- `src/app/coding/**`
- `src/components/coding/**`
- `src/lib/coding/**`
- Dashboard files.
- `src/components/dashboard/**`
- `src/app/v1/**`
- `src/app/api/**`
- `source_proxy/**`
- `source_proxy/cartographer/**`
- `source_proxy/tests/**`
- tests, including `**/__tests__/**`, `*.test.ts`, `*.test.tsx`, and Python tests.
- `package.json`
- lockfiles.
- config files.
- env files.
- generated files.
- Scout files.
- runtime files.
- data files.
- approval, evidence, receipt, queue, or event-storage files.
- any pre-existing dirty file not explicitly listed in the allowed implementation files.

If implementation would require any forbidden file, the decision becomes NO-GO.

## Candidate GET-only Endpoint Allowlist

The later implementation may use only this candidate GET-only allowlist, and only after reconfirming each route remains GET-only immediately before implementation:

| Endpoint | Display purpose | Required handling |
| --- | --- | --- |
| `/v1/cartographer/status` | Status and authority-denial summary | display-only |
| `/v1/cartographer/repo-map` | Repository map summary | display-only |
| `/v1/cartographer/blueprints` | Blueprint map summary | display-only |
| `/v1/cartographer/proposals` | Recommendation/proposal summary | display-only; no review or apply action |
| `/v1/cartographer/v1-evidence` | Existing evidence summary | display-only; no evidence write |
| `/v1/cartographer/audit-trail` | Existing audit hints | display-only; no ledger write |
| `/v1/cartographer/v1-readiness` | Readiness signal | display-only; cannot promote authority |
| `/v1/cartographer/trust-score` | Trust score signal | display-only; cannot promote authority |

No endpoint outside this list is approved by this packet. A future implementation must keep the allowlist as data in the `/map` lane and must fail closed if a requested endpoint is absent from the allowlist.

## Explicitly Blocked Endpoint/Action Classes

The following blocked endpoint classes must remain unavailable:

- Any `POST`, `PUT`, `PATCH`, or `DELETE` endpoint.
- Any endpoint path containing `approve`.
- Any endpoint path containing `review`.
- Any endpoint path containing `apply`.
- Any endpoint path containing `apply-approved`.
- Any endpoint path containing `docs-autopilot/apply`.
- Any endpoint path containing `commit`.
- Any endpoint path containing `push`.
- Any endpoint path containing `branch`.
- Any endpoint path containing `autonomy-promotion`.
- Any endpoint that mutates files, queue state, event state, approval state, evidence, receipts, audit ledgers, branches, worktrees, package state, config state, dashboard state, `/coding` state, runtime state, or tests.

The following action classes must remain blocked:

- File writes.
- Evidence writes.
- Receipt writes.
- Durable queue writes.
- Event storage writes.
- Queue execution.
- Command execution through Cartographer.
- Local shell execution through Cartographer.
- Automatic task selection.
- Approval generation.
- Approval recording.
- Self-approval.
- Approval-token runtime creation.
- Branch creation.
- Worktree creation.
- Commit, push, or merge.
- Stash, checkout, clean, or delete.
- Runtime mutation.
- Test mutation.
- Dashboard mutation.
- `/coding` shell or UI mutation.
- Package, config, environment, generated, Scout, API, or Source Proxy mutation.

Blocked endpoint and blocked action findings may be displayed as inert labels only. They must not become controls.

## Timeout And Fallback Requirements

Any later read-only implementation must use bounded reads:

- Use an explicit short timeout per endpoint.
- Treat timeout as unavailable display data.
- Do not retry indefinitely.
- Do not fan out to unapproved endpoints.
- Do not call mutation endpoints as fallback.
- Do not write timeout evidence, receipts, audit records, events, queue entries, or approval requests.
- Do not schedule monitors, background jobs, alerts, or follow-ups.

Fallback must be conservative:

- Keep `/map` renderable when every endpoint is unavailable.
- Preserve the current static manual-control content as fallback.
- Mark live sections unavailable, stale, or blocked.
- Keep full auto denial visible.
- Keep limited unattended operation denial visible.
- Keep mutation endpoints visibly blocked.
- Never show repair, approve, apply, execute, commit, push, branch, or command controls.

## Recommendation Packet Requirements

A read-only recommendation packet may be displayed only as inert UI data.

Required packet fields:

- `packet_id`
- `status_date`
- `head`
- `branch_summary`
- `dirty_tree_summary`
- `changed_file_list`
- `source_endpoints_observed`
- `source_endpoints_blocked`
- `protected_lane_findings`
- `blocked_action_classes`
- `recommendation_summary`
- `manual_next_step`
- `authority_denials`

Forbidden packet fields:

- Approval token material.
- Secrets.
- Environment values.
- Executable commands.
- Durable queue state.
- Event ledger writes.
- Evidence write instructions.
- Receipt write instructions.
- Apply instructions.
- Commit, push, merge, branch, worktree, stash, checkout, clean, or delete instructions.
- Self-approval fields.
- Autonomous task selection.

Recommendation wording must remain human-facing and inert. It may recommend manual operator review, narrower observation, or stopping. It must not approve or execute anything.

## Blocked Action Classifier Requirements

The later display-only implementation must include a read-only classifier shape that labels blocked actions without executing them.

Classifier requirements:

- Fail closed for unknown action classes.
- Fail closed for ambiguous file scope.
- Fail closed for any trust tier above Tier 1.
- Fail closed for any path in a forbidden file family.
- Fail closed for any endpoint outside the GET-only allowlist.
- Fail closed for any write, command execution, queue execution, approval generation, self-approval, branch/worktree, git mutation, runtime mutation, test mutation, dashboard mutation, `/coding` mutation, package/config/env/generated/Scout mutation, API mutation, or Source Proxy mutation.
- Produce display-only findings with `blocked: true`, blocked class, reason, protected path match if present, and manual next step.

The classifier must not become a runtime permission system, approval system, queue system, action runner, or command runner in Plan 1.

## UI Display-only Requirements

The later `/map` implementation must remain display-only:

- It may render live read-only status.
- It may render recommendation packets.
- It may render blocked endpoint findings.
- It may render fallback and stale states.
- It may render authority denial state.
- It may render manual next-step text.
- It must not render active approval controls.
- It must not render apply controls.
- It must not render execute controls.
- It must not render commit, push, merge, branch, worktree, stash, checkout, clean, or delete controls.
- It must not render command input.
- It must not render shell controls.
- It must not render queue execution controls.
- It must not render kill-switch mutation controls.
- It must not render self-approval controls.
- It must not hide that full auto is not granted.
- It must not hide that limited unattended operation is not granted.

Links for static section navigation may remain. Any interactive control that can mutate state is forbidden.

## Verification Commands Required Before Implementation

Run these commands before any later implementation begins:

```bash
cd /home/source/SpiritOS
git status --branch --short
git rev-parse HEAD
git diff --stat
git diff --name-only
grep -nE "fetch\\(|sourceProxyFetch|proxyCartographer|onClick|<button" src/app/map/page.tsx || true
grep -RInE "export async function (GET|POST|PUT|PATCH|DELETE)" src/app/v1/cartographer --include='route.ts'
```

Required before-implementation result:

- Dirty tree is known and not cleaned.
- HEAD is captured.
- Existing tracked dirty files are not absorbed into Plan 1.
- `/map` still has no fetch/proxy/click/button wiring before implementation starts.
- Candidate endpoints are reconfirmed as GET-only.
- Blocked endpoints are reconfirmed as mutation-capable or authority-promoting.

## Verification Commands Required After Implementation

Run these commands after any later explicitly approved implementation:

```bash
cd /home/source/SpiritOS
git diff --check
grep -nE "POST|PUT|PATCH|DELETE|approve|apply|commit|push|branch|autonomy-promotion" src/app/map/page.tsx src/app/map/read-only-map-data.ts || true
grep -nE "onClick|<button|command|execute|approval token|self-approval" src/app/map/page.tsx src/app/map/read-only-map-data.ts || true
grep -nE "full auto is not granted|limited unattended operation is not granted|display-only|GET-only|blocked endpoint" src/app/map/page.tsx src/app/map/read-only-map-data.ts
npx eslint src/app/map/page.tsx src/app/map/read-only-map-data.ts
git status --branch --short
git diff --stat
git diff --name-only
```

Required after-implementation result:

- `git diff --check` passes.
- Focused ESLint passes.
- Diffs are limited to the exact allowed files.
- `/map` contains only GET-only display reads from the allowlist.
- Mutation/action strings appear only in blocked display text, not executable paths.
- Full auto denial remains visible.
- Limited unattended operation denial remains visible.

## Manual Checks

Manual checks required after any later implementation:

- Load `/map` with backend endpoints available.
- Load `/map` with backend endpoints unavailable.
- Confirm `/map` renders in both cases.
- Confirm endpoint failures show fallback or stale display state.
- Confirm no active approval, apply, execute, commit, push, branch, command, queue, kill-switch mutation, or self-approval controls exist.
- Confirm recommendation packets are display-only.
- Confirm blocked action findings are display-only.
- Confirm static section navigation still works.
- Confirm full auto is not granted.
- Confirm limited unattended operation is not granted.
- Confirm no dashboard, `/coding`, `src/app/v1/**`, `source_proxy/**`, tests, package, config, env, generated, or Scout files were edited.

## Rollback Notes

If later implementation is approved and then must be rolled back, rollback is limited to:

- Remove read-only data usage from `src/app/map/page.tsx`.
- Remove `src/app/map/read-only-map-data.ts`.
- Remove `docs/cartographer-full-auto-plan-1-read-only-map-wiring-implementation-closeout.md`.

Rollback must not touch unrelated dirty files. Rollback must not use checkout, clean, stash, reset, branch, worktree, commit, push, or merge unless a separate human operator explicitly authorizes that exact operation.

## Stop Conditions

Stop immediately and treat implementation as NO-GO if:

- Operator approval for implementation is absent.
- Any required implementation file is outside the exact allowed file list.
- Any forbidden file must be edited.
- Any candidate endpoint is not GET-only.
- Any endpoint outside the allowlist is required.
- Any mutation endpoint is required.
- Any write authority is requested.
- Any command execution authority is requested.
- Any queue execution authority is requested.
- Any approval authority or self-approval is requested.
- Any approval-token runtime is requested.
- Any durable queue or event storage is requested.
- Any runtime, test, dashboard, `/coding`, API, Source Proxy, package, config, env, generated, or Scout mutation is required.
- Any limited unattended operation is implied.
- Any full auto authority is implied.
- Verification fails before implementation.
- Verification fails after implementation.

## Next Recommended Increment

Next recommended increment: operator review of this decision packet and explicit written approval or denial for the narrowly scoped Plan 1 read-only `/map` wiring implementation.

If approved, the next implementation increment should be titled:

Plan 1 Implementation Step 1: Display-only GET Allowlist Adapter And Static Fallback
