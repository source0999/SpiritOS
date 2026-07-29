# Gate 2-J.9 Authority Constants Matrix

status: `CONSTANTS_SEALED_SIX_REMAIN_ABSENT`

schema: `source-proxy.gate-2j-9-authority-constants-matrix/v1`
companion to: `GATE_2J_9_CURRENT_POSITION_AUDIT.md`, `GATE_2J_9_SEALED_EXECUTION_ARCHITECTURE.md`

This matrix records the disposition of every authority constant required by §3.3 of the
amendment assignment. Values are drawn from sealed campaign artifacts and verified source
constants. A constant marked `SEALED` has an attested value; `MISSING` means no sealed value
exists and the value must be supplied by operator decision or a subsequent sealed gate.

## Identity constants

| Constant | Value | Disposition |
|---|---|---|
| Schema version (qualification) | `coding.jcode-qualification/v1` | SEALED (adapter.py) |
| Request envelope schema | `coding.jcode-execution-request/v1` | SEALED (reserved, adapter.py) |
| Result envelope schema | `coding.jcode-execution-result/v1` | SEALED (reserved, adapter.py) |
| Adapter version | `jcode-qualification-adapter/v1` | SEALED (adapter.py) |
| Executor implementation ID | `candidate.jcode-executor` | SEALED (adapter.py) |
| JCode source commit | `2444e7b6bc80d421ae3ee404081bdb41150a1830` | SEALED |
| JCode binary SHA-256 | `2c59d30eeebc6d21e0a8a9a3b90af0022e4b92a7f3e6075db082cd256b3f8ef6` | SEALED + on-disk verified |
| JCode version | `0.58.51-dev` | SEALED |
| Proxy source commit (HEAD) | `cbba33aa6f617bbb6c83438079541035155a9207` | SEALED (branch HEAD) |
| Qualification base commit | `1641ddb1c71e6b364e98aa9aeff4b4719627d926` | SEALED |
| C2 acceptance publication | `17f3ce8739192e5c91534dc7ddde1086e83d5e0e` | SEALED |
| Frozen authority implementation | `2ecbb56d6524215843616d52e08cd95d32bdf4ea` | SEALED |
| Harness ID | `SpiritOS-Source-Proxy / CodingOrchestrator` | SEALED (Proxy remains authoritative) |
| Task schema version | reserved via envelope fields | PARTIAL (shape defined, not sealed per-task) |

## Context binding constants

| Constant | Value | Disposition |
|---|---|---|
| Context packet ID | per-run | MISSING (no per-run packet produced) |
| Context schema version | reserved | MISSING (no schema pinned) |
| Context packet hash | per-run SHA-256 | MISSING (no per-run packet) |
| Ordered context-file manifest | none | MISSING |
| Per-file hashes | none | MISSING |
| Total context bytes / truncation status | none | MISSING |
| Generation process and version | none | MISSING |

> The run packet reserves `JCODE_HOME/input/context.json` and validates its hash, but no
> component constructs the per-run context packet. This is sealed-gap item #2.

## Model / provider binding constants

