# Cartographer 10-Task Supervised Run 01 Clean Baseline v0.1

Date: 2026-05-25

Branch: `main`

HEAD: `c943051f1c08d0fd245ecd4c3415cc138c5cc7cc`

origin/main: `c943051f1c08d0fd245ecd4c3415cc138c5cc7cc`

Task: Clean-main baseline receipt.

Result: PASS.

## Precheck Evidence

```text
git status --branch --short
## main...origin/main

git rev-parse HEAD
c943051f1c08d0fd245ecd4c3415cc138c5cc7cc

git rev-parse origin/main
c943051f1c08d0fd245ecd4c3415cc138c5cc7cc

git diff --check
passed, no output

npm test -- run src/app/map/__tests__/map-display-shell.test.ts
11 passed

.venv/bin/python -m pytest -q source_proxy/tests/test_cartographer_safe_task_queue.py source_proxy/tests/test_cartographer_workflow_runner.py source_proxy/tests/test_cartographer_daily_driver_soak.py source_proxy/tests/test_cartographer_trust_tier_decision_gate.py source_proxy/tests/test_cartographer_approval_token_consumption.py source_proxy/tests/test_cartographer_safe_write.py
90 passed
```

## Baseline State

```text
main_matches_origin_main: true
dirty_tree_clean_at_start: true
activation_started: false
runtime_authority_changed: false
safe_write_enabled: false
queue_execution_enabled: false
task_execution_enabled: false
worker_execution_enabled: false
approval_token_consumption_enabled: false
push_enabled: false
next_task_auto_started: false
hidden_continuation_started: false
```

## Boundary

This receipt records the clean baseline for task 01 of the supervised run. It grants no activation, queue, worker, safe-write, approval-token, commit, push, or runtime authority.

## Rollback

Remove only this exact file after explicit Britton approval:

```text
docs/cartographer-live-receipts/cartographer-main-10-task-supervised-run-01-clean-baseline-v0.1.md
```
