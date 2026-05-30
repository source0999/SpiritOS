# Cartographer Full Auto Plan 2 Implementation Decision: Human-Approved Operator v0.2 Display-Only Scope Approval Or No-Go

status: implementation-decision-packet

Status date: 2026-05-22

Current HEAD: `40141f34d27d915503f265efba119673a412354a`

## Decision Result

Plan 2 Human-Approved Operator v0.2 display-only scope is GO only as a later, explicitly approved, tightly scoped implementation package.

Implementation remains NO-GO in this chat. This packet does not edit `/map`, add runtime behavior, add backend endpoints, call backend mutation endpoints, create approval-token runtime, create durable queue/event storage, enable command execution, enable queue execution, enable unattended writes, grant limited unattended operation, or grant full auto.

The implementation approval must be reviewed after this packet. Until that explicit approval exists, Plan 2 display-only implementation remains unimplemented.

Full auto is not granted. Limited unattended operation is not granted. Command execution is not granted. Queue execution is not granted.

## Current Repo State

Initial commands for this decision packet were run from `/home/source/SpiritOS`.

- Branch state: `main...origin/main [ahead 34]`.
- Current HEAD: `40141f34d27d915503f265efba119673a412354a`.
- Tracked dirty files already present before this packet:
  - `docs/plan-index.md`
  - `package.json`
  - `src/app/coding/page.tsx`
  - `src/app/proxy-backend/page.tsx`
  - `src/app/v1/decisions/prompt-packet/route.ts`
  - `src/components/dashboard/demo-v4/DashboardDemoV4FloatingNav.tsx`
- Initial tracked diff stat:
  - 6 files changed.
  - 363 insertions.
  - 37 deletions.
- Initial tracked dirty file list:
  - `docs/plan-index.md`
  - `package.json`
  - `src/app/coding/page.tsx`
  - `src/app/proxy-backend/page.tsx`
  - `src/app/v1/decisions/prompt-packet/route.ts`
  - `src/components/dashboard/demo-v4/DashboardDemoV4FloatingNav.tsx`
- Existing Plan 2 docs are untracked:
  - `docs/cartographer-full-auto-plan-2-human-approved-operator-v0-2-decision-packet.md`
  - `docs/cartographer-full-auto-plan-2-operator-review-human-approved-operator-v0-2-no-go-acceptance-and-implementation-decision-gate.md`

Those pre-existing tracked and untracked changes are not Plan 2 implementation authority. They must not be cleaned, stashed, checked out, staged, committed, overwritten, deleted, or absorbed into this implementation decision lane.

## Accepted Prior State

Accepted prior state:

- Plan 1 read-only `/map` wiring is accepted and closed only for display-only GET allowlist scope.
- Plan 2 decision packet is accepted as a docs-only NO-GO implementation gate.
- Plan 2 operator review accepted the NO-GO decision and requested an implementation decision packet before any implementation.
- No implementation permission exists yet.
- No runtime, endpoint, dashboard, `/coding`, Source Proxy, test, package, config, env, generated, or Scout file is approved for editing now.

Accepted prior Plan 2 docs:

- `docs/cartographer-full-auto-plan-2-human-approved-operator-v0-2-decision-packet.md`
- `docs/cartographer-full-auto-plan-2-operator-review-human-approved-operator-v0-2-no-go-acceptance-and-implementation-decision-gate.md`

## Exact Allowed Implementation Files If Later Approved

If, and only if, the operator explicitly approves implementation after reviewing this packet, the allowed implementation files are exactly:

- `src/app/map/page.tsx`
- `src/app/map/read-only-map-data.ts`
- `src/app/map/human-approved-operator-data.ts`
- `docs/cartographer-full-auto-plan-2-human-approved-operator-v0-2-implementation-closeout.md`

No other implementation files are allowed by this decision packet.

This file list is not active permission. It becomes usable only after an explicit later chat approval for Plan 2 implementation.

## Exact Forbidden Files

The following remain forbidden for any later Plan 2 implementation:

- `/coding` files.
- `src/app/coding/**`.
- `src/components/coding/**`.
- `src/lib/coding/**`.
- Dashboard files.
- `src/components/dashboard/**`.
- `src/app/v1/**`.
- `src/app/api/**`.
- `src/app/proxy-backend/page.tsx`.
- `source_proxy/**`.
- `source_proxy/cartographer/**`.
- `source_proxy/tests/**`.
- tests, including `**/__tests__/**`, `*.test.ts`, `*.test.tsx`, and Python tests.
- `package.json`.
- lockfiles.
- config files.
- env files.
- generated files.
- Scout files.
- runtime files.
- data files outside the exact allowed file list.
- durable queue files.
- event-storage files.
- approval-token runtime files.
- approval, evidence, receipt, queue, or event mutation files.
- any pre-existing dirty file not explicitly listed in the allowed implementation files.

If implementation would require any forbidden file, the decision becomes NO-GO.

## Exact Authority Still Denied

The following authority remains denied:

- Write authority outside the exact later approved files.
- Evidence write authority.
- Receipt write authority.
- Approval-token runtime authority.
- Approval-token creation.
- Approval-token storage.
- Approval-token mutation.
- Approval generation authority.
- Self-approval authority.
- Backend endpoint creation.
- Backend mutation endpoint calls.
- Durable queue storage.
- Durable event storage.
- Queue execution authority.
- Command execution authority.
- Local shell execution through Cartographer.
- Automatic task selection.
- Branch creation.
- Worktree creation.
- Commit, push, or merge.
- Stash, checkout, clean, or delete.
- Runtime mutation.
- Test mutation.
- Dashboard mutation.
- `/coding` shell or UI mutation.
- Package, config, env, generated, Scout, API, or Source Proxy mutation.
- Limited unattended operation.
- Full auto.

## Candidate Human-Approved Operator Display Scope

The later Plan 2 implementation may add display-only human-approved operator state to `/map`.

Allowed candidate behavior:

- Show Plan 2 implementation-gated state.
- Show human approval requirements.
- Show required approval token fields as inert requirements.
- Show missing approval fields.
- Show approval blockers.
- Show stale HEAD block.
- Show dirty-tree mismatch block.
- Show expired approval block.
- Show self-approval block.
- Show missing rollback block.
- Show missing verification block.
- Show kill-switch blocked state.
- Show exact allowed file and exact forbidden file requirements.
- Show manual operator next step.
- Preserve Plan 1 display-only GET allowlist state and static fallback behavior.

Forbidden candidate behavior:

- Creating approval tokens.
- Storing approval tokens.
- Runtime token validation that mutates state.
- Approval queue storage.
- Approval recording.
- Action execution.
- Backend mutation calls.
- Evidence writes.
- Receipt writes.
- Command execution.
- Queue execution.
- Unattended writes.
- Limited unattended operation.
- Full auto.

## Candidate Endpoint And Action Allowlist

The later implementation may use only existing Plan 1 GET-only display sources unless a future packet reconfirms a narrower set immediately before implementation:

| Candidate | Display purpose | Required handling |
| --- | --- | --- |
| `/v1/cartographer/status` | Status and authority-denial summary | display-only |
| `/v1/cartographer/repo-map` | Repo and dirty-tree summary | display-only |
| `/v1/cartographer/proposals` | Existing proposal summary | display-only; no review or apply action |
| `/v1/cartographer/audit-trail` | Existing audit hints | display-only; no ledger write |
| `/v1/cartographer/v1-readiness` | Readiness signal | display-only; cannot promote authority |
| `/v1/cartographer/trust-score` | Trust score signal | display-only; cannot promote authority |

Allowed display-only action labels:

- Show approval requirements.
- Show missing approval fields.
- Show approval blockers.
- Show manual operator next step.
- Show stop conditions.

No action may mutate state, issue approvals, execute queue items, run commands, write files, or call mutation endpoints.

## Explicitly Blocked Endpoint And Action Classes

Blocked endpoint classes:

- Any `POST`, `PUT`, `PATCH`, or `DELETE` endpoint.
- Any endpoint path containing `approve`.
- Any endpoint path containing `review` if it mutates state.
- Any endpoint path containing `apply`.
- Any endpoint path containing `apply-approved`.
- Any endpoint path containing `docs-autopilot/apply`.
- Any endpoint path containing `commit`.
- Any endpoint path containing `push`.
- Any endpoint path containing `branch`.
- Any endpoint path containing `queue` if it creates, updates, or executes queue state.
- Any endpoint path containing `event` if it writes event state.
- Any endpoint path containing `token` if it creates, stores, validates, or mutates approval-token state.
- Any endpoint path containing `autonomy-promotion`.
- Any endpoint that mutates files, approvals, queue state, event state, evidence, receipts, audit ledgers, branches, worktrees, package state, config state, dashboard state, `/coding` state, runtime state, tests, API state, or Source Proxy state.

