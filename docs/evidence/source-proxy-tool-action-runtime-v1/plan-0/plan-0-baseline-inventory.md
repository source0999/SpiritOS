# Source Proxy Tool Action Runtime v1 Plan 0 Baseline Inventory

Status: Plan 0 evidence, docs-only.

## Source Of Truth

- Active roadmap: `docs/source-proxy-tool-action-runtime-v1-master-plan.md`.
- Active handoff: `docs/source-proxy-tool-action-runtime-v1-new-chat-handoff.txt`.
- Active index entry: `docs/plan-index.md`.
- Supporting Plan 8 handoff: `docs/evidence/agent-runtime-trial-harness/plan-8/plan-8-pivot-evidence.md`.
- Supporting future-roadmap packet: `docs/evidence/agent-runtime-trial-harness/plan-8/future-roadmap-request-packet.json`.
- Supporting final grade: `docs/evidence/agent-runtime-trial-harness/plan-7/final-grade-report.json`.
- Supporting lane-plumbing diagnosis: `docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/lane-plumbing-repair/diagnosis.md`.
- Supporting lane-plumbing closeout: `docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/lane-plumbing-repair/closeout.md`.
- Mac advisory boundary: `docs/mac-worker-operator-contract.md`.

## Precedence

The active Source Proxy Tool Action Runtime v1 roadmap supersedes older benchmark, preflight, and context-orchestration documents for this runtime-hands pivot. Older docs remain evidence only. Benchmarking, stress testing, model comparisons, provider/model routing changes, safe apply, Cartographer mutation, hidden workers, branch/worktree mutation, commit, push, and final CSS polish remain blocked until a later approved plan explicitly authorizes them.

## Phase 0.1 Source Confirmation

- Plan 8 evidence says the harness reached S+ evidence while real frontend use remained `REMEDIATION REQUIRED`.
- The future-roadmap packet says the next roadmap requires Britton approval and forbids Codex-like feature implementation, final CSS polish, safe apply, provider/model routing changes, Cartographer activation, hidden workers, commit, or push.
- The lane-plumbing diagnosis identifies the missing adapter as a workspace-only executor for model-authored Write/Edit/MultiEdit/Bash calls or explicit path/content blocks.
- The lane-plumbing closeout says Source Proxy Qwen was NO-GO and no full gauntlet, other models, or Plan 4 started.
- The Mac worker contract keeps Mac support advisory/check-only; Source Proxy remains the approval/write gate.

GO/NO-GO: GO for Phase 0.1. Source evidence is available and aligned.

## Phase 0.2 Capability Inventory

### /coding Composer And Surfaces

- `src/app/coding/page.tsx` renders `CodingCockpitShell`.
- `src/components/coding/CodingCommandCenterShell.tsx` contains current task/composer state, safe preview controls, allowed/changed file display, preview evidence, trial diagnostics, Mac advisory run state, and advisory helper copy.
- `tests/e2e/coding-ui.spec.mjs` smokes `/coding` and checks that apply-approved diff controls are absent.
- `tests/ui-agent-trials/*` contains historical UI trial fixtures and diagnostics contracts.

### Existing Action Preview, Parser, And Workspace Pieces

- `source_proxy/api/action_preview.py` exposes `POST /v1/actions/preview` and delegates to `build_action_preview`.
- `source_proxy/api/workspace_tools.py` exposes bounded `/v1/workspace/list` and `/v1/workspace/read` endpoints.
- `source_proxy/context/workspace_tools.py` backs read/list behavior with output limits and structured errors.
- `source_proxy/verification/diff.py` contains unified-diff changed-file parsing and verification helpers.
- `source_proxy/decision/proposal_task.py`, `source_proxy/safety/paths.py`, and router tests contain bounded proposal/path safety helpers.
- Existing pieces are not yet the Plan 1-3 native TaskSpec plus generic model-authored tool/action executor.

### Source Proxy Routing And Context

- `source_proxy/decision/router.py` classifies tasks, resolves explicit/inferred targets, identifies unsafe/protected target conditions, and recommends routes.
- `source_proxy/decision/prompt_packet.py` builds prompt packets and context metadata; it still describes Coder Agent output as strict replacement content rather than the new generic action envelope.
- `source_proxy/agents/registry.py` defines provider capabilities as recommendation-only, with no approval/apply/commit/push authority.
- `source_proxy/api/tools_manifest.py`, `source_proxy/api/self_status.py`, and related tests expose current route/tool capability truth.

### Mac, Scout, Search, Design Review, And Helper Packets

- `scripts/mac-worker/spirit_mac_worker.py` supports `system_status`, safe allowlisted checks, repo context search, trial context assist, Scout research packet, browser/design check metadata, and source proxy context discovery.
- `docs/mac-worker-operator-contract.md` keeps Mac support advisory/check-only and forbids direct fixes, Cartographer mutation, provider routing changes, secret access, hidden workers, and autonomous write authority.
- `source_proxy/agents/registry.py` contains advisory swarm roles and provider capability truth.
- `source_proxy/context/source_readiness.py`, Scout docs, and design-agent evidence describe advisory/proposal-only helper boundaries.

GO/NO-GO: GO for Phase 0.2. Existing surfaces are mapped enough to start Plan 1 without implementation.

## Phase 0.3 Pivot Guard

The active roadmap and handoff already contain the pivot guard:

- Benchmarking stays paused until native hands are complete.
- Native hands mean TaskSpec intake, generic tool/action contract and parser, disposable workspace executor, authority validator, bounded loop, receipts, UI diagnostics, Mac/subagent advisory boundaries, and trap-suite proof.
- Fair benchmark comparison requires model-authored generic actions, model-decided paths/content, validation before execution, disposable workspace containment, transcript/action/diff/check/receipt evidence, and no hidden scaffolding.

GO/NO-GO: GO for Phase 0.3. The pivot guard is present and no runtime implementation occurred.

## Forbidden Scope Avoided

No source/runtime files were edited. No provider/model calls, trial prompts, benchmark reruns, safe apply, Cartographer actions, hidden workers, branch/worktree operations, commit, push, stash, reset, checkout, clean, or final CSS polish occurred.
