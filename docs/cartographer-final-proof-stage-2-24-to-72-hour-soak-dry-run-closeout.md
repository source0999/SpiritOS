# Cartographer Final Proof Stage 2 24 To 72 Hour Soak Dry Run Closeout

status: implemented-soak-dry-run-only

Status date: 2026-05-22

## Authority Statement

Final Proof Stage 2 creates a 24 to 72 hour soak dry-run validator only.

It does not start a 24 hour or 72 hour process, schedule background jobs, execute queue items, automatically select tasks, run monitors, write evidence, write receipts, write files, execute local commands, mutate the worktree, create branches, create worktrees, checkout, stash, clean up, commit, push, merge, automatically promote actions, self-approve, grant limited unattended operation, grant full auto, or enable autonomy.

## Source-of-Truth Inputs

- `docs/cartographer-final-proof-stage-1-real-task-gauntlet-dry-run-closeout.md`
- `docs/cartographer-level-11-to-14-runtime-upgrade-plan.md`
- `docs/cartographer-level-11-to-14-autonomous-operator-roadmap.md`

## Allowed Files Touched

- `source_proxy/cartographer/final_proof_stage_2_soak.py`
- `source_proxy/tests/test_cartographer_final_proof_stage_2_soak.py`
- `docs/cartographer-final-proof-stage-2-24-to-72-hour-soak-dry-run-closeout.md`

## Proof Coverage

- Soak duration must be inside the 24 to 72 hour window.
- Soak samples must exist and be ordered.
- Duplicate samples block.
- Kill switch checks are required.
- Hidden mutation blocks.
- HEAD changes block.
- Unexplained dirty worktree state blocks.
- Manual intervention requirements block final readiness.
- Passing the soak dry run does not grant full auto or limited unattended operation.

## Protected Lanes

- proxy UI makeover.
- `/coding` UI implementation wiring.
- Source Proxy stress testing.
- Codex adapter lane.
- verifier lane.
- test runner lane.

## Why This Does Not Interfere With Parallel Work

This increment does not touch src/**, `/coding` UI paths, proxy UI makeover files, Source Proxy stress docs, Codex adapter files, verifier files, long-running task files, package files, API routes, service builders, Next config, or app routing.

It is a direct module and a direct unit test. It is not wired into `source_proxy/api/cartographer.py` or `source_proxy/cartographer/service.py`.

## Manual Checks

```bash
cd /home/source/SpiritOS

git status --branch --short
git rev-parse HEAD
git diff --stat

PYTHONPATH=. .venv/bin/python -m pytest \
  source_proxy/tests/test_cartographer_level_11_runtime_baseline.py \
  source_proxy/tests/test_cartographer_level_11_approval_token.py \
  source_proxy/tests/test_cartographer_level_11_event_ledger.py \
  source_proxy/tests/test_cartographer_level_11_receipt_write_dry_run.py \
  source_proxy/tests/test_cartographer_level_11_evidence_write_dry_run.py \
  source_proxy/tests/test_cartographer_level_11_remaining_boundaries.py \
  source_proxy/tests/test_cartographer_level_12_workflow_runtime.py \
  source_proxy/tests/test_cartographer_level_13_worker_runtime.py \
  source_proxy/tests/test_cartographer_level_14_autonomy_runtime.py \
  source_proxy/tests/test_cartographer_final_proof_stage_1_gauntlet.py \
  source_proxy/tests/test_cartographer_final_proof_stage_2_soak.py

git diff --check

grep -n "does not start a 24 hour or 72 hour process\|Hidden mutation blocks\|Passing the soak dry run does not grant full auto\|Final Proof Stage 3" \
  docs/cartographer-final-proof-stage-2-24-to-72-hour-soak-dry-run-closeout.md

git status --branch --short
```

## Expected Outcome

- Focused Level 11 through Level 14 and Final Proof Stage 1 through 2 tests pass.
- `git diff --check` passes.
- The soak model remains dry-run only.
- Hidden mutation, HEAD changes, unexplained dirty worktree state, missing kill switch checks, and invalid soak duration block.
- Queue execution, automatic task selection, writes, local execution, worker orchestration, branch/worktree authority, commit/push/merge, cleanup, automatic promotion, self-approval, limited unattended operation, full auto, and autonomy remain locked.

## Rollback Notes

Rollback is limited to removing:

- `source_proxy/cartographer/final_proof_stage_2_soak.py`
- `source_proxy/tests/test_cartographer_final_proof_stage_2_soak.py`
- `docs/cartographer-final-proof-stage-2-24-to-72-hour-soak-dry-run-closeout.md`

No source rollback, API rollback, service rollback, UI rollback, package rollback, verifier rollback, stress-lane rollback, branch cleanup, worktree cleanup, stash cleanup, commit cleanup, push cleanup, or merge cleanup should be needed.

## Stop Conditions

Stop if Final Proof Stage 2 requires a real long-running process, background scheduling, queue execution, automatic task selection, monitor runtime, notification sending, file writes, receipt writes, evidence writes, local command execution, worker orchestration, branch/worktree authority, commit/push/merge authority, stash, checkout, cleanup, limited unattended operation, full auto, or protected-lane mutation.

## Next Increment

Final Proof Stage 3: Hidden Mutation And Dirty Worktree Drills Dry Run
