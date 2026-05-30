# Cartographer Full Auto Plan 2 Decision Packet: Human-Approved Operator v0.2 Scope Or No-Go

status: decision-packet

Status date: 2026-05-22

Current HEAD: `40141f34d27d915503f265efba119673a412354a`

## Decision Result

Plan 2 Human-Approved Operator v0.2 implementation is NO-GO.

This packet is docs-only. It does not implement Plan 2, add runtime behavior, add backend endpoints, call backend mutation endpoints, create approval-token runtime, create durable queue/event storage, enable command execution, enable queue execution, enable unattended writes, grant limited unattended operation, or grant full auto.

Full auto is not granted. Limited unattended operation is not granted. Command execution is not granted. Queue execution is not granted.

## Current Repo State

Initial takeover commands were run from `/home/source/SpiritOS`.

- Branch state: `main...origin/main [ahead 34]`.
- Current HEAD: `40141f34d27d915503f265efba119673a412354a`.
- Tracked dirty files already present before this packet:
  - `docs/plan-index.md`
  - `package.json`
  - `src/app/coding/page.tsx`
  - `src/app/v1/decisions/prompt-packet/route.ts`
  - `src/components/dashboard/demo-v4/DashboardDemoV4FloatingNav.tsx`
- Initial tracked diff stat:
  - 5 files changed.
  - 191 insertions.
  - 34 deletions.
- Initial tracked dirty file list:
  - `docs/plan-index.md`
  - `package.json`
  - `src/app/coding/page.tsx`
  - `src/app/v1/decisions/prompt-packet/route.ts`
  - `src/components/dashboard/demo-v4/DashboardDemoV4FloatingNav.tsx`
- Many untracked Cartographer docs, `source_proxy` files, tests, `/coding` files, and `/map` files already exist in the working tree.

Those pre-existing changes are not Plan 2 authority. They must not be cleaned, stashed, checked out, staged, committed, overwritten, deleted, or absorbed into Plan 2 scope.

## Accepted Plan 1 State

Plan 1 read-only `/map` wiring is accepted and closed only for the display-only GET allowlist scope described by `docs/cartographer-full-auto-plan-1-step-4-read-only-map-phase-closeout-decision-and-next-plan-gate.md`.

Accepted Plan 1 state:

- `/map` renders display-only GET allowlist state or static fallback state.
- Allowlisted reads remain GET-only and display-only.
- Fallback proof remains visible.
- Recommendation packets remain inert.
- Blocked endpoint/action findings remain display-only.
- Authority denials remain visible.
- Shared SpiritOS theme-picker buttons may render from the imported floating nav.
- No Cartographer approval, apply, execute, commit, push, branch, queue, command, self-approval, or write controls are accepted.
- Plan 2 was explicitly not approved by Plan 1 closeout.

Accepted Plan 1 files:

- `src/app/map/page.tsx`
- `src/app/map/read-only-map-data.ts`
- `docs/cartographer-full-auto-plan-1-implementation-decision-read-only-map-wiring.md`
- `docs/cartographer-full-auto-plan-1-read-only-map-wiring-implementation-closeout.md`
- `docs/cartographer-full-auto-plan-1-operator-review-read-only-map-wiring-acceptance-and-step-2-permission-gate.md`
- `docs/cartographer-full-auto-plan-1-step-2-read-only-map-packet-shape-hardening-and-fallback-proof.md`
- `docs/cartographer-full-auto-plan-1-step-3-read-only-map-manual-browser-acceptance-and-phase-closeout-gate.md`
- `docs/cartographer-full-auto-plan-1-step-3-1-restart-dev-server-and-rerun-read-only-map-browser-acceptance.md`
- `docs/cartographer-full-auto-plan-1-step-4-read-only-map-phase-closeout-decision-and-next-plan-gate.md`

## Exact Allowed Files If GO

Because this packet decides Plan 2 implementation is NO-GO, there are no files allowed for implementation now.

If a later chat explicitly approves a new Plan 2 implementation packet after review, the candidate allowed files should be exact and limited to:

- `src/app/map/page.tsx`
- `src/app/map/read-only-map-data.ts`
- `src/app/map/human-approved-operator-data.ts`
- `docs/cartographer-full-auto-plan-2-human-approved-operator-v0-2-implementation-decision.md`
- `docs/cartographer-full-auto-plan-2-human-approved-operator-v0-2-implementation-closeout.md`

No file is approved by this packet. The candidate list is not implementation permission.

