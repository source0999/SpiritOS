# Controlled Multi-Agent And Subagent Orchestration Boundary Plan 18/24

Status: closed preview-only coordination contract
Plan: Plan 18/24, Controlled Multi-Agent And Subagent Orchestration Boundary
Mode: PREVIEW ONLY

## Scope

Plan 17/24 closed with GO for map/Cartographer integration gate classification, while keeping live map work, map inclusion in non-Cart visual/CSS work, runtime mutation, evidence writes, Cart activation, and Plan 18 start as NO-GO without explicit operator approval.

The operator then requested the next plan if all good. Plan 17 manual verification passed before this packet started.

This packet records Plan 18 only. It does not start Plan 19/24.

Allowed:
- Worker identity preview.
- Lane ownership preview.
- Allowed/forbidden file preview.
- Handoff packet preview.
- Conflict-report preview.
- Lease/lock awareness preview.
- Block rules.

Forbidden:
- Hidden worker start.
- Worker dispatch.
- Worker registry runtime.
- Lease or lock creation.
- Branch or worktree creation.
- Branch/worktree implication.
- Protected path mutation.
- Source, runtime, test, UI, CSS, package, config, env, generated, cache, approval-token, queue, worker, Cartographer, Scout, or Source Proxy mutation.
- Commit, push, branch, worktree, stash, reset, clean, checkout, stage, or apply.

## Phase 18.1 Worker Identity

### 18.1.1 Define Worker Identity

Allowed work:
- Define preview-only worker identity fields.
- Record evidence from existing worker identity and registry preview docs.

Evidence:
- `docs/cartographer-level-13-worker-identity-registry-schema-preview.md` records a worker identity and registry schema preview only.
- It states no worker registry runtime, worker lease runtime, branch/worktree creation, write authority, local execution, commit/push/merge authority, automatic execution, automatic promotion, or self-approval is enabled.
- It states a worker identity or registry entry must not be treated as permission to dispatch tasks, claim files, create branches, create worktrees, execute commands, write files, reassign work, close out work, or mutate anything.

Required worker identity preview fields:

| Field | Required | Meaning |
| --- | --- | --- |
| `worker_id` | yes | Stable human-readable worker identifier. |
| `worker_type` | yes | `human_codex`, `advisory_subagent`, `mac_advisory_helper`, or `blocked_unknown`. |
| `owner_lane` | yes | The single lane that owns the worker's proposed scope. |
| `task_id` | yes | Stable task or increment identifier. |
| `human_operator` | yes | Human who authorized the preview packet. |
| `declared_scope` | yes | Plain-language scope statement. |
| `allowed_files` | yes | Exact file list or explicit empty list. |
| `forbidden_files` | yes | Exact protected or excluded file list. |
| `authority_level` | yes | `preview_only`, `advisory_only`, or `blocked`. |
| `runtime_status` | yes | Always `not_started` in Plan 18. |
| `write_authority` | yes | Always `false` in Plan 18. |
| `branch_worktree_authority` | yes | Always `false` in Plan 18. |
| `handoff_required` | yes | Whether a later human-reviewed handoff packet is required. |
| `created_from_plan` | yes | `Plan 18/24`. |
| `expires_at` | yes | Human-readable expiry or `end_of_plan`. |

GO / NO-GO:
- GO for worker identity preview fields.
- NO-GO for worker registry runtime, worker dispatch, file claim authority, or write authority.

Next authorized increment: 18.1.2 Define lane ownership.

### 18.1.2 Define Lane Ownership

Allowed work:
- Define lane ownership preview.
- Keep each lane single-owner and fail-closed on ambiguity.

Evidence:
- `docs/cartographer-level-13-ownership-zone-file-lock-preview.md` records ownership zones and file locks as preview only.
- It states ownership zones must be explicit before dispatch and ambiguous ownership must block orchestration.
- Plan 14/24 records advisory subagent packets as inert display-eligible only.
- Plan 15/24 records Scout as parked/manual-controlled with writes disabled.
- Plan 17/24 records map/Cartographer as Cart-only and excluded from non-Cart work.

Lane ownership preview:

| Lane | Owner | Eligible in Plan 18 | Blocked scope |
| --- | --- | --- | --- |
| Source Proxy `/coding` | Source Proxy lane | Preview ownership labels only | Apply, execute-approved, approval token, provider call, queue/worker, Source Proxy writes. |
| Design advisory | Design Agent lane | Advisory helper packet preview only | CSS edits, app UI edits, route/component/token writes, A-grade claim. |
| Scout advisory | Scout lane | Manual-controlled advisory preview only | Discovery execution, proxy intake, promotion finalization, proxy/coding context writes. |
| Mac telemetry/search advisory | Mac support lane | Manual advisory packet preview only | Hidden workers, service control, Docker/Homebrew provider path, autonomous search. |
| Dashboard non-Cart display | Supporting surface lane | Ownership label only | Runtime/provider/storage mutation, action wiring, Cart widgets. |
| Map/Cartographer | Cart-only lane | Excluded except status reference | Live map work, Cart API/runtime/evidence writes, approval-token action, queue/workflow action. |

