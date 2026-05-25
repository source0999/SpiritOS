# Cartographer Greenlight Readiness Limited Daily-Driver Plan v0.1

status: planning-only

date: 2026-05-24

owner: Britton

## 1. Current State

Cartographer is Live, read-only, and NO-GO from the current `/map` state. This is one plan, not another giant master roadmap. The target is limited daily-driver operator readiness, not full unattended autonomy. The greenlight target is A- for limited supervised daily-driver use.

Current local evidence to preserve:

- Cartographer is not daily-driver-active.
- Plan 11 promotion evidence was review-only.
- Plan 12 added a strict limited activation gate and receipt model.
- No real activation occurred.
- No queue execution, task execution, worker dispatch, approval-token consumption, safe write, commit, push, branch/worktree creation, cleanup, reset, stash, checkout, package/config/env/generated/media changes are authorized by this planning task.
- `/map` should never claim authority it does not actually have.
- The active branch observed during this planning task is `lane/main-cleanup-20260524`.
- The visible tree was already dirty before this plan was written, including Cartographer runtime, tests, `/map`, and unrelated lane files.

Local references inspected for this plan:

- `docs/cartographer-a-grade-daily-driver-activation-pivot-plan-v0.1.md`
- `docs/cartographer-daily-driver-autonomy-roadmap-v0.1.md`
- `docs/cartographer-auto-roadmap-v0.2.md`
- `docs/cartographer-full-auto-master-roadmap-v0.1.md`
- `source_proxy/cartographer/soak_promotion.py`
- `source_proxy/cartographer/level_14_autonomy_runtime.py`
- `source_proxy/cartographer/live_state.py`
- `source_proxy/cartographer/safe_task_queue.py`
- `source_proxy/cartographer/local_commit_gate.py`
- `source_proxy/cartographer/controlled_push_queue.py`
- `source_proxy/api/cartographer.py`
- `src/app/map/page.tsx`
- `src/app/map/cartographer-live-state.ts`
- focused Cartographer tests for live state, queue, commit, push, approval, and Plan 12 gates

## 2. Scope

This plan gets Cartographer from the current `/map` posture toward limited daily-driver operator greenlight readiness by proving these items for Britton:

- dirty tree groups
- protected lane warnings
- active branch and HEAD
- stale state
- queue/action authority
- approval state
- kill switch state
- commit readiness
- push readiness
- receipts/evidence
- demotion path

Cartographer may recommend commit/push timing, but must not execute commit/push without explicit approval and exact gates in a later implementation phase.

## 3. Non-Scope

Full unattended auto-push/self-healing remains out of scope. This plan does not authorize:

- self-approval
- hidden workers
- hidden queue execution
- auto-push
- `git add .`
- broad cleanup
- protected lane mutation without explicit scope
- runtime code edits
- test edits
- app UI edits
- CSS edits
- package installs
- queue mutation
- approval-token consumption
- safe-write execution
- commit
- push
- branch, worktree, stash, reset, clean, checkout, merge, tag, or force push

## 4. Authority Boundary

The readiness target is proposal and decision support first. `/map` may display facts, blockers, and recommendations. It must not imply that a displayed recommendation grants action authority.

Required authority truth:

- visible `/map` authority truth
- known kill switch state
- approval gate truth
- one-task-at-a-time queue recommendation
- supervised limited run rehearsal
- receipt trail
- rollback/demotion path
- final GO/NO-GO decision packet

Passing tests is evidence, not authority. A clean branch is evidence, not authority. A completed plan is evidence, not authority. Only Britton can grant the exact future action authority.

## 5. Stop Conditions

Stop immediately and output a NO-GO packet if any of these appear:

- dirty tree cannot be classified
- active branch or HEAD is unknown
- stale state cannot be measured or cleared
- protected lane warnings are hidden, softened, or treated as approved
- kill switch state is unknown
- approval state is unknown, stale, self-approved, expired, malformed, or too broad
- queue/action authority is ambiguous
- any hidden worker, queue, or background loop appears
- commit recommendation lacks an exact file list
- push recommendation targets `main`, uses force push, pushes tags, merges, or proposes broad git action
- any test required for the increment fails
- `/map` claims authority it does not actually have
- receipts/evidence cannot prove what happened and what did not happen
- rollback or demotion path is missing

## 6. PIVOT Workflow Rules

- Work phase-by-phase.
- Work increment-by-increment.
- Each increment must have its own self-check.
- Do not skip increments.
- Do not jump phases.
- Do not treat passing tests as authority.
- Stop at phase boundaries and output a manual verification block.
- At the end of the whole plan, output a copy-paste new-chat handoff that starts Phase 1 Increment 1.
- Do not self-approve.
- Do not run hidden workers.
- Do not run hidden queue execution.
- Do not auto-push.
- Do not use `git add .`.
- Do not do broad cleanup.
- Do not mutate protected lanes without explicit scope.

