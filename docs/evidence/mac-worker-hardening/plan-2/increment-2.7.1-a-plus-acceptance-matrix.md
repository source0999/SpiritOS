# Increment 2.7.1 A+ Acceptance Matrix

Date: 2026-05-28

## Mac worker job acceptance matrix

| Job type | Status | Proof command | Evidence file | Limitations | Safety boundary | Grade |
| --- | --- | --- | --- | --- | --- | --- |
| `system_status` | Proven from Plan 1; final Plan 2 smoke pending | API POST `system_status`; direct Mac worker status | Plan 1 `increment-1.3.1-direct-worker-system-status.md`, `increment-1.3.2-api-system-status.md`; Plan 2 final smoke pending | Plan 2 baseline GET failed while server was down; final smoke must re-run | Read-only status; no repo mutation | A |
| `run_safe_check` | Proven from Plan 1; final Plan 2 smoke pending | API POST allowlisted git status/diff checks | Plan 1 `increment-1.4.1-run-safe-check-git-status.md`, `increment-1.4.2-run-safe-check-diff-check.md`, `increment-1.4.3-safe-command-allowlist.md`; Plan 2 final smoke pending | Only allowlisted commands; unsafe commands block | Advisory check only; blocked unsafe commands return structured failure | A+ |
| `trial_context_assist` | Proven from Plan 1; harness integration exists but Plan 2 harness run did not reach Mac | API POST from Plan 1; harness code path in `run-ui-agent-trials.mjs` | Plan 1 `increment-1.5.2-context-jobs-post-checkout.md`; Plan 2 `increment-2.6.1-proxy-flow-map.md`, `increment-2.6.3-realistic-proxy-mac-flow-proof.md` | Plan 2 realistic harness run failed before Mac use due app navigation; final smoke pending | Candidate context only; no apply/write authority | A- |
| `repo_context_search` | Proven from Plan 1 | API POST repo context search | Plan 1 `increment-1.5.2-context-jobs-post-checkout.md` | Generic tracked-file search only | Advisory candidate files/snippets only | A |
| `source_proxy_context_discovery` | Proven Plan 1 and Plan 2 raw API | API POST `source_proxy_context_discovery` | Plan 1 `increment-1.5.2-context-jobs-post-checkout.md`; Plan 2 `increment-2.6.3-realistic-proxy-mac-flow-proof.md` | Active `/coding` UI opt-in not routed; raw API proof only in Plan 2 | Advisory candidate files/snippets only; Source Proxy remains approval/write gate | B+ |
| `scout_research_packet` | Proven local-only and web-search packet | API POST `mode:"local_only"` and `mode:"web_search_packet"` | Plan 2 `increment-2.3.4-scout-research-api-proof.md`, `increment-2.4.3-web-search-packet-proof.md` | Web depends on local SearXNG at `source-server.local:8080`; snippets are untrusted | No Scout production write; no promotion; no auto-import; no page execution | A+ |
| `browser_design_check` | Callable and honest; screenshot proof blocked | API POST `browser_design_check` | Plan 2 `increment-2.5.2-browser-design-smoke.md`, `increment-2.5.3-browser-design-result-packet.md` | Mac lacks Node/npm/npx/Playwright; no screenshot artifact; no pixel/layout proof | No browser launch; no CSS/design mutation; no fake screenshot claim | B |

## Current Plan 2 grades

- Repo/check integration: A+
- Proxy advisory smoothness: B
- Job status truth: A
- Search/browser proof:
  - Search: A+
  - Browser/design: B

## Safety summary

Across all proven jobs:

- Mac is advisory/check support only.
- Source Proxy remains approval/write authority.
- No hidden workers are authorized.
- No daemon or launch agent is authorized.
- No autonomous execution is authorized.
- No Cartographer mutation is authorized.
- No Scout production mutation is authorized.
- No provider routing or secret mutation is authorized.

## GO / NO-GO

GO for Increment 2.7.1 complete.

Next authorized increment: Increment 2.7.2, run full verification checks.
