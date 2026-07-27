# JCode Architecture and Execution Contract

status: `DISABLED_PREVIEW_CONTRACT_NOT_A_RUNTIME`

JCode is a bounded Layer 4 candidate subordinate to `CodingOrchestrator`.
Proxy issues the immutable task packet, selects context and model authority,
owns approval and terminal truth, and independently derives diff, test,
reviewer, verifier, anti-cheat, and final state.

## Contract boundary

| Contract | Current state |
|---|---|
| `coding.jcode-execution-request/v1` | Envelope shape reserved; Proxy-owned inputs only |
| `coding.jcode-execution-result/v1` | Result shape reserved; executor claim is evidence only |
| `jcode-qualification-adapter/v1` | Fail-closed preview seam |

The request must bind task/correlation identifiers, prompt and context hashes,
base commit, disposable workspace, allowed/protected paths, denied tools,
environment allowlist, fixed loopback endpoint, requested model, budgets, and
fresh evidence roots. Missing or unreconciled identity is a block.

The future result must include raw stdout/stderr, complete event stream,
provider/model identity, tool calls, files read/written, process termination,
retries, cancellation, claimed outcome, and evidence hashes. No executor output
can directly produce `COMPLETED_VERIFIED`.

`JCODE_EXECUTOR_ENABLED` remains disabled. Setting a feature flag cannot make a
preview capable of live execution; external containment and supervision are
prerequisites to any future runner.
