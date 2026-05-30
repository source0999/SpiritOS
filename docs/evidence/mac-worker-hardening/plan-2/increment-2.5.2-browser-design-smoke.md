# Increment 2.5.2 Browser Design Smoke

Date: 2026-05-28

## Scope

Allowed work for this increment:

- Run `browser_design_check` against a safe local target.
- Use local app URL if available.
- Capture screenshot artifact path if produced.
- Do not mutate design files.

## Required command

Command:

```bash
cd /home/source/SpiritOS

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
    "node_id": "spirit-mac-mini",
    "input": {
      "url": "https://127.0.0.1:3000/coding",
      "viewport": "mobile",
      "check": "layout_readability_and_overlap"
    },
    "result": {
      "summary": "Mac browser/design check packet prepared",
      "url": "https://127.0.0.1:3000/coding",
      "safari_manual_check": "Open the URL in Safari on the Mac Mini and capture viewport/screenshot evidence."
    },
    "artifacts": [],
    "recommended_checks": [
      "Safari visual check",
      "Playwright screenshot check when available"
    ]
  },
  "status": {
    "online": true,
    "worker_available": true,
    "last_job_type": "browser_design_check",
    "last_success": true,
    "result_summary": "Mac browser/design check packet prepared"
  }
}
```

## Smoke result

The job is callable through the SpiritOS API and Mac worker.

It does not yet prove browser/design screenshot evidence.

No screenshot artifact was produced:

```text
artifacts: []
```

No visual overlap/readability finding was produced. The current implementation only returns a manual-check packet.

## Safety confirmation

- No browser was launched.
- No screenshot was captured.
- No design files were mutated.
- No CSS was applied.
- No dependency was installed.
- No hidden worker, daemon, launch agent, or persistent browser process was started.
- No Cartographer data, Scout production data, provider routing, secrets, or protected files were changed.

## GO / NO-GO

GO for Increment 2.5.2 complete as callable smoke.

NO-GO for claiming screenshot-backed browser/design proof.

Next authorized increment: Increment 2.5.3, harden design check result packet.