## Exact Forbidden Files

The following remain forbidden for Plan 2 unless a later implementation packet explicitly changes the decision and names exact files:

- `/coding` files.
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
- durable queue files.
- event-storage files.
- approval-token runtime files.
- approval, evidence, receipt, queue, or event mutation files.
- any pre-existing dirty file not explicitly listed in a later allowed implementation file list.

If Plan 2 requires any forbidden file, Plan 2 remains NO-GO.

## Exact Authority Still Denied

The following authority is still denied:

- Write authority.
- Evidence write authority.
- Receipt write authority.
- Approval-token runtime authority.
- Approval generation authority.
- Self-approval authority.
- Backend mutation endpoint authority.
- Durable queue storage authority.
- Durable event storage authority.
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

## Candidate Human-Approved Operator Scope

The candidate Plan 2 scope is human-approved operator display and validation planning only.

A later Plan 2 implementation packet may propose:

- Displaying human approval requirements.
- Displaying approval queue preview state only if it already exists from an approved read-only source.
- Displaying token field requirements.
- Displaying fail-closed validation results.
- Displaying stale HEAD, dirty-tree mismatch, expired approval, self-approval, missing approver, missing rollback, missing verification, and kill-switch blocked states.
- Displaying operator next steps.

The candidate scope must not:

- Create approval tokens.
- Store approval tokens.
- Validate tokens in runtime code unless separately approved.
- Add approval queue storage.
- Execute approved actions.
- Call mutation endpoints.
- Write evidence or receipts.
- Grant write authority.
- Grant command execution.
- Grant queue execution.
- Grant limited unattended operation.
- Grant full auto.

## Candidate Endpoint And Action Allowlist

Because Plan 2 is NO-GO, no endpoint or action is allowed now.

If a later implementation packet is approved, the candidate endpoint allowlist must remain GET-only and display-only:

| Candidate | Purpose | Required handling |
| --- | --- | --- |
| `/v1/cartographer/status` | Status and authority-denial summary | display-only |
| `/v1/cartographer/repo-map` | Repo and dirty-tree summary | display-only |
| `/v1/cartographer/proposals` | Existing proposal summary | display-only; no review or apply action |
| `/v1/cartographer/audit-trail` | Existing audit hints | display-only; no ledger write |
| `/v1/cartographer/v1-readiness` | Readiness signal | display-only; cannot promote authority |
| `/v1/cartographer/trust-score` | Trust score signal | display-only; cannot promote authority |

Candidate display-only actions:

- Show approval requirements.
- Show approval blocked state.
- Show missing token fields.
- Show manual operator next step.
- Show stop conditions.

No candidate action may mutate state.

## Explicitly Blocked Endpoint And Action Classes

Explicitly blocked endpoint classes:

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

Explicitly blocked action classes:

- File writes.
- Evidence writes.
- Receipt writes.
- Approval-token creation.
- Approval-token storage.
- Approval-token runtime validation.
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

Blocked findings may be displayed as inert labels only. They must not become controls.

## Approval Requirements

Any later Plan 2 implementation packet must require a human approval model before runtime token behavior can be considered.

Candidate approval-token fields:

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

Fail-closed requirements:

- Missing operator id fails closed.
- Missing approver id fails closed.
- Self-approval fails closed.
- Missing token id fails closed.
- Missing run id fails closed.
- Missing or ambiguous action type fails closed.
- Missing exact allowed files fails closed.
- Missing exact forbidden files fails closed.
- Expired approval fails closed.
- Missing rollback instructions fails closed.
- Missing verification instructions fails closed.
- Stale HEAD fails closed.
- Dirty-tree mismatch fails closed.
- Kill switch blocked state fails closed.
- Trust tier above approved scope fails closed.
- Any authority broader than the exact token scope fails closed.

These requirements are planning requirements only. They do not create approval-token runtime.

## Timeout And Fallback Requirements

Any later display-only Plan 2 read must use bounded timeout behavior:

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

A Plan 2 recommendation packet may be displayed only as inert UI data.

Required packet fields:

- `packet_id`
- `status_date`
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
- Self-approval fields.
- Autonomous task selection.

Recommendation wording must remain human-facing and inert. It may recommend manual operator review, narrower observation, later explicit implementation planning, or stopping. It must not approve or execute anything.

## Blocked Action Classifier Requirements

