# Mac Search And Check Regression

All probes were invoked through `source_proxy.decision.mac_integration.run_mac_worker_for_task`.

System status:

- Mode: `mac_system_status`
- Status: `INTEGRATED_LIVE`
- Task: `task_d82b6de2411b`
- Job: `mac-mac_system_status-3752dc76700a`
- Worker success: `true`
- Result includes supported job types.

Repository search:

- Mode: `mac_search_packet`
- Status: `INTEGRATED_LIVE`
- Task: `task_6d683bab6fb2`
- Job: `mac-mac_search_packet-7629534d9d30`
- Worker success: `true`
- Candidate files returned.

Safe checks:

- `git rev-parse HEAD`: `INTEGRATED_LIVE`, task `task_818a84eeaf9b`, stdout `ac1c6ddf7cf2d71739801a13c46a3f1f3426ea26`
- `git status --branch --short --untracked-files=normal`: `INTEGRATED_LIVE`, task `task_32a3f034e8e8`, stdout included `?? .spiritos-backups/` and `?? scripts/mac-worker/`

This proves the Mac worker is not write-only; search/check routes remain live and consumed.