| Constant | Value | Disposition |
|---|---|---|
| Provider profile ID | `spiritos-qualification` | SEALED (packet) |
| Permitted host registry endpoint | `http://127.0.0.1:11434` | SEALED (packet) |
| Permitted JCode sandbox endpoint | `http://127.0.0.1:4000/v1` | SEALED (packet) |
| JCode bridge target | `127.0.0.1:4000` (loopback) | SEALED |
| Credentials policy | none / no-auth | SEALED |
| Routing policy | fixed local loopback only, no fallback | SEALED |
| Primary model registry ID | `qwen2.5-coder:7b` | SEALED (packet + registry) |
| Primary model digest | `dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364` | SEALED |
| Primary quantization | `Q4_K_M` | SEALED |
| Challenger model registry ID | `qwen2.5-coder:14b` | SEALED |
| Challenger model digest | `9ec8897f747e246e970bc5cfdda85d22f1123dc2e3d34978a010a75968716849` | SEALED |
| Challenger quantization | `Q4_K_M` | SEALED |
| Provider-reported actual model ID | per-run observation | MISSING (no attesting bridge; identity.py has the checker but no producer) |
| Model response identity evidence | per-run | MISSING |
| Inference bridge ID | `fixed-loopback-unix-bridge/v1` (byte-forwarding) | PARTIAL (current bridge); attesting bridge MISSING |
| Pinned provider profile configuration artifact | none on disk | MISSING (sealed-gap item #3) |
| Generation-request enforcement | none | MISSING (sealed-gap item #4) |
| Fallback policy | `none` (silent substitution prohibited) | SEALED (policy) but UNENFORCED at runtime |

## Capability binding constants

| Constant | Value | Disposition |
|---|---|---|
| Allowed tools | read, glob, grep, ls, write, edit, multiedit, patch, apply_patch | SEALED |
| Required denied tools | bash, batch, browser, communicate, launch, memory, open, selfdev, swarm, webfetch, websearch | SEALED |
| Command policy | `no_shell` | SEALED |
| Network policy | `inference_only_external_guard_required` | SEALED (envelope) / PARTIAL (bwrap unshare-net + loopback relay proven; attesting guard MISSING) |
| Environment allowlist | LANG, LC_ALL, PATH, TZ | SEALED |
| Forced env (commit/push/deploy/memory/mcp/telemetry/network/auto-update off) | all forced safe | SEALED |
| Commit / push / deploy prohibition | `JCODE_ALLOW_* = 0` forced | SEALED |
| Allowed paths (per-task) | per task_packets | SEALED per task |
| Protected paths (per-task) | per task_packets | SEALED per task |
| Writable overlay policy | none | MISSING (sealed-gap item #6) |
| Read-only root policy | bwrap ro-bind proven | PROVEN (negative containment) |
| Fresh disposable worktree per run | declared `True` in packet | DECLARED_ONLY (no implementation) |
| Fresh JCODE_HOME per run | declared `True` | PARTIAL (env builder produces it; no launcher creates/destroys it) |

## Budget binding constants

| Constant | Value | Disposition |
|---|---|---|
| Generation parameters | max_tokens 4096, seed 7, temperature 0 | SEALED (packet) |
| Turn budget | 4 | SEALED |
| Token budget | 32768 | SEALED |
| Wall-clock timeout | 300 s | SEALED (gross) |
| Max output bytes | 2,000,000 | SEALED (gross) |
| Model-request maximum | not specified | MISSING (no request counter in any bridge) |
| Tool-call maximum | not specified | MISSING |
| Retry maximum | not specified | MISSING |
| Process-count maximum | not specified | MISSING (no cgroup pids limit bound) |
| File-write maximum | not specified | MISSING |
| Output-byte maximum (event stream) | not specified | MISSING |
| Event-count maximum | not specified | MISSING |
| Inactivity timeout | not specified | MISSING (only total timeout exists) |

> Gross timeouts/output exist. The per-request, per-tool, per-event, pids, and inactivity
> budgets required by the sealed dispatcher are absent and must be sealed in Gate 2-J.9A.

## Event / evidence constants

| Constant | Value | Disposition |
|---|---|---|
| Strict NDJSON required | `True` | SEALED (policy) |
| Event schema version | none | MISSING |
| Permitted event types | none enumerated | MISSING |
| Event identity fields (id/seq/ts/task/corr/type/source/payload/prev-hash) | none | MISSING |
| NDJSON max line length / max event count | none | MISSING |
| Unknown-event handling | none | MISSING |
| Invalid-line / partial-line / truncation handling | partial (evidence.py flags invalid_json, sequence, missing terminal) | PARTIAL |
| stdout-contamination handling | none | MISSING |
| Raw request/response metadata required | `True` (policy) | DECLARED_ONLY (no producer) |
| Independent diff / protected-path / tests / reviewer / verifier / anti-cheat | required list SEALED | DECLARED_ONLY (no invocation contract) |
| JCode-to-Proxy result mapping | none | MISSING (sealed-gap item #5) |

## Result / terminal-state constants

| Constant | Value | Disposition |
|---|---|---|
| Permitted production terminal classes | `COMPLETED_VERIFIED`, `ESCALATION_CONTEXT_PACK_READY`, `BLOCKED_OR_DEGRADED_TRUTHFULLY` | SEALED (Proxy-only authority) |
| JCode authority over terminal class | none (executor claim is evidence only) | SEALED |
| Outcome->terminal map (timeout/cancel/mismatch/denial/infra/incomplete) | none | MISSING |

## Summary count

- Constants SEALED or PROVEN: identity, model registry digests, gross budgets, capability policy, terminal authority.
- Constants MISSING (6 sealed gaps + per-request/per-tool/inactivity/pids/event-schema budgets): see `GATE_2J_9_SEALED_EXECUTION_ARCHITECTURE.md` "Open operator decisions".
- UNSAFE components: none found. No component grants JCode authority it should not have; the
  adapter is fail-closed by construction.
