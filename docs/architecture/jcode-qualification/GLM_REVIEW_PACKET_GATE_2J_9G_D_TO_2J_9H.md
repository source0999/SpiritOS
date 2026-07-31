# GLM Review Packet: Gate 2-J.9G-D Through 2-J.9H

## Review State

`READY_FOR_INDEPENDENT_GLM_REVIEW`

The prospective batch authorization was committed and pushed at `9f84fe55e`
before implementation. Its canonical content hash is
`df84e61f53d8cf10c592926c02276e0d494fd975d55a8036b142617856533b71`.

## Scorecard

| Gate | Result | Commit |
| --- | --- | --- |
| 2-J.9G-D Topology remediation | PASS | `c764d7501` |
| 2-J.9G-B Sealed fake path | PASS | `bdf79d131` |
| 2-J.9G Contained no-model loop | PASS | `03679a04d` |
| 2-J.9H Read-only local-model smoke | PASS | pending this review packet commit |

## Evidence Summary

- Direct and relay topology evidence: [GATE_2J_9G_D_TOPOLOGY_REMEDIATION_RECEIPT.md](GATE_2J_9G_D_TOPOLOGY_REMEDIATION_RECEIPT.md)
- Fake request-response evidence: [GATE_2J_9G_B_SEALED_BRIDGE_COMPLETION_RECEIPT.md](GATE_2J_9G_B_SEALED_BRIDGE_COMPLETION_RECEIPT.md)
- Task loop, timeout, cancellation, resource, and cleanup evidence: [GATE_2J_9G_NO_MODEL_LOOP_RECEIPT.md](GATE_2J_9G_NO_MODEL_LOOP_RECEIPT.md)
- Exact-model read-only evidence: [GATE_2J_9H_READ_ONLY_MODEL_SMOKE_RECEIPT.md](GATE_2J_9H_READ_ONLY_MODEL_SMOKE_RECEIPT.md)

The selected correction replaces the relay-parent launch with a sibling relay
and JCode exec topology. The final transport uses an inherited supervisor-owned
socketpair because a read-only-mounted Unix socket was denied at `read()` by the
LSM. No containment policy was weakened.

## Counters

- Exact JCode launches in this batch: 10 (2 topology, 1 successful fake path,
  4 no-model-loop evidence, 3 real-model task attempts).
- Fake requests: 5 (one successful integration, one successful no-model loop,
  three controlled slow-fake probes).
- Real model requests: 3, all through the Proxy bridge; one accepted task and
  two independently rejected answer-quality attempts.
- Direct JCode-to-Ollama requests: 0.
- Frozen benchmark changes: 0.
- Daily-runtime changes: 0.

## Remaining Risks

The exact local model completed the minimal read-only smoke but failed two
source-reading answer evaluations. This is retained evidence about model/tool
quality, not a reason to infer broader benchmark capability. No benchmark or
write-task conclusion is authorized.

## Next Action

Independent GLM review before Gate 2-J.9I authorization.
