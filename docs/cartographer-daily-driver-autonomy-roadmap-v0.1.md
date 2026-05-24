# Cartographer Daily Driver Autonomy Roadmap v0.1

## Status

- status: master-roadmap-doc-only
- owner: Britton
- current posture: dry-run/no-go, not daily-driver autonomous yet
- purpose: sequential roadmap from current Cartographer state to daily-driver autonomous Cartographer

## Blunt Current-State Summary

Cartographer has strong dry-run safety proof. The existing live-operation package closed as documentation-only and no-go for limited unattended operation. Full auto is not granted. The Level 14 autonomy runtime remains dry-run only: it does not execute queue items, auto-select tasks, write files, write receipts, execute commands, commit, push, self-approve, or enable autonomy.

The missing parts are live runtime authority, durable state, approval token runtime, first safe write class, command verification runner, workflow runner, safe queue execution, worker orchestration, local commit gate, push gate, dashboard control, and soak promotion.

This roadmap replaces scattered no-go loops with one sequential path into real bounded autonomy. It is still a planning artifact only. It does not implement runtime modules, add routes, wire `/map`, touch `/coding`, touch Scout, touch Source Proxy stress files, stage files, commit, push, create branches, create worktrees, stash, clean, delete, or enable autonomy.

## Definition Of Daily-Driver Autonomous Cartographer

Daily-driver autonomous Cartographer can inspect live repo/project state, maintain a durable queue of approved safe tasks, auto-select allowed tasks under trust-tier policy, execute bounded workflows, perform approved safe writes, run approved verification commands, produce receipts, coordinate workers, recover/stop cleanly, and eventually create local commits or controlled branch pushes under explicit policy.

Daily-driver autonomous does not mean unbounded full auto. It means bounded, useful, recurring autonomy with proof, receipts, stop controls, and escalation.

It must remain able to say no. Missing approval, stale HEAD, unexpected dirty state, protected paths, broad scope, malformed task records, failed verification, unclear ownership, worker conflict, kill switch activation, timeout, or operator stop must block action and produce a human-readable reason.

## Global Execution Protocol

Every plan has phases. Every phase has small increments. Codex/Cursor must complete increments one at a time.

For each increment, Codex/Cursor must:

- state current plan, phase, and increment
- state exact allowed files
- state exact forbidden files
- implement only that increment
- run that increment's manual check itself
- stop if check fails
- output expected result and actual result
- move to the next increment inside the same phase only if the check passes
- at the end of a phase, output one manual check block for Britton
- ask permission before starting the next phase
- never infer approval from previous success

Global forbidden behavior for all plans unless a later phase explicitly approves it: broad full auto, self-approval, hidden background loops, protected-lane mutation, branch/worktree creation, `git add .`, broad shell execution, destructive git commands, cleanup, deletion, stash, force push, package install, environment mutation, secret access, source writes outside approved scope, and treating UI display as authority.

## Manual Check Examples

Use exact commands for the current increment. Examples:

```bash
cd /home/source/SpiritOS
git status --branch --short
git diff --check
git diff --stat
git diff --name-only
PYTHONPATH=. .venv/bin/python -m pytest <exact test file>
curl -k -s <exact endpoint> | jq .
```

## Plan 0: Roadmap Consolidation And Authority Reset

### Purpose

Write this master roadmap, stop scattered no-go loops, define the new source of truth.

### Entry Criteria

- Existing Cartographer docs can be read.
- Current posture is dry-run/no-go.
- Allowed file is exactly `docs/cartographer-daily-driver-autonomy-roadmap-v0.1.md`.

### Exit Criteria

- This roadmap exists.
- It clearly says daily-driver autonomy is not enabled yet.
- It lists Plans 1 through 12 in order.
- Manual checks prove only this roadmap file changed for this task.

### Phases

- Phase 0.1: Create roadmap doc
- Phase 0.2: Validate roadmap is implementation-ready

### Small Increments

