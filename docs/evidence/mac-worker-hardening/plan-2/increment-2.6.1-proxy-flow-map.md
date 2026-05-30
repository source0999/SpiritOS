# Increment 2.6.1 Proxy Flow Map

Date: 2026-05-28

## Scope

Allowed work for this increment:

- Inspect active `/coding` and Source Proxy flow.
- Identify whether Mac worker is only manually callable or naturally used during realistic prompt testing/task context discovery.
- Do not wire broad automation.
- Do not route all tasks to Mac.
- Produce flow map.

No implementation files were changed.

## Files inspected

- `src/components/coding/CodingCommandCenterShell.tsx`
- `src/lib/coding/agent-trials-ui.ts`
- `src/app/coding/page.tsx`
- `src/app/api/coding/mac-worker/route.ts`
- `src/lib/mac-worker/client.ts`
- `scripts/agent-trials/run-ui-agent-trials.mjs`

## Current Mac integration points

### Raw API

`src/app/api/coding/mac-worker/route.ts` exposes:

- `GET /api/coding/mac-worker`
- `POST /api/coding/mac-worker`

The POST validates job type and calls `runMacWorkerJob`.

### `/coding` UI status

`CodingCommandCenterShell.tsx` has Mac worker status state and displays:

- online/offline
- worker available/unavailable
- repo present/missing/unknown
- used for this run yes/no
- last job type
- last success
- last used
- safe check blocked
- result summary
- error
- supported job types

This is useful status truth, but it is not yet an explicit per-task opt-in bridge.

### Agent-trial harness

`scripts/agent-trials/run-ui-agent-trials.mjs` naturally uses the Mac worker during realistic trial runs:

- builds `trial_context_assist` job
- sends it over SSH to `spirit-mac-mini`
- asks the Mac worker for prompt/repo context
- merges successful `candidate_files` into the ability diagnostic
- records Mac summary fields in trial diagnostic/result JSON:
  - `mac_used`
  - `mac_node_status`
  - `mac_job_type`
  - `mac_candidate_files`
  - `mac_result_summary`
  - `mac_error`
  - `mac_duration_ms`

This is the strongest current realistic active-task path, but it is terminal/harness-driven rather than an obvious UI opt-in button for a single live task.

## Flow map

Current realistic harness flow:

1. User prompt
2. Harness selects trial fixture and submitted prompt
3. Task classification from fixture/expected behavior
4. Target discovery from fixture and UI behavior
5. Optional Mac advisory/context call:
   - `trial_context_assist`
   - SSH to Mac worker
   - returns candidate files and summary
6. Candidate files merge into diagnostic if successful
7. Browser/UI trial screenshot/trace/result artifacts are written by Linux harness
8. Result display/report includes Mac summary fields
9. Approval/write gate remains locked:
   - preview only
   - no apply
   - no commit
   - no push
   - no provider change
   - no Cartographer activation
   - no hidden workers

Current `/coding` status-only flow:

1. User opens `/coding`
2. Command center fetches Mac worker status
3. UI shows Mac online/worker/repo/last-job truth
4. User can see whether Mac was used recently
5. No single-task explicit Mac opt-in is currently visible in the inspected UI

Target safe opt-in flow for A+:

1. User prompt
2. Task classification
3. Target discovery
4. User explicitly selects "Use Mac for context/check support"
5. Source Proxy/API calls selected advisory job only
6. Result displays:
   - Mac used this run
   - job type
   - success/failure
   - candidate files
   - summary
   - error/reason code
   - advisory-only boundary
7. Approval/write gate remains Source Proxy only

## Assessment

Mac support is not only raw API because the agent-trial harness uses it in realistic prompt testing.

However, the active `/coding` UI path appears to be status-only, not an explicit per-task opt-in bridge.

Increment 2.6.2 should add a small explicit opt-in bridge if the current UI lacks one.

## Safety confirmation

- No implementation files were changed.
- No broad automation was wired.
- No task was routed automatically to Mac.
- No Mac write authority was changed.
- No hidden worker, daemon, launch agent, or persistent process was started.
- No Cartographer data, Scout production data, provider routing, secrets, or protected files were changed.
- The Mac remains advisory/check support only.

## GO / NO-GO

GO for Increment 2.6.1 complete.

Next authorized increment: Increment 2.6.2, add explicit Mac advisory opt-in path if missing.
