# SpiritOS Campaign 2 Plan

## Identity, status, and firewall

- Campaign: `spiritos-campaign-2`, core coding-OS stabilization.
- Mutable root: `/home/source/SpiritOS-campaign-2-20260716` on branch `codex/spiritos-campaign-2-core-coding-os-20260716`; base `8a20473c2260bc132e595c64230d3fdfc9fef97f` (Campaign 1 terminal tip).
- Protected heads: Source Proxy `594d66ef8280953af767a273d7c91be765d1a6eb`; SpiritFlix `5fde4ae064d471e1133e00d6bf25fb5aecb5d196`; architecture audit `05612d2ae358bc01b6ef997243137649f8d65f14`; Campaign 1 worktree `8a20473c` (read-only terminal GO).
- Never mutate protected product worktrees, product branches, services, SpiritFlix's borrowed `_worktrees/`, or the Campaign 1 worktree. Do not push or begin Campaign 3.

Status vocabulary: `completed` means committed and verified; `not_started` means no accepted implementation exists; `partial` means bounded work exists but is not accepted; `blocked` means an external prerequisite is required; `invalidated` means current evidence contradicts the recorded claim.

## Entry-condition revalidation (Campaign 1 closure)

Campaign 2 is authorized because all four Campaign 1 entry conditions are satisfied:

1. Campaign 1 has explicit full-GO closeout with authenticated browser lifecycle proof: `GO_CAMPAIGN_1_COMPLETE`, receipt `docs/evidence/e2e-loop/2026-07-15T23-36-28-866Z/result.json` (`truth_status=GO`, `commit_safe=true`).
2. Protected heads and borrowed-worktree policy revalidated at closeout (Campaign 1 ledger line 19).
3. Campaign 1 ledger/state/evidence index agree on the same final checkpoint (`8a20473c`, `campaign1_complete`).
4. Product owner authorized Campaign 2 scope in this plan.

If any of these is contradicted by runtime evidence during Campaign 2, halt and record the contradiction before continuing.

## Campaign goal and terminal verdict

### The problem

The core coding OS already has real guarded capabilities, but an operator cannot yet rely on one **canonical, repeatable coding run** to carry a change safely from discovered work through execution, review, verification, and durable evidence. Today those capabilities are strong local protections rather than one enforced end-to-end reliability property:

- The long-running executor applies only an approved diff and re-checks the durable approval binding (`source_proxy/tasks/long_running.py:1157`); the approval authority persists and consumes identity-bound approvals (`scripts/approval-authority.py:92-220`). Those protections are real, but neither defines a single mandatory sequence for every core participant.
- The canonical context broker can produce and acknowledge context consumption (`source_proxy/context/canonical_broker.py:12-381`), and task helpers can record an acknowledgement (`source_proxy/tasks/long_running.py:3676-3728`). A caller can still enter other task and decision paths without a common run-level record that every applicable participant consumed the same context.
- Review, functional verification, anti-cheat, and evidence validation exist (`source_proxy/planning/reviewer.py:40-136`, `source_proxy/decision/verifier_lane.py:15-233`, `source_proxy/verification/anticheat/detectors.py:143`, and `source_proxy/approval/campaign_evidence.py:6-37`). They are invoked by particular verification, specialist, or task paths rather than being required and sequenced by one core-run contract.
- TypeScript chooses a LumaCart target packet and Python resolves it fail-closed (`src/lib/coding/target-plugins/index.ts:18-42`; `source_proxy/target_plugins/adapter.py:183-224`). Cartographer can discover projects and produce an approval-bound selection (`source_proxy/cartographer/project_discovery.py:112-175`; `source_proxy/cartographer/cartographer_selection_authority.py:1-120`), but the selection handoff is not a canonical coding-task entry. The existing lane registry is expressly `model-only` and advisory (`source_proxy/cartographer/lane_registry.py:8-10, 85-235`).
- The durable task machine recovers the lifecycle of one task (`source_proxy/tasks/durable_execution.py:19-93`), not the participation, failure, and recovery state of every core participant. Consequently, a partial run can leave an operator with subsystem-specific receipts rather than one truthful answer to: which required work happened, which authority and context bound it, what failed, what recovered, and whether the final result is safe to trust.

The operator-visible gap is therefore not a missing named component. It is the absence of a single accountable coding-run outcome: a supported coding task cannot yet be run repeatedly with a complete, non-bypassable chain of context, authority, execution, review, verification, recovery, and evidence, then be judged from one coherent receipt.

