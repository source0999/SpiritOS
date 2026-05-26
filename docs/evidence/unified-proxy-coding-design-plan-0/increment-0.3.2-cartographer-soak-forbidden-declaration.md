# Increment 0.3.2: Mark Cartographer Soak Logs/Live Evidence/Runtime State As Forbidden

PLAN: Plan 0, Isolated Proxy Lane Baseline

PHASE: Phase 0.3, Cartographer Soak-Protection Declaration

INCREMENT: Increment 0.3.2, Mark Cartographer Soak Logs/Live Evidence/Runtime State As Forbidden

Objective:
Declare Cartographer soak logs, live evidence, runtime state, queues, receipts, and map surfaces forbidden for Plan 0 work.

Isolated proxy lane scope:
unified-proxy-coding-design-plan-0

Allowed files or file zones:
- Evidence files inside /home/source/SpiritOS/docs/evidence/unified-proxy-coding-design-plan-0/
- Read-only inspection only when needed.

Forbidden files, paths, systems, and actions:
- /home/source/SpiritOS/.codex-cartographer-next-3001.log
- /home/source/SpiritOS/.codex-cartographer-next-3001.err.log
- /home/source/SpiritOS/docs/cartographer-live-evidence/
- /home/source/SpiritOS/docs/cartographer-live-receipts/
- /home/source/SpiritOS/source_proxy/cartographer/
- /home/source/SpiritOS/source_proxy/cartographer/soak-logs/
- /home/source/SpiritOS/source_proxy/tests/test_cartographer_daily_driver_soak.py
- /home/source/SpiritOS/source_proxy/tests/test_cartographer_final_proof_stage_2_soak.py
- /home/source/SpiritOS/src/app/map/cartographer-*.ts
- /home/source/SpiritOS/data/cartographer-v1-freeze/
- /home/source/SpiritOS/data/cartographer-v1-proof-gates/
- /home/source/SpiritOS/data/cartographer-v1-diagnostics/
- /home/source/SpiritOS/data/cartographer_git_approvals.audit.jsonl
- /home/source/SpiritOS/scout/soak-logs/
- /home/source/SpiritOS/scout/data/
- /home/source/SpiritOS/.codex-scout-*.log
- /home/source/SpiritOS/.codex-scout-*.err.log
- Production Source Proxy runtime state.
- Production map state.
- Background workers and queues.
- Git mutations, including branch, worktree, stash, reset, clean, checkout, stage, commit, and push.
- Provider/model calls.
- Apply or execute-approved routes.

Exact work performed:
- Converted the read-only location findings from Increment 0.3.1 into a forbidden-path declaration.
- No Cartographer, Scout, runtime, map, queue, or soak artifact was edited.

Required tests or inspections:
- Manual review of Increment 0.3.1 identified locations.
- Confirmed this declaration is written only inside the authorized evidence root.

Required manual validation:
- Cartographer soak logs are forbidden.
- Cartographer live evidence and receipts are forbidden.
- Cartographer runtime state and queue surfaces are forbidden.
- Map state and Source Proxy runtime state are forbidden.
- Scout soak logs and data are forbidden.

Required evidence artifact:
This file.

Stop conditions:
- Any need to modify forbidden paths.
- Any ambiguity about whether a path is runtime state.
- Any need to run soak-mutating tests.

Rollback or recovery note:
No rollback action is authorized. If a future increment would require touching a forbidden path, stop and report NEEDS OPERATOR REVIEW.

GO / NO-GO exit rule:
GO only if forbidden Cartographer/Scout/shared-state paths are explicit and no forbidden path was touched.

GO / NO-GO:
GO for Increment 0.3.2.

Next authorized increment only:
Plan 0, Phase 0.4, Increment 0.4.1: Classify Dirty Files As Owned/Unowned/Unknown Without Edits.

Cartographer soak dependency status:
SAFE WHILE SOAK RUNS.
