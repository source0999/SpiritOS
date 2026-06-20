# Canonical Mac Write Proof

Canonical success path:

- Status: `INTEGRATED_LIVE`
- Task: `task_1eabe04a1e1c`
- Job: `mac-mac_isolated_write_proof-c4e0123b2c13`
- Trace: `trace_8aa6ed97183047b2`
- Invocation event: `invocation_64f50cd5188a47ec`
- Consumer: `cartographer_mac_assignment_consumer`
- Worker success: `true`
- Reason code: `mac_isolated_write_proof_passed`
- `mac_write_performed=true`
- `verified=true`
- `readback_verified=true`
- `rollback_performed=true`
- `rollback_status=cleaned`

Canonical unsafe path:

- Status: `NEEDS_FIX`
- Task: `task_4e443dda3b2b`
- Job: `mac-mac_isolated_write_proof-8bb9d520735c`
- Reason code: `safe_path_rejected`
- Worker success: `false`
- `mac_write_performed=false`
- Task status: `failed_needs_human`

The unsafe path is intentionally not a GO case. It proves the live path fails closed.
