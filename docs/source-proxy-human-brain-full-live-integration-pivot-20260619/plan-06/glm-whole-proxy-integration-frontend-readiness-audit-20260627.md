# GLM Whole Proxy Integration + Frontend Readiness Audit - 2026-06-27

Audit type: Independent, read-only, audit-only. No source/test/runtime/Plan 6 evidence
modified except this report. No fixes implemented. No Plan 7 work started.

Branch audited: `integration/cleanup-plan3-debug-20260623`
HEAD at audit: `02582e3b` (`Harden Plan 6 conditional candidate closeout`)
Working tree at audit: clean except a pre-existing untracked Windows 8.3 short-name
artifact `NDH6SA~M` (the `nul` device-shadow file noted in prior closeouts; not staged,
not touched, not a forbidden path).

This audit goes beyond Plan 6 closeout grading. It inspects the whole Source Proxy /
SpiritOS operator graph end to end: frontend `/coding`, Next v1 canonical routes, Source
Proxy canonical handler, central/apply gates, acceptance/verifier, cartographer control
plane, Mac/Dell lane, search/research lane, packet-generation lane, local-model fallback,
dormant/legacy routes, and operator-visible truth.

## Executive Verdict

The whole proxy graph **is genuinely wired together enough for Britton to begin controlled
personal frontend testing through `/coding`** — with caveats. The canonical apply chain is
real, fail-closed, gate-enforced before any write, and free of production cheating or
hardcoded pass logic. The `/coding` shell drives a live three-step flow
(`prompt-packet -> diff-preview -> execute-approved`), not a decorative mock.

However, the audit found **six honest caveats that bound what a UI trial can and cannot
tell Britton**, and two of them are material to mental-model formation:

1. **Vocabulary mislabel (HIGH, F-01).** The `/coding` shell renders "brain-stage",
   "specialists and workers", "verifier", "repair" labels that imply a multi-agent system,
   but the live shell dispatches **zero** named specialist/subagent/researcher/cartographer
   workers. The entire `/coding` pipeline is a single provider-route prompt->preview->apply
   path. Britton could form an incorrect mental model of "many cooperating agents" when the
   reality is "one model lane plus diagnostic labels."

2. **Plan-6/operator-narrative vocabulary is entirely absent from `/coding` (HIGH, F-02).**
   Britton **cannot** see from `/coding`: the approval token, central gate state, external
   gate, conditional-candidate state, full-GO-denied, Plan 7 unauthorized, Mac worker, Dell
   limitations, acceptance harness, or cartographer. Those concepts live only under the
   separate `/map` feature surface and in Plan 6 docs. Anyone claiming to observe those
   states during a `/coding` trial is not reading them from the live code path.

3. **Authority limits in the UI are hardcoded constants, not gate-read (MEDIUM, F-03).**
   `plan43ControlAuthorityItems` hardcodes `apply_without_approval: false`,
   `commit: false`, `push: false`. These are honest defaults and the backend independently
   enforces them via `central_gate_check("apply")`, but the UI does not read `.gate/state.json`
   or any approval-token state — so the UI cannot reflect a changed gate.

4. **Stale fabricated phase label in the live prompt (MEDIUM, F-04).** The live prompt-packet
   path bakes `CURRENT_PHASE_LABEL = "Phase 7C"` / `CURRENT_INCREMENT_LABEL = "Increment 7C.4"`
   into every prompt when a task mentions the phase, and always bakes `PROXY_AGENT_CONTEXT`
   ("Coder Agent route selected"). Plan 7C does not exist in this repo's plan history (the
   real current state is Plan 6 conditional hardening). This is a real operator-truth
   hazard inside the live `/coding` prompt stream.

5. **Hardcoded telemetry sink (MEDIUM, F-05).** The canonical `/coding` shell makes 16
   fire-and-forget `fetch` calls to a hardcoded `http://localhost:7784/ingest/da155463-...`
   UUID endpoint. This is out-of-band telemetry/analytics, not SpiritOS business logic, but
   it is an undocumented external localhost service that fires during every trial action.

6. **Mac/Dell no-write is enforced inside the remote worker, not at the dispatch/router
   layer (MEDIUM, F-06).** `run_mac_worker_for_task` passes arbitrary `input_data` to the
   remote worker over SSH and only *reports* `mac_write_performed` afterward. The worker
   script does contain a `mac_isolated_write_proof` mode that **does write** to the Mac
   (temp file, immediately rolled back) and reports `mac_write_performed: True`. The
   system honestly declares `write_capable: true, requires_human_first_write: true`, but
   the no-write guarantee for the modes Plan 6 actually used (`system_status`,
   `run_safe_check`) rests on the worker allowlist, not on a router-level guard.

These caveats are real but they do **not** block a controlled UI trial, because the
backend independently enforces the safety boundaries the UI only displays:
- `central_gate_check("apply")` is called at `long_running.py:905` **before** diff
  verification and before any workspace write; on gate failure the task is marked
  `failed_needs_human` and the exception propagates as HTTP 500 fail-closed.
- `central_gate_check("model_call")` is called at `long_running.py:6306` before any LLM call.
- The Next `/v1/actions/execute-approved` route requires `SPIRIT_CODING_USE_PROXY===true`
  and validates `approved: true`, `task_id`, `approved_diff`, `allowed_files`, protected-path
  checks, and approval-id derivation before forwarding.
- The live `.gate/state.json` is non-apply (`status: RUNNING_INCREMENT`,
  `approved_increment: evaluation-round`, notes "no apply approval") — confirmed unchanged.

**Frontend personal testing readiness: `READY_FOR_BRITTON_UI_TRIAL_WITH_CAVEATS`.**
**Daily-driver promotion status: `CONDITIONAL_DAILY_DRIVER_CANDIDATE`** (confirmed, not
upgraded; the whole-proxy evidence is consistent with conditional and adds no basis to
upgrade to full GO).

The expected honest outcome was `READY_FOR_BRITTON_UI_TRIAL_WITH_CAVEATS` and
`CONDITIONAL_DAILY_DRIVER_CANDIDATE`; the evidence supports exactly that, and the caveats
above are the reason it is "with caveats" rather than clean `READY_FOR_BRITTON_UI_TRIAL`.

## Audit Scope

The whole Source Proxy / SpiritOS operator graph as it pertains to whether Britton can
safely begin controlled personal testing through the `/coding` frontend UI without being
misled by decorative labels, scaffolds, dead lanes, proof-only paths, dormant routes,
local-model overreach, fake GO, or unconsumed outputs.

Out of scope (per task constraints): no fixes, no source/test edits, no Plan 6 evidence
edits except this report, no Plan 7, no touching of SpiritFlix/media/Jellyfin/Mac
optimizer/Obsidian/secrets/env/package/generated XML/repomixes/unrelated dirty files,
no push/reset/clean/checkout/rebase/revert/stash.

## Methods / Commands Run

- Read-only inspection of all required Plan 6 docs/JSON (closeout, status.md/json,
  handoff, new-chat, approval manifest, verifier, prior GLM audits).
- `git rev-parse --abbrev-ref HEAD`, `git rev-parse HEAD`, `git status --porcelain`,
  `git diff --stat HEAD` (baseline + worktree cleanliness; only pre-existing
  `NDH6SA~M` untracked).
- Read `.gate/state.json` (live gate state; non-apply confirmed).
- Read the canonical Next route `src/app/v1/actions/execute-approved/route.ts` in full
  (approval/id/diff/allowed-files/protected-path/contract validation, proxy forwarding).
- Read `source_proxy/approval/external_gate.py` in full (`central_gate_check`,
  `_action_allowed`, env-overridable gate-state path, `increment_mismatch`).
- Read `source_proxy/approval/gate.py` in full (`execute_approved_action` ->
  `execute_approved_long_running_task` handoff).
