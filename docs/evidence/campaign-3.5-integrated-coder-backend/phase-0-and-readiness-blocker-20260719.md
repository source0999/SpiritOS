# Campaign 3.5 — Phase 0 and readiness blocker receipt

## Scope and identity

- Execution worktree: `/home/source/SpiritOS-campaign-3-5-execution-20260719`
- Execution branch: `codex/campaign-3-5-execution-20260719`
- Planning base: `b8a33a3990fbc2f410e451ef306be5dd8373c5c4`
- Corrected Campaign 3 base: `74ac367faf9a72c652061a5482c0180bb0b0c844`
- Benchmark import repair commit: `d30b909b5a904461d9bbe244ad7e6b77be952ef7`

The execution repository was rebuilt as an independent single-branch clone because the SMB source object store failed strict Git pack integrity. The rebuilt repository passed `git fsck --no-reflogs --full --strict`.

## Immutable benchmark preflight

`python3 scripts/validate-campaign-3-5-benchmark.py` passed after restoring the ten CRLF-preserved definition files directly from the immutable v1.1 ZIP. The archive SHA-256 is `a1c7e98c0ff5cf85ad829350fac08a59e695a1101979b37eefdd02a61a531818`; its 100 tasks, distributions, JSON/JSONL equality, schemas, scoring, and core-30 selection passed. The repair changed no semantic content: Git reported no difference when end-of-line whitespace was ignored.

## Isolated production-path smoke attempt

An isolated backend on `127.0.0.1:8788` and HTTPS frontend on `127.0.0.1:3002` were launched from the execution worktree. Both process CWDs were verified as that worktree.

- The canonical frontend operator-session route rejected an unsafe 0755 task-local state directory, then accepted the same request after its directory was restricted to 0700.
- The canonical frontend reset route issued a signed server assertion and the backend accepted the selected LumaCart target-plugin identity.
- The reset receipt was `reset_verified`, with `clean_verified: true`, a zero-file fixture, and source head `d30b909b5a904461d9bbe244ad7e6b77be952ef7`.
- A durable task (`task_62fa3e5789ac`) and canonical coding run (`coding-run-a87a707a9d0e4f5e82cc347297d25e54`) were created. The context-broker output was persisted before advance.
- The first advance truthfully blocked before a model call or fixture mutation. Its durable diagnostic was initially `architect_llm_blocked`; the underlying cause was `gate_missing` for `.gate/state.json` in the isolated execution worktree.

## Diagnostic propagation repair and retest

The generic diagnostic prefix could obscure a more specific Architect policy denial even though the task record retained that specific reason. The repair now preserves the structured Architect reason before the generic operational context. Its focused regression suite passed (14 tests), as did the immutable benchmark validator.

An isolated, actual Source Proxy backend process was then restarted from the execution worktree with a fresh task database. The same selected LumaCart task advanced only as far as the external model-call gate and returned `status: blocked`, `reason_code: architect_gate_missing`, and the same reason in its diagnostic envelope. The runtime process and task-local state were removed after the retest. This did not call a model, create a diff, mutate the fixture, issue approval, or execute an apply.

No model invocation, diff proposal, approval issuance, apply, reviewer result, verifier result, final receipt, or completion claim occurred. The failed task remains a truthful pre-apply block only.

## Blocking conditions

1. Production model calls invoke `central_gate_check("model_call")`. The execution worktree has no configured gate state. The only existing external gate is already running a different increment (`evaluation-round`) and does not authorize `model_call` for Campaign 3.5. Its runbook explicitly prohibits Codex from approving or starting an increment. Creating or redirecting a gate approval would be an unauthorized bypass.
2. `benchmarks/coder-backend-100/v1.1/trace-event-contract-map.json` is `PLANNED_PENDING_PRODUCTION_EVENT_DISCOVERY` and has an empty `mappings` array. The immutable benchmark requires a complete, semantically reviewed production-event map before any core-30 or full-100 run. Therefore the independent oracle and trace-to-claim reconciliation cannot yet be valid.

These are integration/readiness blockers, not failed benchmark tasks. The 30-task core stage and 100-task full stage were not started, so no score, pass count, or completion has been inferred.

## Guardrails preserved

- Campaign 4 state remains `PAUSED_FOR_CAMPAIGN_3_5_BACKEND_PROOF`; no Campaign 4 implementation or resume action occurred.
- The benchmark ZIP and its validated definitions remain byte-identical to the immutable import.
- Private oracle, hidden-test, seed, and credential values were not written to this receipt.
- The isolated service logs, operator cookie/session, task database, generated frontend state, and test secret are task-local runtime state and are removed during cleanup.

## Current terminal assessment

`CAMPAIGN_3_5_BLOCKED_INTEGRATION_INCOMPLETE`
