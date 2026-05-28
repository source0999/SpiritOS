# Controlled Action Authority And Approval Token Ladder Plan 19/24

Status: closed authority-design-only packet
Plan: Plan 19/24, Controlled Action Authority And Approval Token Ladder
Mode: AUTHORITY DESIGN ONLY unless explicitly approved

## Scope

Plan 18/24 closed with GO for preview-only orchestration coordination contract, while keeping worker execution, hidden workers, registry runtime, dispatch, lease/lock creation, branch/worktree authority, protected path mutation, implementation, and Plan 19 start as NO-GO without explicit operator approval.

The operator then requested the next plan if all good. Plan 18 manual verification passed before this packet started.

This packet records Plan 19 only. It does not start Plan 20/24.

Allowed:
- Authority ladder design.
- Token requirements design.
- Event ledger design.
- Read-only evidence inspection.

Forbidden:
- Token creation.
- Token validation for live authority.
- Token consumption.
- Approved writes.
- Execution.
- Apply.
- Execute-approved.
- Commit.
- Push.
- Branch.
- Worktree.
- Queue/worker execution.
- Provider/model calls.
- Runtime mutation.
- Protected path mutation.
- Plan 20 start.

## Phase 19.1 Authority Ladder

### 19.1.1 Observe

Allowed work:
- Define the observe authority level.
- Record evidence that observe grants no mutation.

Evidence:
- Plan 18 records preview-only coordination and no worker, source, runtime, queue, approval-token, apply, or git mutation.
- `source_proxy/cartographer/approval_token_runtime.py` reports approval-token validation as validation-only with all authority fields false.
- `docs/source-proxy-production-hardening-plan.md` records that approval does not equal apply, apply does not equal commit, and commit does not equal push.

Authority definition:

| Level | Name | Allowed | Forbidden |
| --- | --- | --- | --- |
| 1 | `observe` | Read existing files, status, docs, and evidence. | Write, execute, apply, token action, queue/worker, branch/worktree, commit, push. |

GO / NO-GO:
- GO for observe definition.
- NO-GO for treating observation as approval or mutation authority.

Next authorized increment: 19.1.2 Recommend.

### 19.1.2 Recommend

Allowed work:
- Define the recommend authority level.
- Preserve advisory-only boundaries.

Evidence:
- Plan 14 records advisory subagent packets as inert display-eligible only.
- Plan 15 records Scout advisory research with `writes_allowed: false`.
- `docs/source-proxy-design-apply-lane-v0.1.md` records design packs may inform proposal evidence but must not apply changes.

Authority definition:

| Level | Name | Allowed | Forbidden |
| --- | --- | --- | --- |
| 2 | `recommend` | Produce advisory notes, proposed files, risks, and checks. | Apply, execute-approved, provider/model calls, write, token use, or implementation. |

GO / NO-GO:
- GO for recommend definition.
- NO-GO for treating recommendations, packets, scores, or design packs as write authority.

Next authorized increment: 19.1.3 Preview.

### 19.1.3 Preview

Allowed work:
- Define preview authority.
- Keep preview non-mutating.

Evidence:
- `source_proxy/verification/diff.py` and related tests distinguish diff preview and apply checks from actual apply.
- Plan 11 records GO for diff verification map and NO-GO for treating diff-preview as apply authority.
- Plan 18 records branch/worktree proposals as preview-only and not creation authority.

Authority definition:

| Level | Name | Allowed | Forbidden |
| --- | --- | --- | --- |
| 3 | `preview` | Show proposed diff, packet, route, file list, or branch/worktree proposal. | Mutate files, create branches/worktrees, consume tokens, execute commands, or imply approval. |

GO / NO-GO:
- GO for preview definition.
- NO-GO for treating preview as apply, branch, worktree, or execution authority.

Next authorized increment: 19.1.4 Dry run.

### 19.1.4 Dry Run

Allowed work:
- Define dry-run authority.
- Separate dry-run checks from execution.

Evidence:
- `source_proxy/cartographer/level_11_event_ledger.py` records event ledger status as `ledger-model-dry-run-only`, with action, write, and local execution authority false.
- `source_proxy/cartographer/approval_token_runtime.py` records validation-only status and no mutation guarantee.
- Plan 18 records no lease/lock/dispatch creation.

Authority definition:

| Level | Name | Allowed | Forbidden |
| --- | --- | --- | --- |
| 4 | `dry_run` | Run non-mutating validations or simulated ledgers when explicitly scoped. | Write files, consume tokens, execute approved actions, commit, push, mutate runtime, or hide side effects. |