GO / NO-GO:
- GO for lane ownership preview.
- NO-GO for ambiguous lane ownership, ownership reassignment, runtime dispatch, or hidden worker work.

Next authorized increment: 18.1.3 Define allowed/forbidden files.

### 18.1.3 Define Allowed/Forbidden Files

Allowed work:
- Define allowed and forbidden file handling for future worker packets.
- Record protected-path blocks.

Evidence:
- `docs/cartographer-level-13-worker-identity-registry-schema-preview.md` records that forbidden files cannot be overridden by worker identity and protected paths remain blocked.
- `docs/cartographer-level-13-ownership-zone-file-lock-preview.md` records protected paths as blocking for ownership/lock scope.
- Plan 17/24 records `src/app/map/`, `src/app/v1/cartographer/`, `source_proxy/cartographer/`, and `source_proxy/api/cartographer.py` as protected Cart paths.

Allowed files in Plan 18:
- `docs/controlled-multi-agent-subagent-orchestration-boundary-plan-18-24-v0.1.md`

Future packet file rules:
- `allowed_files` must be exact, not glob-expanded by the worker.
- `forbidden_files` must include protected paths and lane-excluded paths.
- Empty `allowed_files` means advisory-only and no repo mutation.
- Unknown files default to blocked until a human adds them to an exact allowed list.

Forbidden in Plan 18:
- `src/**`
- `source_proxy/**`
- `tests/**`
- `package.json`, lockfiles, configs, env files, generated files, cache files.
- `src/app/map/**`
- `src/app/v1/cartographer/**`
- `source_proxy/cartographer/**`
- `source_proxy/api/cartographer.py`
- Any approval-token, queue, worker, apply, execute-approved, Cartographer, Scout runtime, Source Proxy runtime, or provider/model file.

GO / NO-GO:
- GO for allowed/forbidden file preview.
- NO-GO for protected path mutation, broad glob authority, or treating missing file ownership as safe.

## Phase 18.1 Review

Completed increments:
- 18.1.1 GO for worker identity preview; NO-GO for registry runtime or dispatch.
- 18.1.2 GO for lane ownership preview; NO-GO for ambiguous ownership or hidden worker work.
- 18.1.3 GO for allowed/forbidden file preview; NO-GO for protected path mutation.

Evidence exists:
- Worker identity and registry preview evidence is recorded.
- Ownership zone and file lock preview evidence is recorded.
- Plan 14, Plan 15, and Plan 17 lane constraints are recorded.

Forbidden scope avoided:
- No worker runtime, dispatch, lease, lock, branch, worktree, source, runtime, UI, CSS, queue, worker, provider, approval-token, Cartographer, Scout, Source Proxy, git mutation, or protected path mutation occurred.

Checks:
- Read-only grep checks returned expected worker identity, registry, ownership, protected path, branch/worktree, preview, and NO-GO evidence.

Phase result: GO to Phase 18.2; NO-GO for worker execution.

Next authorized increment: 18.2.1 Define handoff packet fields.

## Phase 18.2 Handoff Packets

### 18.2.1 Define Handoff Packet Fields

Allowed work:
- Define preview-only handoff packet fields.

Evidence:
- `docs/cartographer-level-13-handoff-packet-boundary.md` records handoff packets as structured, non-mutating previews.
- It states handoff packets must not transfer authority, mutate registry state, clear locks, reassign tasks, overwrite files, execute commands, create branches, create worktrees, or close work by themselves.

Required handoff packet fields:

| Field | Required | Meaning |
| --- | --- | --- |
| `packet_id` | yes | Stable handoff packet id. |
| `packet_version` | yes | Schema version. |
| `source_worker_id` | yes | Known source worker id or `blocked_unknown`. |
| `target_worker_id` | yes | Known target worker id or `blocked_unknown`. |
| `owner_lane` | yes | Single owning lane. |
| `source_plan` | yes | Plan or increment that created the handoff. |
| `task_id` | yes | Task being handed off. |
| `summary` | yes | Human-readable context summary. |
| `input_refs` | yes | Docs or evidence references. |
| `proposed_output` | yes | Advisory output only. |
| `allowed_files` | yes | Exact list or empty list. |
| `forbidden_files` | yes | Exact list of excluded/protected files. |
| `blocked_reasons` | yes | Fail-closed blockers. |
| `checks_suggested` | yes | Suggested checks; not executed by packet. |
| `checks_not_run` | yes | Required when checks are not run. |
| `authority_statement` | yes | Must say no apply, no write, no dispatch, no branch/worktree. |
| `next_human_decision` | yes | Exact decision needed from the operator. |