- Read `source_proxy/api/long_running_tasks.py` in full (router, execute-approved endpoint).
- Read `source_proxy/tasks/long_running.py` lines 873-1082 (execute path: gate before write)
  and 6295-6377 (`_call_coder_llm` gate + empty-on-malformed honesty), plus grep for all
  `central_gate_check` call sites.
- Read `source_proxy/main.py` in full (router mounting, write policy).
- Read `source_proxy/decision/mac_integration.py` in full (SSH dispatch, no-write
  reporting, mode allowlist).
- Read `src/lib/mac-worker/client.ts`, `contract.ts`, `types.ts`, and
  `scripts/mac-worker/spirit_mac_worker.py` head + write-proof section (parallel TS lane,
  `SAFE_CHECK_COMMANDS`, `mac_isolated_write_proof`).
- Read `src/app/api/coding/mac-worker/route.ts`, `src/app/v1/coding/codex/route.ts`
  references, `src/app/coding/page.tsx`.
- Read `source_proxy/codex/task_packet.py` and `adapter.py` in full (packet structure,
  codex `config_blocked` defaults).
- Read `source_proxy/decision/prompt_packet.py` in full (live prompt-packet; Phase 7C label,
  constraints, context metadata).
- Read `source_proxy/decision/model_lanes.py` lines 1-310 (`preview_only`, sidecars not
  live, ollama config).
- Read `source_proxy/decision/research.py` head (SearXNG + repo + scout source combining).
- Read `source_proxy/api/coding_self_tests.py` (dry-run-only enforcement).
- Grep/grep-count all `@router.*` decorators in `source_proxy/api/*.py` (route inventory).
- Grep CodingCockpitShell.tsx for `localhost:7784`, `7784/ingest`, `da155463`
  (telemetry sink count = 16).
- Read `plan43ControlAuthorityItems` / `plan43ControlContractItems` blocks in
  CodingCockpitShell.tsx (hardcoded authority display).
- Cheating-token scan across `source_proxy/` and `src/` (excluding tests/tsbuildinfo):
  `forced_pass`, `forced_go`, `fake_productive_go`, `fake_daily_driver_promotion`,
  `bypass_gate`, `status_only_go`, `unconsumed_output`, `skipped_required_lane`,
  `demo_mode`, `synthetic_digest`, `prebaked`, `v4_fallback`, `canned`, `mock_apply`,
  `fake_success`, `hardcoded`, `CONDITIONAL_DAILY_DRIVER_CANDIDATE`, `plan6_`, `PLAN6`.
- Verified duplicate route definitions in `source_proxy/api/cartographer.py`
  (lines 397-583 vs 1234-1401: `live-state`, `approval-token/validate`,
  `consume-preview`, `safe-write`, `verification/run`, `queue/run-next`).
- Dispatched three Explore agents for broad fan-out (frontend route registry; acceptance/
  verifier/cartographer lanes; UI label->invocation mapping). Their findings were
  independently spot-checked against direct reads above; where an agent reported a claim,
  this report only states it after direct source confirmation.

Not replayable on this Windows audit host (documented limitation, same as prior GLM
audits):
- The live `/coding` HTTP 200 probe and the live Next `/v1/actions/execute-approved` ->
  Source Proxy fail-closed HTTP 500 calls rest on the recorded Plan 6 proof JSON; the
  dev server / Source Proxy process is not running on this audit host. The route + gate
  mechanisms were verified against source; the live HTTP behavior was not independently
  re-proven here.
- `operator-check.sh` hard-codes `/home/source/SpiritOS` and cannot run on Windows; its
  assertions were verified by direct file/JSON inspection.

The recorded evidence plus the independently verified gate-state file and source
mechanisms are sufficient to support the verdicts; the un-replayed live-HTTP portions are
documented caveats (F-07), not contradictions.

## Files And Commits Inspected

Plan 6 docs/JSON (all under
`docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-06/`):
- `status.md`, `status.json`, `next-plan-handoff.md`, `new-chat-start.md`
- `plan6-conditional-candidate-hardening-closeout-20260627.md`
- `plan6-conditional-hardening-operator-approval-20260627.json`
- `plan6-conditional-hardening-verifier-20260627.json`
- `glm-plan6-addendum-conditional-candidate-audit-20260627.md`
- `glm-plan6-daily-driver-candidate-integrity-audit-20260626.md`

Production source (canonical path, read in full or substantively):
- `src/app/v1/actions/execute-approved/route.ts`
- `src/app/coding/page.tsx`, `src/app/api/coding/mac-worker/route.ts`
- `src/components/coding/CodingCockpitShell.tsx` (targeted reads; 13452 lines)
- `src/lib/coding/shell-registry.ts`, `route-availability.ts`, `backend-truth-surface.ts`,
  `durable-run-store.ts`, `source-proxy-origin.ts`, `approval-gate-binding.ts`
- `src/lib/mac-worker/client.ts`, `contract.ts`, `types.ts`
- `source_proxy/main.py`, `approval/external_gate.py`, `approval/gate.py`,
  `api/long_running_tasks.py`, `tasks/long_running.py` (canonical path sections),
  `api/coding_self_tests.py`
- `source_proxy/decision/mac_integration.py`, `prompt_packet.py`, `model_lanes.py`,
  `research.py`, `router.py`
- `source_proxy/codex/task_packet.py`, `codex/adapter.py`
- `source_proxy/acceptance/plan5_acceptance.py` (denylist), `verification/` (imports)
- `source_proxy/api/cartographer.py` (route inventory + duplicate-route scan),
  `cartographer/{service,apply,safe_write,autopilot_apply,autopilot_config,trust_score,
  trust_tier_decision_gate,autonomy_promotion,final_proof_stage_1_gauntlet,
  level_2_apply,level_2_readiness}.py` (via Explore agent + spot checks)
- `scripts/mac-worker/spirit_mac_worker.py`
- `.gate/state.json`

Commits: HEAD `02582e3b`; Plan 6 recent commits `06c92f30`, `0e953ef5`, `40fa8b80`,
`b68d6c06`, `154dfa9b`.

## Baseline / Scope Lock

Verified against the task's required baseline:

- Branch: `integration/cleanup-plan3-debug-20260623`. **CONFIRMED.**
- HEAD: `02582e3b`. **CONFIRMED.**
- Current Plan 6 status: `PLAN6_CONDITIONAL_CANDIDATE_HARDENING_COMPLETE`. **CONFIRMED**
  (status.md line 3, status.json `status`).
- Recommendation: `CONDITIONAL_DAILY_DRIVER_CANDIDATE`. **CONFIRMED** (status.json
  `daily_driver_promotion_recommendation`).
- Full daily-driver promotion: `NOT_APPROVED`. **CONFIRMED** (status.json
  `full_daily_driver_promotion`, `proof_summary.full_daily_driver_go: false`).
- Plan 7: `NOT_STARTED / NOT_AUTHORIZED`. **CONFIRMED** (status.json `plan7_status`,
  `next_plan_authorized: false`).
- Product-code readiness is **not** claimed. **CONFIRMED**
  (`product_code_changed: false`, `remaining_limitations` lists
  `no_product_code_daily_driver_readiness`).
- Mac write authority is **not** claimed. **CONFIRMED**
  (`phase_6_4_mac_write_occurred: false`, `no_first_mac_write` in limitations).
- Broad apply authority is **not** claimed. **CONFIRMED** (`no_unrestricted_apply_readiness`).
- Worktree status: clean except pre-existing untracked `NDH6SA~M` (Windows 8.3 name for
  the `nul` device-shadow file; present before this audit; not staged; not a forbidden
  path). **CONFIRMED.**

Baseline is true. No scope contradiction found.

## Whole Subsystem Inventory

Classification legend: CA = canonical-active (live in `/coding -> proxy` apply path);
SA = supporting-active (live, read-only or persistence, not apply); AG = apply-gated-active
(can mutate only via central gate + approval); FV = frontend-visible-only (shown but not
invocable from `/coding`); PO = proof-only; DM = dormant; LG = legacy; TO = test-only;
SC = scaffold; UP = unknown/needs proof.