- 0.1.1: Read existing closeout and runtime roadmap docs.
- 0.1.2: Create `docs/cartographer-daily-driver-autonomy-roadmap-v0.1.md`.
- 0.1.3: Include all required plans, phase gates, stop conditions, manual checks, and permission phrases.
- 0.2.1: Run file existence, grep, whitespace, diff stat, and status checks.
- 0.2.2: Confirm no runtime, test, UI, config, Scout, Source Proxy, package, branch, commit, push, stash, cleanup, or generated-file work happened.

### Likely Files Touched Later

- None in Plan 0 beyond this roadmap.

### Manual Checks

```bash
cd /home/source/SpiritOS
test -f docs/cartographer-daily-driver-autonomy-roadmap-v0.1.md
grep -nE "Plan 1|Plan 2|Plan 3|Plan 4|Plan 5|Plan 6|Plan 7|Plan 8|Plan 9|Plan 10|Plan 11|Plan 12|daily-driver autonomous|approval token|safe write|verification command|workflow runner|safe task queue|auto-selection|local commit|controlled push|soak|permission phrase" docs/cartographer-daily-driver-autonomy-roadmap-v0.1.md
git diff --check -- docs/cartographer-daily-driver-autonomy-roadmap-v0.1.md
git diff --stat -- docs/cartographer-daily-driver-autonomy-roadmap-v0.1.md
git diff --name-only -- docs/cartographer-daily-driver-autonomy-roadmap-v0.1.md
git status --branch --short
```

### Stop Conditions

- Any file other than this roadmap is edited for Plan 0.
- The roadmap grants autonomy, limited unattended operation, full auto, command execution, write authority, commit authority, push authority, or self-approval.
- The roadmap loops back into documentation-only no-go without a path to bounded live autonomy.

### Next Permission Phrase

Approve Cartographer Daily Driver Roadmap Plan 1 Phase 1 Live State Collector.

## Plan 1: Live Cartographer State And Protected-Lane Baseline

### Purpose

Give Cartographer a live source of truth before granting action.

### Entry Criteria

- Plan 0 is accepted by Britton.
- Current repo state and dirty work are acknowledged.
- No action authority is granted.

### Exit Criteria

- Cartographer can report live repo/project state.
- It can classify protected-lane risk as blocked, caution, or clear.
- `/map` can display read-only live state without executable controls.

### Phases

- Phase 1.1: Python live repo state collector
- Phase 1.2: API endpoint for live state
- Phase 1.3: `/map` read-only live state display

### Small Increments

- 1.1.1: Add collector model for branch, HEAD, dirty files, untracked files, and unknown files.
- 1.1.2: Add protected-lane classifier for `/coding`, package/config, source_proxy, Scout, generated files, and current plan scope.
- 1.1.3: Add tests for blocked/caution/clear recommendations.
- 1.2.1: Add read-only endpoint returning collector output and recommendation.
- 1.2.2: Add endpoint tests for clean, dirty, protected, and unknown file states.
- 1.3.1: Wire `/map` to display live state only.
- 1.3.2: Verify no buttons execute writes, commands, queue items, commits, or pushes.

### Likely Files Touched Later

- `source_proxy/cartographer/**`
- `source_proxy/api/**`
- exact focused `source_proxy/tests/**`
- `src/app/map/**`
- exact focused frontend tests if approved

### Manual Checks

```bash
cd /home/source/SpiritOS
git status --branch --short
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_live_state.py
curl -k -s http://localhost:3000/api/cartographer/live-state | jq .
git diff --name-only
```

Manual checks must verify branch, HEAD, dirty files, untracked files, protected lane matches, `/coding` dirty state, package/config dirty state, source_proxy dirty state, unknown files, and blocked/caution/clear recommendation.

### Stop Conditions

- Collector writes files or normalizes dirty state.
- Endpoint executes commands beyond approved read-only state collection.
- `/map` gains executable controls.
- Protected-lane dirty state is hidden or reclassified as approved.

