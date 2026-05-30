# Plan 4/8: Mac Advisory Subagent Port v1 Evidence

## Scope

Plan 4 ports a Mac advisory subagent boundary as a one-shot helper contract. It does not start a daemon, launch agent, hidden worker, provider call, apply execution, commit, push, protected-path write, or repo mutation from Mac output.

## Phase 4.1: Telemetry + SSH Baseline

Checks run:

```bash
curl -sk --max-time 8 https://127.0.0.1:3000/api/telemetry/cluster | grep -E "spirit-mac-mini|macos-worker|online" || true
ssh -o BatchMode=yes spirit-mac-mini 'hostname; whoami; sw_vers; python3 --version; curl --version | head -1'
ssh -o BatchMode=yes spirit-mac-mini 'ps aux | grep -Ei "agent|worker|playwright|node|python" | grep -v grep || true'
```

Evidence:

- Telemetry included `spirit-mac-mini`, role `macos-worker`, status `online`, hostname `spirit-mac-mini.local`, platform `darwin`, macOS `15.7.7`.
- SSH identity returned `spirit-mac-mini.local`, user `spiritmac`, macOS `15.7.7`, Python `3.9.6`, and curl `8.7.1`.
- Process scan showed pre-existing macOS agent processes and the existing telemetry process: `/Users/spiritmac/spiritos-mac-node/spiritos_mac_telemetry.py --host 0.0.0.0 --port 3187`.
- No Plan 4 worker, daemon, launch agent, persistent Playwright process, or hidden agent was started.

GO / NO-GO: GO.

## Phase 4.2: Packet Contract

Implemented `MacAdvisoryPacket` with:

- `job_id`
- `job_type`
- `input_summary`
- `mac_host`
- `started_at`
- `completed_at`
- `status`
- `result`
- `citations_or_evidence`
- `safety_boundary`
- `repo_write_authority: false`

Allowed job types:

- `search_packet`
- `screenshot_packet`
- `design_review_packet`
- `test_scribe_packet`
- `docs_summary_packet`

Evidence files:

- `src/lib/mac-advisory/types.ts`
- `src/lib/mac-advisory/packet.ts`
- `src/lib/mac-advisory/__tests__/packet.test.ts`

GO / NO-GO: GO.

## Phase 4.3: One-Shot Mac Adapter

Implemented a bounded SSH one-shot adapter:

- Uses `ssh -o BatchMode=yes spirit-mac-mini <one-shot-command>`.
- Uses allowed job type commands only.
- Returns a packet with `repo_write_authority: false`.
- Converts unsupported jobs and command failures into blocked advisory packets.
- Does not create a daemon, launch agent, service, hidden worker, persistent process, commit, push, apply execution, or provider call.

Evidence files:

- `src/lib/mac-advisory/one-shot.ts`
- `src/app/v1/coding/mac-advisory/route.ts`
- `src/app/v1/coding/mac-advisory/__tests__/route.test.ts`

GO / NO-GO: GO.

## Phase 4.4: Search Packet

Result: honest blocker.

Evidence:

- Source host SearXNG JSON endpoint responded locally at `http://127.0.0.1:8080/search?q=SpiritOS&format=json`.
- Mac-local probes at `127.0.0.1:8080` and `127.0.0.1:8888` did not prove a JSON endpoint from the Mac.
- `docs/evidence/agent-runtime-trial-harness/plan-4/search-packet-blocker.json` records `"job_type": "search_packet"`, `"status": "blocked"`, and `"repo_write_authority": false`.

GO / NO-GO: GO, because the plan permits precise blockers for unavailable Mac search configuration.

## Phase 4.5: Screenshot + Summary Helpers

Completed advisory one-shot proofs:

- `docs/evidence/agent-runtime-trial-harness/plan-4/docs-summary-packet.json`
- `docs/evidence/agent-runtime-trial-harness/plan-4/screenshot-metadata-packet.json`

Both packets record:

- `"status": "completed"`
- `"repo_write_authority": false`
- one-shot SSH/Python evidence
- explicit no-daemon/no-hidden-worker safety boundary

GO / NO-GO: GO.

## Phase 4.6: Phase Checks

Checks run:

```bash
npx --no-install tsc --noEmit --pretty false
npx --no-install vitest run src/app/v1/coding/mac-advisory/__tests__/route.test.ts src/lib/mac-advisory/__tests__/*.test.ts --reporter=basic
ssh -o BatchMode=yes spirit-mac-mini 'ps aux | grep -Ei "agent|worker|playwright|node|python" | grep -v grep || true'
git diff --check
git status --branch --short --untracked-files=normal
```

Evidence:

- TypeScript completed with exit code `0`.
- Vitest exact roadmap command completed with exit code `0`.
- Mac process scan remained limited to normal macOS agent processes and the pre-existing telemetry process; no Plan 4 persistent process was created.
- `git diff --check` completed with exit code `0`.
- Dirty tree contains only the approved roadmap docs, evidence, trial harness files/scripts, and Plan 4 Mac advisory files.

GO / NO-GO: GO.

## Plan 4 Result

GO.

Plan 4 is advisory-only and bounded. The Mac can return one-shot packet evidence, the packet schema enforces `repo_write_authority: false`, the route exposes no apply/commit/push/provider authority, and search remains blocked until a Mac-accessible SearXNG JSON endpoint is configured.
