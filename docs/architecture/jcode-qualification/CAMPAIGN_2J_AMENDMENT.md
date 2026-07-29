# Campaign 2-J Amendment

status: `GATE_2_J_9_AUTHORITY_DECISIONS_SEALED_TERRA_HIGH_GATE_2J_9A_AUTHORIZED`

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
| 2-J.8.5 | Executable run-packet preparation | Commit immutable fixture contents; attest the local model registry; seal hashes, budgets, routes, and deterministic lane order without task execution. |
| 2-J.8.6 | Pinned binary provisioning | Recover the approved binary or reproducibly rebuild and attest it without changing the packet on mismatch. |
| 2-J.9 | Controlled comparison | Paired harness comparison after all prior gates pass. |
| 2-J.10 | Adoption decision | Exactly one bounded JCode verdict; default executor remains unchanged. |

## Gate 2-J.9 operator authorization and preflight

The operator authorized the controlled comparison from
`dad81bd853c21e52a9a9c2555923117db9838094` on 2026-07-27. The required
preflight then failed closed before a model-backed run: the sealed manifest has
`fixture_commit: null`, no tracked diagnostic fixture supplies the immutable
initial contents, and the canonical records do not supply a live-attested
provider route, actual primary/challenger model identities, quantization, or
sealed generation budgets. The execution contract also records that no runner
applies those budgets or produces a live result mapping. See
`GATE_2J_9_PREFLIGHT_BLOCKER.md`. Gate 2-J.8.5 now supplies the missing
fixture commit, registry attestation, fixed parameters/budgets, and sealed
packet at `GATE_2J_8_5_EXECUTABLE_RUN_PACKET.json`; it does not execute a
task, enable JCode, or relax the Gate 2-J.9 binary and runner checks.

## Gate 2-J.0 boundary

## Dell binary reseal status

The Dell remediation authorization established replacement binary
2c59d30eeebc6d21e0a8a9a3b90af0022e4b92a7f3e6075db082cd256b3f8ef6 from
two fresh matching offline builds and resealed the packet to
4fee8fc9d0ffa8711cd300cab473adb5606ebacfdfd444ce9bcfb33b02f3f615.
The binary prerequisite is green. The separately required contained runner and
its no-model preflight remain fail-closed; no comparison task has started.

This gate classifies and preserves the pre-normalization qualification packet.
It neither changes the adapter nor runs JCode. Its only permitted code surface
is retention of the existing disabled adapter and its focused test.


## Gate 2-J.9 - Sealed JCode Transmission, Containment, and Evidence Dispatcher (amendment)

This amendment adds the canonical sealed-execution dispatcher required before JCode may
execute any model-backed task. It is the binding specification Terra High implements
gate-by-gate. It does not execute JCode, call a model, begin the 80-run comparison, touch
the frozen benchmark, modify the daily runtime, or advance another campaign.

Independent audit (`GATE_2J_9_CURRENT_POSITION_AUDIT.md`) corroborates the prior authority-gap
finding: the repository contains fail-closed policy builders but no contained dispatcher. The
binary prerequisite is green; the dispatcher, sealed inference bridge, writable overlay,
independent diff, strict NDJSON attestation, and terminal mapping are MISSING and are specified
here.

### Sealed dispatcher architecture

See `GATE_2J_9_SEALED_EXECUTION_ARCHITECTURE.md` for the full control path and envelope. In
summary: a Proxy-built sealed execution envelope is hash-bound before launch; JCode runs as
exactly one fresh external CLI process per task inside a Bubblewrap namespace sandbox wrapped
in a systemd transient cgroup-v2 scope, with a read-only base and an isolated writable overlay,
no network except a sealed attesting loopback inference bridge to the exact authorized local
model, strict NDJSON event capture, independent Proxy-owned diff, and Proxy-only terminal
authority. Mechanism selections are based on audited host capability
(`GATE_2J_9_CONTAINMENT_SPECIFICATION.md`).

### Companion specifications

- `GATE_2J_9_AUTHORITY_CONSTANTS_MATRIX.md` - every required constant, SEALED or MISSING.
- `GATE_2J_9_CONTAINMENT_SPECIFICATION.md` - bwrap + systemd scope + cgroup v2 boundary.
- `GATE_2J_9_INFERENCE_BRIDGE_SPECIFICATION.md` - attesting loopback bridge; forbidden flows.
- `GATE_2J_9_NDJSON_EVENT_CONTRACT.md` - strict event protocol and permitted types.
- `GATE_2J_9_PROCESS_SUPERVISION_SPECIFICATION.md` - cgroup-owned process-tree lifecycle.
- `GATE_2J_9_WRITABLE_OVERLAY_AND_DIFF_CONTRACT.md` - overlay + independent diff.
- `GATE_2J_9_RESULT_MAPPING.md` - outcome -> terminal class (Proxy-only).
- `GATE_2J_9_ACCEPTANCE_MATRIX.md` - per-gate acceptance criteria.
- `GATE_2J_9_RISK_REGISTER.md` - risks bound to gates.
- `TERRA_HIGH_GATE_2J_9_WORKFLOW_HANDOFF.md` - dependency-ordered workflow for Terra High.

### Gate 2-J.9 sub-gate expansion (dependency-ordered)

Gate 2-J.9 is implemented as atomic sub-gates: 2-J.9A (authority constants and canonical
schemas), 2-J.9B (containment primitive proof), 2-J.9C (process supervisor), 2-J.9D (strict
event bridge), 2-J.9E (writable overlay and independent diff), 2-J.9F (sealed inference
bridge), 2-J.9G (JCode no-model dispatcher integration), 2-J.9H (single contained model smoke
test, separate operator authorization), 2-J.9I (single contained write test, separate operator
authorization), 2-J.9J (controlled failure matrix), 2-J.9K (qualification readiness review).
Gate 2-J.10 remains locked until 2-J.9K receives operator acceptance. Full criteria in the
acceptance matrix and the Terra High handoff.

### Operator decisions still requiring sealing

1. Lane-to-executor binding for lanes A (primary) and C (challenger).
2. Per-run context packet construction rule and context schema version.
3. Pinned provider-profile configuration artifact binding `spiritos-qualification`.
4. Per-request/inactivity/pids/tool-call/retry/event-count budgets and NDJSON max line length.
5. Whether a no-op real-model identity probe is allowed at 2-J.9F (default: deferred to 2-J.9H).

Until these are sealed, Gate 2-J.9A is blocked and no model task may run. The amendment itself
is ready for operator review.