### Next Permission Phrase

Approve Cartographer Daily Driver Roadmap Plan 1 Phase 2 Live State API.

## Plan 2: Approval Token Runtime

### Purpose

Create real human approval tokens that Cartographer can validate but not create for itself.

### Entry Criteria

- Plan 1 live state baseline works.
- Cartographer can read current HEAD and protected-lane state.
- No write authority exists yet.

### Exit Criteria

- Approval token schema exists.
- Validation fails closed for unsafe, stale, malformed, or self-approved tokens.
- Cartographer can preview token validity but cannot mint approval for itself.

### Phases

- Phase 2.1: Token model and schema
- Phase 2.2: Token validation fail-closed tests
- Phase 2.3: Token preview API
- Phase 2.4: Token storage or durable record decision

### Small Increments

- 2.1.1: Define token id, operator id, action class, trust tier, exact allowed files, exact forbidden files, expected HEAD, expires at, created at, used at, revoked, rollback, and verification fields.
- 2.1.2: Define self-approval barrier and token provenance fields.
- 2.2.1: Test missing, expired, stale HEAD, broad scope, protected path, self-approved, wrong action class, wrong trust tier, and malformed approval tokens.
- 2.3.1: Add preview-only API that returns eligible or blocked with reasons.
- 2.4.1: Decide durable storage path or external source of approval records before live consumption.

### Likely Files Touched Later

- `source_proxy/cartographer/**`
- `source_proxy/api/**`
- exact focused `source_proxy/tests/**`
- later durable data path only if explicitly approved

### Manual Checks

```bash
cd /home/source/SpiritOS
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_approval_token.py
curl -k -s http://localhost:3000/api/cartographer/approval-token/preview | jq .
git status --branch --short
```

### Stop Conditions

- Cartographer creates its own human approval token.
- Invalid token validates.
- Token grants broader scope than exact approved files.
- Token display is treated as action authority.

### Next Permission Phrase

Approve Cartographer Daily Driver Roadmap Plan 2 Phase 2 Approval Validation.

## Plan 3: First Safe Write Class

### Purpose

Make Cartographer actually write something safe and useful.

### Entry Criteria

- Plan 2 approval token runtime validates fail-closed.
- Live state baseline can detect HEAD, dirty tree, and protected lanes.
- Britton explicitly approves the first write class.

### Exit Criteria

- Cartographer can perform one approved safe write.
- The write is limited to approved docs/evidence/receipt paths.
- All invalid writes fail closed and produce receipts or blocked reasons.

### Phases

- Phase 3.1: Safe write negative tests
- Phase 3.2: Approved docs/evidence/receipt write service
- Phase 3.3: API endpoint for one approved safe write
- Phase 3.4: First live approved safe write proof

### Small Increments

- 3.1.1: Add tests blocking source code, app code, package/config/env, `/coding`, Scout, generated files, protected paths, broad globs, path traversal, and unapproved docs.
- 3.2.1: Implement write service for initial allowed write class only.
- 3.2.2: Allowed write class is `docs/cartographer-live-evidence/**`, `docs/cartographer-live-receipts/**`, and exact approved docs paths only.
- 3.3.1: Add endpoint for one approved safe write with valid token.
- 3.4.1: Perform first live approved safe write proof and record exact before/after state.

### Likely Files Touched Later

- `source_proxy/cartographer/**`
- `source_proxy/api/**`
- exact focused `source_proxy/tests/**`
- `docs/cartographer-live-evidence/**`
- `docs/cartographer-live-receipts/**`
- exact approved docs paths only

### Manual Checks

```bash
cd /home/source/SpiritOS
git status --branch --short
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_safe_write.py
git diff --stat
git diff --name-only
curl -k -s http://localhost:3000/api/cartographer/safe-write | jq .
```

### Stop Conditions

