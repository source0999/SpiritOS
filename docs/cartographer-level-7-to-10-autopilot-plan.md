# Cartographer Level 7 To Level 10 Limited Autopilot Roadmap

status: planning-only

Status date: 2026-05-20

## Current State Summary

Cartographer is closed out through Level 6.5, Multi-Project Closeout Dashboard. The source of truth is `docs/cartographer-level-3-to-6-closeout-summary.md`, which records the current completed roadmap cap as Level 6.5, the next possible scope as Level 7+ future limited autopilot disabled by default, and the current authority status as read-only unless a specific lower-level approved executor gate explicitly allows otherwise.

The Level 6.5 baseline is backed by the focused manual check:

```bash
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_6_multi_project_closeout or level_6_cross_repo_dirty_tree or level_6_component_ownership or level_6_cross_project_status_board or level_6_project_registry"
```

The closeout summary records the observed result as `10 passed, 195 deselected, 2 warnings`, with all mutation, promotion, and execution flags false.

Current known read-only coordination surfaces include the Level 6 builders in `source_proxy/cartographer/service.py`: `build_cartographer_level_6_project_registry_hardening`, `build_cartographer_level_6_cross_project_status_board`, `build_cartographer_level_6_component_ownership_assignment`, `build_cartographer_level_6_cross_repo_dirty_tree_classifier`, and `build_cartographer_level_6_multi_project_closeout_dashboard`. The corresponding API routes are in `source_proxy/api/cartographer.py`, and the baseline coverage is in `source_proxy/tests/test_cartographer_api.py`.

Cartographer is production-adjacent for read-only coordination and approved local stewardship. It is not production-ready as an autopilot.

## Active Safety Boundary

The following actions remain forbidden:

- No push.
- No push queue creation.
- No branch automation.
- No worktree automation.
- No cleanup.
- No merge.
- No stash.
- No automatic promotion.
- No automatic execution.
- No Level 7 work is active.

Level 7 starts disabled by default. Every new capability must begin as a proposal, preview, or dry-run before execution is ever considered. A future executor gate must be explicit, lower-level, manually approved, and covered by focused tests before any mutation can be discussed.

## Roadmap Rules

Codex must not invent extra levels after Level 10.

Codex must not continue past the current requested increment without permission.

Every increment must include:

- Purpose.
- Allowed files.
- Forbidden actions.
- Expected output.
- Manual check commands.
- Expected manual check result.
- Rollback notes.
- Next increment title.
- Permission gate.

## Level 7: Limited Autopilot, Disabled By Default

Purpose: Cartographer can recommend the next safe action and create dry-run action packets, but it cannot execute actions by itself.

Level 7 rules:

- No push.
- No branch creation.
- No worktree creation.
- No cleanup.
- No stash.
- No merge.
- No automatic commit.
- No automatic execution.
- No self-approval.
- No Level 8 work until Level 7 is closed out and manually approved.

### 7.0: Level 7 Autopilot Boundary Contract

- Purpose: Define the Level 7 disabled-autopilot safety contract before any service, API, UI, or runtime changes.
- Allowed files: `docs/cartographer-level-7-autopilot-boundary-contract.md`; this roadmap file only if a correction is needed.
- Forbidden actions: all implementation changes, tests, runtime behavior changes, push, push queue creation, branch creation, worktree creation, cleanup, stash, merge, automatic commit, automatic execution, and self-approval.
- Expected output: a docs-only boundary contract stating that Level 7 is disabled by default and limited to recommendations and dry-run packets.
- Manual check commands:

```bash
cd /home/source/SpiritOS
git diff --check -- docs/cartographer-level-7-autopilot-boundary-contract.md docs/cartographer-level-7-to-10-autopilot-plan.md
grep -n "disabled by default\|No automatic execution\|No self-approval\|dry-run" docs/cartographer-level-7-autopilot-boundary-contract.md
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_6_multi_project_closeout or level_6_cross_repo_dirty_tree or level_6_component_ownership or level_6_cross_project_status_board or level_6_project_registry"
git status -sb
```