GO / NO-GO:
- GO for dry-run definition.
- NO-GO for dry-run side effects, hidden mutation, or silent escalation.

Next authorized increment: 19.1.5 Approved write.

### 19.1.5 Approved Write

Allowed work:
- Define future approved-write requirements.
- Do not approve any write in Plan 19.

Evidence:
- `docs/source-proxy-design-apply-lane-v0.1.md` records required approval binding: task id, design pack id, source card id, target files, allowed files, diff preview, approval ID, approver, approval timestamp, git head, and post-apply verification plan.
- `source_proxy/cartographer/approval_token_runtime.py` requires exact files, exact lane, exact scope, expected HEAD, expected dirty tree, expiration, human issuance, single action, rollback, verification, and inactive kill switch.
- Plan 11 records NO-GO for running apply or execute-approved without explicit approval.

Authority definition:

| Level | Name | Allowed only after future exact approval | Forbidden in Plan 19 |
| --- | --- | --- | --- |
| 5 | `approved_write` | One exact write action bound to exact files, exact token, exact plan, rollback, and verification. | Any write, apply, execute-approved, token consumption, Source Proxy mutation, or protected path mutation. |

GO / NO-GO:
- GO for approved-write requirement design.
- NO-GO for approving, applying, or writing anything in Plan 19.

Next authorized increment: 19.1.6 Approved local execution.

### 19.1.6 Approved Local Execution

Allowed work:
- Define future approved-local-execution requirements.
- Do not execute commands in Plan 19 beyond read-only verification.

Evidence:
- Plan 18 blocks queue/worker execution, apply, approval-token action, branch/worktree, checkout, stash, clean, reset, stage, commit, push, merge, and hidden mutation.
- `source_proxy/cartographer/approval_token_runtime.py` sets command authority, workflow authority, queue authority, and git authority false.
- Plan 7 records Cartographer approval-token behavior changes require re-soak before production promotion.

Authority definition:

| Level | Name | Allowed only after future exact approval | Forbidden in Plan 19 |
| --- | --- | --- | --- |
| 6 | `approved_local_execution` | One exact non-hidden command or local action with exact token, exact command, exact files, rollback, verification, ledger, and closeout. | Runtime start, queue/worker, provider/model call, Cart activation, apply, commit, push, branch/worktree, or protected path mutation. |

GO / NO-GO:
- GO for approved-local-execution requirement design.
- NO-GO for command execution authority in Plan 19.

## Phase 19.1 Review

Completed increments:
- 19.1.1 GO for observe definition; NO-GO for mutation.
- 19.1.2 GO for recommend definition; NO-GO for advisory-as-authority.
- 19.1.3 GO for preview definition; NO-GO for preview-as-apply.
- 19.1.4 GO for dry-run definition; NO-GO for dry-run side effects.
- 19.1.5 GO for approved-write design; NO-GO for writes.
- 19.1.6 GO for approved-local-execution design; NO-GO for command execution.

Evidence exists:
- Source Proxy hardening ladder evidence.
- Source Proxy design apply lane evidence.
- Approval-token runtime validation-only evidence.
- Level 11 dry-run event ledger evidence.
- Plan 18 block-rule evidence.

Forbidden scope avoided:
- No token creation, token consumption, write, apply, execute-approved, command execution, provider/model call, queue/worker execution, branch, worktree, commit, push, runtime mutation, or protected path mutation occurred.

Checks:
- Read-only grep checks returned expected authority ladder, token, apply, execute-approved, event ledger, no-authority, and NO-GO evidence.

Phase result: GO to Phase 19.2; NO-GO for authority activation.

Next authorized increment: 19.2.1 Required token fields.

## Phase 19.2 Token Requirements

### 19.2.1 Required Token Fields

Allowed work:
- Define required future token fields.
- Do not create, validate for authority, or consume a token.

Evidence:
- `source_proxy/cartographer/approval_token_runtime.py` defines `REQUIRED_APPROVAL_TOKEN_FIELDS`.
- It records validation-only status, no mutation guarantee, token issuance unavailable, and token storage unavailable.

Required token fields:

| Field | Required | Requirement |
| --- | --- | --- |
| `schema_version` | yes | Must match expected schema. |
| `token_id` | yes | Stable token id. |
| `run_id` | yes | Exact run or plan id. |
| `operator_id` | yes | Actor receiving authority; cannot self-approve. |
| `approver_id` | yes | Human approver. |
| `action_type` | yes | Exact single action. |
| `lane_id` | yes | Exact lane; broad lane blocked. |
| `scope` | yes | Exact scope; broad scope blocked. |
| `exact_allowed_files` | yes | Exact file list, no wildcards. |
| `exact_forbidden_files` | yes | Exact forbidden list. |
| `expires_at` | yes | Expiration required. |
| `rollback_instructions` | yes | Required before mutation. |
| `verification_instructions` | yes | Required before mutation. |
| `expected_head` | yes | Must match current HEAD. |
| `expected_dirty_tree` | yes | Must match current dirty tree. |
| `kill_switch_state` | yes | Must require inactive kill switch. |
| `trust_tier` | yes | Exact trust tier. |
| `single_action` | yes | Must be true. |
| `issued_by_human` | yes | Must be true. |
| `human_approved_at` | yes | Approval time required. |

GO / NO-GO:
- GO for required token field design.
- NO-GO for creating, storing, validating for authority, or consuming a token.

Next authorized increment: 19.2.2 Expiration and revocation rules.

### 19.2.2 Expiration And Revocation Rules

Allowed work:
- Define expiration and revocation rules.

Evidence:
- `source_proxy/cartographer/approval_token_runtime.py` sets max token age to 24 hours and rejects future approval time, expired token, stale token, expiration before approval, already-used token, and revoked token conditions.
- Plan 7 records approval-token behavior changes require re-soak before production promotion.

Expiration and revocation rules:
- Token must expire.
- Token must not be older than the maximum allowed age.
- `expires_at` must be after `human_approved_at`.
- Future approval timestamps block.
- Already-used token blocks.
- Revoked token blocks.
- Stale HEAD blocks.
- Stale dirty tree blocks.
- Active kill switch blocks.
- Any future Cart approval-token behavior change requires re-soak review.

GO / NO-GO:
- GO for expiration and revocation rule design.
- NO-GO for accepting non-expiring, stale, reused, revoked, or kill-switch-conflicting tokens.

Next authorized increment: 19.2.3 Scope mismatch failure rules.

### 19.2.3 Scope Mismatch Failure Rules

Allowed work:
- Define mismatch failure rules.

Evidence:
- `source_proxy/cartographer/approval_token_runtime.py` rejects wrong actor, scope mismatch, broad scope, lane mismatch, broad lane, action type mismatch, missing single action, non-human issuance, empty allowed files, wildcard file scope, broad file scope, requested files outside allowed files, forbidden file intersection, allowed/forbidden overlap, trust-tier mismatch, and broad trust tier.
- Plan 18 records protected paths block.

Scope mismatch failure rules:
- Requested actor must match token operator.
- Requested lane must match exact lane.
- Requested action must match exact action type.
- Requested scope must match exact token scope.
- Broad scope values block.
- Broad lane values block.
- Broad trust tier values block.
- Wildcards block.
- Requested files must be a subset of exact allowed files.
- Requested files must not intersect forbidden files.
- Allowed and forbidden files must not overlap.
- Protected paths block even if present in a token.

GO / NO-GO:
- GO for scope mismatch failure rule design.
- NO-GO for broad token scope, scope mismatch, lane mismatch, file mismatch, or protected path override.

## Phase 19.2 Review

Completed increments:
- 19.2.1 GO for required token fields; NO-GO for token creation/consumption.
- 19.2.2 GO for expiration and revocation rules; NO-GO for stale or invalid tokens.
- 19.2.3 GO for scope mismatch failure rules; NO-GO for broad or mismatched authority.

Evidence exists:
- Approval-token runtime required fields are recorded.
- Expiration, revocation, stale state, and kill-switch rejection evidence is recorded.
- Scope, lane, action, file, trust-tier, and protected-path block evidence is recorded.

Forbidden scope avoided:
- No token was created, stored, validated for live authority, consumed, revoked, or used.
- No write, apply, execute-approved, command execution, queue/worker, provider/model call, branch/worktree, commit, push, runtime mutation, or protected path mutation occurred.

Checks:
- Read-only grep checks returned expected required fields, expiration, revocation, scope mismatch, broad scope, exact files, validation-only, and NO-GO evidence.

Phase result: GO to Phase 19.3; NO-GO for token authority.

Next authorized increment: 19.3.1 Define event types.

## Phase 19.3 Event Ledger

### 19.3.1 Define Event Types

Allowed work:
- Define event types for future authority ledger.

Evidence:
- `source_proxy/cartographer/level_11_event_ledger.py` defines dry-run ledger event types and required completed action events.
- It records append-only runtime disabled and action/write/local execution authority false.

