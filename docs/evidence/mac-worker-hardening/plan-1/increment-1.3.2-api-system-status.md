# Increment 1.3.2 API System Status

Date: 2026-05-28

## Required command run

```bash
curl -sk -X POST https://127.0.0.1:3000/api/coding/mac-worker \
  -H 'content-type: application/json' \
  --data '{"job_type":"system_status","input":{"repo_path":"/Users/spiritmac/spiritos-worker/SpiritOS"}}'
```

## Evidence

```json
{"ok":true,"result":{"job_id":"system_status-1779994972522","job_type":"system_status","input":{"repo_path":"/Users/spiritmac/spiritos-worker/SpiritOS"},"node_id":"spirit-mac-mini","started_at":"2026-05-28T19:02:52.000Z","completed_at":"2026-05-28T19:02:52.000Z","success":true,"result":{"summary":"Mac worker status returned","hostname":"spirit-mac-mini.local","platform":"darwin","arch":"x86_64","repo_path":"/Users/spiritmac/spiritos-worker/SpiritOS","repo_present":true,"supported_job_types":["repo_context_search","source_proxy_context_discovery","trial_context_assist","scout_research_packet","browser_design_check","run_safe_check","system_status"]},"stdout":"{\"job_id\": \"system_status-1779994972522\", \"job_type\": \"system_status\", \"input\": {\"repo_path\": \"/Users/spiritmac/spiritos-worker/SpiritOS\"}, \"node_id\": \"spirit-mac-mini\", \"started_at\": \"2026-05-28T19:02:52.000Z\", \"completed_at\": \"2026-05-28T19:02:52.000Z\", \"success\": true, \"result\": {\"summary\": \"Mac worker status returned\", \"hostname\": \"spirit-mac-mini.local\", \"platform\": \"darwin\", \"arch\": \"x86_64\", \"repo_path\": \"/Users/spiritmac/spiritos-worker/SpiritOS\", \"repo_present\": true, \"supported_job_types\": [\"repo_context_search\", \"source_proxy_context_discovery\", \"trial_context_assist\", \"scout_research_packet\", \"browser_design_check\", \"run_safe_check\", \"system_status\"]}, \"stdout\": \"\", \"stderr\": \"\", \"error\": null, \"duration_ms\": 0, \"artifacts\": [], \"candidate_files\": [], \"recommended_checks\": []}\n","stderr":"","error":null,"duration_ms":0,"artifacts":[],"candidate_files":[],"recommended_checks":[]},"status":{"node_id":"spirit-mac-mini","label":"Mac Mini","hostname":"spirit-mac-mini.local","ssh_alias":"spirit-mac-mini","role":"macos-worker","online":true,"worker_available":true,"supported_job_types":["repo_context_search","source_proxy_context_discovery","trial_context_assist","scout_research_packet","browser_design_check","run_safe_check","system_status"],"last_job_type":"system_status","last_used_at":"2026-05-28T19:02:52.000Z","last_success":true,"result_summary":"Mac worker status returned","error":null,"last_result":{"job_id":"system_status-1779994972522","job_type":"system_status","input":{"repo_path":"/Users/spiritmac/spiritos-worker/SpiritOS"},"node_id":"spirit-mac-mini","started_at":"2026-05-28T19:02:52.000Z","completed_at":"2026-05-28T19:02:52.000Z","success":true,"result":{"summary":"Mac worker status returned","hostname":"spirit-mac-mini.local","platform":"darwin","arch":"x86_64","repo_path":"/Users/spiritmac/spiritos-worker/SpiritOS","repo_present":true,"supported_job_types":["repo_context_search","source_proxy_context_discovery","trial_context_assist","scout_research_packet","browser_design_check","run_safe_check","system_status"]},"stdout":"{\"job_id\": \"system_status-1779994972522\", \"job_type\": \"system_status\", \"input\": {\"repo_path\": \"/Users/spiritmac/spiritos-worker/SpiritOS\"}, \"node_id\": \"spirit-mac-mini\", \"started_at\": \"2026-05-28T19:02:52.000Z\", \"completed_at\": \"2026-05-28T19:02:52.000Z\", \"success\": true, \"result\": {\"summary\": \"Mac worker status returned\", \"hostname\": \"spirit-mac-mini.local\", \"platform\": \"darwin\", \"arch\": \"x86_64\", \"repo_path\": \"/Users/spiritmac/spiritos-worker/SpiritOS\", \"repo_present\": true, \"supported_job_types\": [\"repo_context_search\", \"source_proxy_context_discovery\", \"trial_context_assist\", \"scout_research_packet\", \"browser_design_check\", \"run_safe_check\", \"system_status\"]}, \"stdout\": \"\", \"stderr\": \"\", \"error\": null, \"duration_ms\": 0, \"artifacts\": [], \"candidate_files\": [], \"recommended_checks\": []}\n","stderr":"","error":null,"duration_ms":0,"artifacts":[],"candidate_files":[],"recommended_checks":[]}}}
```

## Result

Increment 1.3.2 is complete.

Required check was run directly.

Evidence was written to this file.

GO to the next authorized step: Phase 1.3 closeout.
