# Increment 1.6.1 API Status Truth

Date: 2026-05-28

## Inspection summary

Inspected:

- `src/lib/mac-worker/types.ts`
- `src/lib/mac-worker/registry.ts`
- `src/app/api/coding/mac-worker/route.ts`
- `src/app/api/coding/mac-worker/__tests__/route.test.ts`

Finding:

- The API already exposed `online`, `worker_available`, `last_job_type`, `last_success`, `result_summary`, `error`, and `supported_job_types`.
- `repo_present` was only nested under a `system_status` `last_result`.
- A blocked safe check was reported as `last_success:false`, but the registry also derived `online:false` and `worker_available:false` from last success, which conflated node reachability with job outcome.

## Changes made

Updated `src/lib/mac-worker/types.ts` and `src/lib/mac-worker/registry.ts` so status now exposes:

- `online`
- `worker_available`
- `repo_present`
- `last_job_type`
- `last_success`
- `result_summary`
- `error`
- `supported_job_types`
- `last_reason_code`
- `blocked_command`
- `safe_checks_blocked`

The registry now keeps the last observed `repo_present` value from `system_status` and keeps `online:true` / `worker_available:true` when the worker returns a structured blocked safe-check result.

Updated `src/app/api/coding/mac-worker/__tests__/route.test.ts` to assert the new status truth fields.

## Validation commands run

```bash
npx --no-install vitest run src/app/api/coding/mac-worker/__tests__/route.test.ts src/lib/mac-worker/__tests__/contract.test.ts --reporter=dot
npx --no-install tsc --noEmit --pretty false
curl -sk https://127.0.0.1:3000/api/coding/mac-worker
curl -sk -X POST https://127.0.0.1:3000/api/coding/mac-worker \
  -H 'content-type: application/json' \
  --data '{"job_type":"system_status","input":{"repo_path":"/Users/spiritmac/spiritos-worker/SpiritOS"}}'
curl -sk -X POST https://127.0.0.1:3000/api/coding/mac-worker \
  -H 'content-type: application/json' \
  --data '{"job_type":"run_safe_check","input":{"repo_path":"/Users/spiritmac/spiritos-worker/SpiritOS","check_command":"git pull"}}'
```

## Validation evidence

### Focused tests

```text
Test Files  2 passed (2)
Tests  7 passed (7)
```

### TypeScript

```text
passed with no output
```

### Live GET status after server reload

```json
{"ok":true,"status":{"node_id":"spirit-mac-mini","label":"Mac Mini","hostname":"spirit-mac-mini.local","ssh_alias":"spirit-mac-mini","role":"macos-worker","online":false,"worker_available":false,"repo_present":null,"supported_job_types":["repo_context_search","source_proxy_context_discovery","trial_context_assist","scout_research_packet","browser_design_check","run_safe_check","system_status"],"last_job_type":null,"last_used_at":null,"last_success":null,"result_summary":"No Mac worker job recorded in this server process","error":null,"last_reason_code":null,"blocked_command":null,"safe_checks_blocked":false}}
```

### Live API status after `system_status`

Key status fields:

```json
{"online":true,"worker_available":true,"repo_present":true,"last_job_type":"system_status","last_success":true,"result_summary":"Mac worker status returned","error":null,"safe_checks_blocked":false}
```

### Live API status after blocked `git pull`

Key status fields:

```json
{"online":true,"worker_available":true,"repo_present":true,"last_job_type":"run_safe_check","last_success":false,"result_summary":"check_command is not allowlisted: git pull","error":"check_command is not allowlisted: git pull","last_reason_code":"safe_check_command_not_allowlisted","blocked_command":"git pull","safe_checks_blocked":true}
```

## Result

Increment 1.6.1 is complete.

Required inspection and checks were run directly.

Evidence was written to this file.

GO to the next authorized increment: Increment 1.6.2, ensure `/coding` Mac Mini worker display is honest.