Event types:
- `action_packet_created`
- `approval_requested`
- `approval_granted`
- `approval_rejected`
- `approval_token_created`
- `approval_token_revoked`
- `file_write_requested`
- `file_write_blocked`
- `file_write_completed`
- `command_requested`
- `command_blocked`
- `command_completed`
- `verification_started`
- `verification_passed`
- `verification_failed`
- `rollback_available`
- `rollback_requested`
- `rollback_completed`
- `action_closed_out`

GO / NO-GO:
- GO for event type design.
- NO-GO for append-only runtime activation or ledger mutation in Plan 19.

Next authorized increment: 19.3.2 Define no-silent-rewrite rule.

### 19.3.2 Define No-Silent-Rewrite Rule

Allowed work:
- Define no-silent-rewrite rule.

Evidence:
- `source_proxy/cartographer/level_11_event_ledger.py` rejects duplicate event ids, sequence gaps, unsupported event types, missing ids, missing runs, missing actors, and blocked/failed events missing reasons.
- Plan 18 blocks hidden mutation.

No-silent-rewrite rule:
- Event ids must be unique.
- Sequence must be monotonic with no gaps or reorder.
- Unsupported event types block.
- Every event must name `event_id`, `run_id`, `actor`, and sequence.
- Blocked events require a reason.
- Failed events require a reason.
- Ledger updates must append; no rewriting prior events.
- Any silent rewrite, missing sequence, or hidden mutation forces NO-GO.

GO / NO-GO:
- GO for no-silent-rewrite rule design.
- NO-GO for silent rewrite, missing event identity, or hidden mutation.

Next authorized increment: 19.3.3 Define action closeout requirements.

### 19.3.3 Define Action Closeout Requirements

Allowed work:
- Define future action closeout requirements.

Evidence:
- `source_proxy/cartographer/level_11_event_ledger.py` requires completed actions to include action packet creation, approval requested, approval granted, approval token created, verification started, verification passed, and action closed out.
- `docs/source-proxy-design-apply-lane-v0.1.md` requires post-apply evidence: changed files, checks run, check results, visual verification status when relevant, rollback hint, commit proposal blocked/pending status, and push blocked/pending status.

Future action closeout requirements:
- Action packet created.
- Approval requested.
- Approval granted by human.
- Exact token created under a future approved plan.
- Action requested.
- Action blocked or completed.
- Verification started.
- Verification passed or failed.
- Rollback reference recorded.
- Changed files recorded.
- Commit status recorded as separate blocked/pending/approved.
- Push status recorded as separate blocked/pending/approved.
- Action closed out.

GO / NO-GO:
- GO for action closeout requirement design.
- NO-GO for completed-action claims without ledger, verification, rollback, commit separation, push separation, and closeout.

Next authorized increment: Plan 19/24 closeout.

## Phase 19.3 Review

Completed increments:
- 19.3.1 GO for event type design; NO-GO for ledger runtime activation.
- 19.3.2 GO for no-silent-rewrite rule; NO-GO for silent rewrite or hidden mutation.
- 19.3.3 GO for action closeout requirements; NO-GO for incomplete action claims.

Evidence exists:
- Level 11 event ledger dry-run evidence is recorded.
- Source Proxy design apply post-apply evidence requirements are recorded.
- Plan 18 hidden mutation block evidence is recorded.

Forbidden scope avoided:
- No ledger runtime was activated.
- No ledger event was appended to runtime.
- No token was created or consumed.
- No write, command execution, apply, execute-approved, commit, push, branch, worktree, queue/worker, provider/model call, runtime mutation, or protected path mutation occurred.

Checks:
- Read-only grep checks returned expected event types, no-silent-rewrite, action closeout, post-apply verification, and NO-GO evidence.

Phase result: GO to Plan 19 closeout; NO-GO for Plan 20 start.

Next authorized increment: Plan 19/24 closeout.

## Plan 19/24 Closeout

Phase review:
- Phase 19.1 Authority Ladder: GO for observe, recommend, preview, dry-run, approved-write, and approved-local-execution design; NO-GO for activating authority.
- Phase 19.2 Token Requirements: GO for token field, expiration/revocation, and mismatch failure design; NO-GO for token creation, validation for live authority, or consumption.
- Phase 19.3 Event Ledger: GO for event type, no-silent-rewrite, and action closeout design; NO-GO for ledger runtime activation or mutation.