## 7. Phase 0: Baseline And Lane Boundary

Purpose: establish the exact repo, branch, HEAD, dirty state, and lane boundary before any readiness implementation begins.

Small increments:

1. Increment 0.1: read active branch, HEAD, status, dirty counts, and untracked files.
2. Increment 0.2: classify protected lane warnings across `source_proxy/`, `src/app/map/`, package/config/env, generated/cache, media, and unrelated lanes.
3. Increment 0.3: mark the baseline stale if any timestamped truth packet is older than the accepted window or if HEAD changes during the phase.

Allowed files:

- read-only whole repo inspection
- future docs-only baseline packet only if Britton approves the exact file

Forbidden files:

- runtime code
- tests
- app UI
- CSS
- package/config/env/generated/media files
- `docs/plan-index.md`
- git index and history

Self-checks Codex can run:

```bash
cd /home/source/SpiritOS
git status --branch --short --untracked-files=normal
git rev-parse HEAD
git branch --show-current
git diff --name-only
git ls-files --others --exclude-standard
```

Manual checks Britton can run:

```bash
cd /home/source/SpiritOS
git status --branch --short --untracked-files=normal
git rev-parse HEAD
git diff --name-only
```

Expected output: a baseline packet that names active branch and HEAD, dirty tree groups, protected lane warnings, stale state, and an initial GO/NO-GO. Expected decision is NO-GO for activation.

Stop conditions: wrong branch, unknown HEAD, unclassified dirty files, protected lane uncertainty, stale truth packet, or any proposed mutation.

GO/NO-GO exit gate: GO only to Phase 1 classification when branch, HEAD, dirty tree groups, protected lane warnings, and stale state are visible. NO-GO for activation remains.

## 8. Phase 1: Dirty Tree Classification And Lane Isolation

Purpose: make Cartographer useful to Britton by grouping dirty work and recommending safe commit groups without staging or committing.

Small increments:

1. Increment 1.1: classify dirty tree groups into Cartographer docs, Cartographer runtime, Cartographer tests, `/map`, package/config/env, generated/cache, media, unrelated active lanes, and unknown.
2. Increment 1.2: identify files that should not be committed together, especially runtime with docs-only planning, tests with unrelated UI work, generated/cache with source, media with code, and protected-lane work without exact approval.
3. Increment 1.3: produce exact-file-list-only commit recommendation packets for safe groups.
4. Increment 1.4: prove no recommendation uses `git add .`, cleanup, stash, reset, checkout, or broad git action.

Allowed files:

- read-only status and diff inspection
- future recommendation docs or API/UI surfaces only after separate Britton approval

Forbidden files:

- generated/cache files
- media files
- package/config/env files
- unrelated lane files
- protected lane files without exact future scope
- git index and history

Self-checks Codex can run:

```bash
cd /home/source/SpiritOS
git status --porcelain=v1 -uall
git diff --name-only
git diff --stat
git diff --check
```

Manual checks Britton can run:

```bash
cd /home/source/SpiritOS
git diff --name-only
git status --branch --short --untracked-files=normal
```

Expected output: dirty tree groups, protected lane blockers, safe commit groups, files that should not be committed together, failed-test blockers, stale state blockers, and exact file list only recommendations.

Stop conditions: any unknown file enters a safe group, protected lane blockers are bypassed, failed tests are ignored, stale state is ignored, or a broad staging command is proposed.

GO/NO-GO exit gate: GO only when Britton can see exact file list recommendations and every excluded file has a reason. NO-GO for commit execution remains until later exact approval.

## 9. Phase 2: Kill Switch, Approval, And Authority Truth

Purpose: make `/map` show the truth about kill switch state, approval state, queue/action authority, and mutation authority before any limited operator run.

Small increments:

1. Increment 2.1: verify truth packet fields for authority, stale state, evidence links, and advisory-only status.
2. Increment 2.2: verify kill switch state is known, visible, and blocking when active or unknown.
3. Increment 2.3: verify approval gate truth: no self-approval, exact approval only, expiration and stale HEAD blockers, exact files, forbidden files, and no token consumption by display.
4. Increment 2.4: verify queue/action authority is one-task-at-a-time and recommendation-only until a future approved rehearsal.

Allowed files:

- read-only inspection of `live_state.py`, `level_14_autonomy_runtime.py`, approval modules, queue modules, `/map` display, and focused tests
- future implementation only after separate exact approval