- Any source code, app code, package/config/env, `/coding`, Scout, generated, or protected path is writable.
- Safe write succeeds without valid human approval token.
- Write service stages, commits, pushes, cleans, stashes, or deletes files.

### Next Permission Phrase

Approve Cartographer Daily Driver Roadmap Plan 3 Phase 2 Safe Write Service.

## Plan 4: Controlled Verification Command Runner

### Purpose

Let Cartographer verify its own approved safe work with exact command allowlists.

### Entry Criteria

- Plan 3 safe write class works.
- Approval token can authorize verification action class.
- Command execution remains disabled except this exact runner.

### Exit Criteria

- Cartographer can run approved verification commands only.
- Verification results attach to safe write receipts.
- Forbidden shell forms and mutating commands fail closed.

### Phases

- Phase 4.1: Exact argv command allowlist
- Phase 4.2: Verification runner tests
- Phase 4.3: Verification API
- Phase 4.4: Verification receipt attached to safe write

### Small Increments

- 4.1.1: Represent allowed commands as exact argv arrays, not shell strings.
- 4.1.2: Initial allowed commands: `git diff --check`, `git status --short`, exact pytest command for approved test file, exact npm test command for approved test file.
- 4.2.1: Block shell strings, `bash -c`, pipes, redirects, `rm`, `git clean`, `git reset --hard`, `git checkout`, `git push`, and package install.
- 4.3.1: Add verification API with timeout, cwd, env, stdout/stderr capture, and blocked reason.
- 4.4.1: Attach verification command, exit code, output summary, and timestamp to safe write receipt.

### Likely Files Touched Later

- `source_proxy/cartographer/**`
- `source_proxy/api/**`
- exact focused `source_proxy/tests/**`
- receipt/evidence paths from Plan 3 only

### Manual Checks

```bash
cd /home/source/SpiritOS
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_verification_runner.py
curl -k -s http://localhost:3000/api/cartographer/verification/run | jq .
git status --branch --short
```

### Stop Conditions

- Runner accepts shell strings.
- Runner accepts destructive, broad, network, install, cleanup, checkout, reset, push, or hidden commands.
- Verification mutates files outside the approved command's expected behavior.

### Next Permission Phrase

Approve Cartographer Daily Driver Roadmap Plan 4 Phase 2 Verification Runner Tests.

## Plan 5: Durable Workflow Runner v1

### Purpose

Turn one-off approved actions into visible, stoppable, resumable workflows.

### Entry Criteria

- Plan 3 safe writes and Plan 4 verification command runner exist.
- Approval tokens can bind to workflow steps.
- Durable storage decision is made.

### Exit Criteria

- Workflow state and event ledger are durable.
- Pause, cancel, timeout, retry, and blocker states work.
- First workflow can write safe docs evidence and verify it.

### Phases

- Phase 5.1: Workflow state model
- Phase 5.2: Event ledger
- Phase 5.3: Pause/cancel/timeout/retry controls
- Phase 5.4: First workflow: safe docs evidence write then verify

### Small Increments

- 5.1.1: Model run id, step id, approval token, allowed files, forbidden files, status, blocker reason, verification result, rollback reference, receipt path, and closeout.
- 5.2.1: Add append-only event ledger for workflow created, step started, step blocked, step completed, paused, cancelled, timed out, retried, verified, and closed out.
- 5.3.1: Add pause/cancel/timeout/retry controls with bounded retry counts.
- 5.4.1: Implement first workflow: approved safe docs evidence write then approved verification.

### Likely Files Touched Later

- `source_proxy/cartographer/**`
- `source_proxy/api/**`
- exact focused `source_proxy/tests/**`
- `docs/cartographer-live-evidence/**`
- `docs/cartographer-live-receipts/**`

### Manual Checks

```bash
cd /home/source/SpiritOS
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_workflow_runner.py
curl -k -s http://localhost:3000/api/cartographer/workflows/<run_id> | jq .
git status --branch --short
```

### Stop Conditions

