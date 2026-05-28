# Mac Mini Support Node Plan 2/24 Baseline And Safety Boundary

Date: 2026-05-27

Roadmap: `docs/masterKeyProxyProduction.md`
Plan: Plan 2/24, Mac Mini Support Node Baseline And Safety Boundary
Mode: INFRASTRUCTURE / READ-ONLY FIRST

## Scope

This packet records a read-only Mac Mini support-node baseline and safety boundary. It does not move workloads, start services, create hidden workers, mutate Cartographer, mutate Source Proxy, change runtime behavior, stage, commit, push, branch, create worktrees, clean, stash, reset, checkout, or start Plan 3/24.

## Phase 2.1 Node Identity

### Increment 2.1.1 Hostname, LAN IP, SSH Access, User, And OS Version

- Check run: `ssh -o BatchMode=yes spirit-mac-mini 'hostname; whoami; ipconfig getifaddr en0 ...; sw_vers; ...'`
- SSH alias: `spirit-mac-mini`
- SSH user: `spiritmac`
- Hostname: `spirit-mac-mini.local`
- LAN IP: `10.0.0.147`
- Default gateway: `10.0.0.1`
- Default interface: `en0`
- OS: macOS `15.7.7`
- Build: `24G720`
- Kernel: Darwin `24.6.0`, `x86_64`
- Note: direct `source@10.0.0.147` SSH failed, but configured alias `spirit-mac-mini` succeeded.
- Increment result: GO.

### Increment 2.1.2 Telemetry Identity Visible In SpiritOS

- Check run: `curl -sk --max-time 8 https://127.0.0.1:3000/api/telemetry/cluster`
- Check run: `curl -s --max-time 8 http://10.0.0.147:3187/api/telemetry/self`
- Cluster node id: `spirit-mac-mini`
- Cluster label: `Mac Mini`
- Role: `macos-worker`
- Telemetry URL: `http://10.0.0.147:3187/api/telemetry/self`
- Telemetry status: `online`
- Platform: `darwin`
- Architecture: `x86_64`
- Telemetry capabilities observed: `macos`, `headless-ssh`, `remote-desktop`, `telemetry`, `web-search-worker-ready`, `safari-check-worker-ready`, `docs-index-worker-ready`, `cartographer-observer-ready`
- Cluster summary observed: 3 total nodes, 3 online, 0 offline.
- Increment result: GO.

### Increment 2.1.3 Hardware Profile

- Hardware model: `Macmini8,1`
- Hardware class: Mac Mini 2018
- Memory: `17179869184` bytes, 16 GiB class
- CPU: `Intel(R) Core(TM) i7-8700B CPU @ 3.20GHz`
- Logical CPUs: `12`
- Increment result: GO.

### Phase 2.1 Closeout

- Evidence exists for increments 2.1.1, 2.1.2, and 2.1.3.
- Forbidden scope avoided: no workload migration, hidden worker start, Cart mutation, Source Proxy mutation, branch, worktree, commit, push, cleanup, stash, reset, checkout, or Plan 3 start.
- Checks passed.
- Phase result: GO to Phase 2.2.

## Phase 2.2 Capability Baseline

### Increment 2.2.1 CPU, RAM, Storage, Network, And Uptime

- CPU: Intel i7-8700B, 12 logical CPUs.
- RAM: 16 GiB class.
- Telemetry memory at observation: about 24.4 percent used.
- Root storage: `/dev/disk1s4s1`, 466 GiB size, 10 GiB used, 439 GiB available, 3 percent used by SSH `df`.
- Telemetry storage: about 499.96 GB total, 471.89 GB free, 2.3 percent used.
- Network: `10.0.0.147` on `en0`; gateway `10.0.0.1`.
- Uptime: about 1 day, 13 hours by SSH; telemetry uptime about 134139 seconds.
- Increment result: GO.

### Increment 2.2.2 Docker And macOS Compatibility

- macOS compatibility: confirmed macOS `15.7.7`, Darwin `24.6.0`, x86_64.
- Docker check run: `command -v docker || true; docker --version 2>/dev/null || true`
- Docker observed: no `docker` command output; do not assume Docker is installed or usable.
- Homebrew check run: `command -v brew || true; brew --version 2>/dev/null | head -2 || true`
- Homebrew observed: no `brew` command output; do not assume Homebrew is installed or usable.
- Python check run: `command -v python3 || true; python3 --version 2>/dev/null || true`
- Python observed: `/usr/bin/python3`, Python `3.9.6`.
- Increment result: GO with Docker/Homebrew unavailable or unproven.

### Increment 2.2.3 Service Preference Decision

- Decision: plain-script preference first.
- Reason: SSH, telemetry, and system Python are proven; Docker and Homebrew are not proven by read-only checks.
- Docker service preference: NO-GO until Docker install/status is explicitly proven and approved.
- Homebrew service preference: NO-GO until Homebrew install/status is explicitly proven and approved.
- Plain-script preference: GO for future scoped advisory checks only, not workload migration.
- Increment result: GO.

