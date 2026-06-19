# Design

## Existing Entry Point

The existing browser verifier entry point is `_fip5_browser_verifier` in `source_proxy/api/decision.py`. The receipt truth gate is `_structured_verdict_fields`, also in `source_proxy/api/decision.py`.

## Updated Truth Schema

Each browser verifier result will include a nested `browser_verifier` object:

```json
{
  "status": "GO|PARTIAL_GO|NO_GO|BLOCKED|UNKNOWN|SKIPPED|UNSUPPORTED",
  "attempted": false,
  "real_browser_used": false,
  "tool": "playwright|chromium|unknown",
  "target_url": "",
  "artifact_kind": "html|react|next|unknown",
  "checks": {
    "page_loaded": false,
    "dom_ready": false,
    "required_text_present": false,
    "interactive_behavior_checked": false,
    "console_errors": [],
    "network_errors": [],
    "screenshot_captured": false
  },
  "evidence": {
    "summary": "",
    "screenshot_path": null,
    "trace_path": null
  },
  "degraded_reason": null,
  "notes": []
}
```

Legacy fields remain for compatibility, but receipt `verification_real.browser` should require this structured object to say a real browser was used, a page loaded, DOM was ready, and interactive behavior was checked.

## Real Browser Proof

Real browser proof requires:

- Playwright is available.
- Chromium is launched by the harness.
- The generated artifact is loaded through `page.goto`.
- `document.readyState` and visible DOM text are observed from the page.
- No page errors are captured.
- The verifier explicitly marks `interactive_behavior_checked=true`.

For this patch, the existing lightweight HTML harness remains the implementation. It does not run benchmark batteries or app coding tasks.

## Unsupported Cases

Unsupported/non-browser targets return `UNSUPPORTED` in `browser_verifier.status`, with `attempted=false`, `real_browser_used=false`, and a clear note. Legacy status remains `skipped` for compatibility.

## Degraded Or Missing Browser

Missing Playwright or runtime browser exceptions return `BLOCKED` or `NO_GO`, never `GO`. The structured object includes `degraded_reason`.

## Console And Page Errors

Console/page errors are summarized as bounded arrays from the harness. Full logs, raw HTML, env vars, process args with tokens, and secrets are not emitted.

## Fake Or Synthetic Evidence Rejection

Synthetic `_fip5_browser_probe` success remains rejected by default. Its result will include a structured browser verifier object with `status=NO_GO`, `real_browser_used=false`, and `degraded_reason=synthetic_browser_evidence_rejected`.

## Later productive_go Feed

`_structured_verdict_fields` will prefer the structured `browser_verifier` object when deciding `verification_real.browser`. That makes later `productive_go` hardening consume explicit truth fields instead of legacy `status/passed`.

## Scope Avoidance

This patch does not run model calls, 3x10, benchmark gauntlets, Source Proxy coding tasks, apply/execute actions, service restarts, process kills, Docker mutations, or media mutations.

## Test Plan

Focused tests will cover:

- Real browser pass includes `attempted=true`, `real_browser_used=true`, and behavior truth fields.
- Missing browser/tool returns `BLOCKED`, not `GO`.
- Unsupported artifact returns `UNSUPPORTED`, not `GO`.
- DOM-only/text-only proof does not equal behavior proof.
- Screenshot-only proof does not equal behavior proof.
- Console/page errors are summarized without full log dumps.
- Timeout/runtime failure returns non-GO without throwing.
- Synthetic/fallback evidence is rejected.
- Receipt includes browser verifier truth fields.
- Productive remains false without real browser behavior proof.
- Secret-shaped strings are not exposed.
