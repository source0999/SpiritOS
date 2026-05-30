# Cartographer Final Proof Stage 3 Hidden Mutation And Dirty Worktree Drills Dry Run Closeout

status: implemented-hidden-mutation-dirty-worktree-drills-dry-run-only

Status date: 2026-05-22

## Authority Statement

Final Proof Stage 3 creates hidden mutation and dirty worktree drill validation only.

It does not create dirty files, clean dirty files, stash changes, checkout files, overwrite files, delete files, mutate the worktree, execute local commands, write evidence, write receipts, create branches, create worktrees, commit, push, merge, automatically promote actions, self-approve, grant limited unattended operation, grant full auto, or enable autonomy.

## Source-of-Truth Inputs

- `docs/cartographer-final-proof-stage-2-24-to-72-hour-soak-dry-run-closeout.md`
- `docs/cartographer-level-11-to-14-runtime-upgrade-plan.md`
- `docs/cartographer-level-11-to-14-autonomous-operator-roadmap.md`

## Allowed Files Touched

- `source_proxy/cartographer/final_proof_stage_3_hidden_mutation.py`
- `source_proxy/tests/test_cartographer_final_proof_stage_3_hidden_mutation.py`
- `docs/cartographer-final-proof-stage-3-hidden-mutation-dirty-worktree-drills-dry-run-closeout.md`

## Proof Coverage

- HEAD changes block.
- Unexpected dirty worktree files block.
- Unexpected generated files block.
- Protected paths block.
- Protected lane touches block.
- Unexplained mutation blocks as hidden mutation suspicion.
- Cleanup, stash, and checkout attempts block.
- Passing the drill does not grant full auto or limited unattended operation.

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
  source_proxy/tests/test_cartographer_final_proof_stage_2_soak.py \
  source_proxy/tests/test_cartographer_final_proof_stage_3_hidden_mutation.py

git diff --check

grep -n "does not create dirty files\|Unexplained mutation blocks\|Cleanup, stash, and checkout attempts block\|Final Proof Stage 4" \
  docs/cartographer-final-proof-stage-3-hidden-mutation-dirty-worktree-drills-dry-run-closeout.md

git status --branch --short
```

## Expected Outcome

- Focused Level 11 through Level 14 and Final Proof Stage 1 through 3 tests pass.
- `git diff --check` passes.
- The hidden mutation drill model remains dry-run only.
- HEAD changes, unexpected dirty files, unexpected generated files, protected paths, protected lanes, unexplained mutation, cleanup, stash, and checkout attempts block.
- Writes, local execution, branch/worktree authority, commit/push/merge, cleanup, self-approval, limited unattended operation, full auto, and autonomy remain locked.

## Rollback Notes

Rollback is limited to removing:

- `source_proxy/cartographer/final_proof_stage_3_hidden_mutation.py`
- `source_proxy/tests/test_cartographer_final_proof_stage_3_hidden_mutation.py`
- `docs/cartographer-final-proof-stage-3-hidden-mutation-dirty-worktree-drills-dry-run-closeout.md`

No source rollback, API rollback, service rollback, UI rollback, package rollback, verifier rollback, stress-lane rollback, branch cleanup, worktree cleanup, stash cleanup, commit cleanup, push cleanup, or merge cleanup should be needed.

## Stop Conditions

Stop if Final Proof Stage 3 requires creating dirty files, cleaning, stashing, checkout, overwriting, deleting, worktree mutation, local command execution, file writes, receipt writes, evidence writes, branch/worktree authority, commit/push/merge authority, limited unattended operation, full auto, or protected-lane mutation.

## Next Increment

Final Proof Stage 4: Approval Expiration And Kill Switch Drills Dry Run
