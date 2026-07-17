# Campaign 2 Ledger

Schema: `spiritos-campaign-2-ledger/v1`

## Authoritative current checkpoint

- Campaign: `spiritos-campaign-2`; plan: [campaign-2-plan.md](campaign-2-plan.md); state: [campaign-2-state.json](campaign-2-state.json).
- Worktree / branch: `/home/source/SpiritOS-campaign-2-20260716` / `codex/spiritos-campaign-2-core-coding-os-20260716`.
- Phase: **Campaign 2 complete**.
- Base commit: `8a20473c2260bc132e595c64230d3fdfc9fef97f` (Campaign 1 terminal tip).
- Current gate: `campaign2_complete`; all gates 2.1 through 2.11 are completed.
- GO eligibility: `true`.
- Critical blocker: none. The prior secret-environment stop was recovered through canonical server-side loading and child-only runner injection.
- Terminal verdict: `CAMPAIGN_2_CORE_CODING_OS_STABLE`, proven by the clean isolated Gate 2.11 receipt `docs/evidence/e2e-loop/2026-07-17T03-42-37-924Z/result.json`.
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
| 2.1 Versioned canonical lane registry and contracts | completed | EXTEND + BUILD | `6f0281b5`: authority-bearing `cartographer/lane_registry.py`, versioned seven-participant contract catalog, focused contract/shared-contract tests, `campaign-2:validate-authority`, and typecheck pass |
| 2.2 Canonical orchestrator and lane-state machine | completed | BUILD | `f529dff5`, `15e71a98`: `coding/orchestrator.py` persists lane state, has explicit tested transitions, and delegates writes to `execute_approved_long_running_task()` |
| 2.3 Canonical context broker and consumption acknowledgement | completed | ADOPT | broker behavior unchanged; `f529dff5` persists `build_context_broker_report()` then uses `acknowledge_task_context_consumer()` through the canonical broker; focused broker tests pass |
| 2.4 Source Proxy routing, health, fallback truthfulness | completed | EXTEND | `2cab5321`, `ec21cf32`, `f95a9ec5`: explicit async fallback receipts, request-explicit dual spend preflight, selected-provider evidence, and a silent-substitution falsification test; 19 focused tests + typecheck pass |
| 2.5 TS and Python target-plugin adapter reconciliation | completed | ADOPT + reconcile | `e1e08f5a`: TS gateway, Python resolver, e2e harness, current Campaign 2 worktree identity, prompt/context/profile, and server-resolved source head reconcile; 11 focused tests + typecheck pass |
| 2.6 Canonical executor and lane-scoped authority | completed | ADOPT + BUILD | `17ee097c`: Campaign 2 authority namespace and `coding-executor:coder` durable lane binding; executor forwards lane identity; mismatch rejection test and typecheck pass |
| 2.7 Reviewer, verifier, anti-cheat, evidence identity binding | completed | ADOPT | reviewer, verifier, 15-detector anti-cheat, and evidence identity binding retained; 44 focused tests + typecheck pass under Campaign 2 lane authority |
| 2.8 Cartographer core discovery/proposal integration | completed | ADOPT + BUILD | `617e369e`: the canonical orchestrator consumes a Cartographer proposal selection only as `coding-executor:coder` before starting; the focused handoff and existing durable-selection authority tests pass with typecheck |
| 2.9 Task lifecycle reliability and recovery | completed | EXTEND | `49768ffa`: interrupted persisted lane state is restored; only an explicit successful recovery action can complete it, while missing or failed action is persisted as a truthful degraded/blocked result; 15 recovery-focused tests + typecheck pass |
| 2.10 Canonical shell observability | completed | EXTEND | `605f3e7b`: read-only `/v1/coding/tasks/{task_id}/observability` exposes persisted lane participation, orchestrator receipt, Campaign 2 lane authority, and target-plugin identity; factual absence or binding mismatch is pending/degraded, never a success claim; 50 focused tests + typecheck pass |
| 2.11 Core proving task and final acceptance | completed | BUILD execution | `b5fbe4a4`, `d46676e3`, `c8a86ec2`, `cf51cbda`: canonical server-side secret loading with child-only injection, live route preflight, isolated browser-origin binding, controlled local-model timeout and validation failures recovered through explicit Qwen 14B primary selection, and clean isolated proof GO at `docs/evidence/e2e-loop/2026-07-17T03-42-37-924Z/result.json`; model-authored create, approval/apply, verifier, managed Chromium, undo/reset, and clean rerun all passed. |

## Discovery classification log

Every newly discovered item during Campaign 2 must be classified here as exactly one of: `mandatory-c2`, `deferred-c3`, `deferred-c4-repair`, `deferred-later-coding`, `obsolete-removable`. Unclassified discoveries do not imply scope expansion.

| Discovered item | Classification | Reasoning | Date |
| --- | --- | --- | --- |
| Post-apply durable authority snapshot retains `campaign_1_approval` and unscoped `coding-executor` labels after Campaign 2 lane-scoped consumption | mandatory-c2 | Repaired in `2061c7db`: durable approval, preview, and evidence acknowledgement names now preserve Campaign 2 / `coding-executor:coder`; 91 focused authority/task tests pass | 2026-07-16 |
| Authenticated final proving task cannot issue Prompt 1 | mandatory-c2 | Recovered in `b5fbe4a4` and `d46676e3`: canonical `0600` secret loading is server-side and forwarded only to the Playwright child; the live trusted-origin route is preflighted without a credential. | 2026-07-17 |
| Isolated approval session, central gate, and managed-browser verifier retained production defaults | mandatory-c2 | Recovered by isolated `0700` operator state, explicit Gate 2.11 state, and loopback-only `SPIRITOS_E2E_FRONTEND_ORIGIN`; the source verifier proved the same isolated `:3105` browser route rather than silently using `:3000`. | 2026-07-17 |
| Local primary model exceeded the initial 45-second proving budget and a non-coder model emitted an invalid storefront bundle | mandatory-c2 | Controlled fail-closed proving failures were retained as NO_GO receipts; the isolated declared Qwen 14B coding primary recovered them and produced a verifier-approved, model-authored diff. | 2026-07-17 |

## Designer boundary log

Designer code may be touched only to preserve behavior, preserve Campaign 1 boundaries, repair a coding-system regression, or prevent a contract change from breaking the existing route. Record any such touch here.

| Designer file touched | Reason | Scope | Date |
| --- | --- | --- | --- |
| _(none yet)_ | | | |

## Closeout rules

- The JSON state is the machine-readable source for completion evaluation. This Markdown ledger is a human reconciliation record and is never parsed to infer JSON values.
- Any future change that reopens a Campaign 2 gate must first change the JSON state to a non-terminal checkpoint and record a new explicit closeout decision; stale historical prose cannot reopen the campaign.
- Campaign 3 requires a separate authorization and is not implied by progress in this campaign. Campaign 3 entry requires `CAMPAIGN_2_CORE_CODING_OS_STABLE`, the core proving task passed, the versioned lane registry accepted, no unresolved mandatory core-lane gap, and the Campaign 2 recovery anchor verified.
