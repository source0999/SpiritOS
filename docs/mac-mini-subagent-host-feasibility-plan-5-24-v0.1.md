# Mac Mini Subagent Host Feasibility Plan 5/24

Date: 2026-05-27

Roadmap: `docs/masterKeyProxyProduction.md`
Plan: Plan 5/24, Mac Mini Subagent Host Feasibility
Mode: SUBAGENT ADVISORY / NO WRITE AUTHORITY

## Scope

This packet records advisory subagent feasibility only. It does not start subagents, create a hidden worker host, create queues, apply code, mutate Cartographer, start Cart workflows, mutate Source Proxy, write repo files from the Mac, stage, commit, push, branch, create worktrees, clean, stash, reset, checkout, or start Plan 6/24.

Baseline inputs:

- Plan 2/24 Mac Mini baseline: `docs/mac-mini-support-node-plan-2-24-baseline-safety-boundary-v0.1.md`
- Plan 3/24 workload placement: `docs/mac-mini-workload-placement-matrix-plan-3-24-v0.1.md`
- Plan 4/24 search routing contract: `docs/mac-mini-internet-search-scout-intake-node-plan-4-24-v0.1.md`
- Mac hardware: Macmini8,1, 16 GiB RAM class, i7-8700B, 12 logical CPUs.
- Proven Mac primitives: SSH alias `spirit-mac-mini`, Python `3.9.6`, curl, osascript, telemetry online.
- Unproven Mac primitives: Docker and Homebrew command paths.

## Phase 5.1 Subagent Inventory

### Increment 5.1.1 Component Mapper

- Role: inspect provided component/file inventories and produce a read-only component map packet.
- Fit: feasible as a bounded CPU-only advisory task.
- Allowed output: component map, ownership notes, uncertainty list.
- Forbidden output: file edits, code generation applied to repo, branch/worktree/git actions.
- Decision: GO for future advisory packet production only.

### Increment 5.1.2 Safety Reviewer

- Role: review proposed plans or packets for authority drift, hidden writes, unsafe scope, and missing manual gates.
- Fit: feasible as a bounded CPU-only advisory task.
- Allowed output: safety findings, blocked reasons, required manual checks.
- Forbidden output: approval-token authority, runtime mutation, source edits, Cart workflow actions.
- Decision: GO for future advisory packet production only.

### Increment 5.1.3 Test Scribe

- Role: draft test ideas, acceptance criteria, and manual verification blocks.
- Fit: feasible only when output remains advisory text.
- Allowed output: test plan packet and suggested commands.
- Forbidden output: writing test files, running test suites, modifying fixtures, changing package/config.
- Decision: GO for advisory drafting; NO-GO for test writes or execution.

### Increment 5.1.4 Design Packet Reviewer

- Role: review design packets for completeness, evidence quality, source/proxy handoff clarity, and safe display boundaries.
- Fit: feasible as a bounded advisory task.
- Allowed output: design packet review, score, missing evidence list.
- Forbidden output: CSS edits, screenshot fabrication, browser automation without scope, Source Proxy mutation.
- Decision: GO for future advisory packet production only.

### Increment 5.1.5 Scout Research Helper

- Role: prepare Scout/search advisory packets using the Plan 4 search boundary.
- Fit: feasible as a bounded search/advisory task.
- Allowed output: citations, summaries, candidate sources, blocked-reason notes.
- Forbidden output: Scout intake writes, discovery job creation, source candidate extraction into Scout state, proxy memory writes.
- Decision: GO for future advisory packet production only.

### Phase 5.1 Closeout

- Evidence exists for increments 5.1.1 through 5.1.5.
- Forbidden scope avoided: no subagent process start, no hidden worker, no queue, no Cart workflow, no Source Proxy mutation, no repo write from Mac, no git mutation, and no Plan 6 start.
- Phase result: GO to Phase 5.2.

## Phase 5.2 Compute Fit

### Increment 5.2.1 CPU-Only Agent Fit

Observed read-only Mac facts:

- Hostname: `spirit-mac-mini.local`
- Memory: `17179869184` bytes
- Logical CPUs: `12`
- Uptime/load at check: about 1 day 13 hours; load averages about `0.93 1.12 1.18`
- Current process sample did not show heavy user workloads.

CPU-only advisory jobs fit if they are bounded, single-shot, and output-only.

Increment result: GO.

### Increment 5.2.2 Memory Budget Per Agent

Memory budget:

| Agent class | Max memory budget | Decision |
| --- | ---: | --- |
| Component mapper | 1.5 GiB | GO |
| Safety reviewer | 1.5 GiB | GO |
| Test scribe | 1.0 GiB | GO advisory only |
| Design packet reviewer | 1.5 GiB | GO |
| Scout research helper | 1.0 GiB plus provider responses | GO after Plan 4 scope |
| Browser/Safari check helper | 2.0 GiB | Later only |
| Local model inference | More than 4 GiB typical | NO-GO on this plan |

Increment result: GO with explicit memory caps.

### Increment 5.2.3 Concurrency Cap For 16GB RAM

Concurrency cap:

