# Increment 0.3.1: Identify Active Cartographer Soak Locations

PLAN: Plan 0, Isolated Proxy Lane Baseline

PHASE: Phase 0.3, Cartographer Soak-Protection Declaration

INCREMENT: Increment 0.3.1, Identify Active Cartographer Soak Locations

Objective:
Identify Cartographer soak-related locations by read-only inspection so Plan 0 can explicitly avoid them.

Isolated proxy lane scope:
unified-proxy-coding-design-plan-0

Allowed files or file zones:
- Read-only path/process inspection.
- Evidence files inside /home/source/SpiritOS/docs/evidence/unified-proxy-coding-design-plan-0/

Forbidden files, paths, systems, and actions:
- Production source files.
- Source Proxy runtime files.
- Cartographer runtime files.
- Cartographer soak logs.
- Scout soak logs.
- Cartographer live evidence.
- Map state.
- Git mutations, including branch, worktree, stash, reset, clean, checkout, stage, commit, and push.
- Provider/model calls.
- Apply or execute-approved routes.
- Background worker or queue mutation.

Exact work performed:
- Used read-only `find` and `ps` inspections.
- `rg` was attempted first per standard search preference but is not installed in this environment, so `find` was used as fallback.
- No soak files were opened for content editing or modified.

Required tests or inspections:
```text
$ ps -ef | grep -Ei 'cartographer|soak|scout' | grep -v grep
root 2884 2705 ... /usr/local/bin/python3.12 /usr/local/bin/uvicorn scout.main:app --host 0.0.0.0 --port 8077
```

Identified protected Cartographer/soak-related locations:
- /home/source/SpiritOS/.codex-cartographer-next-3001.log
- /home/source/SpiritOS/.codex-cartographer-next-3001.err.log
- /home/source/SpiritOS/docs/cartographer-live-evidence/
- /home/source/SpiritOS/docs/cartographer-live-receipts/
- /home/source/SpiritOS/source_proxy/cartographer/
- /home/source/SpiritOS/source_proxy/cartographer/soak-logs/
- /home/source/SpiritOS/source_proxy/tests/test_cartographer_daily_driver_soak.py
- /home/source/SpiritOS/source_proxy/tests/test_cartographer_final_proof_stage_2_soak.py
- /home/source/SpiritOS/src/app/map/cartographer-live-state.ts
- /home/source/SpiritOS/src/app/map/cartographer-stop-controls.ts
- /home/source/SpiritOS/src/app/map/cartographer-approval-token.ts
- /home/source/SpiritOS/src/app/map/cartographer-queue-status.ts
- /home/source/SpiritOS/src/app/map/cartographer-receipt-evidence.ts
- /home/source/SpiritOS/src/app/map/cartographer-workflow-status.ts
- /home/source/SpiritOS/data/cartographer-v1-freeze/
- /home/source/SpiritOS/data/cartographer-v1-proof-gates/
- /home/source/SpiritOS/data/cartographer-v1-diagnostics/
- /home/source/SpiritOS/data/cartographer_git_approvals.audit.jsonl

Also identified protected Scout soak/runtime-adjacent locations:
- /home/source/SpiritOS/.codex-scout-*.log
- /home/source/SpiritOS/.codex-scout-*.err.log
- /home/source/SpiritOS/scout/
- /home/source/SpiritOS/scout/soak-logs/
- /home/source/SpiritOS/scout/data/

Required manual validation:
- Identified paths are specific and outside the Plan 0 evidence root.
- Cartographer soak logs, live evidence, receipts, runtime, queues, and map state are protected.
- Running Scout service was observed and not disturbed.

Required evidence artifact:
This file.

Stop conditions:
- Any need to write to soak logs or runtime state.
- Any need to stop, restart, signal, or otherwise disturb active processes.
- Any unclear Cartographer path boundary.

Rollback or recovery note:
No rollback action is authorized. If soak paths become unclear, stop and report NEEDS OPERATOR REVIEW.

GO / NO-GO exit rule:
GO only if active/protected Cartographer soak locations are identified without touching them.

GO / NO-GO:
GO for Increment 0.3.1.

Next authorized increment only:
Plan 0, Phase 0.3, Increment 0.3.2: Mark Cartographer Soak Logs/Live Evidence/Runtime State As Forbidden.

Cartographer soak dependency status:
SAFE WHILE SOAK RUNS.