- Workflow runs without explicit approval token.
- Event ledger can be silently rewritten.
- Cancelled workflow continues work.
- Retry becomes unbounded or hidden.

### Next Permission Phrase

Approve Cartographer Daily Driver Roadmap Plan 5 Phase 2 Event Ledger.

## Plan 6: Approved Safe Task Queue And Auto-Selection

### Purpose

First real autonomy. Cartographer can select exactly one approved safe task and execute it.

### Entry Criteria

- Plan 5 workflow runner is durable and stoppable.
- Safe write and verification classes are proven.
- Kill switch policy exists.

### Exit Criteria

- Durable safe task queue exists.
- Cartographer can auto-select one eligible approved safe task.
- `run-next` executes one task only and stops.

### Phases

- Phase 6.1: Queue model and durable task records
- Phase 6.2: Trust-tier safe task classes
- Phase 6.3: run-next one-task-only endpoint
- Phase 6.4: Kill switch drill
- Phase 6.5: First auto-selected safe task run

### Small Increments

- 6.1.1: Model durable task id, class, trust tier, approval token, allowed files, forbidden files, status, attempts, created at, selected at, completed at, and blocked reason.
- 6.2.1: Add initial task classes: `safe_docs_evidence_maintenance`, `safe_receipt_closeout`, `safe_project_health_snapshot`, `safe_blueprint_refresh_proposal_only`, `safe_stale_plan_summary_proposal_only`.
- 6.3.1: Add `run-next` endpoint that selects exactly one eligible task per invocation.
- 6.4.1: Drill kill switch before selection, after selection, and before write/verification.
- 6.5.1: Run first auto-selected safe task and produce receipt.

### Likely Files Touched Later

- `source_proxy/cartographer/**`
- `source_proxy/api/**`
- exact focused `source_proxy/tests/**`
- `docs/cartographer-live-evidence/**`
- `docs/cartographer-live-receipts/**`
- exact future queue storage path if approved

### Manual Checks

```bash
cd /home/source/SpiritOS
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_safe_task_queue.py
curl -k -s http://localhost:3000/api/cartographer/queue/run-next | jq .
git status --branch --short
```

Rules: one task per invocation, exact trust tier, exact approval token, no source writes, no self-approval, no background loops at first.

### Stop Conditions

- Queue item executes without valid token.
- Auto-selection picks more than one task.
- Background loop starts.
- Source, package, config, `/coding`, Scout, protected, or generated files are writable.

### Next Permission Phrase

Approve Cartographer Daily Driver Roadmap Plan 6 Phase 2 Trust Tier Safe Task Classes.

## Plan 7: Operator Dashboard And /map Command Center

### Purpose

Make `/map` usable as the Cartographer cockpit, not a static wall of confusing widgets.

### Entry Criteria

- Plans 1 through 6 expose live state, approvals, queue, workflow, receipts, and stop controls through safe APIs.
- Dashboard work is explicitly approved.
- UI display is not treated as authority.

### Exit Criteria

- `/map` shows what Cartographer is doing, what is blocked, what is approved, what ran, and what Britton needs to verify.
- Stop controls and kill switch state are visible and usable under approved policy.
- Receipt/evidence browser supports operator review.

### Phases

- Phase 7.1: `/map` information architecture reset
- Phase 7.2: Live state panel
- Phase 7.3: Approval token panel
- Phase 7.4: Queue panel
- Phase 7.5: Workflow run panel
- Phase 7.6: Kill switch and stop controls
- Phase 7.7: Receipt/evidence browser

### Small Increments

- 7.1.1: Replace confusing static layout with simple operational sections.
- 7.2.1: Show branch, HEAD, dirty state, protected-lane state, and recommendation.
- 7.3.1: Show token validity and blocked reasons without minting approvals.
- 7.4.1: Show queue status and one-task run eligibility.
- 7.5.1: Show active and recent workflow runs with step status.
- 7.6.1: Add kill switch and stop controls only where backend policy already exists.
- 7.7.1: Add receipt/evidence browser for approved docs artifacts.