- Default cap: one advisory job at a time.
- Burst cap: two lightweight advisory jobs only after telemetry confirms memory pressure remains low.
- Browser automation plus search plus indexing in parallel: NO-GO.
- Local model inference plus any other job: NO-GO.
- Hidden queue/worker concurrency: NO-GO.

Increment result: GO.

### Phase 5.2 Closeout

- Evidence exists for increments 5.2.1 through 5.2.3.
- Forbidden scope avoided: no workload start, no hidden worker, no queue, no Cart workflow, no Source Proxy mutation, no repo write from Mac, no git mutation, and no Plan 6 start.
- Compute fit supports advisory packet production only.
- Phase result: GO to Phase 5.3.

## Phase 5.3 Routing Boundary

### Increment 5.3.1 Mac Subagents Can Prepare Packets

Mac subagents may prepare advisory packets after explicit scope. Minimum packet fields:

```json
{
  "packet_type": "mac_subagent_advisory_packet",
  "subagent_role": "component_mapper",
  "request_id": "mac-subagent-YYYYMMDD-NNN",
  "input_scope": "explicit operator-provided docs or read-only paths",
  "output_scope": "advisory_packet_only",
  "allowed_use": "operator review",
  "forbidden_use": "no apply, no repo write, no Cart workflow, no Source Proxy mutation",
  "manual_decision_needed": true
}
```

Increment result: GO.

### Increment 5.3.2 Mac Subagents Cannot Apply Code

Mac subagents cannot apply code, write files, edit tests, modify configs, stage, commit, push, branch, create worktrees, clean, stash, reset, checkout, or execute approved actions.

Increment result: GO.

### Increment 5.3.3 Mac Subagents Cannot Start Cart Workflows

Mac subagents cannot start Cartographer workflows, mutate `/map`, touch live Cart evidence, consume approval tokens, execute queues, dispatch workers, alter trust tiers, or affect soak behavior.

Increment result: GO.

### Increment 5.3.4 Mac Subagents Report Back To Source Proxy

Mac subagent output returns to Source Proxy or Britton as an advisory packet. Source Proxy remains the write/apply gate, and Britton remains the promotion/approval decision point.

Increment result: GO.

### Phase 5.3 Closeout

- Evidence exists for increments 5.3.1 through 5.3.4.
- Forbidden scope avoided: no apply authority, no Cart workflows, no hidden worker host, no direct commits, no repo writes from Mac, no Source Proxy mutation, and no Plan 6 start.
- Routing boundary is recorded.
- Phase result: GO to Plan 5/24 closeout.

## Plan 5/24 Closeout

- All phases reviewed: Phase 5.1, Phase 5.2, Phase 5.3.
- All increments reviewed: 5.1.1 through 5.3.4.
- Evidence exists: yes.
- Forbidden actions occurred: no.
- Component mapper feasibility: GO advisory only.
- Safety reviewer feasibility: GO advisory only.
- Test scribe feasibility: GO advisory drafting only; NO-GO for test writes/runs.
- Design packet reviewer feasibility: GO advisory only.
- Scout research helper feasibility: GO advisory only after scoped search approval.
- Concurrency cap: one advisory job at a time by default.
- Hidden worker host: NO-GO.
- Apply/code write authority: NO-GO.
- Cart workflow authority: NO-GO.
- Final Plan 5/24 result: GO for advisory subagent feasibility; NO-GO for execution, hidden workers, apply, or Cart workflows.
- Next roadmap plan only: `Plan 6/24: Mac Mini Remote Worker Control And Telemetry Dashboard Integration`.
- Plan 6 started by this packet: `false`.

## Manual Verification Block

```bash
cd /home/source/SpiritOS
git status --branch --short --untracked-files=normal
git rev-parse HEAD
ssh -o BatchMode=yes spirit-mac-mini 'hostname; sysctl -n hw.memsize; sysctl -n hw.logicalcpu; uptime'
grep -nE "Plan 5/24|Component Mapper|Safety Reviewer|Test Scribe|Design Packet Reviewer|Scout Research Helper|one advisory job|mac_subagent_advisory_packet|cannot apply code|Cannot Start Cart|Source Proxy remains|NO-GO|Plan 6/24" docs/mac-mini-subagent-host-feasibility-plan-5-24-v0.1.md
git diff --check -- docs/mac-mini-subagent-host-feasibility-plan-5-24-v0.1.md
```

## Expected Output

- `git status` shows existing untracked roadmap/evidence files plus this Plan 5 packet.
- `git rev-parse HEAD` prints `caeccea45b18d39f94c463a3376a6eb911256ea8`.
- SSH shows hostname `spirit-mac-mini.local`, memory `17179869184`, 12 logical CPUs, and uptime/load.
- `grep` shows subagent role table, one-job concurrency cap, packet type, no-apply/no-Cart/no-hidden-worker boundaries, NO-GO terms, and Plan 6 title.
- `git diff --check` exits cleanly with no output.

## Rollback Guidance

If rollback is required, remove only `docs/mac-mini-subagent-host-feasibility-plan-5-24-v0.1.md` after explicit Britton approval.

Do not reset, checkout, stash, clean up, broadly restore files, mutate branches or worktrees, push, or force push.