Increment evidence:
- 19.1.1 Observe: recorded.
- 19.1.2 Recommend: recorded.
- 19.1.3 Preview: recorded.
- 19.1.4 Dry run: recorded.
- 19.1.5 Approved write: design recorded; execution NO-GO.
- 19.1.6 Approved local execution: design recorded; execution NO-GO.
- 19.2.1 Required token fields: recorded.
- 19.2.2 Expiration and revocation rules: recorded.
- 19.2.3 Scope mismatch failure rules: recorded.
- 19.3.1 Event types: recorded.
- 19.3.2 No-silent-rewrite rule: recorded.
- 19.3.3 Action closeout requirements: recorded.

Evidence exists:
- `docs/source-proxy-production-hardening-plan.md`
- `docs/source-proxy-production-hardening-consolidation-plan-11-24-v0.1.md`
- `docs/source-proxy-design-apply-lane-v0.1.md`
- `docs/cartographer-live-evidence/cartographer-plan-7-24-activation-boundary-resoak-decision-v0.1.md`
- `docs/controlled-multi-agent-subagent-orchestration-boundary-plan-18-24-v0.1.md`
- `source_proxy/cartographer/approval_token_runtime.py`
- `source_proxy/cartographer/level_11_event_ledger.py`
- `src/components/coding/CodingCommandCenterShell.tsx`

Forbidden actions review:
- No token was created.
- No token was consumed.
- No token was used for live authority.
- No approved write occurred.
- No execution occurred beyond read-only inspection/checks.
- No apply or execute-approved occurred.
- No commit or push occurred.
- No branch or worktree was created.
- No queue or worker was executed.
- No provider/model call occurred.
- No runtime or protected path was mutated.
- No Plan 20 work started.

Authority design packet:
- Authority ladder is observe -> recommend -> preview -> dry_run -> approved_write -> approved_local_execution.
- Approved write and approved local execution remain future-only and require separate exact human approval.
- Token requirements are exact, human-issued, single-action, expiring, scoped, lane-bound, file-bound, HEAD-bound, dirty-tree-bound, kill-switch-bound, trust-tier-bound, rollback-bound, and verification-bound.
- Scope mismatch, broad scope, stale token, revoked token, used token, protected path overlap, and missing expiration fail closed.
- Event ledger design requires append-only sequencing, explicit blocked/failed reasons, verification, rollback, commit separation, push separation, and action closeout.

Final Plan 19/24 result: GO for authority design packet; NO-GO for token consumption, approved writes, execution, apply, execute-approved, commit, push, branch, worktree, queue/worker execution, provider/model calls, runtime mutation, protected path mutation, or Plan 20 start without explicit operator approval.

Next roadmap plan only: `Plan 20/24: Visual Evidence And Browser Proof Harness`.

## Manual Verification

Copy-paste verification:

```bash
cd /home/source/SpiritOS && git status --branch --short --untracked-files=normal && grep -nE "Plan 19/24|observe|recommend|preview|dry_run|approved_write|approved_local_execution|required token fields|expiration|revocation|scope mismatch|event types|no-silent-rewrite|action closeout|NO-GO|Plan 20/24" docs/controlled-action-authority-approval-token-ladder-plan-19-24-v0.1.md && grep -nE "approval does not equal apply|apply does not equal commit|commit does not equal push|validation-only|REQUIRED_APPROVAL_TOKEN_FIELDS|token_expired|token_stale|scope_mismatch|broad_scope|single_action|issued_by_human|LEVEL_11_LEDGER_EVENT_TYPES|LEVEL_11_COMPLETED_ACTION_REQUIRED_EVENTS|design-pack approval is not the same thing as apply approval|No approval-token mutation|No approval-token consumption|NO-GO" docs/source-proxy-production-hardening-plan.md docs/source-proxy-production-hardening-consolidation-plan-11-24-v0.1.md docs/source-proxy-design-apply-lane-v0.1.md docs/cartographer-live-evidence/cartographer-plan-7-24-activation-boundary-resoak-decision-v0.1.md source_proxy/cartographer/approval_token_runtime.py source_proxy/cartographer/level_11_event_ledger.py && git diff --check -- docs/controlled-action-authority-approval-token-ladder-plan-19-24-v0.1.md
```

Expected output:
- Git status shows the existing untracked plan docs, including this Plan 19 packet.
- Plan 19 grep prints authority ladder levels, token requirements, expiration/revocation, scope mismatch, event ledger rules, action closeout, NO-GO boundaries, and Plan 20 title.
- Evidence grep prints Source Proxy separation rules, approval-token validation-only fields and failure reasons, event ledger types, design apply approval separation, and prior no-token/no-authority boundaries.
- `git diff --check` prints no output.