### Likely Files Touched Later

- `src/app/map/**`
- approved frontend components only
- exact focused frontend tests
- approved API route clients only

### Manual Checks

```bash
cd /home/source/SpiritOS
git diff --check
npm test -- --runTestsByPath <exact approved map test file>
curl -k -s http://localhost:3000/api/cartographer/live-state | jq .
git status --branch --short
```

Rules: The page should be simple, functional, readable, and operational. No pretty glass polish. No confusing modal-heavy UI. It must show what Cartographer is doing, what is blocked, what is approved, what ran, and what Britton needs to verify.

### Stop Conditions

- Dashboard grants authority without backend approval.
- UI includes broad full-auto, self-approval, broad write, broad command, commit, push, checkout, reset, clean, stash, or destructive controls.
- UI hides blocker reasons or protected-lane state.

### Next Permission Phrase

Approve Cartographer Daily Driver Roadmap Plan 7 Phase 2 Live State Panel.

## Plan 8: Worker Orchestration And Handoff Packets

### Purpose

Coordinate Codex, Scout, Proxy, Designer, Blueprinter, and sub-cartographers without file conflicts.

### Entry Criteria

- Queue and workflow runner exist.
- `/map` can show worker and blocker state.
- No branch/worktree creation is approved yet.

### Exit Criteria

- Worker registry, ownership zones, locks, conflict detection, handoff packets, stale-worker proposals, and one-worker proof exist.
- Cartographer can assign one worker to one task in one file-zone without conflict.

### Phases

- Phase 8.1: Worker registry
- Phase 8.2: File ownership and locks
- Phase 8.3: Conflict detection
- Phase 8.4: Handoff packet format
- Phase 8.5: Stale worker closeout proposal
- Phase 8.6: One worker, one task, one file-zone proof

### Small Increments

- 8.1.1: Define worker id, role, active state, stale state, current task, allowed files, forbidden files, and heartbeat.
- 8.2.1: Add ownership and lock records for exact file zones.
- 8.3.1: Block worker dispatch on dirty conflicts, overlapping file ownership, protected lanes, or stale lock ambiguity.
- 8.4.1: Define handoff packet with task, scope, expected files, checks, receipts, and closeout.
- 8.5.1: Produce stale worker closeout proposal only, not automatic cleanup.
- 8.6.1: Run one worker, one task, one file-zone proof.

### Likely Files Touched Later

- `source_proxy/cartographer/**`
- `source_proxy/api/**`
- exact focused `source_proxy/tests/**`
- `/map` worker panel only if approved
- exact worker packet storage path if approved

### Manual Checks

```bash
cd /home/source/SpiritOS
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_worker_orchestration.py
curl -k -s http://localhost:3000/api/cartographer/workers | jq .
git status --branch --short
```

No branch/worktree creation yet unless later approved.

### Stop Conditions

- Cartographer overwrites worker files.
- Worker conflicts are treated as warnings when they should block.
- Stale worker cleanup runs automatically.
- Branch/worktree creation happens without a later explicit approval.

### Next Permission Phrase

Approve Cartographer Daily Driver Roadmap Plan 8 Phase 2 File Ownership And Locks.

## Plan 9: Local Commit Gate

### Purpose

Daily-driver autonomy needs a way to close safe work locally instead of leaving endless dirty files.

### Entry Criteria

- Safe task queue and workflow receipts are durable.
- Worker ownership can prove exact file scope.
- Britton approves local commit gate planning and implementation.

### Exit Criteria

- Commit proposal model exists.
- Human-approved local commit works.
- Auto local commit is limited to safe docs/evidence/receipt classes only if promoted.

### Phases

- Phase 9.1: Commit proposal model
- Phase 9.2: Commit proposal API
- Phase 9.3: Human-approved local commit
- Phase 9.4: Auto local commit for safe docs/evidence/receipt classes only