GO / NO-GO:
- GO for handoff packet field preview.
- NO-GO for handoff runtime, task reassignment, authority transfer, or hidden dispatch.

Next authorized increment: 18.2.2 Define conflict-report fields.

### 18.2.2 Define Conflict-Report Fields

Allowed work:
- Define conflict-report preview fields.

Evidence:
- `docs/cartographer-level-13-conflict-detection-dry-run-boundary.md` exists as a Level 13 conflict detection dry-run boundary.
- `docs/cartographer-level-13-ownership-zone-file-lock-preview.md` records lock conflict rules and protected path blocks.
- Existing Level 13 closeout keeps conflict detection runtime locked.

Required conflict-report fields:

| Field | Required | Meaning |
| --- | --- | --- |
| `conflict_id` | yes | Stable conflict id. |
| `worker_id` | yes | Worker associated with the conflict. |
| `task_id` | yes | Task associated with the conflict. |
| `owner_lane` | yes | Owning lane. |
| `path` | yes | Exact path or `not_applicable`. |
| `protected_path_match` | yes | `true` or `false`. |
| `overlap_lane` | yes | Conflicting lane or `none`. |
| `conflict_type` | yes | `unknown_worker`, `missing_task`, `missing_lane`, `protected_path`, `hidden_mutation`, `branch_worktree_implication`, or `scope_overlap`. |
| `severity` | yes | `blocker`, `high`, `medium`, or `low`; protected path and hidden mutation are always `blocker`. |
| `required_decision` | yes | Human decision needed. |
| `status` | yes | `blocked`, `advisory_only`, or `resolved_by_human_review`. |

GO / NO-GO:
- GO for conflict-report field preview.
- NO-GO for conflict detection runtime, automatic resolution, or hidden scope widening.

Next authorized increment: 18.2.3 Define lease/lock awareness.

### 18.2.3 Define Lease/Lock Awareness

Allowed work:
- Define lease/lock awareness fields without creating leases or locks.

Evidence:
- `docs/cartographer-level-13-worker-lease-boundary.md` records worker lease boundaries only and states the boundary is not worker lease authority.
- `docs/cartographer-level-13-ownership-zone-file-lock-preview.md` records ownership and file lock preview only and states no ownership/file lock runtime is enabled.
- `docs/cartographer-level-13-closeout-and-level-14-gate.md` records worker registry mutation, lease creation/release, ownership lock creation/release, and protected path writes as locked.

Required lease/lock awareness fields:

| Field | Required | Plan 18 value |
| --- | --- | --- |
| `lease_requested` | yes | `false` |
| `lease_created` | yes | `false` |
| `lock_requested` | yes | `false` |
| `lock_created` | yes | `false` |
| `lock_release_required` | yes | `false` |
| `branch_worktree_required` | yes | `false` |
| `protected_path_in_scope` | yes | `false` or `blocked` |
| `dispatch_allowed` | yes | `false` |
| `write_allowed` | yes | `false` |

GO / NO-GO:
- GO for lease/lock awareness preview.
- NO-GO for lease creation, lock creation, dispatch, file claiming, or worker execution.

## Phase 18.2 Review

Completed increments:
- 18.2.1 GO for handoff packet fields; NO-GO for handoff runtime or authority transfer.
- 18.2.2 GO for conflict-report fields; NO-GO for conflict runtime or automatic resolution.
- 18.2.3 GO for lease/lock awareness; NO-GO for lease/lock creation or dispatch.

Evidence exists:
- Handoff packet boundary evidence is recorded.
- Conflict detection dry-run and ownership/file lock evidence are recorded.
- Worker lease boundary and Level 13 closeout lock evidence are recorded.

Forbidden scope avoided:
- No handoff runtime, worker reassignment, conflict runtime, lease, lock, dispatch, branch, worktree, source edit, runtime edit, or git mutation occurred.

Checks:
- Read-only grep checks returned expected handoff, conflict, lease, lock, branch/worktree, preview, and NO-GO evidence.

Phase result: GO to Phase 18.3; NO-GO for packet execution.

Next authorized increment: 18.3.1 Block unknown worker, task, or lane.

## Phase 18.3 Block Rules