| Subsystem / lane | Files/routes/functions inspected | Classification | Frontend reachable? | Output consumed downstream? | Operator-visible? | Proof/evidence | Caveats/gaps |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `/coding` route | `src/app/coding/page.tsx` | CA | YES (the entry) | Renders shell | YES | Renders `<CodingCockpitShell/>` + Receipt/Trace anchors | Imports `dashboard-demo-v4.css` (cosmetic name) |
| CodingCockpitShell | `src/components/coding/CodingCockpitShell.tsx` (13452 lines) | CA | YES | Drives 3 canonical + ~13 supporting routes | YES (ledgers) | Drives live prompt-packet/diff-preview/execute-approved | Vocabulary mislabel (F-01); hardcoded authority (F-03); telemetry sink (F-05) |
| `prompt-packet` (Next) | `src/app/v1/decisions/prompt-packet/` | CA | YES | Forwards to Source Proxy | YES | In `codingApiRouteRegistry` canonical | — |
| `diff-preview` (Next) | `src/app/v1/verification/...` | CA | YES | Forwards to Source Proxy | YES | Canonical in registry | — |
| `/v1/actions/execute-approved` (Next) | `src/app/v1/actions/execute-approved/route.ts` | CA | YES | Forwards to `/v1/tasks/long-running/{id}/execute-approved` | YES | Validates approved/task_id/diff/allowed_files/protected-paths; requires `SPIRIT_CODING_USE_PROXY` | The single apply authority boundary |
| Source Proxy canonical handler | `source_proxy/api/long_running_tasks.py`, `approval/gate.py`, `tasks/long_running.py` | CA | via Next route | YES (causal trace) | YES | `execute_approved_action -> execute_approved_long_running_task` | Gate before write confirmed (long_running.py:905) |
| Central gate / apply gate | `source_proxy/approval/external_gate.py` (`central_gate_check`) | AG | NO (backend-only) | YES (receipt) | via receipts only | Reads `.gate/state.json`; `increment_mismatch` real | Not surfaced in `/coding` UI (F-02) |
| Acceptance harness | `source_proxy/acceptance/plan5_acceptance.py` | PO | NO | NO (test only) | NO | `FORBIDDEN_PLAN5_STATES` denylist; imported only by its test | Not in live apply path |
| Phase verifier | `source_proxy/verification/{diff,contracts}.py` | CA | NO | YES (in apply path) | via result | Imported by `long_running.py`; runs before/during apply | — |
| Verification runner (cartographer) | `cartographer/verification_runner.py` | SA | via `/v1/cartographer` only | NO from `/coding` | NO from `/coding` | argv-allowlist command runner | Separate from `/coding` apply path |
| Browser/operator proof lane | `mac_worker browser_design_check`, design-vault preview | FV/PO | design-vault preview route exists | NO live | advisory JSON | `advisory_only`, `preview_only` | Not wired to live apply |
| Research / SearXNG lane | `source_proxy/decision/research.py`, `scout_research.py` | SA | `research-preview` route is **dormant** in registry | advisory | `research_route` shown in ledger | Combines repo + scout + SearXNG sources | Not invoked live from `/coding` shell (F-08) |
| Repo/context lane | `research.py REPO_RESEARCH_PATHS`, `context_inventory.py`, `context_index.py` | SA | workspace-read route (read-only) | YES (prompt context) | via prompt packet | Source-owned path listing | Sources are repo-owned, not model-synthesized |
| Packet-generation lane | `codex/task_packet.py`, `prompt_packet.py`, `packet_decomposition.py` | SA/PO | `codex` route is **dormant** in registry | packet built for paste-back | `proposed_diff` in preview | Well-formed packet; codex adapter `config_blocked` | Codex escalation is dormant (F-09) |
| Local model lane | `decision/model_lanes.py`, `tasks/long_running.py:_call_coder_llm` | AG | via prompt-packet (model hint) | YES (LLM output) | `model_lane` in `/v1/self/status` | `preview_only`, ollama `http://127.0.0.1:11434`, `central_gate_check("model_call")` | Returns "" on malformed (honest); uncertainty does not auto-escalate (F-10) |
| Codex handoff lane | `codex/adapter.py`, `src/app/v1/coding/codex/route.ts` | DM | codex route dormant (emits `plan4_route_status: dormant`) | NO | header only | `config_blocked`, `would_run_task: false` | Dormant; not auto-invoked |
| GLM audit lane | (this report) | PO | NO | NO | this report | n/a | n/a |
| Mac worker lane | `decision/mac_integration.py` (SSH), `src/lib/mac-worker/` (TS), `api/coding/mac-worker/route.ts` | AG/SA | `/v1/coding/mac-worker` POST route exists; not invoked by `/coding` shell | consumed by cartographer consumer in Plan 6 proof | capability descriptor | `write_capable: true, requires_human_first_write: true`; `SAFE_CHECK_COMMANDS` allowlist | No-write enforced in remote worker not router (F-06); `mac_isolated_write_proof` mode writes (rolled back) |
| Dell/Mac dispatch | `mac_integration.py` (single SSH alias) | AG | NO from `/coding` | Plan 6 proof only | proof JSON | Dell vs Mac not distinguished in UI | F-11 |
| Verifier/diff preview lane | `verification/diff.py` (`preview_diff_verification`) | CA | YES (diff-preview) | YES | preview result | Runs in execute path | — |
| Repair lane | `decision/artifact_repair_loop.py`, `parser_repair_used` reason | SA | NO (backend) | `parser_repair_used` flag | via reason code | No client "repair agent"; backend repair attempts | Vocabulary implies agent (F-01) |
| Refusal lane | `execute-approved` returns 4xx; `central_gate_check` raises `ExternalGateError` | AG | YES (HTTP status) | task `failed_needs_human` | via status | Decision-bearing; cannot launder | — |
| Degraded-lane honesty lane | `model_lanes` `known_failure_modes`, `hardline_integration.reject_go_like_label` | SA | via `/v1/self/status` | advisory | status | `status_only_go`/`unconsumed_output` detection | Real anticheat, not decorative |
| Dormant/advisory routes | `research-preview`, `helper-agents/preview`, `gauntlet/preview`, `cartographer/preview`, `design-vault/preview`, `mac-advisory` | DM/FV | routes exist | advisory JSON only | `advisory_only`, `preview_only` | All authority flags false | Honest dormancy; could mislead if treated as active (F-12) |
| Specialists/workers/subagents shown in UI | CodingCockpitShell ledgers | FV | NO live dispatch | diagnostic labels | ledger rows | `provider_call_made` real; "specialist/worker" is wording | No Architect/Debugger/Scout agents dispatched (F-01) |
| Cartographer control plane | `source_proxy/api/cartographer.py` (134 routes), `cartographer/*.py` | SA/SC | via `/v1/cartographer/*` (not `/coding`) | status/observation mostly | status payloads | Most functions `*_authority_granted=False`; `apply.py` + `safe_write.py` + `autopilot_apply.py` mutate (gated) | Duplicate route definitions (F-13); Level 11-14 scaffold |
| Agent-lab / trial infra | `src/app/v1/coding/agent-lab-*`, `trial-*`, `hermes-stress-smoke` | TO/SA | routes exist | baseline/sweep/reconcile | run store | test-adjacent plumbing | Not in registry (untracked surface) |
| self-tests passthrough | `src/app/v1/coding/self-tests/run` -> `api/coding_self_tests.py` | TO | route exists | dry-run results | diagnostic | **dry_run mode only** (HTTP 400 on other modes) | Blind passthrough but backend forces dry-run |

## Runtime Path Trace Findings

The canonical active path was traced end to end:

```
/coding (GET) -> CodingCockpitShell.tsx
  -> POST /v1/decisions/prompt-packet (Next) -> Source Proxy /v1/decisions/prompt-packet
       (builds PromptPacket; route_decision; constraints; "Coder Agent route selected")
  -> POST /v1/verification/diff-preview (Next) -> Source Proxy /v1/verification/diff-preview
       (preview_diff_verification; gated by central_gate_check for apply, not for preview)
  -> POST /v1/actions/execute-approved (Next)
       validates: approved=true, task_id, approved_diff, allowed_files, protected paths,
                  approval_id derivation, SPIRIT_CODING_USE_PROXY===true
       -> forwards to Source Proxy /v1/tasks/long-running/{taskId}/execute-approved
            -> execute_approved_action (approval/gate.py)
            -> execute_approved_long_running_task (tasks/long_running.py:873)
                 -> central_gate_check("apply", run_id) at line 905   <-- BEFORE any write
                      on failure: task -> failed_needs_human, raise -> HTTP 500 fail-closed
                 -> approval_id_for_approved_diff re-derivation/match
                 -> preview_diff_verification (verification/diff.py) re-run
                 -> _apply_verified_diff (the ONLY write) at line 1024
                 -> backup manifest + audit log + ast_snapshot
                 -> task -> applied_needs_verification
```

**Frontend-reachable active lanes** (3 canonical + supporting persistence): prompt-packet,
diff-preview, execute-approved, `/v1/coding/runs*`, `/v1/self/status`,
`/v1/coding/{workspace-read, trial-receipt-reconcile, trial-fixture-baseline,
agent-lab-baseline, agent-lab-sweep, hermes-stress-smoke}`.

**Backend-only lanes** (live but not directly invoked from `/coding`): central gate, phase
verifier (`verification/diff.py`), repair loop, model_call gate, cartographer control plane.

**Proof-only lanes**: `plan5_acceptance` (imported only by its test), `final_proof_stage_*`
(all `would_execute=False`), Level 11-14 autonomy runtime dataclasses.

**Dead/dormant lanes** (routes exist, registry-flagged dormant, authority flags false):
`codex`, `bounded-diff-preview`, `research-preview`, `helper-agents/preview`,
`gauntlet/preview`, `cartographer/preview`, `design-vault/preview`, `mac-advisory`.

**Lanes visible in UI but not invocable from `/coding`**: cartographer, acceptance harness,
Mac worker, approval token, central/external gate — these concepts are **absent from
CodingCockpitShell.tsx** (zero matches) and live only under the separate `/map` feature.

**Lanes invocable but not consumed downstream**: none found in the canonical path. The
diff-preview output is consumed by execute-approved; prompt-packet output is consumed by
diff-preview and the UI ledgers; the apply output is consumed by the durable run store
(`preserveServerApplyProof`). The Mac lane output is consumed by
`cartographer_mac_assignment_consumer` in the Plan 6 proof path but not by the live
`/coding` apply path.

## Dormant / Legacy Route Scan

Enumerated all registered Source Proxy routers (`source_proxy/api/*.py`) and Next routes
under `src/app/v1/` and `src/app/api/` touching `/coding`, Mac worker, Source Proxy, or
operator lanes.

Source Proxy API route counts (production surface): cartographer 134, long_running_tasks 11,
decision 9, sandbox_terminal 4, runtime_status 3, workspace_tools 2, diff_verification 2,
codex_adapter 2, chat 2, and 8 single-route modules.

Classification highlights:

- **canonical-active**: `long_running_tasks` (the apply endpoint), `decision`
  (prompt-packet + route decisions), `diff_verification` (preview + apply verification),
  `healthcheck`, `self_status`, `runtime_status`, `workspace_tools` (read-only),
  `context_inventory`/`context_index` (read-only).
- **supporting-active**: `cartographer` (control plane; status/observation; gated apply),
  `action_preview`, `chat`, `scout_intake`, `obsidian_context`, `tools_manifest`,
  `coding_self_tests` (dry-run only), `sandbox_terminal`.
- **dormant/legacy (Next side)**: `src/app/v1/coding/codex/route.ts` and
  `bounded-diff-preview/route.ts` emit `x-spiritos-plan4-route-status: dormant` headers,
  require `SPIRIT_CODING_USE_PROXY===true` to even forward, and on proxy failure return 200
  with all authority flags false. They point to the canonical replacement chain. **Honest
  dormancy.**
- **preview/advisory-only**: `research-preview`, `helper-agents/preview`, `gauntlet/preview`,
  `cartographer/preview`, `design-vault/preview`, `mac-advisory` — all return
  `advisory_only`/`preview_only` with all authority flags false. Cannot dispatch, apply,
  commit, or push.

Central-gate / execute-boundary analysis:

- **No route under `src/app/v1/coding/` can bypass the execute-approved boundary.** Every
  mutating route (codex, bounded-diff-preview) is dormant + env-gated and fails closed.
- **No Source Proxy route can apply/write without `central_gate_check("apply")`.** The live
  apply path calls it at `long_running.py:905` before the write at line 1024.
  `cartographer/apply.py` and `safe_write.py` and `autopilot_apply.py` also call
  `central_gate_check("apply")` before their (gated, scoped) writes.
- **One latent hazard (F-13)**: `source_proxy/api/cartographer.py` defines six routes twice
  (`live-state`, `approval-token/validate` GET+POST, `consume-preview` GET+POST,
  `safe-write` GET+POST, `verification/run` GET+POST, `queue/run-next` GET+POST). FastAPI
  shadows the first definition with the second for the same path. The duplicate
  `safe-write` POST handlers are currently functionally equivalent, so behavior is benign
  today, but this is a real reviewability/correctness hazard in the cartographer control
  plane. None of these are reachable from `/coding`; they are `/v1/cartographer/*` only.
- **Could a dormant route confuse Britton during frontend testing?** Not from `/coding`:
  the dormant/advisory routes are not invoked by the canonical shell. They could confuse
  an operator hitting them directly via `/v1/coding/codex` etc., but each honestly labels
  itself `dormant`/`advisory_only`. (F-12, LOW.)

## UI Label To Invocation Mapping

The active `/coding` shell is `CodingCockpitShell.tsx`. It invokes **16 distinct live
network endpoints** (3 canonical + supporting + a hardcoded telemetry sink). The canonical
three-step flow (`prompt-packet -> diff-preview -> execute-approved`) is **genuinely
driven** with real `fetchWithTimeout` calls and an endpoint-status state machine.

| UI label | Frontend file/component | Actual function/route invoked | Output contract | Downstream consumer | Operator-visible artifact | Classification |
| --- | --- | --- | --- | --- | --- | --- |
| prompt-packet / "Coder Agent route selected" | CodingCockpitShell prompt path | POST `/v1/decisions/prompt-packet` -> `prompt_packet.build_prompt_packet` | PromptPacket payload | diff-preview + UI ledger | proposed_diff, route decision | CA (live) |
| diff-preview / "verifier" | CodingCockpitShell preview path | POST `/v1/verification/diff-preview` -> `verification/diff.preview_diff_verification` | verifier result, changed files | execute-approved gate | blocked reason codes | CA (live) |
| execute-approved / "route_backed_apply" | CodingCockpitShell apply path | POST `/v1/actions/execute-approved` -> `execute_approved_long_running_task` | task + execution + causal_trace | durable run store | applied run receipt | CA (live) |
| "specialists and workers" ledger | `plan42SpecialistWorkerItems` | **none** (state-derived display) | n/a | display only | provider_call_made flag | **FV (decorative)** |
| "brain-stage" timeline | stage timeline render | **none** (reads previewState) | n/a | display only | status mirror | **FV (decorative)** |
| "trial_worker" | state label | **none** (reversibleSuiteState mirror) | n/a | display only | progress | **FV (decorative)** |
| "Hermes" / configured local model | hermes-stress-smoke + self/status | POST `/v1/coding/hermes-stress-smoke` -> `/v1/chat/completions` | stress smoke result | display | model lane status | CA (live, stress) |
| "repair" / `parser_repair_used` | reason code | backend repair attempts | reason code | flag | reason | SA (no client agent) |
| "verifier" / verifierSummary | diff-preview response | `/v1/verification/diff-preview` | verifier summary | gate | summary | CA (live) |
| task_id / trace_id / output_hash / invocation_event_id | ledgers | populated from live responses | causal fields | display | ledger rows | CA (live-derived, may be null) |
| Mac worker / cartographer / acceptance / approval token / central gate / external gate | **absent** | **not invoked** | n/a | n/a | n/a | **absent from /coding** |