- Expected manual check result: diff check has no output; grep finds the required boundary terms; focused Level 6 baseline still passes; git status shows docs-only changes.
- Rollback notes: remove `docs/cartographer-level-7-autopilot-boundary-contract.md` and revert any roadmap correction.
- Next increment title: Level 7.1: Disabled-By-Default Feature Flag.
- Permission gate: explicit user approval is required before writing the Level 7.0 boundary contract, and separate approval is required before Level 7.1.

### 7.1: Disabled-By-Default Feature Flag

- Purpose: Add a contract and focused tests for a disabled-by-default flag that exposes no active autopilot authority when unset.
- Allowed files: the Level 7.1 planning doc, the minimum service/API/test files needed only after approval, and no UI files unless separately approved.
- Forbidden actions: push, branch creation, worktree creation, cleanup, stash, merge, automatic commit, automatic execution, self-approval, and enabling the flag by default.
- Expected output: a disabled flag contract that reports inactive Level 7 status without creating action authority.
- Manual check commands:

```bash
cd /home/source/SpiritOS
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_7_disabled_by_default or level_6_multi_project_closeout or level_6_cross_repo_dirty_tree or level_6_component_ownership or level_6_cross_project_status_board or level_6_project_registry"
git status -sb
```

- Expected manual check result: focused Level 7 disabled-default tests pass with the Level 6 baseline; runtime flags remain false unless explicitly configured in test scope.
- Rollback notes: revert the Level 7.1 doc and any approved minimal service/API/test changes; no repo cleanup should be needed because no mutation is allowed.
- Next increment title: Level 7.2: Next Safe Action Recommendation Contract.
- Permission gate: explicit user approval is required before implementation or test edits.

### 7.2: Next Safe Action Recommendation Contract

- Purpose: Define a read-only recommendation payload for the next safe human action based on current blockers and Level 6 status.
- Allowed files: the Level 7.2 planning doc and approved minimal service/API/test files.
- Forbidden actions: all mutation, automatic execution, automatic commit, branch or worktree creation, cleanup, stash, merge, push, and self-approval.
- Expected output: a recommendation-only contract that explains why an action is safe, blocked, or unavailable.
- Manual check commands:

```bash
cd /home/source/SpiritOS
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_7_next_safe_action or level_7_disabled_by_default or level_6_multi_project_closeout or level_6_cross_repo_dirty_tree or level_6_component_ownership or level_6_cross_project_status_board or level_6_project_registry"
git status -sb
```

- Expected manual check result: tests prove recommendations are read-only, explain blockers, and leave all execution flags false.
- Rollback notes: revert the Level 7.2 doc and approved minimal code/test changes.
- Next increment title: Level 7.3: Dry-Run Action Packet Builder.
- Permission gate: explicit user approval is required before implementation or test edits.

### 7.3: Dry-Run Action Packet Builder

- Purpose: Create dry-run action packets that describe intended steps, evidence, required approvals, and rollback notes without executing anything.
- Allowed files: the Level 7.3 planning doc and approved minimal service/API/test files.
- Forbidden actions: actual execution, automatic execution, automatic commit, push, branch creation, worktree creation, cleanup, stash, merge, and self-approval.
- Expected output: dry-run packets with stable ids, allowed-file previews, blockers, required approval fields, and `actions_taken` false.
- Manual check commands:

```bash
cd /home/source/SpiritOS
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_7_dry_run_action_packet or level_7_next_safe_action or level_7_disabled_by_default or level_6_multi_project_closeout or level_6_cross_repo_dirty_tree or level_6_component_ownership or level_6_cross_project_status_board or level_6_project_registry"
git status -sb
```

- Expected manual check result: tests prove packets are previews only and no write, stage, commit, push, branch, worktree, stash, merge, or cleanup action occurs.
- Rollback notes: revert the Level 7.3 doc and approved minimal code/test changes; no generated evidence should require cleanup.
- Next increment title: Level 7.4: Exact Approval Handshake Contract.
- Permission gate: explicit user approval is required before implementation or test edits.

### 7.4: Exact Approval Handshake Contract

- Purpose: Specify an exact human approval handshake for future packet execution without adding execution behavior.
- Allowed files: the Level 7.4 planning doc and approved minimal service/API/test files.
- Forbidden actions: accepting loose approvals, self-approval, automatic execution, automatic commit, push, branch creation, worktree creation, cleanup, stash, and merge.
- Expected output: a handshake preview that validates required fields and still refuses execution.
- Manual check commands:

```bash
cd /home/source/SpiritOS
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_7_exact_approval_handshake or level_7_dry_run_action_packet or level_7_next_safe_action or level_7_disabled_by_default or level_6_multi_project_closeout or level_6_cross_repo_dirty_tree or level_6_component_ownership or level_6_cross_project_status_board or level_6_project_registry"
git status -sb
```

- Expected manual check result: tests prove exact approval shape is validated as preview only and cannot execute, self-approve, or mutate state.
- Rollback notes: revert the Level 7.4 doc and approved minimal code/test changes.
- Next increment title: Level 7.5: Level 7 Closeout Dashboard.
- Permission gate: explicit user approval is required before implementation or test edits.

### 7.5: Level 7 Closeout Dashboard

- Purpose: Summarize Level 7 status, disabled flag state, recommendations, dry-run packets, approval preview status, and blockers.
- Allowed files: the Level 7.5 planning doc and approved minimal service/API/test/UI files.
- Forbidden actions: execution, automatic promotion, automatic commit, push, branch creation, worktree creation, cleanup, stash, merge, and self-approval.
- Expected output: a closeout dashboard showing Level 7 remains disabled unless deliberately configured and has performed no mutation.
- Manual check commands:

```bash
cd /home/source/SpiritOS
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_7_closeout_dashboard or level_7_exact_approval_handshake or level_7_dry_run_action_packet or level_7_next_safe_action or level_7_disabled_by_default or level_6_multi_project_closeout or level_6_cross_repo_dirty_tree or level_6_component_ownership or level_6_cross_project_status_board or level_6_project_registry"
git status -sb
```

- Expected manual check result: tests prove Level 7 is closed out as disabled by default, recommendation/dry-run only, and all execution and mutation flags remain false.
- Rollback notes: revert the Level 7.5 doc and approved minimal code/test/UI changes.
- Next increment title: Level 8.0: Workflow Runner Boundary Contract.
- Permission gate: Level 8 must not begin until Level 7 is closed out, manually checked, and explicitly approved.

## Level 8: Approved Workflow Runner

Purpose: Cartographer can model and display a sequence of safe approved steps, but the human must approve each step. It should feel like a controlled operations cockpit, not an autonomous agent.

Level 8 rules:

- Human approval required per step.
- No push or merge by default.
- No background execution.
- No cross-project mutation.
- No autonomous retry loops.
- All actions must be visible in a receipt journal.

### 8.0: Workflow Runner Boundary Contract

- Purpose: Define the Level 8 workflow runner as visible, stepwise, and human-approved before any execution is considered.
- Allowed files: a Level 8.0 planning doc and this roadmap only if a correction is needed.
- Forbidden actions: implementation changes, push, merge, background execution, cross-project mutation, autonomous retries, and hidden receipt writes.
- Expected output: a docs-only boundary contract for a controlled workflow runner.
- Manual check commands:

```bash
cd /home/source/SpiritOS
git diff --check -- docs/cartographer-level-8-workflow-runner-boundary-contract.md docs/cartographer-level-7-to-10-autopilot-plan.md
grep -n "Human approval required per step\|No background execution\|receipt journal" docs/cartographer-level-8-workflow-runner-boundary-contract.md
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_7_closeout_dashboard or level_6_multi_project_closeout or level_6_cross_repo_dirty_tree or level_6_component_ownership or level_6_cross_project_status_board or level_6_project_registry"
git status -sb
```

- Expected manual check result: docs diff is clean; boundary terms are present; Level 7 closeout and Level 6 baseline remain green.
- Rollback notes: remove the Level 8.0 planning doc and revert any roadmap correction.
- Next increment title: Level 8.1: Workflow Run Card Model.
- Permission gate: explicit user approval is required after Level 7 closeout.

### 8.1: Workflow Run Card Model

- Purpose: Model workflow cards that show steps, current approval state, blockers, receipts, and stop conditions.
- Allowed files: the Level 8.1 planning doc and approved minimal service/API/test/UI files.
- Forbidden actions: executing steps, background execution, autonomous retries, push, merge, cross-project mutation, and hidden writes.
- Expected output: visible workflow run cards with no execution authority.
- Manual check commands:

```bash
cd /home/source/SpiritOS
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_8_workflow_run_card or level_7_closeout_dashboard or level_6_multi_project_closeout"
git status -sb
```

- Expected manual check result: tests prove workflow cards are display/model only and no steps run.
- Rollback notes: revert the Level 8.1 doc and approved minimal changes.
- Next increment title: Level 8.2: Step Approval UI/API Contract.
- Permission gate: explicit user approval is required before implementation or test edits.

### 8.2: Step Approval UI/API Contract

- Purpose: Define per-step approval controls and API payloads with exact approval requirements.
- Allowed files: the Level 8.2 planning doc and approved minimal service/API/test/UI files.
- Forbidden actions: approving multiple hidden steps, execution without visible approval, push, merge, background execution, cross-project mutation, and autonomous retries.
- Expected output: a per-step approval preview contract that does not execute.
- Manual check commands:

```bash
cd /home/source/SpiritOS
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_8_step_approval or level_8_workflow_run_card or level_7_closeout_dashboard"
git status -sb
```

- Expected manual check result: tests prove approval is per-step, exact, visible, and non-executing unless a later approved gate exists.
- Rollback notes: revert the Level 8.2 doc and approved minimal changes.
- Next increment title: Level 8.3: Receipt Journal And Evidence Trail.
- Permission gate: explicit user approval is required before implementation or test edits.

### 8.3: Receipt Journal And Evidence Trail

- Purpose: Add a visible receipt journal model for proposed, approved, skipped, canceled, failed, and completed steps.
- Allowed files: the Level 8.3 planning doc and approved minimal service/API/test/UI files.
- Forbidden actions: hidden receipt creation, background execution, automatic retry loops, push, merge, and cross-project mutation.
- Expected output: a receipt journal preview with evidence references and no hidden autonomy.
- Manual check commands:

```bash
cd /home/source/SpiritOS
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_8_receipt_journal or level_8_step_approval or level_8_workflow_run_card"
git status -sb
```

- Expected manual check result: tests prove the journal is visible, ordered, auditable, and not a background execution log.
- Rollback notes: revert the Level 8.3 doc and approved minimal changes.
- Next increment title: Level 8.4: Cancel, Stop, And Failed-Step Handling.
- Permission gate: explicit user approval is required before implementation or test edits.

### 8.4: Cancel, Stop, And Failed-Step Handling

- Purpose: Define stop behavior when a human cancels, a step fails, or a blocker appears.
- Allowed files: the Level 8.4 planning doc and approved minimal service/API/test/UI files.
- Forbidden actions: autonomous retries, continuing after failure without approval, background execution, push, merge, and cross-project mutation.
- Expected output: deterministic stopped states that require human review before continuing.
- Manual check commands:

```bash
cd /home/source/SpiritOS
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_8_cancel_stop_failed_step or level_8_receipt_journal or level_8_step_approval"
git status -sb
```

- Expected manual check result: tests prove cancellation and failed steps stop the workflow and cannot trigger autonomous retry or continuation.
- Rollback notes: revert the Level 8.4 doc and approved minimal changes.
- Next increment title: Level 8.5: Level 8 Closeout Smoke.
- Permission gate: explicit user approval is required before implementation or test edits.

### 8.5: Level 8 Closeout Smoke

- Purpose: Verify Level 8 behaves as a controlled operations cockpit with visible per-step approval and no hidden autonomy.
- Allowed files: the Level 8.5 planning doc and approved minimal service/API/test/UI files.
- Forbidden actions: push, merge, background execution, cross-project mutation, autonomous retry loops, and hidden writes.
- Expected output: a closeout smoke proving Level 8 remains permission-gated and auditable.
- Manual check commands:

```bash
cd /home/source/SpiritOS
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_8_closeout_smoke or level_8_cancel_stop_failed_step or level_8_receipt_journal or level_8_step_approval or level_8_workflow_run_card"
git status -sb
```

- Expected manual check result: focused Level 8 checks pass and show all actions visible in the receipt journal with no push, merge, background execution, or cross-project mutation.
- Rollback notes: revert the Level 8.5 doc and approved minimal changes.
- Next increment title: Level 9.0: Multi-Worker Boundary Contract.
- Permission gate: Level 9 must not begin until Level 8 is closed out, manually checked, and explicitly approved.