### 18.3.1 Block Unknown Worker, Task, Or Lane

Allowed work:
- Define fail-closed block rules for unknown identity, task, or lane.

Evidence:
- `docs/cartographer-level-13-handoff-packet-boundary.md` records handoff is blocked without source or target worker identity.
- `docs/cartographer-level-13-branch-worktree-proposal-boundary.md` records branch/worktree proposals are blocked without worker identity.
- `docs/cartographer-level-13-ownership-zone-file-lock-preview.md` records ambiguous ownership must block orchestration.

Block rules:
- Unknown `worker_id`: block.
- Unknown `task_id`: block.
- Missing `owner_lane`: block.
- Multiple owner lanes: block.
- Worker-lane mismatch: block.
- Missing human operator: block.
- Missing allowed/forbidden files: block.

GO / NO-GO:
- GO for unknown identity/task/lane block rules.
- NO-GO for default-allow orchestration.

Next authorized increment: 18.3.2 Block protected path scope.

### 18.3.2 Block Protected Path Scope

Allowed work:
- Define protected path block rules.

Evidence:
- Plan 17/24 records Cart map/runtime/API paths as protected and Cart-only excluded from non-Cart work.
- Level 13 worker identity, lease, ownership, handoff, and branch/worktree docs all keep protected paths blocked.

Protected path block table:

| Path or scope | Status | Rule |
| --- | --- | --- |
| `src/app/map/**` | `protected_cart_path` | Block. |
| `src/app/v1/cartographer/**` | `protected_cart_api_path` | Block. |
| `source_proxy/cartographer/**` | `protected_cart_runtime_path` | Block. |
| `source_proxy/api/cartographer.py` | `protected_cart_api_path` | Block. |
| Approval-token paths | `protected_authority_path` | Block. |
| Queue/worker paths | `protected_execution_path` | Block. |
| Source Proxy apply/execute-approved paths | `protected_apply_path` | Block. |
| Scout runtime/proxy memory/coding context writes | `protected_scout_path` | Block. |
| Package/config/env/generated/cache paths | `protected_repo_infra_path` | Block. |

GO / NO-GO:
- GO for protected path block rules.
- NO-GO for protected path scope, protected path mutation, or future worker packet overlap.

Next authorized increment: 18.3.3 Block hidden mutation or branch/worktree implication.

### 18.3.3 Block Hidden Mutation Or Branch/Worktree Implication

Allowed work:
- Define hidden mutation and branch/worktree implication blocks.

Evidence:
- `docs/cartographer-level-13-branch-worktree-proposal-boundary.md` states branch/worktree proposal packets must not create branches, create worktrees, checkout, stash, clean files, stage files, commit, push, merge, delete branches, delete worktrees, or mutate anything by themselves.
- `docs/cartographer-level-13-closeout-and-level-14-gate.md` records Level 14 remains locked and blocked if branch/worktree authority is implied.
- Plan 18 mode is preview only.

Block rules:
- Hidden worker start: block.
- Background mutation: block.
- Queue/worker execution: block.
- Apply or execute-approved: block.
- Approval-token action: block.
- Branch/worktree implication: block.
- Branch/worktree creation: block.
- Checkout, stash, clean, reset, stage, commit, push, merge: block.
- "This packet authorizes coding" language: block.
- Missing no-authority statement: block.

GO / NO-GO:
- GO for hidden mutation and branch/worktree implication block rules.
- NO-GO for branch/worktree authority, hidden mutation, git mutation, or worker execution.

Next authorized increment: Plan 18/24 closeout.

## Phase 18.3 Review

Completed increments:
- 18.3.1 GO for unknown worker/task/lane block rules; NO-GO for default-allow orchestration.
- 18.3.2 GO for protected path block rules; NO-GO for protected path scope.
- 18.3.3 GO for hidden mutation and branch/worktree implication blocks; NO-GO for worker/git mutation.

Evidence exists:
- Handoff and branch/worktree identity block evidence is recorded.
- Plan 17 protected Cart path evidence is recorded.
- Level 13 branch/worktree and closeout lock evidence is recorded.

Forbidden scope avoided:
- No worker start, queue/worker execution, apply, execute-approved, approval-token action, branch, worktree, checkout, stash, clean, reset, stage, commit, push, merge, source edit, runtime edit, protected path mutation, or hidden mutation occurred.

Checks:
- Read-only grep checks returned expected unknown identity, protected path, hidden mutation, branch/worktree, preview-only, and NO-GO evidence.

Phase result: GO to Plan 18 closeout; NO-GO for Plan 19 start.

Next authorized increment: Plan 18/24 closeout.

