# JCode Security and Trust Audit

## Trust verdict

`BLOCKER`: the pinned source is not safe to grant unsandboxed write-capable
production execution. The audit does not allege malicious intent; it identifies
missing enforcement and evidence guarantees required by Source Proxy.

| ID | Finding | Evidence/classification | Severity | Required control |
| --- | --- | --- | --- | --- |
| S-01 | Safety classifier is not universal | `agent/turn_execution.rs:459-479` executes registry; permission tool is ambient-only. VERIFIED FACT | critical | external Proxy capability and filesystem enforcement |
| S-02 | Destructive shell surface exists | deterministic harness ran Bash; issue #604 is corroborating but not reproduced. REPRODUCED + DOCUMENTED | critical | deny Bash/batch; process sandbox before any later shell trial |
| S-03 | Path/symlink/repository escape not proven contained | edit tools receive filesystem paths; no Proxy manifest binding | critical | mount namespace/landlock-style write root plus independent diff |
| S-04 | Network surface is broader than inference | provider, MCP, browser, web tools exist | high | OS-level default-deny egress with one loopback inference endpoint |
| S-05 | MCP defaults on for `run` | `src/cli/commands.rs:2479-2499` | high | `JCODE_RUN_MCP=0`, empty fresh HOME, reject MCP config |
| S-06 | Auto-poke defaults on | `commands.rs:2469,2564` | high | disable and cap turns externally |
| S-07 | Project/global instructions and overlays load | `jcode-base/src/prompt.rs:396-410,815-890` | high | preflight AGENTS; reject both overlay locations; fresh HOME |
| S-08 | Session/memory can cross task boundaries | persistent session/memory modules | high | one fresh JCODE_HOME/session per task; memory/resume off |
| S-09 | Sidecar permission flow is incomplete | bridge says `permission_response not yet supported`; sessions partial | high | do not use persistent sidecar |
| S-10 | Stream corruption can lose evidence/tool args | issues #609/#610; malformed chunks may be ignored by tests | high | byte-framed capture, monotonic sequence, terminal sentinel, independent diff |
| S-11 | Provider/model/credential drift risk | multiple provider/auth stores and issue #380 class | high | no inherited secrets; loopback no-auth profile; verify actual model |
| S-12 | Auto-update/selfdev harms reproducibility | startup/dispatch/selfdev source | high | `--no-update --no-selfdev`; pinned binary hash |
| S-13 | VCS/commit/push workflows exist | ambient/selfdev/VCS source | high | exclude tools; read-only `.git` where practical; Proxy checks remote refs |
| S-14 | Cancellation race/process descendants unproven | cancel API exists but no qualification process supervisor | medium-high | process group, deadline, kill/reap, post-stop diff reconciliation |
| S-15 | Concurrent/swarm edits can race | swarm and batch parallel surfaces | high | swarm/batch disabled; one process/worktree |
| S-16 | Environment/secret inheritance | subprocess/provider code can read environment | high | strict environment allowlist; no cloud credentials |
| S-17 | Telemetry/remote service risk | telemetry docs and networked provider features | medium-high | dual opt-out flags plus egress block and traffic evidence |
| S-18 | Dependency/supply-chain and host-resource burden | large Cargo workspace/lock; default build SIGSEGV | medium | locked/no-default build, artifact hash, isolated toolchain, resource limits |
| S-19 | False success after partial stream is possible without adapter checks | JCode claimed outcome is not independent truth | critical | executor claim ceiling; Proxy verifier/anti-cheat/finalizer only |

## Adapter controls present

`source_proxy/jcode/adapter.py` is non-executing and disabled by default. It:

- validates prompt/context hashes and isolated prompt/evidence/JCODE_HOME roots;
- validates allowed/protected repo paths with existing Proxy path safety helpers;
- permits only read/search/edit-family tool names and requires the complete deny set;
- forces MCP, memory, swarm, telemetry, auto-poke, auto-update, browser, network,
  session resume, commit, push, and deploy off in its contract;
- strips inherited credentials through a four-variable environment allowlist;
- accepts only loopback inference endpoints without embedded credentials;
- emits a command/provider preview and explicitly reports `live_ready: false`;
- grants JCode no approval, apply, review, verification, terminal, commit, push,
  or deployment authority.

## Controls deliberately not claimed

The seam does not execute a process, sandbox filesystem syscalls, enforce
network egress, supervise cancellation, translate NDJSON to a complete result,
or join the orchestrator. Allowed paths currently exist only in the envelope
and prompt packet; that is not runtime enforcement. Those are remediations,
not hidden TODOs, and block live tasks.
