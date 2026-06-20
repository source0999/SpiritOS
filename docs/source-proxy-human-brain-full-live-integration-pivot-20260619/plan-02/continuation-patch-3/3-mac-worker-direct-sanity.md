# Mac Worker Direct Sanity

Direct worker invocation used the synced Mac script at:

`/Users/spiritmac/spiritos-worker/SpiritOS/scripts/mac-worker/spirit_mac_worker.py`

Valid proof:

- `success=true`
- `job_type=mac_isolated_write_proof`
- `write_performed=true`
- `mac_write_performed=true`
- `verified=true`
- `readback_verified=true`
- `rollback_performed=true`
- `rollback_status=cleaned`
- `reason_code=mac_isolated_write_proof_passed`
- proof path under Mac temp root: `/private/var/folders/py/2tb50by14n94wl7b0n_txzsm0000gn/T/spiritos-plan2-mac-write-proof/plan2-mac-write-proof.txt`

Missing trace proof:

- `success=false`
- `error=missing_trace`
- `reason_code=missing_trace_fields`
- `write_performed=false`

Unsafe path proof:

- `success=false`
- `error=safe_path_rejected`
- `reason_code=safe_path_rejected`
- requested path was inside `/Users/spiritmac/spiritos-worker/SpiritOS`
- `write_performed=false`
- `mac_write_performed=false`

This sanity proof is direct worker evidence only; canonical Source Proxy consumption is recorded separately.
