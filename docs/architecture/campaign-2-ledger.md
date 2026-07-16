# Campaign 2 Ledger

Schema: `spiritos-campaign-2-ledger/v1`

## Authoritative current checkpoint

- Campaign: `spiritos-campaign-2`; plan: [campaign-2-plan.md](campaign-2-plan.md); state: [campaign-2-state.json](campaign-2-state.json).
- Worktree / branch: `/home/source/SpiritOS-campaign-2-20260716` / `codex/spiritos-campaign-2-core-coding-os-20260716`.
- Phase: **Campaign 2 in progress**.
- Base commit: `8a20473c2260bc132e595c64230d3fdfc9fef97f` (Campaign 1 terminal tip).
- Current gate: `gate_2_1_versioned_lane_registry_and_contracts`; completed gates: none yet.
- GO eligibility: `false`. This campaign is not terminal.
- Critical blocker: `none`. Partial gates: `none`.
- Terminal verdict target: `CAMPAIGN_2_CORE_CODING_OS_STABLE` after Gate 2.11 passes from a clean isolated baseline.
- Campaign 3 is not started (`false`).

## Entry-condition revalidation (recorded at branch-off)

All four Campaign 1 entry conditions were verified before authoring this campaign:

1. Campaign 1 GO closeout with authenticated browser lifecycle proof: `GO_CAMPAIGN_1_COMPLETE`, receipt `docs/evidence/e2e-loop/2026-07-15T23-36-28-866Z/result.json`.
2. Protected heads revalidated: Source Proxy `594d66ef`, SpiritFlix `5fde4ae0`, architecture audit `05612d2a`, Campaign 1 terminal `8a20473c`.
3. Campaign 1 ledger/state/evidence index agree on `8a20473c` / `campaign1_complete`.
4. Product owner authorized Campaign 2 scope in [campaign-2-plan.md](campaign-2-plan.md).

## Gate status

| Gate | Status | Verdict (adopt/extend/build) | Evidence / next |
| --- | --- | --- | --- |
| 2.1 Versioned canonical lane registry and contracts | not_started | EXTEND + BUILD | promote `cartographer/lane_registry.py`; build lane contract schema in `packages/contracts/schemas/` |
| 2.2 Canonical orchestrator and lane-state machine | not_started | BUILD | net-new; route through existing executor `long_running.py:1157` |
| 2.3 Canonical context broker and consumption acknowledgement | not_started | ADOPT | wire orchestrator to `context/canonical_broker.py`; do not rebuild |
| 2.4 Source Proxy routing, health, fallback truthfulness | not_started | EXTEND | health + routes exist; build explicit fallback layer; truthful fallback evidence |
| 2.5 TS and Python target-plugin adapter reconciliation | not_started | ADOPT + reconcile | both sides built; reconcile any drift |
| 2.6 Canonical executor and lane-scoped authority | not_started | ADOPT + BUILD | executor adopted; build lane-scoped authority |
| 2.7 Reviewer, verifier, anti-cheat, evidence identity binding | not_started | ADOPT | all four exist; confirm orchestrator routes through them |
| 2.8 Cartographer core discovery/proposal integration | not_started | ADOPT + BUILD | wire selection into executor; preserve proposal-only invariant |
| 2.9 Task lifecycle reliability and recovery | not_started | EXTEND | adopt per-task SM; extend to lane-level recovery |
| 2.10 Canonical shell observability | not_started | EXTEND | extend status endpoints to canonical observability |
| 2.11 Core proving task and final acceptance | not_started | BUILD execution | ADOPT LumaCart battery; prove every lane; controlled failure + clean rerun |

## Discovery classification log

Every newly discovered item during Campaign 2 must be classified here as exactly one of: `mandatory-c2`, `deferred-c3`, `deferred-c4-repair`, `deferred-later-coding`, `obsolete-removable`. Unclassified discoveries do not imply scope expansion.

| Discovered item | Classification | Reasoning | Date |
| --- | --- | --- | --- |
| _(none yet)_ | | | |

## Designer boundary log

Designer code may be touched only to preserve behavior, preserve Campaign 1 boundaries, repair a coding-system regression, or prevent a contract change from breaking the existing route. Record any such touch here.

| Designer file touched | Reason | Scope | Date |
| --- | --- | --- | --- |
| _(none yet)_ | | | |

## Closeout rules

- The JSON state is the machine-readable source for completion evaluation. This Markdown ledger is a human reconciliation record and is never parsed to infer JSON values.
- Any future change that reopens a Campaign 2 gate must first change the JSON state to a non-terminal checkpoint and record a new explicit closeout decision; stale historical prose cannot reopen the campaign.
- Campaign 3 requires a separate authorization and is not implied by progress in this campaign. Campaign 3 entry requires `CAMPAIGN_2_CORE_CODING_OS_STABLE`, the core proving task passed, the versioned lane registry accepted, no unresolved mandatory core-lane gap, and the Campaign 2 recovery anchor verified.
