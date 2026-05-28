# Mac Mini Remote Worker Control And Telemetry Dashboard Integration Plan 6/24

Date: 2026-05-27

Roadmap: `docs/masterKeyProxyProduction.md`
Plan: Plan 6/24, Mac Mini Remote Worker Control And Telemetry Dashboard Integration
Mode: INFRASTRUCTURE / OBSERVABILITY

## Scope

This packet records Mac Mini visibility, SSH read-only control boundaries, and dashboard planning only. It does not edit dashboard code, start services, restart services, create hidden workers, migrate workloads, mutate Cartographer, mutate Source Proxy, write repo files from the Mac, stage, commit, push, branch, create worktrees, clean, stash, reset, checkout, or start Plan 7/24.

Baseline inputs:

- Plan 2/24 Mac Mini baseline: `docs/mac-mini-support-node-plan-2-24-baseline-safety-boundary-v0.1.md`
- Plan 3/24 workload placement: `docs/mac-mini-workload-placement-matrix-plan-3-24-v0.1.md`
- Plan 4/24 search routing: `docs/mac-mini-internet-search-scout-intake-node-plan-4-24-v0.1.md`
- Plan 5/24 subagent feasibility: `docs/mac-mini-subagent-host-feasibility-plan-5-24-v0.1.md`

## Phase 6.1 Telemetry

### Increment 6.1.1 Node Status In Dashboard

- Check run: `curl -sk --max-time 8 https://127.0.0.1:3000/api/telemetry/cluster`
- Cluster summary observed: 3 total nodes, 3 online, 0 offline, 0 degraded, 0 unknown.
- Mac node id: `spirit-mac-mini`
- Mac label: `Mac Mini`
- Mac role: `macos-worker`
- Mac status: `online`
- Mac telemetry URL: `http://10.0.0.147:3187/api/telemetry/self`
- Dashboard integration state: visibility exists through cluster telemetry API; this plan does not edit UI.
- Increment result: GO for visibility; NO-GO for control buttons.

### Increment 6.1.2 Uptime, Storage, Memory, And CPU Telemetry

Mac telemetry observed:

- Hostname: `spirit-mac-mini.local`
- Platform: `darwin`
- Architecture: `x86_64`
- OS: macOS `15.7.7`, build `24G720`
- CPU: Intel i7-8700B, 12 logical CPUs, usage about 9.4 percent at cluster check.
- Load averages: about `1.13`, `1.29`, `1.24`.
- Memory: `17179869184` total bytes, about 24.2 to 24.3 percent used.
- Storage: root SSD about 499.96 GB total, about 471.89 GB free, about 2.3 percent used.
- Uptime: about 135000 seconds.
- Increment result: GO.

### Increment 6.1.3 Stale And Offline State Handling

Existing telemetry route behavior records node status as `online`, `offline`, `degraded`, or `unknown`; cluster response includes summary counts. Required dashboard planning behavior:

- If Mac telemetry is stale or offline, display offline/stale status only.
- Do not auto-restart telemetry.
- Do not start fallback workers.
- Do not hide stale telemetry behind a green status.
- Operator next action should be a manual read-only SSH check.

Increment result: GO.

### Phase 6.1 Closeout

- Evidence exists for increments 6.1.1 through 6.1.3.
- Forbidden scope avoided: no dashboard code edit, no service start/restart, no hidden worker, no Cart mutation, no Source Proxy mutation, no git mutation, and no Plan 7 start.
- Phase result: GO to Phase 6.2.

## Phase 6.2 SSH Control

### Increment 6.2.1 Read-Only SSH Check Commands

Allowed read-only SSH checks:

```bash
ssh -o BatchMode=yes spirit-mac-mini 'hostname; whoami; uptime'
ssh -o BatchMode=yes spirit-mac-mini 'sysctl -n hw.model; sysctl -n hw.memsize; sysctl -n hw.logicalcpu'
ssh -o BatchMode=yes spirit-mac-mini 'df -h /'
ssh -o BatchMode=yes spirit-mac-mini 'ps -axo pid,pcpu,pmem,comm | sort -k2 -nr | head -12'
ssh -o BatchMode=yes spirit-mac-mini 'launchctl list | head -40'
```

Observed proof:

- SSH alias works: `spirit-mac-mini`
- SSH user: `spiritmac`
- `launchctl` exists at `/bin/launchctl`
- `launchctl list | head -20` is readable.

Increment result: GO.

### Increment 6.2.2 Approved Service Restart Command Templates

No restart authority is granted by this plan.

Future restart commands, if explicitly approved, must name the exact service label and reason. Template only:

```bash
ssh -o BatchMode=yes spirit-mac-mini 'launchctl print gui/$(id -u)/EXACT_LABEL'
ssh -o BatchMode=yes spirit-mac-mini 'launchctl kickstart -k gui/$(id -u)/EXACT_LABEL'
```

Rules:

- Template is not approval.
- `EXACT_LABEL` must be replaced only after Britton approves the service.
- Capture before/after telemetry.
- Record rollback guidance.
- Stop if the service touches Cart, Source Proxy writes, queues, workers, approval tokens, or repo files.

