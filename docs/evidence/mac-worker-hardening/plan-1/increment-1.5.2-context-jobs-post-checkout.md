# Increment 1.5.2 Context Jobs Post Checkout

Date: 2026-05-28

## Required commands run

```bash
curl -sk -X POST https://127.0.0.1:3000/api/coding/mac-worker \
  -H 'content-type: application/json' \
  --data '{"job_type":"trial_context_assist","input":{"repo_path":"/Users/spiritmac/spiritos-worker/SpiritOS","prompt":"mac worker hardening repo checkout safe check","max_results":5}}'

curl -sk -X POST https://127.0.0.1:3000/api/coding/mac-worker \
  -H 'content-type: application/json' \
  --data '{"job_type":"repo_context_search","input":{"repo_path":"/Users/spiritmac/spiritos-worker/SpiritOS","query":"mac worker hardening","max_results":5}}'

curl -sk -X POST https://127.0.0.1:3000/api/coding/mac-worker \
  -H 'content-type: application/json' \
  --data '{"job_type":"source_proxy_context_discovery","input":{"repo_path":"/Users/spiritmac/spiritos-worker/SpiritOS","prompt":"source proxy mac worker route contract","max_results":5}}'
```

## Evidence

### `trial_context_assist`

Result:

- `ok:true`
- `success:true`
- `job_id:"trial_context_assist-1779995225455"`
- `summary:"Mac searched 1538 tracked files for 7 prompt tokens."`
- `result_summary:"trial_context_assist returned 5 candidate files"`

Candidate files:

```text
docs/cartographer-level-5-multi-worker-safety-smoke.md
docs/mac-mini-remote-worker-control-telemetry-dashboard-plan-6-24-v0.1.md
docs/mac-mini-support-node-plan-2-24-baseline-safety-boundary-v0.1.md
scout/src/scout/tests/test_phase8_safety_audit.py
scout/src/scout/tests/test_repomap.py
```

### `repo_context_search`

Result:

- `ok:true`
- `success:true`
- `job_id:"repo_context_search-1779995225501"`
- `summary:"Mac searched 1538 tracked files for 3 prompt tokens."`
- `result_summary:"repo_context_search returned 5 candidate files"`

Candidate files:

```text
docs/mac-mini-remote-worker-control-telemetry-dashboard-plan-6-24-v0.1.md
source_proxy/tests/test_cartographer_level_13_worker_runtime.py
source_proxy/tests/test_cartographer_multi_worker_branch_workflow.py
source_proxy/tests/test_cartographer_worker_contract.py
source_proxy/cartographer/level_13_worker_runtime.py
```

### `source_proxy_context_discovery`

Result:

- `ok:true`
- `success:true`
- `job_id:"source_proxy_context_discovery-1779995225568"`
- `summary:"Mac searched 1538 tracked files for 6 prompt tokens."`
- `result_summary:"source_proxy_context_discovery returned 5 candidate files"`

Candidate files:

```text
source_proxy/tests/test_cartographer_worker_contract.py
source_proxy/cartographer/worker_contract.py
source_proxy/tests/test_cartographer_level_13_worker_runtime.py
source_proxy/tests/test_cartographer_multi_worker_branch_workflow.py
source_proxy/tests/test_cartographer_proxy_consultation_contract.py
```

## Result

Increment 1.5.2 is complete.

Required checks were run directly.

Evidence was written to this file.

GO to the next authorized step: Phase 1.5 closeout.
