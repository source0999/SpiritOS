# Campaign 2-J Amendment

status: `GATE_2_J_4_PROCESS_SUPERVISION_COMPLETE`

## Identity and dependency

| Field | Value |
|---|---|
| Formal name | Campaign 2-J - Post-Campaign-2 JCode Executor Qualification |
| Type | Non-advancing qualification campaign |
| Worktree | `/home/source/SpiritOS-source-proxy-jcode-qualification-20260726` |
| Branch | `codex/source-proxy-jcode-qualification-20260726` |
| Qualification base | `1641ddb1c71e6b364e98aa9aeff4b4719627d926` |
| C2 acceptance publication | `17f3ce8739192e5c91534dc7ddde1086e83d5e0e` |
| Frozen authority implementation | `2ecbb56d6524215843616d52e08cd95d32bdf4ea` |

Campaign 2-J starts only because Campaign 2 benchmark authority has been
explicitly accepted. It is a side branch: it does not replace Campaign 3, does
not unblock Campaign 4, and does not make JCode a default executor.

## Non-negotiable invariants

1. `CodingOrchestrator` remains the sole durable task, routing, approval,
   terminal-truth, benchmark-oracle, commit, push, and deployment authority.
2. JCode is a disabled Layer 4 candidate only. It may eventually own a bounded
   within-task loop and raw event production, never campaign or terminal truth.
3. `source_proxy/jcode/adapter.py` remains fail closed: live-task flags are
   false, `JCODE_EXECUTOR_ENABLED` defaults to `0`, and the denied-tool list is
   preserved.
4. No production import, route, service, database, benchmark mutation, or live
   JCode execution is authorized by Gate 2-J.0.
5. The frozen 100-task benchmark remains immutable and unexecuted by JCode.
6. The dirty daily runtime `/home/source/SpiritOS` remains outside every proof
   path.

## Ordered gates

| Gate | Scope | Exit condition |
|---|---|---|
| 2-J.0 | Artifact normalization | Raw qualification evidence preserved, nine canonical artifacts and a consolidation index committed. |
| 2-J.1 | Baseline hygiene | Python environment and coding-pack order pollution characterized without claiming green. |
| 2-J.2 | Filesystem containment | OS-enforced negative proof blocks escapes and protected writes. |
| 2-J.3 | Network and credential containment | Default-deny egress with only the permitted loopback endpoint. |
| 2-J.4 | Process supervision | Bounded process lifecycle and SIGSEGV root cause evidenced. |
| 2-J.5 | Binary/provider/model truth | Exact binary, requested and actual model identities reconcile fail closed. |
| 2-J.6 | Evidence mapping | Complete event mapping while Proxy retains terminal authority. |
| 2-J.7 | Clean reproduction | A fresh environment reproduces 2-J.1 through 2-J.6. |
| 2-J.8 | Diagnostic fixture seal | The 20-task manifest is committed and sealed, not executed. |
| 2-J.9 | Controlled comparison | Paired harness comparison after all prior gates pass. |
| 2-J.10 | Adoption decision | Exactly one bounded JCode verdict; default executor remains unchanged. |

## Gate 2-J.0 boundary

This gate classifies and preserves the pre-normalization qualification packet.
It neither changes the adapter nor runs JCode. Its only permitted code surface
is retention of the existing disabled adapter and its focused test.
