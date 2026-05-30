# Increment 1.1.1 Linux Baseline

Date: 2026-05-28

## Required commands run

```bash
cd /home/source/SpiritOS
git status --branch --short --untracked-files=normal
git rev-parse HEAD
curl -sk https://127.0.0.1:3000/api/coding/mac-worker
```

## Evidence

### Linux branch, HEAD, and dirty tree

```text
## main...origin/main
 M _reference/dashboardDemo/index.html
 M _reference/dashboardDemo/src/App.tsx
 M _reference/dashboardDemo/src/index.css
 M _reference/dashboardDemo/vite.config.ts
 M docs/plan-index.md
 M package-lock.json
 M package.json
 M playwright.config.mjs
 M src/components/coding/CodingCommandCenterShell.tsx
 M src/components/coding/__tests__/coding-command-center-shell.test.tsx
 M src/lib/coding/plain-english-scope.ts
?? basic.js
?? docs/agent-runtime-trial-harness-mac-subagent-port-master-plan-v0.1.md
?? docs/agent-runtime-trial-harness-mac-subagent-port-new-chat-handoff-v0.1.md
?? docs/evidence/agent-runtime-trial-harness/
?? docs/spiritos-coding-readiness-roadmap-to-codex-like-features.md
?? scripts/agent-trials/
?? scripts/mac-worker/
?? src/app/api/coding/
?? src/app/v1/coding/mac-advisory/
?? src/lib/coding/__tests__/agent-trials-ui.test.ts
?? src/lib/coding/__tests__/plain-english-scope.test.ts
?? src/lib/coding/agent-trials-ui.ts
?? src/lib/mac-advisory/
?? src/lib/mac-worker/
?? tests/ui-agent-trials/
```

HEAD:

```text
ac1c6ddf7cf2d71739801a13c46a3f1f3426ea26
```

### Current Mac worker API status

```json
{"ok":true,"status":{"node_id":"spirit-mac-mini","label":"Mac Mini","hostname":"spirit-mac-mini.local","ssh_alias":"spirit-mac-mini","role":"macos-worker","online":true,"worker_available":true,"supported_job_types":["repo_context_search","source_proxy_context_discovery","trial_context_assist","scout_research_packet","browser_design_check","run_safe_check","system_status"],"last_job_type":"system_status","last_used_at":"2026-05-28T18:52:26.000Z","last_success":true,"result_summary":"Mac worker status returned","error":null,"last_result":{"job_id":"system_status-1779994346295","job_type":"system_status","input":{"repo_path":"/Users/spiritmac/spiritos-worker/SpiritOS"},"node_id":"spirit-mac-mini","started_at":"2026-05-28T18:52:26.000Z","completed_at":"2026-05-28T18:52:26.000Z","success":true,"result":{"summary":"Mac worker status returned","hostname":"spirit-mac-mini.local","platform":"darwin","arch":"x86_64","repo_path":"/Users/spiritmac/spiritos-worker/SpiritOS","repo_present":false,"supported_job_types":["repo_context_search","source_proxy_context_discovery","trial_context_assist","scout_research_packet","browser_design_check","run_safe_check","system_status"]},"stdout":"{\"job_id\": \"system_status-1779994346295\", \"job_type\": \"system_status\", \"input\": {\"repo_path\": \"/Users/spiritmac/spiritos-worker/SpiritOS\"}, \"node_id\": \"spirit-mac-mini\", \"started_at\": \"2026-05-28T18:52:26.000Z\", \"completed_at\": \"2026-05-28T18:52:26.000Z\", \"success\": true, \"result\": {\"summary\": \"Mac worker status returned\", \"hostname\": \"spirit-mac-mini.local\", \"platform\": \"darwin\", \"arch\": \"x86_64\", \"repo_path\": \"/Users/spiritmac/spiritos-worker/SpiritOS\", \"repo_present\": false, \"supported_job_types\": [\"repo_context_search\", \"source_proxy_context_discovery\", \"trial_context_assist\", \"scout_research_packet\", \"browser_design_check\", \"run_safe_check\", \"system_status\"]}, \"stdout\": \"\", \"stderr\": \"\", \"error\": null, \"duration_ms\": 0, \"artifacts\": [], \"candidate_files\": [], \"recommended_checks\": []}\n","stderr":"","error":null,"duration_ms":0,"artifacts":[],"candidate_files":[],"recommended_checks":[]}}}
```

## Result

Increment 1.1.1 is complete.

Required checks were run directly.

Evidence was written to this file.

GO to the next authorized increment: Increment 1.1.2, capture current Mac-side status.