### Canonical goal

Campaign 2 makes a core coding task **operationally dependable**: from one supported entry point, the system must either produce a truthful, identity-bound receipt showing that every applicable mandatory participant performed meaningful work under the same current context and approved authority, or stop/degrade with the exact failing participant, reason, and recoverable state. An operator must be able to repeat that task from a clean isolated baseline without hidden state or a silently substituted model/provider changing the claim.

A skeptic can observe the goal is met only when all of the following are true:

1. A supported core coding task has one versioned, fail-closed definition of who may participate, what each participant accepts and returns, what failure and acknowledgement mean, and which evidence proves it; incompatible or unversioned callers cannot quietly enter the run.
2. The same task has one accountable run record from discovery/context through approved execution, review, verification, bounded repair when needed, and evidence. Each applicable participant is recorded as genuinely performed, skipped with a documented reason, failed, or recovered; no component may be counted by a no-op, isolated helper, or stale identity.
3. Authority, target identity, context acknowledgement, provider/fallback outcome, and final evidence remain mutually consistent throughout the run. A mismatch, missing acknowledgement, stale target, or hidden fallback fails closed or reports degradation rather than producing a success claim.
4. If an expected, controlled fault occurs, the run exposes the fault and its recovery/degraded outcome. A fresh clean rerun thereafter completes with a non-empty, reversible, verified result and no inherited success state.

Every gate in this plan directly serves that goal: 2.1 establishes the versioned participant contract; 2.2 sequences and records the run; 2.3 makes context consumption accountable; 2.4 makes routing/fallback claims truthful; 2.5 preserves target identity across the wire; 2.6 binds execution authority to the participant; 2.7 makes review, verification, anti-cheat, and evidence part of the accountable outcome; 2.8 supplies a safe discovered-work entry; 2.9 recovers participant-level interruption; 2.10 exposes the run truth to the operator; and 2.11 demonstrates the complete reliability property. No gate is retained merely because it names an implementation mechanism.

Terminal verdict: `CAMPAIGN_2_CORE_CODING_OS_STABLE`. It is valid only after every mandatory gate is accepted and the core proving task passes from a clean isolated baseline, a controlled failure has been injected and recovered truthfully, and a subsequent clean rerun passes. Campaign 3 is not started by this closeout.

## Critical: Campaign 2 is NOT greenfield

A precise audit of the base commit shows that most of the core coding OS already exists and is authoritative. Campaign 2 must **adopt** what exists, **extend** what is partial, and **build** only the genuine gaps. Rebuilding existing machinery is a scope violation.

| Component | Verdict | Anchor |
| --- | --- | --- |
| Canonical context broker + consumption acknowledgement | ADOPT as-is | `source_proxy/context/canonical_broker.py:12,22,254` |
| Durable executor + approval authority | ADOPT as-is | `source_proxy/tasks/long_running.py:1157,1217,1234` |
| Coding authority wrapper (consume/finalize, target binding) | ADOPT as-is | `source_proxy/approval/campaign_authority.py:26,47,72,157` |
| Reviewer | ADOPT as-is | `source_proxy/planning/reviewer.py:15,40,101` |
| Verifier + diff/contract verification | ADOPT as-is | `source_proxy/decision/verifier_lane.py:11`, `source_proxy/verification/` |
| Anti-cheat (15 detectors) | ADOPT as-is | `source_proxy/verification/anticheat/detectors.py:143` |
| Evidence recorder + acknowledgement envelope | ADOPT as-is | `source_proxy/approval/campaign_evidence.py:6,20,37` |
| Target-plugin identity binding | ADOPT as-is | `source_proxy/target_plugins/adapter.py:35,55,183` |
| Cartographer discovery + proposals + AR-002 selection | ADOPT as-is | `source_proxy/cartographer/` |
| 10-prompt LumaCart battery + grader + e2e harness | ADOPT as-is | `src/lib/coding/target-plugins/lumacart/`, `scripts/run-coding-e2e-loop.mjs` |
| Lane registry (path-ownership vocabulary) | EXTEND to authority-bearing | `source_proxy/cartographer/lane_registry.py:8,71-80,200` |
| Source Proxy routing + health | EXTEND with explicit fallback | `source_proxy/api/healthcheck.py:12`, `source_proxy/routing/` |
| Task lifecycle durable state machine | EXTEND to lane-level recovery | `source_proxy/tasks/durable_execution.py:19-93,185,398` |
| Shell status endpoints | EXTEND to canonical observability | `source_proxy/api/runtime_status.py`, `source_proxy/api/self_status.py` |
| Canonical orchestrator + lane-state machine | BUILD net-new | (none today; only per-task SM exists) |
| Lane-scoped authority | BUILD net-new | (today authority is per-consumer, not per-lane) |
| Cartographer selection wired into coding executor | BUILD net-new | (no `consume_cartographer_selection` in `tasks/`) |
| Versioned lane contract schema | BUILD net-new | (0 lane schemas in `packages/contracts/`) |

