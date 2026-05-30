# Increment 1.4.3 Safe Command Allowlist

Date: 2026-05-28

## Inspection summary

Files inspected:

- `scripts/mac-worker/spirit_mac_worker.py`
- `scripts/mac-worker/spirit-mac-worker.mjs`
- `src/lib/mac-worker/types.ts`
- `src/lib/mac-worker/contract.ts`
- `src/lib/mac-worker/client.ts`
- `src/lib/mac-worker/registry.ts`
- `src/app/api/coding/mac-worker/route.ts`
- `src/lib/mac-worker/__tests__/contract.test.ts`
- `src/app/api/coding/mac-worker/__tests__/route.test.ts`

Finding:

- Python worker already allowlisted only `git status --branch --short --untracked-files=normal` and `git diff --check`, but blocked failures were generic.
- Node worker mirror allowed `npm test`, which is broader than the requested hardening list.
- Blocked results did not expose `reason_code` and `blocked_command`.

## Changes made

Updated `scripts/mac-worker/spirit_mac_worker.py`:

- Added exact safe command allowlist:
  - `git status --branch --short --untracked-files=normal`
  - `git diff --check`
  - `git rev-parse HEAD`
  - `git branch --show-current`
  - `python3 --version`
  - `node --version`
  - `npm --version`
  - `npx --no-install tsc --noEmit --pretty false`
- Added structured blocked safe-check result with:
  - `success:false`
  - `error`
  - `reason_code`
  - `blocked_command`
  - `recommended_checks`

Updated `scripts/mac-worker/spirit-mac-worker.mjs`:

- Mirrored the same exact safe command allowlist.
- Removed broad `npm test` allowance.
- Avoided shell parsing by executing allowlisted argv arrays with `execFile`.
- Added structured blocked safe-check result.

Updated `src/lib/mac-worker/__tests__/contract.test.ts`:

- Added test coverage proving structured blocked safe-check failures are preserved by normalization.

Synced only the updated worker scripts to the Mac overlay at:

```text
/Users/spiritmac/spiritos-worker/SpiritOS/scripts/mac-worker/
```

## Validation commands run

```bash
npx --no-install vitest run src/lib/mac-worker/__tests__/contract.test.ts --reporter=dot
python3 -m py_compile scripts/mac-worker/spirit_mac_worker.py
node --check scripts/mac-worker/spirit-mac-worker.mjs
curl -sk -X POST https://127.0.0.1:3000/api/coding/mac-worker \
  -H 'content-type: application/json' \
  --data '{"job_type":"run_safe_check","input":{"repo_path":"/Users/spiritmac/spiritos-worker/SpiritOS","check_command":"rm -rf ."}}'
```

## Validation evidence

### Contract test

```text
Test Files  1 passed (1)
Tests  4 passed (4)
```

### Python compile

```text
passed with no output
```

### Node syntax check

```text
passed with no output
```

### Blocked unsafe command