### Small Increments

- 9.1.1: Model exact file list, exact commit message, verification result, rollback command, HEAD, status, task ids, receipt paths, and approval token.
- 9.2.1: Add proposal API that cannot run `git add` or commit.
- 9.3.1: Add human-approved local commit using exact file list only.
- 9.4.1: Add auto local commit only for safe docs/evidence/receipt classes, after soak promotion.

### Likely Files Touched Later

- `source_proxy/cartographer/**`
- `source_proxy/api/**`
- exact focused `source_proxy/tests/**`
- safe docs/evidence/receipt files already produced by earlier plans

### Manual Checks

```bash
cd /home/source/SpiritOS
git status --branch --short
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_local_commit_gate.py
curl -k -s http://localhost:3000/api/cartographer/commit/proposal | jq .
git log --oneline -1
```

Rules: No `git add .`. No source files in first auto-commit tier. Exact file list required. Exact commit message required. Verification must pass. Rollback command must be recorded. No push.

### Stop Conditions

- Broad staging occurs.
- Source files enter first auto-commit tier.
- Commit runs without exact approval and passing verification.
- Push, merge, checkout, reset, clean, stash, or delete occurs.

### Next Permission Phrase

Approve Cartographer Daily Driver Roadmap Plan 9 Phase 2 Commit Proposal API.

## Plan 10: Controlled Push Queue

### Purpose

Prepare pushes safely without granting reckless main branch mutation.

### Entry Criteria

- Local commit gate is proven.
- Repo state can prove exact commit SHA and clean status.
- Britton explicitly approves push queue planning and implementation.

### Exit Criteria

- Push proposal only mode exists.
- Human-approved push to dedicated branch works.
- Push receipt and rollback guidance are produced.
- Decision gate decides whether isolated branch auto-push is ever allowed.

### Phases

- Phase 10.1: Push proposal only
- Phase 10.2: Human-approved push to dedicated branch
- Phase 10.3: Push receipt and rollback guidance
- Phase 10.4: Decision gate for whether isolated branch auto-push is ever allowed

### Small Increments

- 10.1.1: Model remote, branch, commit SHA, clean status, exact file lineage, verification, rollback guidance, and approval token.
- 10.1.2: Add push proposal API with no push authority.
- 10.2.1: Add human-approved push to dedicated branch only.
- 10.3.1: Write push receipt and rollback guidance.
- 10.4.1: Decide if auto-push to isolated branch is ever allowed.

### Likely Files Touched Later

- `source_proxy/cartographer/**`
- `source_proxy/api/**`
- exact focused `source_proxy/tests/**`
- receipt paths from earlier plans

### Manual Checks

```bash
cd /home/source/SpiritOS
git status --branch --short
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_controlled_push_queue.py
curl -k -s http://localhost:3000/api/cartographer/push/proposal | jq .
git remote -v
```

Rules: No push to main at first. No force push. No tags. No broad push. No push without exact branch, remote, commit SHA, and clean status.

### Stop Conditions

- Push to main is allowed in first tier.
- Force push, tag push, broad push, or push without exact SHA is allowed.
- Push occurs without human approval before explicit isolated branch auto-push promotion.

### Next Permission Phrase

Approve Cartographer Daily Driver Roadmap Plan 10 Phase 2 Human Approved Dedicated Branch Push.

## Plan 11: Daily Driver Soak And Promotion

### Purpose

Prove Cartographer can run as a real daily-driver operator.

### Entry Criteria

- Plans 1 through 10 are complete or explicitly scoped to the promotion tier under review.
- Kill switch, stop controls, receipts, rollback guidance, and operator dashboard exist.
- Britton approves soak start.

### Exit Criteria

- 10-task supervised run passes.
- 24-hour soak passes.
- 72-hour soak passes.
- Kill switch and rollback drills pass.
- Promotion decision is recorded.

### Phases