Flagged labels:
- **No corresponding live invocation**: "specialist"/"subagent"/"researcher"/"lane"(as
  worker)/"cartographer"/"acceptance harness"/"Mac worker" — all **absent** or decorative
  in CodingCockpitShell.tsx. The multi-agent vocabulary has no backing dispatch.
- **Only static decoration**: "brain-stage", "specialists and workers", "trial_worker".
- **Only proof-only wiring**: cartographer/acceptance appear only in Plan 6 proof JSON,
  not in the live `/coding` path.
- **No operator-visible result for absent labels**: Britton cannot see central gate, approval
  token, conditional-candidate, or Plan 7 status from `/coding`.

## Mac / Dell Lane Findings

- **Dispatch mechanism**: two parallel implementations.
  - Python: `run_mac_worker_for_task` (`decision/mac_integration.py`) runs
    `ssh spirit-mac-mini ... python3 scripts/mac-worker/spirit_mac_worker.py`, passing a
    JSON job over stdin. Used by Plan 6 Phase 6.4 proof (via the task layer).
  - TS: `src/lib/mac-worker/client.ts` `runMacWorkerJob` does the same SSH (or local
    subprocess if `SPIRIT_MAC_WORKER_TRANSPORT=local`), invoked by
    `src/app/api/coding/mac-worker/route.ts` POST.
- **Frontend reachability**: the `/v1/coding/mac-worker` POST route exists and is reachable,
  but **the CodingCockpitShell does not invoke it** (zero "Mac" matches in the shell). It is
  not part of the live `/coding` apply flow.
- **No-write enforcement location**: enforced **inside the remote worker script**
  (`SAFE_CHECK_COMMANDS` allowlist for `run_safe_check`; `system_status` is read-only),
  **not at the dispatch/router layer**. `run_mac_worker_for_task` passes arbitrary
  `input_data` to the worker and only *reports* `mac_write_performed` afterward. This is
  the F-06 gap: the router trusts the worker to self-limit.
- **Mac worker script safety**: `system_status` and `run_safe_check` (allowlisted git
  commands) are no-write. **However**, the worker also implements `mac_isolated_write_proof`
  which **does write** a temp proof file to the Mac and reports `mac_write_performed: True`
  (then unlinks it). This mode is honestly declared but is a real Mac write capability.
- **Mac optimizer/media worker paths**: not touched by `mac_integration.py` (generic module;
  no optimizer/media tokens). Protected.
- **Dell vs Mac distinguished**: **NO.** There is a single `spirit-mac-mini` SSH alias; no
  Dell node is modeled. The "Dell/Mac dispatch" naming in Plan 6 is aspirational; the
  implementation is Mac-only.
- **Output consumed downstream**: in Plan 6 proof, Mac output consumed by
  `cartographer_mac_assignment_consumer` + `plan6_phase_gate_consumer`. In the live `/coding`
  path, Mac output is **not** consumed (the lane is not invoked).
- **Operator-visible result**: capability descriptor (`write_capable: true,
  requires_human_first_write: true`) is available via `/v1/coding/mac-worker` GET but not
  surfaced in `/coding` shell.

**Does `/coding` imply more Mac/Dell authority than exists?** No — `/coding` does not
mention Mac/Dell at all (F-02). The Mac lane's own descriptor honestly declares
`write_capable: true` but `requires_human_first_write: true`. The risk is the inverse: the
operator narrative ("Mac/Dell dispatch proven in Plan 6") is **not visible from `/coding`**,
so a UI trial cannot validate it.

## Search / Research Lane Findings

- **SearXNG/research configuration**: `decision/research.py` reads `SEARXNG_URL` env; if
  unset, internet search is skipped (returns only repo + scout sources). The
  `run_local_research_preview` combines repo-owned sources, scout sources, then SearXNG.
- **Research lane code path**: `run_repo_research_preview` (over `REPO_RESEARCH_PATHS`) ->
  `run_scout_research_preview` -> SearXNG (optional).
- **Frontend reachable**: **NO live invocation from `/coding`**. The `research-preview`
  Next route is **dormant** in the shell registry (`dormantReason` documented) and returns
  static advisory JSON. The shell shows a `research_route` ledger field but does not call a
  research route live.
- **Sources source-owned vs model-owned**: repo sources are **source-owned** (real repo
  file paths in `REPO_RESEARCH_PATHS`); scout sources come from `scout_research.py`; SearXNG
  results are raw URL references. No model-synthesized sources in the research path.
- **Internet-required fail-closed**: if `SEARXNG_URL` is missing, the function returns
  without internet sources rather than fabricating them. Honest fail-closed.
- **Research separated from implementation/verifier proof**: research feeds the prompt
  context (`research_sources` on PromptPacket); it does not feed the verifier or the apply
  gate. Separation holds.
- **Can packet generation use research without laundering into GO?** Research sources
  attach to `PromptPacket.research_sources` as references. They cannot trigger apply; apply
  requires `central_gate_check("apply")` + approved diff. No laundering path found.

**Set A's research durability** (the durable, source-owned research capability) is **not
meaningfully reachable from the frontend daily-driver workflow** today — the research route
is dormant and the `/coding` shell does not call it. The research capability exists in
source but is not wired into the live `/coding` trial. (F-08.)

## Packet Quality And Stronger-Model Handoff Findings

`build_codex_task_packet` (`codex/task_packet.py`) produces a well-formed packet. Coverage
of the required fields:

| Required packet field | Present? | Notes |
| --- | --- | --- |
| branch / HEAD / repo status | YES | `current_branch`, `current_head` via `_git_value` |
| durable task state snapshot | PARTIAL | task_summary + source_task_id; not a full run snapshot |
| current step | NO | not modeled |
| prior failures | NO | not in packet |
| success criteria for this trace | NO | not explicit |
| objective | YES | `task_summary` |
| relevant repo context | YES | `relevant_files` |
| research sources if used | NO (in codex packet) | research_sources live on PromptPacket, not codex packet |
| allowed paths | YES | `allowed_files` |
| forbidden paths | YES | `forbidden_files` |
| authority level | YES | all four authority flags `false` |
| apply gate state | NO | gate state not embedded in packet |
| local model confidence / fallback reason | NO | not embedded |
| validation commands | YES | `manual_checks_required` (git status, git diff --check) |
| proof requirements | PARTIAL | via `expected_output_format` |
| stop conditions | PARTIAL | via `safety_rules` ("Stop if the target is ambiguous") |
| commit rules | YES | `safety_rules`: "Do not commit", "Do not push" |
| final response format | YES | `expected_output_format` |
| caveats / handoff | PARTIAL | `rollback_instruction` |

The Codex adapter (`codex/adapter.py`) defaults to `status: config_blocked`,
`would_run_task: false`, `can_run_live_task: false` unless a `codex` binary is found and
version-probed. It blocks `--dangerously-bypass-approvals-and-sandbox`, `--yolo`, and
`danger-full-access` sandboxes.

**Can the system say "too complex for local; here is a packet for Codex/GLM/GPT" without
pretending it completed?** The local model path (`_call_coder_llm`) returns `""` (empty) on
malformed/empty completion — it does **not** fabricate success. There is a `CODER_BLOCKED:`
self-declaration protocol. However, the **automatic** escalation from local-model
uncertainty to packet generation is **not wired into the live `/coding` path**:
`brain_switch_advisory_from_model_lane_attempts` exists and can recommend
`LOCAL_DECOMPOSITION_RECOMMENDED`, but the codex handoff route is dormant and no code path
in the live apply chain auto-emits a stronger-model packet on local uncertainty. (F-09,
F-10.) So the honest "here's a packet" capability exists as a function but is not
automatically triggered; a UI trial would not see automatic escalation.

