# Mac Mini Workload Placement Matrix Plan 3/24

Date: 2026-05-27

Roadmap: `docs/masterKeyProxyProduction.md`
Plan: Plan 3/24, Mac Mini Workload Placement Matrix
Mode: PLANNING / NO MIGRATION YET

## Scope

This packet records a workload inventory and placement matrix only. It does not migrate workloads, start services, start hidden workers, mutate Cartographer, touch Cart live evidence, mutate Source Proxy, apply code, stage, commit, push, branch, create worktrees, clean, stash, reset, checkout, or start Plan 4/24.

Baseline inputs:

- Plan 2/24 Mac Mini baseline: `docs/mac-mini-support-node-plan-2-24-baseline-safety-boundary-v0.1.md`
- Mac Mini: `spirit-mac-mini.local`, `10.0.0.147`, user `spiritmac`, Macmini8,1, 16 GiB RAM class, i7-8700B, 12 logical CPUs.
- Proven primitives: SSH alias `spirit-mac-mini`, HTTP telemetry on `http://10.0.0.147:3187/api/telemetry/self`, system Python `3.9.6`.
- Unproven primitives: Docker and Homebrew command paths.

## Phase 3.1 Workload Inventory

### Increment 3.1.1 Scout Workloads

Inventory:

| Workload | Current evidence | Authority needed later |
| --- | --- | --- |
| Manual Scout review packets | Scout v0.8/v0.9 docs and current system-state docs describe Scout as manual-controlled, parked/advisory, and read-only until promoted. | Explicit advisory/search scope. |
| Discovery source review | Scout v0.9 source allowlist, design intake, review grouping, and manual-triggered discovery docs. | Explicit manual-triggered discovery scope. |
| Search result candidate shaping | `scout/docs/V0_3_PHASE2_CONTROLLED_SEARCH_PROVIDER.md` and `scout/docs/V0_3_PHASE3_SEARCH_RESULT_CANDIDATES.md`. | Explicit Plan 4 provider/search boundary. |
| Scout-to-Proxy manual import recommendations | Scout v0.5/v0.6 docs define manual import and dry-run receipt lanes, not automatic proxy memory writes. | Separate Source Proxy approval/write gate. |

Increment result: GO for planning; NO-GO for migration.

### Increment 3.1.2 Subagent Workloads

Inventory:

| Workload | Current evidence | Authority needed later |
| --- | --- | --- |
| Component mapper | Design Agent ecosystem Plan 10 identifies component mapper diagnostic work. | Advisory packet scope only. |
| Safety reviewer | Design Agent ecosystem Plan 10 identifies safety reviewer diagnostic work. | Advisory packet scope only. |
| Test scribe | Design Agent ecosystem Plan 10 identifies test scribe diagnostic work. | Advisory packet scope only. |
| Design packet reviewer | Design Agent Plan C and related closeouts define subagent/read-only packet evidence boundaries. | Advisory packet scope only. |
| Scout research helper | Scout v0.9 and roadmap Plan 5 identify Scout research helper as future advisory subagent work. | Advisory packet scope only. |

Increment result: GO for planning; NO-GO for hidden worker execution.

### Increment 3.1.3 Internet Search Workloads

Inventory:

| Workload | Current evidence | Authority needed later |
| --- | --- | --- |
| Search summaries with citations | Roadmap Plan 4 intends Mac Mini internet search and Scout intake node. | Explicit Plan 4 search routing scope. |
| Candidate source discovery | Scout controlled search provider and source candidate docs. | Manual-triggered search scope and rate limits. |
| Research packet production | Chat workspace and Scout docs support research packet/citation concepts. | Advisory packet scope. |
| Browser/Safari checks | Plan 2 telemetry reports `safari-check-worker-ready`, but that is capability only. | Explicit browser-check scope; no hidden scheduling. |

Increment result: GO for planning; NO-GO for search execution.

### Increment 3.1.4 Telemetry And Dashboard Workloads

Inventory:

| Workload | Current evidence | Authority needed later |
| --- | --- | --- |
| Mac Mini self telemetry | Plan 2 confirms HTTP telemetry endpoint online. | Already registered for visibility only. |
| Cluster dashboard status | `/api/telemetry/cluster` and dashboard docs describe live cluster polling. | Visibility only unless controls are approved. |
| Capability registry facts | README and capability docs describe deterministic capability answers. | Read-only fact display. |
| Service control dashboard | Roadmap Plan 6 reserves SSH/service controls for later. | Explicit service control authority. |

Increment result: GO for planning; NO-GO for new dashboard controls.

### Phase 3.1 Closeout

- Evidence exists for increments 3.1.1 through 3.1.4.
- Forbidden scope avoided: no migration, service start, hidden worker, Cart live evidence access, Cart mutation, Source Proxy mutation, branch, worktree, commit, push, cleanup, stash, reset, checkout, or Plan 4 start.
- Phase result: GO to Phase 3.2.

## Phase 3.2 Placement Decision

### Increment 3.2.1 Placement Matrix

| Workload | Placement | Rationale | Required future gate |
| --- | --- | --- | --- |
| Mac self telemetry | Mac preferred | Already running and observed online; low overhead. | Keep read-only. |
| Cluster dashboard display of Mac telemetry | Server preferred | Server aggregates cluster status; Mac only supplies its own telemetry. | No control buttons without Plan 6 approval. |
| Scout manual review UI/state | Server preferred | Scout state and UI are existing server-side/repo responsibilities. | Scout lane approval. |
| Scout search candidate gathering | Mac preferred later | Mac is suitable for bounded advisory search packets if Plan 4 approves. | Plan 4 search routing. |
| Scout-to-Proxy import/write | Do not move | Source Proxy remains write/apply gate; Mac must not write proxy memory. | Separate Source Proxy approval. |
| Component mapper | Mac preferred later | CPU-bound advisory analysis can fit Mac if run one job at a time. | Plan 5 advisory subagent scope. |
| Safety reviewer | Mac preferred later | Advisory review workload fits read-only packet production. | Plan 5 advisory subagent scope. |
| Test scribe | Server preferred unless read-only | Test writing or running can mutate or depend on repo state; keep server-gated. | Explicit source/test scope. |
| Design packet reviewer | Mac preferred later | Packet review can be advisory and bounded. | Plan 5 advisory subagent scope. |
| Scout research helper | Mac preferred later | Fits advisory/search role. | Plan 4 or Plan 5 scope. |
| Browser/Safari visual checks | Mac preferred later | Safari checks require macOS; still must be explicit and non-hidden. | Browser-check scope. |
| Internet search summaries | Mac preferred later | Fits Mac advisory/search node role. | Plan 4 provider/search approval. |
| Provider/model calls | Server preferred or later | Credentials, cost, and audit should stay centralized until policy exists. | Provider approval. |
| Local LLM inference | GPU node preferred or later | 16 GiB Mac should not be primary local inference host. | Separate compute plan. |
| Always-on worker queue | Do not move | Hidden workers are forbidden; queue authority not granted. | Explicit worker authority, likely re-soak. |
| Repo-writing automation | Do not move | Mac cannot write repo files without explicit approval. | Exact file/write approval. |

Increment result: GO for future scoped setup plans only.

### Increment 3.2.2 Memory-Heavy Jobs Not For 16 GiB Mac

Not Mac preferred:

- Local LLM inference as primary workload.
- Embedding/indexing jobs over large corpora.
- Parallel browser automation plus search plus indexing.
- GPU-heavy vision/model work.
- Long-running multi-agent concurrency.
- Docker-heavy stacks until Docker is proven and memory headroom is measured.

Increment result: GO.

### Increment 3.2.3 Always-On Jobs That Fit The Mac

Fit today or later:

- Current read-only telemetry endpoint.
- Heartbeat/status reporting.
- One bounded advisory search job at a time, after Plan 4 approval.
- One bounded advisory packet reviewer at a time, after Plan 5 approval.
- Optional Safari/browser check worker, after explicit browser-check approval.