## Naming-collision hazards (READ BEFORE NAMING ANYTHING)

The word "lane" is overloaded in this codebase. Do not reuse these names for new Campaign 2 concepts:

- `lane_registry` / `LaneRegistryRecord` already exists at `source_proxy/cartographer/lane_registry.py` — it is a path-ownership registry with all authority flags frozen `false` and status `model-only`. Campaign 2 promotes this to authority-bearing; do not create a parallel registry under a similar name.
- `verifier_lane` exists at `source_proxy/decision/verifier_lane.py` — it is a packet builder, not a work lane. Do not name a work lane "verifier lane".
- `model_lanes` exists at `source_proxy/decision/model_lanes.py` — it is LLM selection. Do not name a work lane "model lane".
- `workflow_runner` exists at `source_proxy/cartographer/workflow_runner.py` — it is a proposal-only docs-evidence workflow with `workflow_execution_authority_granted: False`. Do not confuse it with a canonical coding orchestrator.
- `canonical_broker` exists at `source_proxy/context/canonical_broker.py` and is authoritative. Extend it; do not replace it or create a sibling "context broker".

When a new concept is needed, choose a name that does not collide (e.g. `coding_orchestrator`, `lane_contract`, `coding_lane_state`) and record the choice in the ledger.

## Mandatory dependency-ordered gates

Campaign 2 must execute in this order. Do not begin a later item while an earlier foundational dependency remains structurally incomplete. Focused work may overlap when necessary, but no later gate may be accepted based on a stub, mock, or future promise in an earlier gate.

### Gate 2.1 — Versioned canonical lane registry and contracts

Verdict: EXTEND + BUILD.

- Promote the path-ownership lane vocabulary at `source_proxy/cartographer/lane_registry.py` into a canonical, authority-bearing lane registry. The existing record (`LaneRegistryRecord`, `LANE_REGISTRY_SCHEMA_VERSION = "cartographer.lane-registry.v0.1"`) is the starting point, not a thing to discard.
- Build the versioned lane contract schema net-new in `packages/contracts/schemas/`. Each lane contract must declare: lane ID, contract version, owner, authority class, input schema, output schema, failure schema, acknowledgement schema, evidence schema, compatible consumer versions, deprecation state. Zero lane schemas exist today.
- Breaking-change discipline: a contract change that alters required inputs, output meaning, authority, failure behavior, or acknowledgement requirements must (1) increment the contract version, (2) identify every production producer and consumer, (3) migrate those callers explicitly, (4) reject incompatible consumers fail-closed, (5) add compatibility handling only when bounded and justified, (6) update fixtures, profiles, evidence, and shell presentation, and (7) prevent silent schema drift.
- No lane may accept arbitrary unversioned payloads as a permanent compatibility mechanism.

Acceptance: lane contract schema committed under `packages/contracts/schemas/`; lane registry produces authority-bearing records; the existing model-only status is superseded; a focused contract validator passes.

### Gate 2.2 — Canonical orchestrator and lane-state machine

Verdict: BUILD net-new.