Forbidden files:

- approval token storage mutation
- approval token consumption
- queue mutation
- task execution
- worker dispatch
- safe write
- commit/push execution

Self-checks Codex can run:

```bash
cd /home/source/SpiritOS
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_live_state.py source_proxy/tests/test_cartographer_approval_token_runtime.py source_proxy/tests/test_cartographer_approval_token_consumption.py source_proxy/tests/test_cartographer_safe_task_queue.py source_proxy/tests/test_cartographer_level_14_autonomy_runtime.py
git diff --check -- source_proxy/cartographer source_proxy/api src/app/map
```

Manual checks Britton can run:

```bash
cd /home/source/SpiritOS
git status --branch --short --untracked-files=normal
```

Britton should also open `/map` and confirm visible authority truth, kill switch state, approval state, queue/action authority, stale state, and NO-GO default.

Expected output: `/map` displays no hidden authority, no self-approval, no hidden workers, no hidden queue execution, known kill switch state, approval gate truth, and a one-task-at-a-time queue recommendation.

Stop conditions: kill switch unknown, approval truth hidden, authority fields contradict runtime gates, `/map` implies action authority, or tests fail.

GO/NO-GO exit gate: GO only when `/map` truth is visible and consistent with runtime gates. NO-GO for real activation remains.

## 10. Phase 3: Commit Recommendation Engine

Purpose: let Cartographer recommend when to commit while blocking commit execution unless Britton later approves the exact commit.

Small increments:

1. Increment 3.1: define commit recommendation inputs: active branch, HEAD, dirty tree groups, protected lane warnings, stale state, approval state, test results, receipt paths, and exact file list.
2. Increment 3.2: define safe commit groups with exact files only.
3. Increment 3.3: define files that should not be committed together.
4. Increment 3.4: define blockers: protected lane blockers, failed-test blockers, stale state blockers, missing receipt blockers, unknown file blockers, and approval blockers.
5. Increment 3.5: prove recommendation output never stages, commits, cleans, stashes, resets, checkouts, merges, tags, or pushes.

Allowed files:

- proposal model and display surfaces only after exact future approval
- focused commit gate tests only after exact future approval

Forbidden files:

- git index
- git history
- generated/cache/media files
- package/config/env files unless explicitly included in a future exact approval
- protected lane mutation

Self-checks Codex can run:

```bash
cd /home/source/SpiritOS
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_local_commit_gate.py
git diff --check -- source_proxy/cartographer/local_commit_gate.py source_proxy/tests/test_cartographer_local_commit_gate.py
```

Manual checks Britton can run:

```bash
cd /home/source/SpiritOS
git diff --name-only
git status --branch --short --untracked-files=normal
```

Expected output: a commit recommendation packet with exact file list only, exact proposed commit message, verification status, blocked files, receipt paths, expected HEAD, branch, stale state, and human approval requirement.

Stop conditions: `git add .`, broad file globs, missing exact file list, protected-lane blocker ignored, failed-test blocker ignored, stale state ignored, or commit execution proposed in this phase.

GO/NO-GO exit gate: GO when Cartographer can recommend a safe commit group and name blockers. NO-GO for commit execution remains until Britton separately approves the exact commit in a later implementation phase.

## 11. Phase 4: Push Recommendation Engine

Purpose: let Cartographer recommend when a future push could be safe while keeping push proposal-only by default.

Small increments:

1. Increment 4.1: define push recommendation inputs: branch, upstream, ahead/behind, exact commit SHA, clean status, exact file lineage, verification receipts, approval state, rollback guidance, and risk.
2. Increment 4.2: block push to `main`, `master`, and `trunk`.
3. Increment 4.3: block force push, tags, merge, broad git action, branch/worktree creation, checkout, reset, stash, clean, and auto-push.
4. Increment 4.4: allow only future human-approved dedicated branch push after exact gates pass.
5. Increment 4.5: require push receipt and rollback guidance before any later promotion discussion.

Allowed files:

- proposal-only push model and tests only after exact future approval
- `/map` display of proposal-only push readiness only after exact future approval

Forbidden files:

- git remote state mutation
- push execution
- push to main
- force push
- tag push
- merge
- broad git action

Self-checks Codex can run:

```bash
cd /home/source/SpiritOS
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_controlled_push_queue.py
git diff --check -- source_proxy/cartographer/controlled_push_queue.py source_proxy/tests/test_cartographer_controlled_push_queue.py
```

Manual checks Britton can run:

```bash
cd /home/source/SpiritOS
git status --branch --short --untracked-files=normal
git log --oneline --decorate -5
```