## Frontend Readiness Findings

`/coding` (CodingCockpitShell) readiness checklist:

| Check | Result | Detail |
| --- | --- | --- |
| Shows conditional candidate state | **NO** | zero matches in shell |
| Shows full GO denied | **NO** | absent |
| Shows Plan 7 unauthorized | **NO** | absent |
| Shows approval token / external gate visibility | **NO** | absent from shell |
| Shows apply authority as limited | **PARTIAL** | hardcoded constants `apply_without_approval: false`, `commit: false`, `push: false` in `plan43ControlAuthorityItems`; not gate-read (F-03) |
| Shows level/boundary constraints | PARTIAL | `route_backed_apply` shows `/v1/actions/execute-approved` when approved |
| Shows task id | **YES** | ledger |
| Shows trace id | **YES** | ledger (may be null) |
| Shows receipt | **YES** | AppliedRunReceipt, reconciled via trial-receipt-reconcile |
| Shows output hash | **PARTIAL** | `output_hash` field; populated only when backend returns it |
| Shows route | **YES** | `routeCalled`, `provider_model_source_route_at_apply_time` |
| Shows blocked/refused/degraded states | **PARTIAL** | `blocked` status + reason codes surfaced; "refused"/"degraded" absent |
| Shows packet output clearly | **YES** | `proposed_diff` consumed from prompt-packet |
| Shows no hidden apply success | **YES** | apply requires explicit approved=true + gate |
| Shows stop/cancel/resume truth | **YES** | `route_backed_suite_stop`, `resume_from_prompt` |
| Shows Mac/Dell limitations honestly | **NO** | absent from shell (F-02) |
| Shows research/source limitations honestly | **PARTIAL** | `research_route` shown but research route is dormant (F-08) |
| Does not imply product-code readiness | **YES** | no product-code claims in shell |
| Does not imply broad apply readiness | **YES** | hardcoded limits + backend gate |
| Does not imply Mac write readiness | **YES** | Mac not mentioned in shell |

**Specifically**: `/coding` does **not** surface current approval-token state, central/external
gate state, or honest "apply authority: limited" messaging derived from gate state. The
authority display is hardcoded constants that happen to be correct defaults, but the UI
cannot reflect a changed gate. This is acceptable for a controlled trial (the backend
enforces the gate regardless) but means a UI trial cannot *validate* the gate from the UI.

The shell does **not** read `.gate/state.json` or any approval-token file.

## Local Model / Packet Fallback Findings

- **Local model invocation path**: `_call_coder_llm` (`long_running.py:6298`) calls
  `get_router().completion(model=alias, ...)`. `alias` resolves to ollama models
  (`qwen2.5-coder:7b`, `hermes4:latest`, `gemma3n:e4b`) at `http://127.0.0.1:11434`.
- **Model selection/fallback**: `model_lanes.py` registry is `metadata_only_no_model_calls`
  with `sidecar_lanes_live: False`. Primary coder lane = `qwen_local_coder`. Sidecars
  (hermes, gemma) are `preview`/`future` and not executed.
- **Local-vs-external decision logic**: `decide_route` (router.py) classifies the task
  (implementation/codebase_analysis/current_research) and sets a model hint; the live coder
  path uses the local ollama model. External/paid routes are gated by spend-before-send
  approval (`approval/gate.py SpendApprovalRequired`).
- **Can local-model uncertainty trigger packet generation?** **Not automatically in the
  live path.** `brain_switch_advisory_from_model_lane_attempts` can recommend
  `LOCAL_DECOMPOSITION_RECOMMENDED`, which feeds `local_decomposition` into the PromptPacket,
  but the codex packet route is dormant and no live code auto-emits a stronger-model packet
  on local uncertainty. (F-09, F-10.)
- **Can fallback silently pretend success?** **NO.** On empty/malformed completion,
  `_call_coder_llm` returns `""`. There is no canned-success path. The `CODER_BLOCKED:`
  protocol lets the model self-declare a block with a reason code.
- **Is packet mode visible in the UI?** The Codex route is dormant; packet mode is not a
  visible UI mode in `/coding`. The prompt-packet *is* visible (proposed_diff).
- **Clean handoff artifact?** `build_codex_task_packet` produces a clean, well-structured
  packet with rollback instructions and safety rules. But it is not auto-emitted.
- **Codex/GLM/GPT escalation explicit and source-backed?** The packet's `safety_rules`
  explicitly forbid commit/push/apply and require file-change reporting. The handoff is
  explicit *if invoked*, but invocation is manual/dormant.
- **Are local model failures decision-bearing?** Yes — empty output propagates as empty,
  which blocks the diff-preview/apply chain. No silent success.

**No path found where a local model can produce fake confidence or an unconsumed output.**
The empty-on-malformed behavior is the key honesty guarantee. The gap is the *absence* of
automatic escalation (F-09), not the presence of fake success.

## Cheating / Hardcoding Findings

Cheating-token scan across `source_proxy/` and `src/` (excluding tests/tsbuildinfo/plan-06 docs):

| Token | Hits | Classification |
| --- | --- | --- |
| `fake_productive_go` | `acceptance/plan5_acceptance.py` | **acceptable instrumentation** — in `FORBIDDEN_PLAN5_STATES` denylist (states the harness rejects) |
| `status_only_go` | `decision/hardline_integration.py` | **acceptable instrumentation** — detection flag (`not status_only_go_detected`) |
| `unconsumed_output` | `hardline_integration.py`, `plan5_acceptance.py` | **acceptable instrumentation** — detection/denylist |
| `skipped_required_lane` | `plan5_acceptance.py` | **acceptable instrumentation** — denylist |
| `fake_go` | `tasks/durable_execution.py` | **acceptable instrumentation** — `not any(fake_go_detected.values())` guard |
| `synthetic_digest` | `tests/test_plan3_stage4r_packet_runner.py` | test-only |
| `bypass` | `long_running.py:2009`, `api/decision.py:7859` | **acceptable** — anti-bypass comments/instructions ("Do not bypass the portal") |
| `CONDITIONAL_DAILY_DRIVER_CANDIDATE`, `plan6_`, `PLAN6` | **none** in production source or frontend | clean — recommendation value lives only in Plan 6 docs/JSON |
| `FULL_DAILY_DRIVER_GO`, `daily_driver_promotion` | **none** in frontend | clean |
| `forced_pass`, `forced_go`, `bypass_gate`, `demo_mode`, `prebaked`, `v4_fallback`, `canned`, `mock_apply`, `fake_success`, `hardcoded` | **none** in canonical apply path | clean |

**Hardcoded values found (operator-truth concerns, not cheating):**
- `prompt_packet.py`: `CURRENT_PHASE_LABEL = "Phase 7C"`, `CURRENT_INCREMENT_LABEL =
  "Increment 7C.4"` baked into live prompts. Plan 7C does not exist in this repo's plan
  history. **F-04.**
- CodingCockpitShell.tsx: `plan43ControlAuthorityItems` hardcoded authority flags. **F-03.**
- CodingCockpitShell.tsx: 16 hardcoded `http://localhost:7784/ingest/da155463-...` telemetry
  fetches. **F-05.**
- `macWorkerCapabilityDescriptor`: `write_capable: true, requires_human_first_write: true`
  hardcoded (honest declaration). Not a defect.

**No suspicious production behavior, no hardcoded pass logic, no proof tailoring detected**
in runtime/frontend paths. The Plan 6 recommendation value lives only in Plan 6 docs/JSON,
not in production code or the frontend.

## Protected-Scope Findings

Clean. This audit performed read-only inspection only. `git status --porcelain` shows only
the pre-existing untracked `NDH6SA~M` (Windows 8.3 `nul` shadow; not staged, not touched).
`git diff --stat HEAD` is empty (no source/test/runtime edits by this audit).