- Build the canonical coding orchestrator that sequences every mandatory core lane through the canonical flow: context broker -> planner -> coder -> reviewer -> verifier -> repair loop -> evidence. No such module exists today.
- Build the lane-state machine (distinct from the per-task durable state machine at `source_proxy/tasks/durable_execution.py:19-93`, which governs one task's lifecycle and is ADOPTED). The lane-state machine governs lane transitions and participation.
- The orchestrator must consume the authority-bearing lane registry from Gate 2.1 and the context broker acknowledgement from Gate 2.3.

Acceptance: orchestrator module committed; lane-state machine transitions are explicit and tested; orchestrator routes through the existing executor at `long_running.py:1157` rather than duplicating it.

### Gate 2.3 — Canonical context broker and consumption acknowledgement

Verdict: ADOPT as-is (already authoritative).

- The canonical context broker at `source_proxy/context/canonical_broker.py` already implements: `CANONICAL_CONTEXT_CONSUMERS`, `build_context_broker_report()` (the only decision-bearing context report), `acknowledge_context_consumer()` (the acknowledgement envelope), and granular fail-closed blocker codes.
- This gate is met by confirming the broker remains the sole context truth source and that the orchestrator (Gate 2.2) consumes it. Do not rebuild the broker.

Acceptance: broker unchanged in behavior; orchestrator wires to `build_context_broker_report()` and `acknowledge_context_consumer()`; existing context tests pass.

### Gate 2.4 — Source Proxy routing, health checks, and fallback truthfulness

Verdict: EXTEND.

- Health check exists at `source_proxy/api/healthcheck.py:12` and routes are registered at `source_proxy/main.py:33-50`. ADOPT both.
- Model routing exists at `source_proxy/routing/litellm_router.py` but has no explicit Source-Proxy-level fallback layer. BUILD the explicit routing/health/fallback layer.
- Fallback must be truthful: the harness at `scripts/run-coding-e2e-loop.mjs:114,121,290` currently hard-asserts `fallback_allowed: false`. Any fallback path added must record which provider was primary, why it failed, which secondary was used, and must not claim primary success when a fallback fired.

Acceptance: explicit fallback layer committed; health + routing remain green; fallback events are recorded truthfully in evidence; a falsification test proves a silently-swapped fallback is rejected.

### Gate 2.5 — TypeScript and Python target-plugin adapter reconciliation

Verdict: ADOPT and reconcile.

- Both sides are built and bound: TS gateway `src/lib/coding/target-plugins/index.ts:22`, Python resolver `source_proxy/target_plugins/adapter.py:183`. ADOPT both.
- Reconcile any drift between the TS-selected plugin packet and the Python-resolved identity so they agree on schema version, plugin id, repository, worktree, fixture root, prompt, context, execution profile, and source head. The adapter already validates all of these fail-closed.

Acceptance: reconciliation diff (if any) committed; existing target-plugin tests pass; the TS packet and Python identity are provably the same object across the wire.

### Gate 2.6 — Canonical executor and authority enforcement

Verdict: ADOPT (executor) + BUILD (lane-scoped authority).

- The canonical executor and approval authority are ADOPTED as-is: `execute_approved_long_running_task()` at `long_running.py:1157`, the central gate at `long_running.py:1217`, the coding authority consume at `long_running.py:1234`, finalize at `long_running.py:1515`.
- BUILD lane-scoped authority: today authority is per-consumer (`coding-executor`, `spiritflix-admin-executor`, `design-writeback`, `cartographer-transfer-consumer`). Extend it so a lane-bound approval carries the lane identity and the executor enforces it.

Acceptance: executor unchanged in its existing enforcement; lane-scoped authority committed; a focused test proves a lane-mismatched approval is rejected fail-closed.

### Gate 2.7 — Reviewer, verifier, anti-cheat, and evidence identity binding

Verdict: ADOPT as-is.

- Reviewer `source_proxy/planning/reviewer.py`, verifier `source_proxy/verification/` + `decision/verifier_lane.py`, anti-cheat `source_proxy/verification/anticheat/` (15 detectors), and evidence envelope `source_proxy/approval/campaign_evidence.py` are all ADOPTED.
- The identity binding already requires every consumer (`coding-executor`, `coding-reviewer`, `coding-verifier`, `evidence-recorder`) to echo back the identical `target_plugin_identity` (else `approval_target_plugin_acknowledgement_mismatch`). This gate is met by confirming the orchestrator routes through these lanes and that identity remains bound end-to-end.

Acceptance: no regressions in the existing reviewer/verifier/anti-cheat/evidence suites; orchestrator participation is recorded per consumer with identical identity.

### Gate 2.8 — Cartographer core discovery/proposal integration

Verdict: ADOPT (Cartographer) + BUILD (executor wiring).

- Cartographer discovery (`cartographer/project_discovery.py`), proposals (`cartographer/proposals.py`), and AR-002 selection authority (`cartographer/cartographer_selection_authority.py`, `CONSUMER = "cartographer-transfer-consumer"`) are ADOPTED.
- BUILD the wiring from Cartographer selection into the coding executor. Today there is no `consume_cartographer_selection` call inside `source_proxy/tasks/`. The orchestrator must be able to consume a Cartographer selection as the entry to a coding task.
- `ALLOWED_DOWNSTREAM_CONSUMERS = {"design-writeback", "coding-executor"}` already permits this; the wiring is the missing piece.

Acceptance: a coding task can be initiated from a Cartographer selection through the canonical orchestrator; the selection authority's proposal-only invariant (Cartographer never issues approval or writes) is preserved; AR-002 tests remain green.

### Gate 2.9 — Task lifecycle reliability and recovery

Verdict: EXTEND.

- The per-task durable state machine (`tasks/durable_execution.py:19-93`) and its recovery (`:185,398,425`) are ADOPTED. EXTEND to lane-level recovery: when a lane fails or is interrupted mid-execution, the orchestrator must recover or degrade truthfully rather than leave the task in a stuck state.

Acceptance: lane-level recovery committed; recovery paths are tested; a stuck lane produces a truthful degraded verdict, not a silent hang or a false success.

### Gate 2.10 — Canonical shell observability

Verdict: EXTEND.

- Status endpoints exist (`api/runtime_status.py`, `api/self_status.py`, `self_status.py`). EXTEND into a canonical shell-observability layer that surfaces lane participation, orchestrator state, authority state, and evidence identity to the shell.

Acceptance: canonical observability layer committed; shell surfaces lane/orchestrator/authority/evidence state; no new designer shell work (designer boundary).

### Gate 2.11 — Core proving task and final acceptance

Verdict: BUILD the proving-task execution; ADOPT the battery it draws from.

The core proving task definition (mandatory):

- Selected before the final integration gate and recorded here. Proving task: a LumaCart coding exercise routed through every mandatory core lane.
- Complex enough to require every mandatory core lane; small enough to complete repeatedly in an isolated workspace; deterministic enough to support expected assertions; capable of producing a meaningful non-empty model-authored diff; reversible through Undo/reset; safe to rerun; independent of Scout, Mac, Obsidian, and Design Studio; suitable for controlled failure injection.
- The task must give genuine work to: orchestrator, Cartographer, context broker, coding-context models, model router, target adapter, coder, executor, reviewer, verifier, anti-cheat, evidence recorder. Invoking a lane with a no-op payload does not count as participation.
- The proving task must include at least one controlled failure, such as: primary coder model unavailable, context-model timeout, malformed optional-lane output, stale target-plugin snapshot, interrupted execution before apply, reviewer rejection requiring one bounded retry. The proof must show the documented recovery or fallback path and then complete a clean rerun.

Acceptance: the proving task passes from a clean isolated baseline; the controlled failure is injected and recovered truthfully; the clean rerun passes; the final acceptance receipt records every lane's genuine participation; `CAMPAIGN_2_CORE_CODING_OS_STABLE` is returned only after this.

## New-discovery classification policy

Campaign 2 must not expand merely because another coding-related feature is discovered. Every newly discovered item must be classified as exactly one of:

- mandatory for Campaign 2
- deferred to Campaign 3
- deferred to Campaign 4 repair
- deferred to a later coding campaign
- obsolete and removable

The classification and reasoning must be recorded in `docs/architecture/campaign-2-ledger.md`. Unclassified discoveries do not imply scope expansion.

## Designer boundary enforcement

Campaign 2 may touch designer code only when necessary to: preserve its existing behavior; preserve Campaign 1 security boundaries; repair a regression directly caused by coding-system work; prevent a shared contract change from breaking the existing route. Any such change must be minimal and recorded as compatibility preservation.

Prohibited in Campaign 2: new designer orchestration; new designer agents; expanded design writeback; designer benchmark execution; designer target-plugin development; designer shell expansion; design-quality improvement work. When a discovered issue is designer-specific, record it in the deferred designer backlog and continue the coding campaign.

## GO, failures, and turn ends

- `CAMPAIGN_2_CORE_CODING_OS_STABLE`: valid only after Gate 2.11 passes from a clean isolated baseline.
- Terminal gate: `campaign2_complete`. Campaign 3 is not started by this closeout.
- Stop only on real critical blockers (SSH down, irreconcilable product intent, missing unique data, hardware failure, credential genuinely unavailable after checking). Ordinary test failures and ordinary commits are not stop conditions — repair within the turn and continue.
- Turn-end format when a real critical blocker is hit: `TURN_ENDED_CAMPAIGN_2_BLOCKED - reason: <reason>`. Otherwise continue to the next slice without ending the turn.
- Do not push or mutate protected product worktrees from this Campaign checkout.
