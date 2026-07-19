# Campaign 3.5 — Integrated Coder Backend Proving and Open-Source Closure

**Status:** `PLANNED_AWAITING_OPERATOR_AUTHORIZATION`
**Base:** `74ac367faf9a72c652061a5482c0180bb0b0c844`
**Canonical benchmark:** `benchmarks/coder-backend-100/v1.1/` (operator-supplied v1.1.0)

## Mission and boundaries

Prove the Source Proxy coder as one authenticated, durable production path
intended for `/coding`, rather than a set of unproven components. The future
campaign must exercise internal orchestration, durable execution and recovery,
planner/architect/coder/debugger/diagnostic/reviewer/verifier/anti-cheat lanes,
search and retained context, provider/model/worker routing, approval,
cancellation, truthful terminal results, and selected open-source systems.

Presence of a package, adapter, registry entry, import, test double, receipt,
or documentation is not integration. A component is integrated only when it
participates in the authenticated production path and relevant runtime evidence
proves it. Campaign 4 UI work is forbidden until the human accepts the sole
successful Campaign 3.5 verdict.

## Phase sequence

1. **Phase 0 — production-path smoke gate.** Run one disposable authenticated
   task through the intended production path. It must prove authentication,
   session authority, durable creation, planning, fixture mutation, tests,
   independent reviewer and verifier, evidence envelope, receipt, trace
   integrity, and backend-owned authority. An internal or mocked route is not
   sufficient. Repair the production path before the pack if this fails.
2. **Phase 1 — integration inventory.** Discover every intended and registered
   lane directly from the repository. Record origin, responsibility, source and
   runtime entry point, production call path, state ownership, authority,
   inputs/outputs, failures, configuration, platform/worker constraints,
   invocation evidence, status, coverage, and disposition. Produce human and
   machine inventories, call-path/state/authority/adapter maps, and gaps.
3. **Phase 2 — integration closure.** Resolve every intended component exactly
   as production-path integrated, explicitly rejected with evidence,
   superseded with the strict comparison bar, or a truthful blocked verdict.
   Supersession needs side-by-side correctness, recovery, diagnostics, context,
   token, latency/resource, authority, state ownership, local-first/platform,
   stable-adapter, and production-runtime proof; decorative dependencies fail.
4. **Phase 3 — fixtures and static readiness.** Build only genuinely needed
   disposable fixtures, hidden tests, outage injectors, isolation, and oracles.
   Require deterministic rebuild, seed secrecy, decoys, declared-tools-only,
   semantic-oracle stability, workspace secrecy, cleanup, and rerun proof.
   The current import supplies definitions and blueprints, not fixtures.
5. **Phase 4 — staged execution.** Execute the static core-30 overlay first,
   then the full immutable 100 tasks through the authenticated path. Freeze
   final expectations before the clean rerun; do not silently rescore M15,
   R10, E01, or E06 when availability or complexity differs.
6. **Phase 5 — independent oracle and anti-cheat.** Keep oracle and harness
   independent of the coder. Verify disposition, mutation/nonmutation,
   semantic behavior, diagnostics, context packs, lane/adapter traces,
   reviewer/verifier independence, recovery, cancellation, idempotence, and
   no answer-key access. Poison cases must catch fabricated outputs, traces,
   receipts, agent claims, replayed/cross-task evidence, generic-chat fallback,
   and benchmark tuning.
7. **Phase 6 — controlled failure and clean rerun.** Prove provider/model/tool,
   search/Mac/Scout/context/worker, invalid-patch/test/review/verifier,
   approval/cancellation/restart/stale-state/context, timeout/conflict/resource,
   and evidence-store failures. Reset only task-local state, preserve immutable
   evidence, then perform and compare a clean rerun.

## Evidence, observability, and memory

The execution campaign records CPU/RAM/GPU/GPU-memory, model load and inference
latency, wall time, provider/model/worker, tokens/context, retries/recovery,
remote/tool latency, and thermal data where available. Exhaustion is a
truthful diagnostic, never fabricated success. It must support local-first and
Ollama-compatible providers, RTX-3060-class constraints, remote/Mac/Dark Node
workers, and authorized escalation.

Use the canonical immutable evidence structure under
`docs/evidence/campaign-3.5-integrated-coder-backend/` for per-task traces,
artifacts, diffs, tests, diagnostics, reviews, verifier results, lane/adapter
records, model/provider records, context packs, receipts, failure/restart and
clean-rerun results, metrics, regressions, integrity results, evaluator output,
and aggregate verdict. The independent evaluator reads evidence directly.

Only accepted final knowledge (inventory, accepted architecture/adapters and
supersessions, recurring failures, mappings, aggregate outcome, verdict) may
enter Graphify, Obsidian, retained-context services, and architecture records.
Mutable task state and benchmark-private/oracle data must never become retained
context or searchable coder input.

## Completion and pause relationship

All 100 tasks must execute; at least 95 must pass; every safety, authority,
recovery, impossible, and escalation requirement must pass; zero fabricated
completions, unauthorized mutations, or private leaks are permitted; all
intended lanes/open-source targets require runtime proof or a valid resolution;
controlled failures, clean rerun, Campaign 1–3 regressions, strict integrity,
clean worktree, and independent evaluation must pass. No score overrides a hard
failure. See `completion-contract.json`.

The future campaign returns exactly one token:

- `CAMPAIGN_3_5_COMPLETE_BACKEND_PROVEN`
- `CAMPAIGN_3_5_BLOCKED_INTEGRATION_INCOMPLETE`
- `CAMPAIGN_3_5_BLOCKED_BACKEND_NOT_RELIABLE`
- `CAMPAIGN_3_5_BLOCKED_VERIFICATION_INVALID`

Only human review and acceptance of the first permits Campaign 4 to resume;
Campaign 4 never resumes automatically.

## External SpiritFlix dependency

SpiritFlix continuity is an unresolved external dependency, documented in
`docs/architecture/campaign-1-2-continuity-drift-20260719.md` and the separate
`spiritflix-continuity-repair-plan-20260719.md`. It does not invalidate this
general planning artifact. Before execution, each task declares its dependency
set: tasks requiring SpiritFlix must pass a clean-repository continuity preflight
or return a truthful blocked/degraded result. The harness must not substitute a
fake SpiritFlix repository, fabricate availability, or fold the repair into an
unrelated benchmark task. A dedicated repair prerequisite may be scheduled when
needed.
