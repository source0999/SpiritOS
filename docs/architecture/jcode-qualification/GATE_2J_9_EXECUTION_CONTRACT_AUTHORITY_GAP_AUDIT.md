# Gate 2-J.9 Execution Contract Authority Gap Audit

status: BLOCKED_SEALED_EXECUTION_CONSTANTS_INCOMPLETE

## Evidence reviewed

- GATE_2J_8_5_EXECUTABLE_RUN_PACKET.json
- JCODE_ARCHITECTURE_EXECUTION_CONTRACT.md
- GATE_2J_9_RESEALED_NO_MODEL_PREFLIGHT.md
- archive/pre-2j-normalization-20260727/JCODE_QUALIFICATION_EXPERIMENT.md
- source_proxy/jcode/adapter.py, containment.py, network_bridge.py,
  supervision.py, and evidence.py

## Proven green inputs

The Dell canonical JCode binary is attested and provisioned, the fixture commit
and tree digest are sealed, both local model registry identities are sealed,
and the packet fixes the 80-run order, allow/deny tools, route endpoint,
generation values, and gross timeout/output/turn/token budgets.

## Missing sealed execution constants

1. The packet labels lanes A through D but contains no lane-to-executor binding.
   In particular, it does not name the existing canonical-harness command,
   configuration, or implementation commit required for A and C.
2. It does not supply the per-run context packet contents or SHA-256 required by
   the reserved JCodeExecutionEnvelope and the execution contract.
3. It names the JCode provider profile spiritos-qualification but contains no
   pinned profile/configuration artifact that binds the profile to the local
   OpenAI-compatible bridge and no-auth policy.
4. The declared seed, temperature, and max-token values are not applied by a
   current executor, request-enforcement proxy, or sealed configuration. The
   existing Unix bridge is intentionally byte-forwarding and does not attest or
   enforce the outbound request body or actual response model.
5. The current evidence mapper accepts only a Proxy-defined terminal result
   schema. No sealed JCode-to-Proxy event mapping, raw-output location, or
   independent checker invocation contract exists.
6. The existing containment component proves a read-only negative boundary. It
   does not define the required writable allowed-path overlay for mutation tasks,
   post-run diff collection, or the exact fresh-worktree construction policy.

## Disposition

Implementing a runner would require choosing the missing baseline harness,
context construction, writable overlay, provider configuration, request
enforcement, and evidence mapping. Those are fixed comparison conditions, not
ordinary code-completion details. The historical Gate 2-J.9 preflight expressly
states that adding a runner would change or invent conditions after
authorization; the newer Dell authorization resolves binary provisioning only
and does not supply these absent canonical values.

Therefore no live task, provider request, model request, or fixture execution
is permitted. The required next action is an operator-sealed execution-contract
amendment that supplies these exact values or explicitly authorizes their
creation and a subsequent packet reseal.
