# Increment 2.7.3 Final Mac Smoke Proof

Date: 2026-05-28

## Required command results

### GET Mac worker status

Command:

```bash
curl -sk https://127.0.0.1:3000/api/coding/mac-worker
```

Result summary:

```json
{
  "ok": true,
  "status": {
    "online": true,
    "worker_available": true,
    "last_job_type": "source_proxy_context_discovery",
    "last_success": true,
    "result_summary": "source_proxy_context_discovery returned 5 candidate files"
  }
}
```

### `system_status`

Command:

```bash
curl -sk -X POST https://127.0.0.1:3000/api/coding/mac-worker \
  -H 'content-type: application/json' \
  --data '{"job_type":"system_status","input":{"repo_path":"/Users/spiritmac/spiritos-worker/SpiritOS"}}'
```

Result summary:

```json
{
  "ok": true,
  "result": {
    "job_type": "system_status",
    "success": true,
    "result": {
      "repo_present": true,
      "repo_path": "/Users/spiritmac/spiritos-worker/SpiritOS"
    }
  }
}
```

### `run_safe_check`

Command:

```bash
curl -sk -X POST https://127.0.0.1:3000/api/coding/mac-worker \
  -H 'content-type: application/json' \
  --data '{"job_type":"run_safe_check","input":{"repo_path":"/Users/spiritmac/spiritos-worker/SpiritOS","check_command":"git status --branch --short --untracked-files=normal"}}'
```

Result summary:

```json
{
  "ok": true,
  "result": {
    "job_type": "run_safe_check",
    "success": true,
    "stdout": "## main...origin/main\n?? scripts/mac-worker/\n"
  }
}
```

### `trial_context_assist`

Command:

```bash
curl -sk -X POST https://127.0.0.1:3000/api/coding/mac-worker \
  -H 'content-type: application/json' \
  --data '{"job_type":"trial_context_assist","input":{"repo_path":"/Users/spiritmac/spiritos-worker/SpiritOS","prompt":"realistic proxy mac integration proof","max_results":5}}'
```

Result summary:

```json
{
  "ok": true,
  "result": {
    "job_type": "trial_context_assist",
    "success": true,
    "result": {
      "summary": "Mac searched 1538 tracked files for 5 prompt tokens."
    },
    "candidate_files": [
      "docs/design-agent-design-system-a-grade-preflight-readiness-plan-e-source-proxy-read-only-integration-proof-v0.1.md",
      "docs/visual-proof/source-proxy-agent-integration-preflight-plan-10/chat-desktop.png",
      "docs/visual-proof/source-proxy-agent-integration-preflight-plan-10/chat-mobile.png",
      "docs/visual-proof/source-proxy-agent-integration-preflight-plan-10/coding-desktop.png",
      "docs/visual-proof/source-proxy-agent-integration-preflight-plan-10/coding-mobile.png"
    ]
  }
}
```

### `scout_research_packet`

Command:

```bash
curl -sk -X POST https://127.0.0.1:3000/api/coding/mac-worker \
  -H 'content-type: application/json' \
  --data '{"job_type":"scout_research_packet","input":{"repo_path":"/Users/spiritmac/spiritos-worker/SpiritOS","query":"Mac worker Source Proxy advisory search proof","max_results":5,"mode":"local_only"}}'
```

Result summary:

```json
{
  "ok": true,
  "result": {
    "job_type": "scout_research_packet",
    "success": true,
    "result": {
      "mode": "local_only",
      "confidence": "medium",
      "limitations": [
        "Local-only packet; no public web search was performed.",
        "No Scout production storage was written.",
        "No packet was promoted or imported into Source Proxy."
      ]
    },
    "candidate_files": [
      "source_proxy/tests/test_cartographer_final_proof_stage_1_gauntlet.py",
      "source_proxy/tests/test_cartographer_final_proof_stage_2_soak.py",
      "source_proxy/tests/test_cartographer_final_proof_stage_3_hidden_mutation.py",
      "source_proxy/tests/test_cartographer_final_proof_stage_4_approval_kill_switch.py",
      "source_proxy/tests/test_cartographer_final_proof_stage_5_rollback.py"
    ]
  }
}
```

### `browser_design_check`

Command:

```bash
curl -sk -X POST https://127.0.0.1:3000/api/coding/mac-worker \
  -H 'content-type: application/json' \
  --data '{"job_type":"browser_design_check","input":{"repo_path":"/Users/spiritmac/spiritos-worker/SpiritOS","url":"https://127.0.0.1:3000/coding","viewport":"mobile","check":"layout_readability_and_overlap"}}'
```

Result summary:

```json
{
  "ok": true,
  "result": {
    "job_type": "browser_design_check",
    "success": true,
    "result": {
      "severity": "blocked",
      "screenshot_artifacts": [],
      "no_mutation_confirmed": true,
      "limitations": [
        "No browser was launched.",
        "No screenshot was captured.",
        "No layout pixels were inspected.",
        "This packet is advisory metadata only until browser tooling is approved and available."
      ]
    }
  }
}
```

## Safety confirmation

- Final smoke started no hidden workers.
- Final smoke granted no Mac write authority.
- Final smoke performed no apply, commit, push, provider change, Cartographer activation, or Scout production mutation.
- Browser/design check did not launch a browser or capture a screenshot.
- Mac remains advisory/check support only.

## GO / NO-GO

GO for Increment 2.7.3 complete.

Next authorized increment: Plan 2 closeout.