## Plan 18/24 Closeout

Phase review:
- Phase 18.1 Worker Identity: GO for worker identity, lane ownership, and allowed/forbidden file previews; NO-GO for worker execution.
- Phase 18.2 Handoff Packets: GO for handoff packet, conflict-report, and lease/lock awareness previews; NO-GO for packet execution.
- Phase 18.3 Block Rules: GO for fail-closed block rules; NO-GO for hidden mutation, protected path scope, or branch/worktree implication.

Increment evidence:
- 18.1.1 Worker identity fields: recorded.
- 18.1.2 Lane ownership: recorded.
- 18.1.3 Allowed/forbidden file rules: recorded.
- 18.2.1 Handoff packet fields: recorded.
- 18.2.2 Conflict-report fields: recorded.
- 18.2.3 Lease/lock awareness: recorded.
- 18.3.1 Unknown worker/task/lane block: recorded.
- 18.3.2 Protected path block: recorded.
- 18.3.3 Hidden mutation and branch/worktree implication block: recorded.

Evidence exists:
- Level 13 worker identity/registry preview.
- Level 13 worker lease boundary.
- Level 13 ownership zone/file lock preview.
- Level 13 conflict detection dry-run boundary.
- Level 13 handoff packet boundary.
- Level 13 branch/worktree proposal boundary.
- Level 13 closeout and Level 14 gate.
- Plan 14 advisory subagent boundary.
- Plan 15 Scout manual-controlled no-write boundary.
- Plan 17 Cart/map protected path boundary.

Forbidden actions review:
- No hidden worker was started.
- No worker registry runtime was created.
- No worker was dispatched.
- No lease or lock was created.
- No branch or worktree was created.
- No branch/worktree authority was implied.
- No protected path was mutated.
- No source/runtime/test/UI/CSS/package/config/env/generated/cache file was changed.
- No provider/model call, queue/worker execution, approval-token action, apply, execute-approved, Cart activation, Scout activation, Source Proxy mutation, or git mutation occurred.

Orchestration preview contract:
- Worker identity is required and preview-only.
- Exactly one owner lane is required.
- Allowed and forbidden files must be exact.
- Unknown worker, task, lane, or file scope blocks.
- Protected paths block.
- Handoff packets are advisory and non-mutating.
- Conflict reports block by default.
- Lease/lock fields are awareness-only; Plan 18 creates no lease or lock.
- Hidden mutation and branch/worktree implication block.

Final Plan 18/24 result: GO for preview-only orchestration coordination contract; NO-GO for worker execution, hidden workers, registry runtime, dispatch, lease/lock creation, branch/worktree authority, protected path mutation, implementation, or Plan 19 start without explicit operator approval.

Next roadmap plan only: `Plan 19/24: Controlled Action Authority And Approval Token Ladder`.

## Manual Verification

Copy-paste verification:

```bash
cd /home/source/SpiritOS && git status --branch --short --untracked-files=normal && grep -nE "Plan 18/24|worker_id|owner_lane|allowed_files|forbidden_files|preview_only|lane ownership|handoff packet|conflict-report|lease/lock|unknown worker|protected path|hidden mutation|branch/worktree|NO-GO|Plan 19/24" docs/controlled-multi-agent-subagent-orchestration-boundary-plan-18-24-v0.1.md && grep -nE "Worker Identity|worker identity|worker registry|Worker Lease|worker lease|Ownership Zone|ownership lock|handoff packet|Handoff|branch/worktree|protected path|preview|No multi-agent worker authority|Level 14 remains locked|NO-GO" docs/cartographer-level-13-worker-identity-registry-schema-preview.md docs/cartographer-level-13-worker-lease-boundary.md docs/cartographer-level-13-ownership-zone-file-lock-preview.md docs/cartographer-level-13-conflict-detection-dry-run-boundary.md docs/cartographer-level-13-handoff-packet-boundary.md docs/cartographer-level-13-branch-worktree-proposal-boundary.md docs/cartographer-level-13-closeout-and-level-14-gate.md && git diff --check -- docs/controlled-multi-agent-subagent-orchestration-boundary-plan-18-24-v0.1.md
```

Expected output:
- Git status shows the existing untracked plan docs, including this Plan 18 packet.
- Plan 18 grep prints worker identity, lane ownership, allowed/forbidden files, handoff packet, conflict-report, lease/lock awareness, block rules, NO-GO boundaries, and Plan 19 title.
- Level 13 grep prints worker identity, worker lease, ownership/file lock, conflict, handoff, branch/worktree, protected path, preview-only, Level 14 lock, and no-authority evidence.
- `git diff --check` prints no output.