Expected output: a push recommendation packet that is proposal-only, blocks protected base branches, blocks force push, blocks tags, blocks merge, blocks auto-push, requires exact commit SHA, requires clean status, and requires a human-approved dedicated branch.

Stop conditions: auto-push appears, push to main appears, force push appears, tag push appears, merge appears, broad git action appears, or exact approval is missing.

GO/NO-GO exit gate: GO only for proposal-only push guidance. NO-GO for push execution remains.

## 12. Phase 5: Supervised Limited Operator Rehearsal

Purpose: prove limited operator readiness through a supervised limited operator rehearsal without full unattended autonomy.

Small increments:

1. Increment 5.1: choose exactly one low-risk task class and one exact task. Default recommendation is a proposal-only health or dirty worktree summary task.
2. Increment 5.2: verify approval gate truth, expected HEAD, dirty tree expectation, exact allowed files, exact forbidden files, kill switch known, and no active kill switch.
3. Increment 5.3: rehearse one-task-at-a-time queue selection with no hidden workers and no hidden background loop.
4. Increment 5.4: produce a receipt trail that records what was recommended, what was blocked, what was performed by Britton, and what Cartographer did not do.
5. Increment 5.5: stop after one task and require Britton manual review before any next task.

Allowed files:

- future approved receipt/evidence docs only if Britton approves exact files
- future approved safe task proposal surfaces only if Britton approves exact files

Forbidden files:

- queue execution without approval
- task execution without approval
- worker dispatch
- command execution
- safe write
- commit
- push
- background scheduler

Self-checks Codex can run:

```bash
cd /home/source/SpiritOS
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_safe_task_queue.py source_proxy/tests/test_cartographer_level_14_autonomy_runtime.py source_proxy/tests/test_cartographer_daily_driver_soak.py
git diff --check -- source_proxy/cartographer source_proxy/tests
```

Manual checks Britton can run:

```bash
cd /home/source/SpiritOS
git status --branch --short --untracked-files=normal
```

Britton should confirm the selected task, the exact approval state, kill switch state, receipt path, and that no second task starts automatically.

Expected output: one supervised limited run rehearsal packet with queue recommendation, approval truth, kill switch truth, receipt trail, and a hard stop after one task.

Stop conditions: more than one task selected, hidden worker appears, queue executes without approval, kill switch unknown, approval missing, receipt missing, or task tries to write/commit/push.

GO/NO-GO exit gate: GO only if one supervised task can be recommended and fully receipted with no hidden execution. NO-GO for daily-driver activation remains until final packet.

## 13. Phase 6: Receipts, Demotion, And Rollback Proof

Purpose: prove that every readiness claim has evidence and that demotion/rollback is clear before greenlight.

Small increments:

1. Increment 6.1: collect receipt/evidence links for branch/HEAD, dirty tree groups, protected lane warnings, stale state, approval state, kill switch state, queue recommendation, commit recommendation, push recommendation, and rehearsal.
2. Increment 6.2: define demotion path: engage kill switch, demote to supervised-only, preserve receipts, stop queue/action authority, and open an incident plan.
3. Increment 6.3: define rollback guidance for docs-only, source/test, commit, and push scenarios without executing rollback.
4. Increment 6.4: verify receipts show no hidden workers, no hidden queue execution, no self-approval, no auto-push, no commit execution, and no push execution unless a future exact approval exists.

Allowed files:

- future approved receipt/evidence docs only after exact approval
- read-only inspection of receipt/evidence browser and tests

Forbidden files:

- receipt deletion
- evidence deletion
- rollback execution
- cleanup
- reset
- stash
- checkout
- force push

Self-checks Codex can run:

```bash
cd /home/source/SpiritOS
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_final_proof_stage_5_rollback.py source_proxy/tests/test_cartographer_final_proof_stage_6_dashboard.py source_proxy/tests/test_cartographer_final_proof_stage_7_readiness.py
git diff --check
```

Manual checks Britton can run:

```bash
cd /home/source/SpiritOS
git status --branch --short --untracked-files=normal
```

Britton should inspect `/map` receipt/evidence display and confirm the demotion path is visible.

Expected output: receipt trail, rollback guidance, demotion path, and evidence that Cartographer remains bounded.

Stop conditions: missing receipt, unverifiable evidence, rollback guidance implies force push or destructive git, demotion path missing, or `/map` hides NO-GO facts.

GO/NO-GO exit gate: GO only when receipts/evidence and demotion/rollback proof are complete. NO-GO if any action cannot be proven or safely demoted.

## 14. Phase 7: Final Greenlight Decision Packet