Increment result: GO for template documentation; NO-GO for restart execution.

### Increment 6.2.3 Forbidden Commands During Soak Or Cart Isolation

Forbidden during Cart isolation:

- Any command touching Cartographer runtime, `/map`, live Cart evidence, queues, workers, approval tokens, trust tiers, or soak behavior.
- Any `launchctl` start/restart for a Cart-related service.
- Any repo write, apply, stage, commit, push, branch, worktree, cleanup, stash, reset, checkout.
- Any hidden worker or scheduled discovery start.
- Any Source Proxy write/apply action.

Increment result: GO.

### Phase 6.2 Closeout

- Evidence exists for increments 6.2.1 through 6.2.3.
- Forbidden scope avoided: no restart command executed, no hidden worker start, no Cart mutation, no Source Proxy mutation, no repo mutation, no git mutation, and no Plan 7 start.
- Phase result: GO to Phase 6.3.

## Phase 6.3 Operator UX

### Increment 6.3.1 Mac Status In Dashboard Planning

Dashboard should display Mac status as telemetry only:

- Node label: `Mac Mini`
- Status: online/offline/degraded/unknown
- Hostname
- CPU usage and load
- Memory used percent
- Root storage used percent
- Uptime
- Last collected timestamp
- Capability chips as read-only facts

No restart, search, subagent, queue, Cart, or Source Proxy action button should appear without later explicit approval.

Increment result: GO for planning; NO-GO for UI implementation in this plan.

### Increment 6.3.2 Mac Search/Subagent Job Status Later

Future dashboard job status can display:

- last advisory search packet status
- last subagent advisory packet status
- current job count
- concurrency cap
- blocked reason
- manual decision needed

It must not start jobs, retry jobs, schedule jobs, or write packets directly.

Increment result: GO for later planning only.

### Increment 6.3.3 Manual Controls Only After Approval

Manual controls require later approval and exact command scope. Required control fields:

- command id
- command label
- exact SSH command
- service label
- allowed reason
- forbidden reason
- expected output
- rollback guidance
- before/after telemetry capture
- manual confirmation checkbox

This plan grants no manual control implementation.

Increment result: GO.

### Phase 6.3 Closeout

- Evidence exists for increments 6.3.1 through 6.3.3.
- Forbidden scope avoided: no dashboard code edit, no service start/restart, no hidden worker, no Cart mutation, no Source Proxy mutation, no repo mutation, no git mutation, and no Plan 7 start.
- Operator UX plan is recorded.
- Phase result: GO to Plan 6/24 closeout.

## Plan 6/24 Closeout

- All phases reviewed: Phase 6.1, Phase 6.2, Phase 6.3.
- All increments reviewed: 6.1.1 through 6.3.3.
- Evidence exists: yes.
- Forbidden actions occurred: no.
- Mac telemetry visibility: GO.
- SSH read-only checks: GO.
- Dashboard planning: GO.
- Service restart authority: NO-GO.
- Hidden worker authority: NO-GO.
- Dashboard implementation: NO-GO in this plan.
- Cart mutation: NO-GO.
- Source Proxy mutation: NO-GO.
- Final Plan 6/24 result: GO for visibility and observability planning only; NO-GO for restart/control implementation or worker execution.
- Next roadmap plan only: `Plan 7/24: Cartographer Activation Boundary And Re-Soak Decision`.
- Plan 7 started by this packet: `false`.

## Manual Verification Block

```bash
cd /home/source/SpiritOS
git status --branch --short --untracked-files=normal
git rev-parse HEAD
curl -sk --max-time 8 https://127.0.0.1:3000/api/telemetry/cluster
ssh -o BatchMode=yes spirit-mac-mini 'hostname; whoami; uptime; df -h /; command -v launchctl; launchctl list | head -20'
grep -nE "Plan 6/24|Node Status In Dashboard|Read-Only SSH Check Commands|Approved Service Restart Command Templates|NO-GO for restart|Mac Status In Dashboard Planning|Manual Controls Only After Approval|Plan 7/24" docs/mac-mini-remote-worker-control-telemetry-dashboard-plan-6-24-v0.1.md
git diff --check -- docs/mac-mini-remote-worker-control-telemetry-dashboard-plan-6-24-v0.1.md
```

## Expected Output

- `git status` shows existing untracked roadmap/evidence files plus this Plan 6 packet.
- `git rev-parse HEAD` prints `caeccea45b18d39f94c463a3376a6eb911256ea8`.
- Cluster telemetry shows `spirit-mac-mini` / `Mac Mini` online and summary counts.
- SSH read-only check shows hostname, user, uptime, root disk summary, `launchctl`, and a read-only launchctl list excerpt.
- `grep` shows Plan 6 observability, read-only SSH commands, restart template boundary, NO-GO restart/control state, and Plan 7 title.
- `git diff --check` exits cleanly with no output.

## Rollback Guidance

If rollback is required, remove only `docs/mac-mini-remote-worker-control-telemetry-dashboard-plan-6-24-v0.1.md` after explicit Britton approval.

Do not reset, checkout, stash, clean up, broadly restore files, mutate branches or worktrees, push, or force push.