Do not fit today:

- Hidden always-on workers.
- Queue consumers.
- Repo-writing daemons.
- Cart runtime, map mutation, approval-token, or trust-tier tasks.

Increment result: GO.

### Phase 3.2 Closeout

- Evidence exists for increments 3.2.1 through 3.2.3.
- Forbidden scope avoided: no migration, service start, hidden worker, Cart live evidence access, Cart mutation, Source Proxy mutation, branch, worktree, commit, push, cleanup, stash, reset, checkout, or Plan 4 start.
- Placement matrix is recorded.
- Phase result: GO to Phase 3.3.

## Phase 3.3 Conflict Model

### Increment 3.3.1 Cart Conflict Rule

If a Mac job touches Cartographer, map, live evidence, runtime, queue, worker, approval-token, trust-tier, or soak behavior, stop and switch to ONE-LANE / CARTOGRAPHER ISOLATED.

Increment result: GO.

### Increment 3.3.2 Repo Write Conflict Rule

If a Mac job writes repo files, applies code, stages, commits, pushes, branches, creates worktrees, cleans, stashes, resets, checkouts, or mutates Source Proxy state, require explicit approval and exact file/action scope.

Increment result: GO.

### Increment 3.3.3 Advisory-Only Parallel Rule

If a Mac job only searches and creates advisory packets, limited parallel mode can be considered after explicit Plan 4 scope. Outputs must be citations, summaries, candidates, or packet drafts only.

Increment result: GO.

### Phase 3.3 Closeout

- Evidence exists for increments 3.3.1 through 3.3.3.
- Forbidden scope avoided: no migration, service start, hidden worker, Cart live evidence access, Cart mutation, Source Proxy mutation, branch, worktree, commit, push, cleanup, stash, reset, checkout, or Plan 4 start.
- Conflict model is recorded.
- Phase result: GO to Plan 3/24 closeout.

## Plan 3/24 Closeout

- All phases reviewed: Phase 3.1, Phase 3.2, Phase 3.3.
- All increments reviewed: 3.1.1 through 3.3.3.
- Evidence exists: yes.
- Forbidden actions occurred: no.
- Placement matrix complete: yes.
- Mac Mini workload migration: NO-GO.
- Mac Mini service start: NO-GO.
- Mac Mini hidden worker authority: NO-GO.
- Mac Mini advisory/search future setup: GO only for next scoped plan.
- Final Plan 3/24 result: GO for placement planning; NO-GO for migration or execution.
- Next roadmap plan only: `Plan 4/24: Mac Mini Internet Search And Scout Intake Node`.
- Plan 4 started by this packet: `false`.

## Manual Verification Block

```bash
cd /home/source/SpiritOS
git status --branch --short --untracked-files=normal
git rev-parse HEAD
grep -nE "Plan 3/24|Scout workloads|Subagent workloads|Internet Search Workloads|Telemetry And Dashboard Workloads|Placement Matrix|Mac preferred later|Server preferred|GPU node preferred|Do not move|NO-GO|Plan 4/24" docs/mac-mini-workload-placement-matrix-plan-3-24-v0.1.md
git diff --check -- docs/mac-mini-workload-placement-matrix-plan-3-24-v0.1.md
```

## Expected Output

- `git status` shows existing untracked roadmap/evidence files plus this Plan 3 packet.
- `git rev-parse HEAD` prints `caeccea45b18d39f94c463a3376a6eb911256ea8`.
- `grep` shows workload inventory, placement classes, conflict boundaries, NO-GO migration/execution state, and next plan title.
- `git diff --check` exits cleanly with no output.

## Rollback Guidance

If rollback is required, remove only `docs/mac-mini-workload-placement-matrix-plan-3-24-v0.1.md` after explicit Britton approval.

Do not reset, checkout, stash, clean up, broadly restore files, mutate branches or worktrees, push, or force push.