The Plan 2 blocked action classifier must remain display-only unless a later packet explicitly approves runtime validation code.

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
- Fail closed for any write, command execution, queue execution, approval generation, token creation, self-approval, branch/worktree, git mutation, runtime mutation, test mutation, dashboard mutation, `/coding` mutation, package/config/env/generated/Scout mutation, API mutation, or Source Proxy mutation.
- Produce display-only findings with `blocked: true`, blocked class, reason, protected path match if present, missing approval fields if present, and manual next step.

The classifier must not become an action runner, command runner, queue runner, approval generator, token creator, or self-approval path.

## UI Display Requirements

Any later `/map` Plan 2 UI must remain display-only:

- It may render Plan 2 NO-GO state.
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
- It must not hide that Plan 2 implementation is not approved.
- It must not hide that full auto is not granted.
- It must not hide that limited unattended operation is not granted.
- It must not hide that command execution is not granted.
- It must not hide that queue execution is not granted.

## Verification Commands Required Before Any Later Implementation

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

## Verification Commands Required After Any Later Implementation

Run these commands after any later explicitly approved Plan 2 implementation:

```bash
cd /home/source/SpiritOS
git diff --check
grep -nE "POST|PUT|PATCH|DELETE|approve|apply|execute|commit|push|branch|queue|event|token|autonomy-promotion" src/app/map/page.tsx src/app/map/read-only-map-data.ts src/app/map/human-approved-operator-data.ts || true
grep -nE "onClick|<button|command|execute|approval token|self-approval|queue execution|write control" src/app/map/page.tsx src/app/map/read-only-map-data.ts src/app/map/human-approved-operator-data.ts || true
grep -nE "Plan 2|NO-GO|not approved|full auto is not granted|limited unattended operation is not granted|command execution is not granted|queue execution is not granted|display-only|blocked" src/app/map/page.tsx src/app/map/read-only-map-data.ts src/app/map/human-approved-operator-data.ts
npx eslint src/app/map/page.tsx src/app/map/read-only-map-data.ts src/app/map/human-approved-operator-data.ts
git status --branch --short
git diff --stat
git diff --name-only
```

Required after-implementation result:

- `git diff --check` passes.
- Focused ESLint passes.
- Diffs are limited to the exact allowed files from the later implementation packet.
- `/map` remains display-only.
- Approval/token/queue/action strings appear only in blocked display text, not executable paths.
- Plan 2 implementation approval remains exact and scoped.
- Full auto denial remains visible.
- Limited unattended operation denial remains visible.
- Command execution denial remains visible.
- Queue execution denial remains visible.

## Manual Checks

```bash
cd /home/source/SpiritOS

git diff --check

grep -nE "Plan 2|GO|NO-GO|Human-Approved Operator|not approved|full auto.*not granted|limited unattended operation.*not granted|command execution.*not granted|queue execution.*not granted|Forbidden|Next Recommended Increment Title" \
  docs/cartographer-full-auto-plan-2-human-approved-operator-v0-2-decision-packet.md

git status --branch --short

git diff --stat
```

## Expected Output

```text
git diff --check prints nothing.

The grep shows the Plan 2 decision packet title, Human-Approved Operator language, the NO-GO decision, not-approved implementation language, full-auto denial, limited-unattended denial, command-execution denial, queue-execution denial, forbidden scope, and the next recommended increment title.

git status still shows the broader pre-existing dirty/untracked worktree plus this new docs-only Plan 2 decision packet.

git diff --stat still shows the pre-existing tracked dirty files. This new untracked docs-only packet may not appear in git diff --stat until tracked by git.
```

## Rollback Notes

Rollback for this docs-only packet is limited to removing:

- `docs/cartographer-full-auto-plan-2-human-approved-operator-v0-2-decision-packet.md`

Rollback must not touch unrelated dirty files. Rollback must not use checkout, clean, stash, reset, branch, worktree, commit, push, or merge unless a separate human operator explicitly authorizes that exact operation.

## Stop Conditions

Stop immediately if:

- Plan 2 implementation approval is absent.
- Any implementation file must be edited in this docs-only packet.
- Any required implementation file is outside a later exact allowed file list.
- Any forbidden file must be edited.
- Any backend endpoint must be added.
- Any backend mutation endpoint must be called.
- Any endpoint outside the GET-only display allowlist is required.
- Any write authority is requested.
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

## Next Recommended Increment Title

Plan 2 Operator Review: Human-Approved Operator v0.2 NO-GO Acceptance And Implementation Decision Gate