Blocked action classes:

- File writes outside the exact later approved files.
- Evidence writes.
- Receipt writes.
- Approval-token creation.
- Approval-token storage.
- Approval-token runtime validation with mutation.
- Approval generation.
- Approval recording.
- Self-approval.
- Durable queue writes.
- Event storage writes.
- Queue execution.
- Command execution through Cartographer.
- Local shell execution through Cartographer.
- Automatic task selection.
- Branch creation.
- Worktree creation.
- Commit, push, or merge.
- Stash, checkout, clean, or delete.
- Runtime mutation.
- Test mutation.
- Dashboard mutation.
- `/coding` shell or UI mutation.
- Package, config, environment, generated, Scout, API, or Source Proxy mutation.
- Limited unattended operation.
- Full auto.

Blocked findings may be displayed as inert labels only.

## Approval Requirements

Any later Plan 2 implementation must display approval requirements without granting approval authority.

Required approval fields for display:

- Operator id.
- Approver id.
- Token id.
- Run id.
- Action type.
- Exact allowed files.
- Exact forbidden files.
- Expiry.
- Rollback instructions.
- Verification instructions.
- Current HEAD.
- Expected dirty tree state.
- Kill switch state.
- Trust tier.
- Human approval timestamp.

Fail-closed display states required:

- Missing operator id.
- Missing approver id.
- Self-approval.
- Missing token id.
- Missing run id.
- Missing or ambiguous action type.
- Missing exact allowed files.
- Missing exact forbidden files.
- Expired approval.
- Missing rollback instructions.
- Missing verification instructions.
- Stale HEAD.
- Dirty-tree mismatch.
- Kill switch blocked state.
- Trust tier above approved scope.
- Any authority broader than exact scope.

The implementation must not create, store, validate, or mutate approval tokens unless a later packet explicitly approves exact runtime behavior.

## Timeout And Fallback Requirements

Any later Plan 2 display-only read must use bounded timeout behavior:

- Use an explicit short timeout per endpoint.
- Treat timeout as unavailable display data.
- Do not retry indefinitely.
- Do not fan out to unapproved endpoints.
- Do not call mutation endpoints as fallback.
- Do not write timeout evidence, receipts, audit records, events, queue entries, or approval requests.
- Do not schedule monitors, background jobs, alerts, or follow-ups.

Fallback must be conservative:

- Keep `/map` renderable when every endpoint is unavailable.
- Preserve Plan 1 display-only fallback state.
- Mark Plan 2 approval sections unavailable, stale, blocked, or not approved.
- Keep full auto denial visible.
- Keep limited unattended operation denial visible.
- Keep command execution denial visible.
- Keep queue execution denial visible.
- Never show approve, apply, execute, commit, push, branch, queue-run, command, token-create, or self-approval controls.

## Recommendation Packet Requirements

The later implementation may show an inert Plan 2 recommendation packet.

Required packet fields:

- `packet_id`
- `status_date`
- `packet_kind`
- `head`
- `branch_summary`
- `dirty_tree_summary`
- `changed_file_list`
- `source_endpoints_observed`
- `source_endpoints_blocked`
- `approval_requirements`
- `missing_approval_fields`
- `approval_blockers`
- `protected_lane_findings`
- `blocked_action_classes`
- `recommendation_summary`
- `manual_next_step`
- `authority_denials`

Forbidden packet fields:

- Secrets.
- Environment values.
- Approval token secrets or bearer material.
- Durable queue execution state.
- Event ledger write instructions.
- Evidence write instructions.
- Receipt write instructions.
- Executable commands.
- Apply instructions.
- Commit, push, merge, branch, worktree, stash, checkout, clean, or delete instructions.
- Self-approval fields that imply approval.
- Autonomous task selection.

Recommendation wording must remain human-facing and inert. It may recommend manual operator review, narrower observation, later explicit implementation planning, or stopping. It must not approve or execute anything.