### Phase 2.2 Closeout

- Evidence exists for increments 2.2.1, 2.2.2, and 2.2.3.
- Forbidden scope avoided: no service start, workload movement, Cart mutation, Source Proxy mutation, hidden worker, branch, worktree, commit, push, cleanup, stash, reset, checkout, or Plan 3 start.
- Checks passed; Docker/Homebrew are explicitly not assumed.
- Phase result: GO to Phase 2.3.

## Phase 2.3 Safety Boundary

### Increment 2.3.1 Cartographer Boundary

- Mac Mini cannot mutate Cartographer while Cartographer is gated.
- Mac Mini cannot touch Cart runtime, queues, workers, approval tokens, trust tiers, live map state, live Cart evidence, or soak behavior while Cartographer remains isolated.
- `cartographer-observer-ready` telemetry capability is not action authority.
- Increment result: GO.

### Increment 2.3.2 Source Proxy Boundary

- Mac Mini cannot write to Source Proxy without explicit approval.
- Mac Mini cannot apply code, execute approved actions, stage, commit, push, branch, create worktrees, clean, stash, reset, or checkout Source Proxy state.
- Source Proxy remains the approval/write gate.
- Increment result: GO.

### Increment 2.3.3 Search And Advisory Boundary

- Mac Mini may run search/advisory jobs only after explicit scope.
- Allowed future outputs after approval: research packets, citations, summaries, candidates, and read-only advisory evidence.
- Forbidden future outputs without approval: repo writes, Cart mutation, Source Proxy mutation, hidden scheduled discovery, hidden workers, workload migration, or promotion claims.
- Increment result: GO.

### Phase 2.3 Closeout

- Evidence exists for increments 2.3.1, 2.3.2, and 2.3.3.
- Forbidden scope avoided: no workload migration, autonomous writes, Cart mutation, Source Proxy mutation, hidden workers, branch, worktree, commit, push, cleanup, stash, reset, checkout, or Plan 3 start.
- Safety boundary is recorded.
- Phase result: GO to Plan 2/24 closeout.

## Plan 2/24 Closeout

- All phases reviewed: Phase 2.1, Phase 2.2, Phase 2.3.
- All increments reviewed: 2.1.1 through 2.3.3.
- Evidence exists: yes.
- Forbidden actions occurred: no.
- Mac Mini support node registration: GO.
- Workload migration: NO-GO.
- Docker-based workload plan: NO-GO until Docker is proven and approved.
- Homebrew-service workload plan: NO-GO until Homebrew is proven and approved.
- Plain-script advisory baseline: GO for future scoped plans only.
- Final Plan 2/24 result: GO for support-node baseline and safety boundary; NO-GO for workload migration or autonomous work.
- Next roadmap plan only: `Plan 3/24: Mac Mini Workload Placement Matrix`.
- Plan 3 started by this packet: `false`.

## Manual Verification Block

```bash
cd /home/source/SpiritOS
git status --branch --short --untracked-files=normal
git rev-parse HEAD
curl -s --max-time 8 http://10.0.0.147:3187/api/telemetry/self
ssh -o BatchMode=yes spirit-mac-mini 'hostname; whoami; ipconfig getifaddr en0; sw_vers; sysctl -n hw.model; sysctl -n hw.memsize; sysctl -n machdep.cpu.brand_string; sysctl -n hw.logicalcpu; df -h /; uptime; command -v docker || true; command -v brew || true; python3 --version'
grep -nE "Plan 2/24|spirit-mac-mini|spiritmac|10.0.0.147|Macmini8,1|17179869184|i7-8700B|Docker|Homebrew|plain-script|cannot mutate Cartographer|cannot write to Source Proxy|Plan 3/24" docs/mac-mini-support-node-plan-2-24-baseline-safety-boundary-v0.1.md
git diff --check -- docs/mac-mini-support-node-plan-2-24-baseline-safety-boundary-v0.1.md
```

## Expected Output

- `git status` shows existing untracked roadmap/evidence files plus this Plan 2 packet.
- `git rev-parse HEAD` prints `caeccea45b18d39f94c463a3376a6eb911256ea8`.
- Telemetry shows `spirit-mac-mini`, status `online`, hostname `spirit-mac-mini.local`, platform `darwin`, macOS `15.7.7`, and 16 GiB class memory.
- SSH shows hostname `spirit-mac-mini.local`, user `spiritmac`, IP `10.0.0.147`, model `Macmini8,1`, memory `17179869184`, CPU `Intel(R) Core(TM) i7-8700B CPU @ 3.20GHz`, 12 logical CPUs, root disk summary, uptime, no Docker/Homebrew command path unless installed later, and Python `3.9.6`.
- `grep` shows the baseline and safety boundary terms.
- `git diff --check` exits cleanly with no output.

## Rollback Guidance

If rollback is required, remove only `docs/mac-mini-support-node-plan-2-24-baseline-safety-boundary-v0.1.md` after explicit Britton approval.

Do not reset, checkout, stash, clean up, broadly restore files, mutate branches or worktrees, push, or force push.