## Level 9: Multi-Worker Coordination

Purpose: Cartographer helps coordinate multiple Codex workers safely so they do not collide across files, branches, tasks, or project ownership zones.

Level 9 rules:

- Recommendations only unless explicitly approved.
- No automatic branch or worktree creation yet.
- No automatic reassignment.
- No force overwrite.
- No commit/push/merge without lower-level approved gates.
- Must detect conflicts before suggesting parallel work.

### 9.0: Multi-Worker Boundary Contract

- Purpose: Define multi-worker coordination as recommendation-only until explicit approval exists for any mutation.
- Allowed files: a Level 9.0 planning doc and this roadmap only if a correction is needed.
- Forbidden actions: automatic branch creation, automatic worktree creation, automatic reassignment, force overwrite, commit, push, merge, cleanup, and stash.
- Expected output: a docs-only safety contract for worker coordination and conflict prevention.
- Manual check commands:

```bash
cd /home/source/SpiritOS
git diff --check -- docs/cartographer-level-9-multi-worker-boundary-contract.md docs/cartographer-level-7-to-10-autopilot-plan.md
grep -n "Recommendations only\|No automatic branch\|No force overwrite\|detect conflicts" docs/cartographer-level-9-multi-worker-boundary-contract.md
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_8_closeout_smoke or level_7_closeout_dashboard or level_6_multi_project_closeout"
git status -sb
```

- Expected manual check result: docs diff is clean; boundary terms are present; prior closeout baselines remain green.
- Rollback notes: remove the Level 9.0 planning doc and revert any roadmap correction.
- Next increment title: Level 9.1: Worker Registry And Assignment Model.
- Permission gate: explicit user approval is required after Level 8 closeout.

### 9.1: Worker Registry And Assignment Model

- Purpose: Model workers, assigned tasks, ownership zones, and active file scopes without reassigning or mutating work.
- Allowed files: the Level 9.1 planning doc and approved minimal service/API/test/UI files.
- Forbidden actions: automatic reassignment, force overwrite, branch creation, worktree creation, commit, push, merge, cleanup, and stash.
- Expected output: a read-only worker registry with assignment status and blockers.
- Manual check commands:

```bash
cd /home/source/SpiritOS
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_9_worker_registry or level_8_closeout_smoke"
git status -sb
```

- Expected manual check result: tests prove registry output is read-only and cannot assign or reassign workers.
- Rollback notes: revert the Level 9.1 doc and approved minimal changes.
- Next increment title: Level 9.2: One Worker, One Task, One Branch Rule.
- Permission gate: explicit user approval is required before implementation or test edits.

### 9.2: One Worker, One Task, One Branch Rule

- Purpose: Add a rule model that flags workers with ambiguous task or branch ownership before parallel work is suggested.
- Allowed files: the Level 9.2 planning doc and approved minimal service/API/test/UI files.
- Forbidden actions: branch creation, branch checkout, automatic reassignment, force overwrite, commit, push, merge, cleanup, and stash.
- Expected output: conflict warnings for multiple tasks, missing branch proposals, or ambiguous ownership.
- Manual check commands:

```bash
cd /home/source/SpiritOS
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_9_one_worker_one_task_one_branch or level_9_worker_registry"
git status -sb
```

- Expected manual check result: tests prove rule violations are reported as blockers and do not create branches or assignments.
- Rollback notes: revert the Level 9.2 doc and approved minimal changes.
- Next increment title: Level 9.3: Allowed-File Conflict Checker.
- Permission gate: explicit user approval is required before implementation or test edits.

### 9.3: Allowed-File Conflict Checker

- Purpose: Detect overlapping allowed-file scopes before suggesting parallel work.
- Allowed files: the Level 9.3 planning doc and approved minimal service/API/test/UI files.
- Forbidden actions: force overwrite, automatic reassignment, branch creation, worktree creation, commit, push, merge, cleanup, and stash.
- Expected output: file-scope conflict reports with clear blocked/safe recommendations.
- Manual check commands:

```bash
cd /home/source/SpiritOS
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_9_allowed_file_conflict_checker or level_9_one_worker_one_task_one_branch"
git status -sb
```