Purpose: produce the final GO/NO-GO decision packet for A- limited supervised daily-driver readiness.

Small increments:

1. Increment 7.1: assemble facts: active branch, HEAD, dirty tree groups, protected lane warnings, stale state, queue/action authority, approval state, kill switch state, commit readiness, push readiness, receipts/evidence, and demotion path.
2. Increment 7.2: score the A- target for limited daily-driver readiness: UI truth, authority truth, safety gates, recommendation quality, rehearsal proof, receipts, and rollback/demotion.
3. Increment 7.3: state the exact remaining NO-GO blockers.
4. Increment 7.4: output final GO/NO-GO with allowed next action and forbidden actions.

Allowed files:

- future final decision packet docs only if Britton approves exact file

Forbidden files:

- runtime code
- tests
- UI
- CSS
- package/config/env/generated/media
- git mutation
- queue/action mutation

Self-checks Codex can run:

```bash
cd /home/source/SpiritOS
git status --branch --short --untracked-files=normal
git diff --check
```

Manual checks Britton can run:

```bash
cd /home/source/SpiritOS
git status --branch --short --untracked-files=normal
```

Britton should compare the final packet to `/map`, receipts, and terminal output.

Expected output: final GO/NO-GO decision packet. A GO can only mean limited supervised daily-driver operator readiness. It cannot grant full unattended autonomy, auto-push, self-healing, or hidden execution.

Stop conditions: evidence mismatch, stale HEAD, hidden authority, missing kill switch state, missing approval truth, missing demotion path, failed tests, or broad git recommendation.

GO/NO-GO exit gate: GO only when Britton accepts the packet. Otherwise NO-GO with exact blockers and next limited increment.

## 15. Manual Verification Blocks

Phase 0 manual block:

```bash
cd /home/source/SpiritOS
git status --branch --short --untracked-files=normal
git rev-parse HEAD
git branch --show-current
git diff --name-only
```

Phase 1 manual block:

```bash
cd /home/source/SpiritOS
git status --branch --short --untracked-files=normal
git diff --name-only
git diff --stat
git diff --check
```

Phase 2 manual block:

```bash
cd /home/source/SpiritOS
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_live_state.py source_proxy/tests/test_cartographer_approval_token_runtime.py source_proxy/tests/test_cartographer_approval_token_consumption.py source_proxy/tests/test_cartographer_safe_task_queue.py source_proxy/tests/test_cartographer_level_14_autonomy_runtime.py
git status --branch --short --untracked-files=normal
```

Phase 3 manual block:

```bash
cd /home/source/SpiritOS
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_local_commit_gate.py
git status --branch --short --untracked-files=normal
```

Phase 4 manual block:

```bash
cd /home/source/SpiritOS
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_controlled_push_queue.py
git status --branch --short --untracked-files=normal
```

Phase 5 manual block:

```bash
cd /home/source/SpiritOS
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_safe_task_queue.py source_proxy/tests/test_cartographer_level_14_autonomy_runtime.py source_proxy/tests/test_cartographer_daily_driver_soak.py
git status --branch --short --untracked-files=normal
```

Phase 6 manual block:

```bash
cd /home/source/SpiritOS
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_final_proof_stage_5_rollback.py source_proxy/tests/test_cartographer_final_proof_stage_6_dashboard.py source_proxy/tests/test_cartographer_final_proof_stage_7_readiness.py
git status --branch --short --untracked-files=normal
```

Phase 7 manual block:

```bash
cd /home/source/SpiritOS
git status --branch --short --untracked-files=normal
git diff --check
```

## 16. New Chat Handoff

Copy-paste handoff:

```text
cd /home/source/SpiritOS

Start Cartographer Greenlight Readiness Limited Daily-Driver Plan v0.1.

Begin Phase 1 Increment 1 only: Dirty Tree Classification And Lane Isolation.

Use PIVOT:
- Work only this increment.
- Classify dirty tree groups for Britton.
- Preserve active branch and HEAD.
- Identify protected lane warnings.
- Identify stale state blockers.
- Produce exact-file-list-only safe commit recommendation candidates.
- Name files that should not be committed together.
- Do not stage, commit, push, branch, worktree, stash, reset, clean, checkout, merge, tag, force push, safe-write, consume approvals, mutate queues, start workers, edit runtime code, edit tests, edit UI, edit CSS, edit package/config/env/generated/media, or edit docs/plan-index.md.
- No git add .
- No auto-push.
- No self-approval.
- No hidden workers.
- No hidden queue execution.

Allowed output: a Phase 1 Increment 1 classification packet and manual verification block.
Stop after the increment and ask Britton before Phase 1 Increment 2.
```