- Phase 11.1: 10-task supervised run
- Phase 11.2: 24-hour soak
- Phase 11.3: 72-hour soak
- Phase 11.4: Kill switch and rollback drills
- Phase 11.5: Promotion decision

### Small Increments

- 11.1.1: Run 10 supervised approved safe tasks with receipts.
- 11.2.1: Run 24-hour soak with bounded invocations and no hidden loops.
- 11.3.1: Run 72-hour soak with drift, protected-lane, and queue checks.
- 11.4.1: Drill kill switch before selection, mid-workflow, after verification, and before commit/push.
- 11.5.1: Record promotion decision with exact tier and allowed actions.

### Likely Files Touched Later

- soak evidence and receipt paths only
- exact focused runtime/test/dashboard files only if a bug fix is separately approved

### Manual Checks

```bash
cd /home/source/SpiritOS
git status --branch --short
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_daily_driver_soak.py
curl -k -s http://localhost:3000/api/cartographer/soak/status | jq .
git diff --stat
```

Promotion tiers:

- Tier 1: auto safe docs/evidence/receipt tasks, human-gated commit/push
- Tier 2: auto safe docs/evidence/receipt tasks plus auto local commits, human-gated push
- Tier 3: auto safe docs/evidence/receipt tasks plus auto local commits and auto push to isolated branch only

No broad full auto until a later roadmap.

### Stop Conditions

- Hidden background loop starts.
- Cartographer runs outside approved tier.
- Kill switch fails.
- Receipts are missing, misleading, or not durable.
- Protected-lane mutation occurs.

### Next Permission Phrase

Approve Cartographer Daily Driver Roadmap Plan 11 Phase 2 Twenty Four Hour Soak.

## Plan 12: Broader Autonomy Expansion

### Purpose

After daily-driver proof, expand task classes carefully.

### Entry Criteria

- Plans 1 through 11 pass.
- Promotion tier is explicit.
- Britton approves broader expansion.

### Exit Criteria

- New task classes are proposed, tested, and gated.
- New trust-tier decision gate blocks premature expansion.
- Future work remains bounded and reversible.

### Phases

- Phase 12.1: Safe test maintenance proposals
- Phase 12.2: Safe docs/runbook updates
- Phase 12.3: Safe blueprint refresh writes
- Phase 12.4: Controlled multi-worker branch workflow
- Phase 12.5: New trust-tier decision gate

### Small Increments

- 12.1.1: Propose safe test maintenance only; no source/test writes until separately approved.
- 12.2.1: Add safe docs/runbook update class with exact paths and receipts.
- 12.3.1: Add safe blueprint refresh writes after proposal-only proof.
- 12.4.1: Design controlled multi-worker branch workflow with explicit branch/worktree approval.
- 12.5.1: Create new trust-tier decision gate for any expansion beyond daily-driver scope.

### Likely Files Touched Later

- Exact future task-class files after approval.
- Exact docs/runbook/blueprint paths after approval.
- Exact runtime, API, test, and dashboard files only after approval.

### Manual Checks

```bash
cd /home/source/SpiritOS
git status --branch --short
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest <exact approved expansion test file>
curl -k -s <exact approved expansion endpoint> | jq .
git diff --name-only
```

This plan must stay future-gated and not be implemented until Plans 1 through 11 pass.

### Stop Conditions

- Plan 12 starts before Plans 1 through 11 pass.
- Expansion bypasses trust-tier review.
- Source/test/branch/multi-worker authority is granted implicitly.
- Broad full auto is granted.

### Next Permission Phrase

Approve Cartographer Daily Driver Roadmap Plan 12 Phase 1 Safe Test Maintenance Proposals.

## Closeout

Current task complete when this roadmap exists and passes manual checks.

Next implementation step: Plan 1 Phase 1, Live Cartographer State Collector.

Exact next approval phrase: Approve Cartographer Daily Driver Roadmap Plan 1 Phase 1 Live State Collector.