## Blocked Action Classifier Requirements

The later implementation may add display-only Plan 2 blocked-action classifier data.

Classifier requirements:

- Fail closed for unknown action classes.
- Fail closed for ambiguous file scope.
- Fail closed for any trust tier above the approved scope.
- Fail closed for missing approval fields.
- Fail closed for stale HEAD.
- Fail closed for dirty-tree mismatch.
- Fail closed for expired approval.
- Fail closed for self-approval.
- Fail closed for active kill switch state.
- Fail closed for any path in a forbidden file family.
- Fail closed for any endpoint outside the GET-only allowlist.
- Fail closed for any write outside exact approved files.
- Fail closed for command execution, queue execution, approval generation, token creation, self-approval, branch/worktree, git mutation, runtime mutation, test mutation, dashboard mutation, `/coding` mutation, package/config/env/generated/Scout mutation, API mutation, or Source Proxy mutation.
- Produce display-only findings with `blocked: true`, blocked class, reason, protected path match if present, missing approval fields if present, and manual next step.

The classifier must not become an action runner, command runner, queue runner, approval generator, token creator, token validator with mutation, or self-approval path.

## UI Display Requirements

Any later `/map` Plan 2 UI must remain display-only:

- It may render Plan 2 implementation-gated state.
- It may render human approval requirements.
- It may render missing approval fields.
- It may render blocked approval state.
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
- It must not render token creation controls.
- It must not render token validation mutation controls.
- It must not render kill-switch mutation controls.
- It must not render self-approval controls.
- It must not hide that implementation still requires explicit approval.
- It must not hide that full auto is not granted.
- It must not hide that limited unattended operation is not granted.
- It must not hide that command execution is not granted.
- It must not hide that queue execution is not granted.

Shared SpiritOS theme-picker buttons may continue to exist if inherited from existing navigation. Cartographer action controls remain forbidden.

## Verification Commands Required Before Implementation

Run these commands before any later Plan 2 implementation begins:

```bash
cd /home/source/SpiritOS
git status --branch --short
git rev-parse HEAD
git diff --stat
git diff --name-only
git diff --check
grep -nE "full auto is not granted|limited unattended operation is not granted|display-only|GET-only|blocked endpoint|fallback" src/app/map/page.tsx src/app/map/read-only-map-data.ts
grep -nE "onClick|<button|approve|apply|execute|commit|push|branch|queue execution|command controls|self-approval|token" src/app/map/page.tsx src/app/map/read-only-map-data.ts || true
grep -RInE "export async function (GET|POST|PUT|PATCH|DELETE)" src/app/v1/cartographer --include='route.ts'
```

Required before-implementation result:

- Dirty tree is known and not cleaned.
- HEAD is captured.
- Existing tracked dirty files are not absorbed into Plan 2.
- `/map` still shows Plan 1 display-only state.
- Candidate endpoints are reconfirmed as GET-only before use.
- Mutation, approval, queue, event, token, apply, commit, push, branch, and autonomy-promotion routes remain blocked.

## Verification Commands Required After Implementation

Run these commands after any later explicitly approved Plan 2 implementation:

```bash
cd /home/source/SpiritOS
git diff --check
grep -nE "POST|PUT|PATCH|DELETE|approve|apply|execute|commit|push|branch|queue|event|token|autonomy-promotion" src/app/map/page.tsx src/app/map/read-only-map-data.ts src/app/map/human-approved-operator-data.ts || true
grep -nE "onClick|<button|command|execute|approval token|self-approval|queue execution|write control" src/app/map/page.tsx src/app/map/read-only-map-data.ts src/app/map/human-approved-operator-data.ts || true
grep -nE "Plan 2|implementation-gated|not approved|full auto is not granted|limited unattended operation is not granted|command execution is not granted|queue execution is not granted|display-only|blocked" src/app/map/page.tsx src/app/map/read-only-map-data.ts src/app/map/human-approved-operator-data.ts
npx eslint src/app/map/page.tsx src/app/map/read-only-map-data.ts src/app/map/human-approved-operator-data.ts
git status --branch --short
git diff --stat
git diff --name-only
```

Required after-implementation result:

- `git diff --check` passes.
- Focused ESLint passes.
- Diffs are limited to the exact allowed files from this packet.
- `/map` remains display-only.
- Approval/token/queue/action strings appear only in blocked display text, not executable paths.
- Full auto denial remains visible.
- Limited unattended operation denial remains visible.
- Command execution denial remains visible.
- Queue execution denial remains visible.

## Manual Checks

```bash
cd /home/source/SpiritOS

git diff --check

grep -nE "Plan 2|GO|NO-GO|Human-Approved Operator|implementation remains NO-GO|not approved|not granted|Exact Allowed Implementation Files|Exact Forbidden Files|approval-token runtime|durable queue|command execution|queue execution|full auto|limited unattended operation|Next Recommended Increment Title" \
  docs/cartographer-full-auto-plan-2-human-approved-operator-v0-2-decision-packet.md \
  docs/cartographer-full-auto-plan-2-operator-review-human-approved-operator-v0-2-no-go-acceptance-and-implementation-decision-gate.md \
  docs/cartographer-full-auto-plan-2-human-approved-operator-v0-2-implementation-decision.md

grep -nE "src/app/map/page.tsx|src/app/map/read-only-map-data.ts|src/app/map/human-approved-operator-data.ts|src/app/v1|source_proxy|src/app/proxy-backend/page.tsx|package.json|tests|dashboard|/coding" \
  docs/cartographer-full-auto-plan-2-human-approved-operator-v0-2-implementation-decision.md

git status --short -- \
  docs/cartographer-full-auto-plan-2-human-approved-operator-v0-2-decision-packet.md \
  docs/cartographer-full-auto-plan-2-operator-review-human-approved-operator-v0-2-no-go-acceptance-and-implementation-decision-gate.md \
  docs/cartographer-full-auto-plan-2-human-approved-operator-v0-2-implementation-decision.md \
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

The first grep shows Plan 2, GO later only, implementation remains NO-GO now, not-approved and not-granted authority, exact allowed files, exact forbidden files, approval-token runtime denial, durable queue denial, command/queue execution denial, full-auto denial, limited-unattended denial, and the next recommended increment title.

The second grep shows exact candidate implementation files and forbidden file families, including src/app/v1, source_proxy, src/app/proxy-backend/page.tsx, package.json, tests, dashboard, and /coding.

Focused status shows the three Plan 2 docs as untracked, plus the pre-existing tracked dirty files.

Repo status still shows the broader pre-existing dirty/untracked worktree.

git diff --stat still shows tracked dirty files only unless docs are later staged or tracked by an explicit human git operation.
```

## Rollback Notes

Rollback for this docs-only packet is limited to removing:

- `docs/cartographer-full-auto-plan-2-human-approved-operator-v0-2-implementation-decision.md`

Rollback must not touch unrelated dirty files. Rollback must not use checkout, clean, stash, reset, branch, worktree, commit, push, or merge unless a separate human operator explicitly authorizes that exact operation.

## Stop Conditions

Stop immediately if:

- Plan 2 implementation approval is absent.
- Any implementation begins before explicit operator approval.
- Any required implementation file is outside the exact allowed file list.
- Any forbidden file must be edited.
- Any backend endpoint must be added.
- Any backend mutation endpoint must be called.
- Any endpoint outside the GET-only display allowlist is required.
- Any write authority outside exact approved files is requested.
- Any command execution authority is requested.
- Any queue execution authority is requested.
- Any approval generation or self-approval is requested.
- Any approval-token runtime is requested.
- Any durable queue or event storage is requested.
- Any runtime, test, dashboard, `/coding`, API, Source Proxy, package, config, env, generated, or Scout mutation is required.
- Any limited unattended operation is implied.
- Any full auto authority is implied.
- Any git staging, commit, push, merge, stash, checkout, clean, branch, or worktree operation is required.
- Verification fails before implementation.
- Verification fails after implementation.

## Permission Required For Next Phase

Do not implement Plan 2 unless the operator explicitly approves the next implementation increment in chat.

Acceptable next responses:

- `APPROVE PLAN 2 DISPLAY-ONLY IMPLEMENTATION`
- `APPROVE NEXT DOCS-ONLY GATE`
- `STOP`

Approval for the next docs-only gate is not approval to implement runtime behavior.

## Next Recommended Increment Title

Plan 2 Implementation Step 1: Display-Only Human Approval Requirements And Blocked-State Map UI