None of the following were touched, staged, or implied as safe for frontend trial by this
audit:
- SpiritFlix, media, Jellyfin, Obsidian — absent from all audit operations.
- Mac optimizer/media workers — not invoked; `mac_integration.py` is generic.
- secrets/env files — `.env.local`, `.env.example` exist but were only listed (for the
  `SPIRIT_CODING_USE_PROXY` check), never read/modified/staged.
- package files (`package.json`, lockfiles) — not touched.
- generated XML packs — not touched.
- `repomixes/` — not touched.
- Plan 7 or outside-Plan-6 work — not started; no `plan-07` directory exists.
- external irreversible systems — no push/reset/clean/checkout/rebase/revert/stash
  performed; no Mac write performed.

## Gap Table

| Gap ID | Severity | Area | Evidence | Impact | Risk of false confidence during UI trial | Fix before Britton UI trial? | Recommendation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| F-01 | HIGH | UI vocabulary vs reality | CodingCockpitShell renders "brain-stage", "specialists and workers", "verifier", "repair" but dispatches zero named agents; single model lane + diagnostic labels | Britton may form a multi-agent mental model when reality is one provider-route pipeline | High | optional | Britton should be briefed before the trial that `/coding` is a single-lane prompt->preview->apply pipeline, not a multi-agent swarm. The labels are diagnostic, not agents. |
| F-02 | HIGH | Plan-6/operator narrative absent from /coding | Zero matches in CodingCockpitShell for approval token, central gate, external gate, conditional candidate, full-GO-denied, Plan 7, Mac worker, Dell, acceptance harness, cartographer | A `/coding` UI trial cannot validate the Plan 6 safety narrative; those concepts live only in /map and Plan 6 docs | High | no | Accept for trial. Britton must read Plan 6 status.md/json, not the UI, for gate/promotion truth. Do not expect to see gate state in `/coding`. |
| F-03 | MEDIUM | UI authority not gate-read | `plan43ControlAuthorityItems` hardcodes `apply_without_approval: false`, `commit: false`, `push: false`; does not read `.gate/state.json` | UI cannot reflect a changed gate; defaults are correct but not enforced-by-state at UI layer | Medium | optional | Backend independently enforces the gate, so safety holds. Optional future: have the UI read gate state. Not a blocker. |
| F-04 | MEDIUM | Stale fabricated phase label in live prompt | `prompt_packet.py` bakes "Phase 7C" / "Increment 7C.4" into prompts; Plan 7C does not exist | Live prompts carry a fabricated phase label; operator-truth hazard in the prompt stream | Medium | optional | Britton should avoid tasks mentioning "phase"/"increment" during the trial, or accept that the prompt carries a stale label. Optional future: remove the hardcoded phase or make it env-driven. |
| F-05 | MEDIUM | Hardcoded telemetry sink | 16 `fetch("http://localhost:7784/ingest/da155463-...")` in CodingCockpitShell | Out-of-band localhost telemetry fires on every trial action; undocumented external service | Low (localhost) | optional | Britton should be aware telemetry posts to localhost:7784 during the trial. Optional future: gate behind env or document it. |
| F-06 | MEDIUM | Mac no-write enforced in worker not router | `run_mac_worker_for_task` passes arbitrary input to remote worker; only reports `mac_write_performed` afterward; worker has `mac_isolated_write_proof` write mode | No-write guarantee rests on remote worker allowlist, not router-level guard | Low (not invoked from /coding) | no | Accept for trial (Mac lane not invoked from `/coding`). For any future Mac trial, restrict modes at the router before dispatch. |
| F-07 | LOW | Verification realism | Live `/coding` HTTP probe and execute-approved fail-closed HTTP 500 calls not re-run on this Windows host; `operator-check.sh` is Linux-only | Live/operator-surface claims rest on recorded Plan 6 JSON | Low | no | Replay `operator-check.sh` and a live fail-closed probe on the Linux runtime before any promotion beyond CONDITIONAL. |
| F-08 | LOW | Research lane not live from /coding | `research-preview` route dormant in registry; `/coding` shell does not call a research route | A UI trial cannot exercise durable source-owned research | Low | no | Accept for trial. Research is a source capability, not a `/coding` live path. |
| F-09 | LOW | Codex/stronger-model escalation dormant | `codex` route dormant; no live auto-escalation from local uncertainty to packet | A UI trial cannot exercise automatic "too complex, here's a packet" | Low | no | Accept for trial. The packet function exists and is well-formed; auto-invocation is a future enhancement. |
| F-10 | LOW | Local model uncertainty does not auto-trigger packet | `brain_switch_advisory` exists but no live code auto-emits a packet on local uncertainty | Local model returns "" on failure (honest) but does not auto-hand off | Low | no | Accept for trial. No fake success; the gap is absence of auto-escalation. |
| F-11 | LOW | Dell vs Mac not distinguished | Single `spirit-mac-mini` SSH alias; no Dell node modeled | "Dell/Mac dispatch" naming is aspirational; implementation is Mac-only | Low | no | Accept for trial. Mac lane is not invoked from `/coding` anyway. |
| F-12 | LOW | Dormant routes could mislead if hit directly | `codex`, `research-preview`, etc. emit dormant/advisory labels but exist as routes | An operator hitting them directly might misread advisory JSON as active | Low | no | Accept for trial (not invoked from `/coding`). Routes honestly self-label. |
| F-13 | LOW | Duplicate cartographer route definitions | `api/cartographer.py` defines 6 routes twice (lines 397-583 vs 1234-1401); FastAPI shadows first with second | Latent reviewability/correctness hazard in cartographer control plane; currently benign (handlers equivalent) | Low (not reachable from /coding) | no | Optional future: deduplicate. Not reachable from `/coding`; does not affect the UI trial. |
| F-14 | INFO | demo/v4 naming | `/coding/page.tsx` imports `dashboard-demo-v4.css`; design-vault preview references it | Cosmetic name only; no demo/v4 behavior in live path | Low | no | None. Cosmetic. |
| F-15 | INFO | self-tests passthrough | `/v1/coding/self-tests/run` forwards verbatim to backend | Backend forces `dry_run` mode only (HTTP 400 otherwise) | Low | no | None. Backend constrains it. |

No BLOCKER findings. Two HIGH findings (F-01, F-02) are mental-model/truth-visibility
concerns, not safety violations — they are addressable by briefing Britton before the trial,
not by code changes. All safety boundaries are backend-enforced regardless of UI display.

## Recommended Britton UI Trial Tasks

These tasks are scoped to what `/coding` can actually exercise live, in increasing order of
authority. Each is safe to run now given the backend gate is non-apply.

1. **Read-only status task** (safe now)
   - Task text: "Show me the current repo status, branch, and HEAD."
   - Expected behavior: prompt-packet returns a read-only packet; no diff; no apply.
   - Pass signal: `/v1/self/status` returns model lane + approval boundaries; no apply
     attempted; task_id/trace_id appear in ledger.
   - Fail signal: any apply attempt or a "completed" apply receipt.
   - Authority required: none (read-only).

2. **Diff-preview-only task** (safe now)
   - Task text: "Propose a one-line comment addition to a Plan 6 docs file and show me the
     diff preview only."
   - Expected behavior: diff-preview returns a proposed diff with changed files; apply is
     NOT triggered.
   - Pass signal: `proposed_diff` shown; `route_backed_apply` shows `locked`; no applied
     receipt.
   - Fail signal: an apply succeeds without explicit approval, or the gate is bypassed.
   - Authority required: none (preview only).

3. **Forbidden-path refusal task** (safe now)
   - Task text: "Apply a change to `.env`."
   - Expected behavior: execute-approved rejects with `protected path in approved_diff`
     (HTTP 403) before reaching the proxy; or diff-preview blocks it.
   - Pass signal: HTTP 403 / blocked reason code; no `.env` mutation.
   - Fail signal: `.env` is touched or staged.
   - Authority required: none (refusal).

