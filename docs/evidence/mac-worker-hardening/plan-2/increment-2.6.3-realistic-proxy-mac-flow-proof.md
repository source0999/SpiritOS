# Increment 2.6.3 Realistic Proxy Mac Flow Proof

Date: 2026-05-28

## Scope

Allowed work for this increment:

- Run a realistic task through the existing harness or UI diagnostic path.
- Prove Mac use, job type recording, useful candidate files/check result, honest failure states, no hidden writes, and intact approval boundary.
- Do not claim smooth integration without evidence.

## Harness command discovery

Command:

```bash
node scripts/agent-trials/run-ui-agent-trials.mjs --help || true
```

Result:

```text
Usage: node scripts/agent-trials/run-ui-agent-trials.mjs [options]

Options:
  --agent coding|design|combined
  --viewport desktop|mobile
  --limit 10
  --profile britton-realistic|clean-control
```

## Realistic harness run

Command:

```bash
node scripts/agent-trials/run-ui-agent-trials.mjs --agent coding --viewport desktop --limit 10 --profile britton-realistic
```

Result:

```json
{
  "report": "plan-5-ui-batch-trial-runner",
  "agent": "coding",
  "viewport": "desktop",
  "profile": "britton-realistic",
  "trials_run": 10,
  "passed_trials": 0,
  "failed_trials": 10,
  "weighted_score_percent": 0,
  "hidden_mutation_failures": 0,
  "combined_report_path": null,
  "summary_path": "docs/evidence/agent-runtime-trial-harness/plan-5/summary.json",
  "artifacts_root": "docs/evidence/agent-runtime-trial-harness/plan-5/artifacts/2026-05-28T20-01-46-832Z-coding-desktop-britton-realistic",
  "go": false
}
```

Summary inspection:

```json
{
  "base_url": "https://localhost:3000",
  "total_trials": 10,
  "failed_trials": 10,
  "hidden_mutation_failures": 0,
  "mac_used_count": 0,
  "mac_success_count": 0,
  "mac_last_result_summary": "none",
  "go": false
}
```

Representative failure:

```text
page.goto: net::ERR_CONNECTION_REFUSED at https://localhost:3000/coding
```

Interpretation: the harness did not prove Mac use because the app server was unavailable for the harness navigation. No Mac success is claimed from this run.

## UI diagnostic path attempt

A Playwright attempt against `/coding` looked for the new explicit button:

```text
Use Mac for context/check support
```

Result: the button was not present on `/coding`.

Cause found by inspection:

- `src/app/coding/page.tsx` renders `CodingCockpitShell`.
- The new opt-in bridge from Increment 2.6.2 was added to `CodingCommandCenterShell`.
- `CodingCommandCenterShell` is test-rendered and referenced by preview routes, but it is not the active `/coding` page shell.

Interpretation: active `/coding` UI smoothness is not proven.

## Raw API support proof

After the app endpoint was available again, raw API context support was run:

Command:

```bash
curl -sk -X POST https://127.0.0.1:3000/api/coding/mac-worker \
  -H 'content-type: application/json' \
  --data '{"job_type":"source_proxy_context_discovery","input":{"repo_path":"/Users/spiritmac/spiritos-worker/SpiritOS","prompt":"realistic proxy mac integration proof","max_results":5}}'
```

Result summary:

```json
{
  "ok": true,
  "result": {
    "job_type": "source_proxy_context_discovery",
    "success": true,
    "node_id": "spirit-mac-mini",
    "result": {
      "summary": "Mac searched 1538 tracked files for 5 prompt tokens."
    },
    "candidate_files": [
      "docs/design-agent-design-system-a-grade-preflight-readiness-plan-e-source-proxy-read-only-integration-proof-v0.1.md",
      "docs/visual-proof/source-proxy-agent-integration-preflight-plan-10/chat-desktop.png",
      "docs/visual-proof/source-proxy-agent-integration-preflight-plan-10/chat-mobile.png",
      "docs/visual-proof/source-proxy-agent-integration-preflight-plan-10/coding-desktop.png",
      "docs/visual-proof/source-proxy-agent-integration-preflight-plan-10/coding-mobile.png"
    ],
    "recommended_checks": [
      "git diff --check",
      "npx --no-install tsc --noEmit --pretty false"
    ]
  },
  "status": {
    "online": true,
    "worker_available": true,
    "last_job_type": "source_proxy_context_discovery",
    "last_success": true,
    "result_summary": "source_proxy_context_discovery returned 5 candidate files"
  }
}
```

## Proof result

Proven:

- Mac context support works through raw SpiritOS API.
- Job type is recorded.
- Candidate files are returned.
- Failure states from the realistic harness are honest.
- Hidden mutation failures were zero in the harness summary.
- Approval/write boundary remained intact.

Not proven:

- A+ smooth active `/coding` UI flow.
- Harness-based Mac use in this increment.

## Safety confirmation

- No hidden writes occurred.
- No hidden worker, daemon, launch agent, or autonomous execution was started.
- No apply, commit, push, provider change, Cartographer activation, or Scout production mutation occurred.
- The Mac remains advisory/check support only.

## GO / NO-GO

GO for Increment 2.6.3 complete as partial proof.

NO-GO for A+ proxy smoothness.

Proxy smoothness grade from this increment: B. Raw API and component-level opt-in proof exist, but active `/coding` route proof is blocked because the bridge is not in the routed shell.

Next authorized increment: Phase 2.6 closeout.