- Expected manual check result: tests prove conflicts are detected before parallel work is suggested and no files are overwritten.
- Rollback notes: revert the Level 9.3 doc and approved minimal changes.
- Next increment title: Level 9.4: Branch And Worktree Proposal Queue.
- Permission gate: explicit user approval is required before implementation or test edits.

### 9.4: Branch And Worktree Proposal Queue

- Purpose: Queue branch and worktree proposals for human review without creating them.
- Allowed files: the Level 9.4 planning doc and approved minimal service/API/test/UI files.
- Forbidden actions: automatic branch creation, automatic worktree creation, checkout, cleanup, stash, commit, push, merge, and force overwrite.
- Expected output: proposal queue entries with intended branch/worktree names, blockers, conflicts, and approval requirements.
- Manual check commands:

```bash
cd /home/source/SpiritOS
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_9_branch_worktree_proposal_queue or level_9_allowed_file_conflict_checker"
git status -sb
```

- Expected manual check result: tests prove branch/worktree outputs are proposals only and no Git topology changes occur.
- Rollback notes: revert the Level 9.4 doc and approved minimal changes; no branch or worktree cleanup should be needed.
- Next increment title: Level 9.5: Stale Worker Detection And Closeout Packet.
- Permission gate: explicit user approval is required before implementation or test edits.

### 9.5: Stale Worker Detection And Closeout Packet

- Purpose: Identify stale worker assignments and produce closeout packets for human review.
- Allowed files: the Level 9.5 planning doc and approved minimal service/API/test/UI files.
- Forbidden actions: automatic reassignment, automatic closeout, branch deletion, worktree deletion, cleanup, stash, commit, push, merge, and force overwrite.
- Expected output: stale worker reports with proposed closeout actions and no mutation.
- Manual check commands:

```bash
cd /home/source/SpiritOS
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_9_stale_worker_closeout_packet or level_9_branch_worktree_proposal_queue"
git status -sb
```

- Expected manual check result: tests prove stale worker handling is a proposal packet only and cannot close, reassign, delete, or clean up work.
- Rollback notes: revert the Level 9.5 doc and approved minimal changes.
- Next increment title: Level 9.6: Level 9 Coordination Dashboard.
- Permission gate: explicit user approval is required before implementation or test edits.

### 9.6: Level 9 Coordination Dashboard

- Purpose: Summarize workers, tasks, branch/worktree proposals, file conflicts, stale assignments, and blocked parallel work.
- Allowed files: the Level 9.6 planning doc and approved minimal service/API/test/UI files.
- Forbidden actions: automatic branch or worktree creation, automatic reassignment, force overwrite, cleanup, stash, commit, push, merge, and hidden mutation.
- Expected output: a coordination dashboard that helps humans plan safe parallel work without acting for them.
- Manual check commands:

```bash
cd /home/source/SpiritOS
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_9_coordination_dashboard or level_9_stale_worker_closeout_packet or level_9_allowed_file_conflict_checker"
git status -sb
```

- Expected manual check result: tests prove dashboard data is recommendation-only and conflict-aware.
- Rollback notes: revert the Level 9.6 doc and approved minimal changes.
- Next increment title: Level 10.0: Production Operator Boundary Contract.
- Permission gate: Level 10 must not begin until Level 9 is closed out, manually checked, and explicitly approved.

## Level 10: Production Operator Mode

Purpose: Cartographer becomes a daily command center for SpiritOS repo operations, closeouts, evidence, and next-step planning while still respecting all safety gates.

Level 10 rules:

- Still no hidden autonomy.
- Still no background mutation.
- Still no push/merge/cleanup unless future approved executor gates exist.
- Must be explainable to a human operator.
- Must have clear rollback and audit path.
- Must stop at Level 10.7 unless the user explicitly asks for a new roadmap.

### 10.0: Production Operator Boundary Contract

- Purpose: Define production operator mode as command-center visibility and gated planning, not hidden autonomy.
- Allowed files: a Level 10.0 planning doc and this roadmap only if a correction is needed.
- Forbidden actions: hidden autonomy, background mutation, push, merge, cleanup, stash, automatic execution, automatic promotion, and inventing Level 11.
- Expected output: a docs-only boundary contract for production operator mode.
- Manual check commands:

```bash
cd /home/source/SpiritOS
git diff --check -- docs/cartographer-level-10-production-operator-boundary-contract.md docs/cartographer-level-7-to-10-autopilot-plan.md
grep -n "no hidden autonomy\|no background mutation\|rollback and audit\|stop at Level 10.7" docs/cartographer-level-10-production-operator-boundary-contract.md
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_9_coordination_dashboard or level_8_closeout_smoke or level_7_closeout_dashboard"
git status -sb
```

- Expected manual check result: docs diff is clean; boundary terms are present; prior closeout baselines remain green.
- Rollback notes: remove the Level 10.0 planning doc and revert any roadmap correction.
- Next increment title: Level 10.1: Operator Dashboard Polish Plan.
- Permission gate: explicit user approval is required after Level 9 closeout.

### 10.1: Operator Dashboard Polish Plan

- Purpose: Plan operator dashboard polish for daily scanning, blockers, evidence, and next-step review.
- Allowed files: the Level 10.1 planning doc and approved minimal UI/test files if later authorized.
- Forbidden actions: runtime mutation, hidden autonomy, background mutation, push, merge, cleanup, automatic execution, and automatic promotion.
- Expected output: a dashboard polish plan or approved UI-only update that preserves all gates.
- Manual check commands:

```bash
cd /home/source/SpiritOS
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_10_operator_dashboard_polish or level_9_coordination_dashboard"
git status -sb
```

- Expected manual check result: checks prove dashboard polish is explainable, visible, and non-mutating.
- Rollback notes: revert the Level 10.1 doc and approved minimal changes.
- Next increment title: Level 10.2: Project Health Timeline.
- Permission gate: explicit user approval is required before implementation or test edits.

### 10.2: Project Health Timeline

- Purpose: Show project health, blockers, evidence, and closeout history as an operator timeline.
- Allowed files: the Level 10.2 planning doc and approved minimal service/API/test/UI files.
- Forbidden actions: background mutation, hidden writes, cleanup, push, merge, automatic execution, and automatic promotion.
- Expected output: a read-only project health timeline with evidence references and audit context.
- Manual check commands:

```bash
cd /home/source/SpiritOS
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_10_project_health_timeline or level_10_operator_dashboard_polish"
git status -sb
```

- Expected manual check result: tests prove timeline data is read-only and does not alter evidence or repo state.
- Rollback notes: revert the Level 10.2 doc and approved minimal changes.
- Next increment title: Level 10.3: Closeout Packet Generator.
- Permission gate: explicit user approval is required before implementation or test edits.

### 10.3: Closeout Packet Generator

- Purpose: Generate human-reviewable closeout packets from existing status, evidence, manual checks, and blockers.
- Allowed files: the Level 10.3 planning doc and approved minimal service/API/test/UI files.
- Forbidden actions: automatic closeout, automatic promotion, hidden evidence writes, cleanup, push, merge, and background mutation.
- Expected output: closeout packet previews that humans can review before any record is finalized.
- Manual check commands:

```bash
cd /home/source/SpiritOS
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_10_closeout_packet_generator or level_10_project_health_timeline"
git status -sb
```

- Expected manual check result: tests prove packets are generated as previews and do not finalize, promote, or mutate evidence automatically.
- Rollback notes: revert the Level 10.3 doc and approved minimal changes.
- Next increment title: Level 10.4: Run History And Evidence Browser.
- Permission gate: explicit user approval is required before implementation or test edits.

### 10.4: Run History And Evidence Browser

- Purpose: Browse prior manual checks, run results, closeout packets, and evidence links without changing them.
- Allowed files: the Level 10.4 planning doc and approved minimal service/API/test/UI files.
- Forbidden actions: evidence mutation, hidden writes, cleanup, push, merge, background mutation, automatic execution, and automatic promotion.
- Expected output: read-only run history and evidence browsing with clear provenance.
- Manual check commands:

```bash
cd /home/source/SpiritOS
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_10_run_history_evidence_browser or level_10_closeout_packet_generator"
git status -sb
```

- Expected manual check result: tests prove browsing does not edit evidence, create receipts, or alter run history.
- Rollback notes: revert the Level 10.4 doc and approved minimal changes.
- Next increment title: Level 10.5: Scout And Blueprint Handoff Preview.
- Permission gate: explicit user approval is required before implementation or test edits.

