# JCode Capability Gap Matrix

| Required Proxy capability | JCode evidence at pin | Gap | Disposition |
| --- | --- | --- | --- |
| Canonical task/correlation identity | sessions/messages have their own ids | must echo Proxy ids and never originate authority | adapter envelope |
| Immutable prompt/context binding | prompt can be passed to `run` | no native Proxy packet/hash enforcement | adapter validates file/hash before preview; runtime shim still needed |
| Exact allowed/protected paths | file tools operate in working directory | tool allowlist is not a path allowlist | BLOCKER: external filesystem sandbox/capability shim |
| Command policy | tools can be selected/disabled | Bash/batch are powerful and normal safety is incomplete | baseline denies shell; later command broker only |
| Network policy | providers/MCP/web/browser can use network | no proven inference-only OS egress boundary | BLOCKER: process network sandbox |
| Fixed provider/model | profile/model flags exist | actual provider identity can drift/fallback | capture and compare every request/result |
| Approval binding | ambient permission queue exists | normal session lacks it; not Proxy authority | JCode approval capability always false |
| Durable state | sessions persist | creates competing state and contamination | fresh session/JCODE_HOME; Proxy sole state |
| Cancellation/timeout | cancel surface exists | process tree and post-cancel writes unproven | Proxy process-group supervision required |
| Complete raw evidence | NDJSON and harness events exist | truncation/skipped-event risk; no complete result mapper | BLOCKER: framed capture, byte counts, sequence checks |
| Independent diff | JCode can report writes | self-report is not authoritative | Proxy captures Git diff independently |
| Reviewer/verifier/anti-cheat | JCode has review/test concepts | would duplicate authority | always use existing Proxy participants |
| Commit/push/deploy control | JCode has VCS/selfdev workflows | unauthorized irreversible action risk | tools/flags denied; Proxy remains sole authority |
| Reproducible pin | exact source can build locked | large workspace/default features stress host | pinned build recipe and binary hash needed |
| Rollback | per-task process can exit | persistent state can survive | per-task CLI and disposable roots |

`RECOMMENDATION`: close only the minimum gaps needed for an isolated diagnostic
run. Do not reimplement JCode's optional memory, swarm, browser, MCP, server, or
self-development features during baseline qualification.