```json
{"ok":false,"result":{"job_id":"run_safe_check-1779995141946","job_type":"run_safe_check","input":{"repo_path":"/Users/spiritmac/spiritos-worker/SpiritOS","check_command":"rm -rf ."},"node_id":"spirit-mac-mini","started_at":"2026-05-28T19:05:42.000Z","completed_at":"2026-05-28T19:05:42.000Z","success":false,"result":{"reason_code":"safe_check_command_not_allowlisted","blocked_command":"rm -rf .","recommended_checks":["git status --branch --short --untracked-files=normal","git diff --check","git rev-parse HEAD","git branch --show-current"]},"stdout":"{\"job_id\": \"run_safe_check-1779995141946\", \"job_type\": \"run_safe_check\", \"input\": {\"repo_path\": \"/Users/spiritmac/spiritos-worker/SpiritOS\", \"check_command\": \"rm -rf .\"}, \"node_id\": \"spirit-mac-mini\", \"started_at\": \"2026-05-28T19:05:42.000Z\", \"completed_at\": \"2026-05-28T19:05:42.000Z\", \"success\": false, \"result\": {\"reason_code\": \"safe_check_command_not_allowlisted\", \"blocked_command\": \"rm -rf .\", \"recommended_checks\": [\"git status --branch --short --untracked-files=normal\", \"git diff --check\", \"git rev-parse HEAD\", \"git branch --show-current\"]}, \"stdout\": \"\", \"stderr\": \"\", \"error\": \"check_command is not allowlisted: rm -rf .\", \"duration_ms\": 0, \"artifacts\": [], \"candidate_files\": [], \"recommended_checks\": [\"git status --branch --short --untracked-files=normal\", \"git diff --check\", \"git rev-parse HEAD\", \"git branch --show-current\"]}\n","stderr":"","error":"check_command is not allowlisted: rm -rf .","duration_ms":0,"artifacts":[],"candidate_files":[],"recommended_checks":["git status --branch --short --untracked-files=normal","git diff --check","git rev-parse HEAD","git branch --show-current"]},"status":{"node_id":"spirit-mac-mini","label":"Mac Mini","hostname":"spirit-mac-mini.local","ssh_alias":"spirit-mac-mini","role":"macos-worker","online":false,"worker_available":false,"supported_job_types":["repo_context_search","source_proxy_context_discovery","trial_context_assist","scout_research_packet","browser_design_check","run_safe_check","system_status"],"last_job_type":"run_safe_check","last_used_at":"2026-05-28T19:05:42.000Z","last_success":false,"result_summary":"check_command is not allowlisted: rm -rf .","error":"check_command is not allowlisted: rm -rf .","last_result":{"job_id":"run_safe_check-1779995141946","job_type":"run_safe_check","input":{"repo_path":"/Users/spiritmac/spiritos-worker/SpiritOS","check_command":"rm -rf ."},"node_id":"spirit-mac-mini","started_at":"2026-05-28T19:05:42.000Z","completed_at":"2026-05-28T19:05:42.000Z","success":false,"result":{"reason_code":"safe_check_command_not_allowlisted","blocked_command":"rm -rf .","recommended_checks":["git status --branch --short --untracked-files=normal","git diff --check","git rev-parse HEAD","git branch --show-current"]},"stdout":"{\"job_id\": \"run_safe_check-1779995141946\", \"job_type\": \"run_safe_check\", \"input\": {\"repo_path\": \"/Users/spiritmac/spiritos-worker/SpiritOS\", \"check_command\": \"rm -rf .\"}, \"node_id\": \"spirit-mac-mini\", \"started_at\": \"2026-05-28T19:05:42.000Z\", \"completed_at\": \"2026-05-28T19:05:42.000Z\", \"success\": false, \"result\": {\"reason_code\": \"safe_check_command_not_allowlisted\", \"blocked_command\": \"rm -rf .\", \"recommended_checks\": [\"git status --branch --short --untracked-files=normal\", \"git diff --check\", \"git rev-parse HEAD\", \"git branch --show-current\"]}, \"stdout\": \"\", \"stderr\": \"\", \"error\": \"check_command is not allowlisted: rm -rf .\", \"duration_ms\": 0, \"artifacts\": [], \"candidate_files\": [], \"recommended_checks\": [\"git status --branch --short --untracked-files=normal\", \"git diff --check\", \"git rev-parse HEAD\", \"git branch --show-current\"]}\n","stderr":"","error":"check_command is not allowlisted: rm -rf .","duration_ms":0,"artifacts":[],"candidate_files":[],"recommended_checks":["git status --branch --short --untracked-files=normal","git diff --check","git rev-parse HEAD","git branch --show-current"]}}}
```

## Observed follow-up issue

After a deliberately blocked check, the current registry reports:

```text
online:false
worker_available:false
```

The blocked state itself is honest, but this status conflates worker availability with last job success. This is deferred to Phase 1.6 API/UI truth hardening.

## Result

Increment 1.4.3 is complete.

Required inspection, hardening, and focused checks were run directly.

Evidence was written to this file.

GO to the next authorized step: Phase 1.4 closeout.