### 10.5: Scout And Blueprint Handoff Preview

- Purpose: Preview Scout and blueprint handoff context for operator decisions without writing to Scout, proxy memory, coding context, or blueprint files.
- Allowed files: the Level 10.5 planning doc and approved minimal service/API/test/UI files.
- Forbidden actions: Scout writes, proxy memory writes, coding context writes, blueprint writes, background mutation, cleanup, push, merge, automatic execution, and automatic promotion.
- Expected output: handoff previews with source references, blockers, and no write authority.
- Manual check commands:

```bash
cd /home/source/SpiritOS
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_10_scout_blueprint_handoff_preview or level_10_run_history_evidence_browser"
git status -sb
```

- Expected manual check result: tests prove handoff output is preview-only and does not write to Scout, proxy memory, coding context, or blueprints.
- Rollback notes: revert the Level 10.5 doc and approved minimal changes.
- Next increment title: Level 10.6: Level 10 Production Readiness Checklist.
- Permission gate: explicit user approval is required before implementation or test edits.

### 10.6: Level 10 Production Readiness Checklist

- Purpose: Verify operator-mode readiness, explainability, rollback, audit path, safety gates, and known limitations.
- Allowed files: the Level 10.6 planning doc and approved minimal service/API/test/UI files.
- Forbidden actions: hidden autonomy, background mutation, cleanup, push, merge, automatic execution, automatic promotion, and inventing new levels.
- Expected output: a readiness checklist that blocks production operator mode when any safety or audit requirement is missing.
- Manual check commands:

```bash
cd /home/source/SpiritOS
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_10_production_readiness_checklist or level_10_scout_blueprint_handoff_preview"
git status -sb
```

- Expected manual check result: tests prove readiness fails closed and remains explainable to a human operator.
- Rollback notes: revert the Level 10.6 doc and approved minimal changes.
- Next increment title: Level 10.7: Level 10 Closeout And Next-Roadmap Gate.
- Permission gate: explicit user approval is required before implementation or test edits.

### 10.7: Level 10 Closeout And Next-Roadmap Gate

- Purpose: Close out Level 10 and require explicit user direction before any future roadmap is written.
- Allowed files: the Level 10.7 planning doc and approved minimal service/API/test/UI files.
- Forbidden actions: hidden autonomy, background mutation, cleanup, push, merge, automatic execution, automatic promotion, and adding Level 11 or extra levels.
- Expected output: a Level 10 closeout with a hard stop and a next-roadmap permission gate.
- Manual check commands:

```bash
cd /home/source/SpiritOS
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_10_closeout_next_roadmap_gate or level_10_production_readiness_checklist or level_9_coordination_dashboard or level_8_closeout_smoke or level_7_closeout_dashboard"
git status -sb
```

- Expected manual check result: tests prove Level 10 closes with no hidden autonomy, no background mutation, no unapproved push/merge/cleanup, and no roadmap beyond Level 10.7.
- Rollback notes: revert the Level 10.7 doc and approved minimal changes.
- Next increment title: None. Stop at Level 10.7 unless the user explicitly asks for a new roadmap.
- Permission gate: explicit user approval is required before any next-roadmap planning or implementation prompt.

## Recommended Next Active Increment

The next active increment should be Level 7.0: Level 7 Autopilot Boundary Contract.

Do not implement 7.1 or beyond until 7.0 is complete, manually checked, and explicitly approved.

## Manual Checks For This Planning Task

```bash
cd /home/source/SpiritOS

git diff --check -- docs/cartographer-level-7-to-10-autopilot-plan.md

grep -n "Level 7: Limited Autopilot\|Level 8: Approved Workflow Runner\|Level 9: Multi-Worker Coordination\|Level 10: Production Operator Mode\|Recommended Next Active Increment" docs/cartographer-level-7-to-10-autopilot-plan.md

PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_6_multi_project_closeout or level_6_cross_repo_dirty_tree or level_6_component_ownership or level_6_cross_project_status_board or level_6_project_registry"

git status -sb
```

Expected outcome:

- diff check has no output.
- grep finds every required roadmap section.
- focused Level 6 baseline still passes.
- git status shows only the new roadmap doc, plus any explicitly justified docs index change if needed.
- no implementation files changed.
