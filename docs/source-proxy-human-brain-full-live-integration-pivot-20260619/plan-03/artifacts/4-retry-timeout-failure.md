# Stage 4 Retry, Timeout, And Failure

Result: `INTEGRATED_LIVE`.

Implementation:
- `PLAN3_FAILURE_CLASSES`
- `record_plan3_failure_attempt`

Failure classes:
- `policy_blocked`
- `blocked_human`
- `blocked_env`
- `worker_unavailable`
- `provider_unavailable`
- `model_timeout`
- `model_failed`
- `verifier_failed`
- `repair_failed`
- `unsafe_path_rejected`
- `unsupported_job_type`
- `validation_failed`
- `unknown_error`

Retry proof:
- task: `task_d8d08a4b6385`
- trace: `trace_393ed0cf0d1140de`
- failure class: `model_timeout`
- max_attempts: 2
- attempt_count after proof: 2
- terminal status: `failed_needs_human`
- causal events include: `retry`, `failure`

Raw evidence:
- `/home/source/spiritos-evidence/plan-03/plan3-disposable-proof.json`