4. **Fail-closed apply probe** (safe now)
   - Task text: "Attempt to execute-approved on a docs target without an approval token."
   - Expected behavior: `central_gate_check("apply")` raises `increment_mismatch` (gate is
     `evaluation-round`, not an apply increment); HTTP 500 fail-closed; task ->
     `failed_needs_human`.
   - Pass signal: HTTP 500; `failed_needs_human`; gate state unchanged.
   - Fail signal: apply succeeds, or gate state changes.
   - Authority required: none (fail-closed).

5. **Packet-generation task** (safe now)
   - Task text: "Generate a prompt-packet for an implementation task and show me the
     paste-back instructions."
   - Expected behavior: prompt-packet returns constraints, requested output, paste-back
     instructions, route decision.
   - Pass signal: packet visible; `target_model_hint`; no apply.
   - Fail signal: apply triggered or packet claims completion.
   - Authority required: none.

6. **Stop/cancel/resume test** (safe now)
   - Task text: "Start a reversible trial suite, then stop it, then resume."
   - Expected behavior: durable run store records stop/resume; `route_backed_suite_stop`
     shows `/v1/coding/runs/[runId]`; `resume_from_prompt` unlocks.
   - Pass signal: run state transitions are recorded and resumable.
   - Fail signal: hidden apply during stop/resume.
   - Authority required: none (browser/local state).

7. **Local-model stress smoke** (safe now, requires ollama running)
   - Task text: "Run the Hermes stress smoke."
   - Expected behavior: POST `/v1/coding/hermes-stress-smoke` -> `/v1/chat/completions`;
     returns a stress result.
   - Pass signal: model lane status surfaces; `provider_call_made: true`; no apply.
   - Fail signal: apply triggered or fake success on empty completion.
   - Authority required: model_call gate (gate is `evaluation-round` which allows
     `model_call`? verify — the live token notes "model_call approval"; if blocked, expect
     fail-closed, which is also a valid pass).

8. **Complex local-model fallback packet task** (safe now, expected to degrade honestly)
   - Task text: "Refactor a large file across many modules."
   - Expected behavior: local model either returns content (if capable) or returns "" /
     `CODER_BLOCKED:` (if not). No automatic Codex escalation (F-09).
   - Pass signal: either a real diff-preview, or an honest empty/blocked response — never a
     fake success.
   - Fail signal: fake confidence, unconsumed output, or silent success.
   - Authority required: model_call gate.

9. **Research-with-sources task** (safe now, expected to be dormant)
   - Task text: "Research the current coding route decisions and cite sources."
   - Expected behavior: research route is dormant; the shell shows `research_route` in the
     ledger but does not invoke a live research call (F-08).
   - Pass signal: no fabricated sources; if SearXNG_URL unset, no internet sources returned.
   - Fail signal: model-synthesized sources presented as real research.
   - Authority required: none.

10. **Mac no-write task** (safe now, not reachable from /coding)
    - Task text: "Run a Mac system_status dispatch."
    - Expected behavior: only reachable via `/v1/coding/mac-worker` or the Python task
      layer, NOT from `/coding` shell; returns read-only system status; `mac_write_performed:
      false`.
    - Pass signal: read-only status; no Mac write.
    - Fail signal: Mac write outside the `mac_isolated_write_proof` mode, or write without
      rollback.
    - Authority required: none for `system_status`/`run_safe_check` modes.

**Important briefing before the trial**: Britton must understand that (a) `/coding` is a
single model-lane prompt->preview->apply pipeline, not a multi-agent swarm (F-01); (b) the
Plan 6 gate/promotion/conditional-candidate narrative is NOT visible from `/coding` and must
be read from Plan 6 status.md/json (F-02); (c) the live gate is non-apply, so any apply
attempt should fail-closed; (d) the prompt may carry a stale "Phase 7C" label (F-04); (e)
telemetry posts to localhost:7784 (F-05).

## Final Grades

- **Whole proxy integration grade: B+ (87/100).** The canonical apply chain is genuinely
  wired end to end, gate-enforced before write, fail-closed, free of production cheating,
  and free of hardcoded pass logic. Points deducted for: vocabulary mislabel implying
  multi-agent (F-01), operator narrative absent from `/coding` (F-02), stale phase label in
  live prompts (F-04), Mac no-write enforced in worker not router (F-06), dormant
  research/escalation lanes not wired into `/coding` (F-08, F-09), and duplicate cartographer
  routes (F-13). None of these are safety violations; they are truth-visibility and
  mental-model concerns.

- **Frontend readiness grade: B (83/100).** The shell is genuinely live for its core
  three-step flow and honestly hardcodes conservative authority limits. Points deducted for:
  authority not gate-read (F-03), gate/promotion/conditional state invisible (F-02),
  vocabulary mislabel (F-01), telemetry sink (F-05), and research/escalation not live (F-08,
  F-09). Ready for a controlled trial with briefing.

- **Packet-generation readiness grade: B+ (88/100).** `build_codex_task_packet` is
  well-formed with allowed/forbidden files, branch/head, checks, safety rules, rollback, and
  all authority flags false. Codex adapter defaults to `config_blocked`. Points deducted for:
  missing fields (current step, prior failures, success criteria, gate state, local-model
  confidence), dormant escalation (F-09), and research sources not embedded in the codex
  packet.

- **Daily-driver promotion grade: B+ (88/100).** Consistent with the prior addendum audit.
  The whole-proxy evidence corroborates `CONDITIONAL_DAILY_DRIVER_CANDIDATE` and adds no
  basis to upgrade to full GO. Full GO remains blocked by: no product-code soak, no Mac
  write authority, no broad apply authority, no external approval-token enforcement,
  self-instrumented consumer/verifier identities, and un-replayed live-HTTP portions (F-07).

## Final Verdicts

**Frontend personal testing readiness: `READY_FOR_BRITTON_UI_TRIAL_WITH_CAVEATS`.**

The `/coding` shell is genuinely live, the canonical apply chain is gate-enforced and
fail-closed, and no production cheating or fake-GO path exists. Britton can safely begin
controlled personal testing through `/coding` provided the six caveats (F-01 through F-06)
are understood beforehand. The two HIGH caveats (F-01 vocabulary mislabel, F-02 operator
narrative absent) are mental-model concerns addressable by briefing, not safety blockers —
all safety boundaries are backend-enforced regardless of UI display.

**Daily-driver promotion status: `CONDITIONAL_DAILY_DRIVER_CANDIDATE`.**

The whole-proxy graph supports the current `CONDITIONAL_DAILY_DRIVER_CANDIDATE` status. It
should NOT be downgraded before frontend testing (the canonical path is sound and honest),
and it should NOT be upgraded to full GO (the prior blockers remain: no product-code soak,
no Mac write, no broad apply, no external approval enforcement). The whole-proxy audit
corroborates the conditional recommendation; it does not change it.

**Final recommendation:** Proceed with a controlled Britton UI trial of `/coding` after
briefing Britton on F-01 (single-lane pipeline, not multi-agent) and F-02 (read Plan 6
status.md/json for gate/promotion truth, not the UI). Do not promote beyond CONDITIONAL.
Do not start Plan 7. Replay `operator-check.sh` and a live fail-closed probe on the Linux
runtime before any future promotion decision.

Confirmations:
- Only this audit report was modified by this audit; `git diff --stat HEAD` is empty for all
  source/test/runtime files.
- No Plan 7 or outside-Plan-6 files changed.
- Forbidden paths (SpiritFlix/media/Jellyfin/Mac optimizer/Obsidian/secrets/env/package/
  generated XML/repomixes) were not touched or staged.
- No package/env/generated XML/repomix files were staged.
- No push/reset/clean/checkout/rebase/revert/stash occurred during this audit.
- Plan 7 was not started; no `plan-07` directory exists.
- The real `.gate/state.json` was read and confirmed non-apply
  (`status: RUNNING_INCREMENT`, `approved_increment: evaluation-round`, "no apply approval").

GLM_WHOLE_PROXY_FRONTEND_READINESS_AUDIT_READY_FOR_BRITTON_REVIEW
