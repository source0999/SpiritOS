# Increment 1.7.2 Final Mac Smoke

Date: 2026-05-28

## Required checks run

```bash
cd /home/source/SpiritOS

curl -sk https://127.0.0.1:3000/api/coding/mac-worker

curl -sk -X POST https://127.0.0.1:3000/api/coding/mac-worker \
  -H 'content-type: application/json' \
  --data '{"job_type":"system_status","input":{"repo_path":"/Users/spiritmac/spiritos-worker/SpiritOS"}}'

curl -sk -X POST https://127.0.0.1:3000/api/coding/mac-worker \
  -H 'content-type: application/json' \
  --data '{"job_type":"run_safe_check","input":{"repo_path":"/Users/spiritmac/spiritos-worker/SpiritOS","check_command":"git status --branch --short --untracked-files=normal"}}'

curl -sk -X POST https://127.0.0.1:3000/api/coding/mac-worker \
  -H 'content-type: application/json' \
  --data '{"job_type":"run_safe_check","input":{"repo_path":"/Users/spiritmac/spiritos-worker/SpiritOS","check_command":"git diff --check"}}'

ssh -o BatchMode=yes spirit-mac-mini 'cd /Users/spiritmac/spiritos-worker/SpiritOS && git status --branch --short --untracked-files=normal && git rev-parse HEAD'
```

## Initial API availability note

The first API smoke attempt returned curl exit code 7 because no local SpiritOS server was listening on `https://127.0.0.1:3000`.

A temporary visible dev server was started with:

```bash
npm run dev:https
```

It was stopped after the smoke checks with `Ctrl-C`. No persistent process was left running.

Next.js reported that it loaded `.env.local` as part of normal runtime startup; the file was not read, edited, or copied by this work.

## Evidence

### Initial GET after temporary server start

```json
{"ok":true,"status":{"node_id":"spirit-mac-mini","label":"Mac Mini","hostname":"spirit-mac-mini.local","ssh_alias":"spirit-mac-mini","role":"macos-worker","online":false,"worker_available":false,"repo_present":null,"supported_job_types":["repo_context_search","source_proxy_context_discovery","trial_context_assist","scout_research_packet","browser_design_check","run_safe_check","system_status"],"last_job_type":null,"last_used_at":null,"last_success":null,"result_summary":"No Mac worker job recorded in this server process","error":null,"last_reason_code":null,"blocked_command":null,"safe_checks_blocked":false}}
```

### API `system_status`

Key result:

```json
{"ok":true,"success":true,"hostname":"spirit-mac-mini.local","platform":"darwin","arch":"x86_64","repo_path":"/Users/spiritmac/spiritos-worker/SpiritOS","repo_present":true,"status":{"online":true,"worker_available":true,"repo_present":true,"last_job_type":"system_status","last_success":true}}
```

### API `run_safe_check` git status

Key result:

```json
{"ok":true,"success":true,"summary":"git status --branch --short --untracked-files=normal completed","stdout":"## main...origin/main\n?? scripts/mac-worker/\n","status":{"online":true,"worker_available":true,"repo_present":true,"last_job_type":"run_safe_check","last_success":true}}
```

### API `run_safe_check` git diff check

Key result:

```json
{"ok":true,"success":true,"summary":"git diff --check completed","stdout":"","stderr":"","status":{"online":true,"worker_available":true,"repo_present":true,"last_job_type":"run_safe_check","last_success":true,"result_summary":"git diff --check completed"}}
```

### Final GET after safe checks

Key result:

```json
{"ok":true,"status":{"online":true,"worker_available":true,"repo_present":true,"last_job_type":"run_safe_check","last_success":true,"result_summary":"git diff --check completed","error":null,"safe_checks_blocked":false}}
```

### SSH git status and HEAD

```text
## main...origin/main
?? scripts/mac-worker/
ac1c6ddf7cf2d71739801a13c46a3f1f3426ea26
```

## Result

Increment 1.7.2 is complete.

Required checks were run directly.

Evidence was written to this file.

GO to the next authorized step: Plan 1 closeout.
