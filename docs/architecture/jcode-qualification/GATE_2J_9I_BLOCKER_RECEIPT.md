# Gate 2-J.9I Pre-Execution Safety Blocker

## Verdict

`GATE_2J_9I_BLOCKED_SAFETY_OR_EVIDENCE_FAILURE`

The sealed task, exact 14B registry identity, and static enforcement were
prepared. Both authorized contained launches reached the Proxy compatibility
bridge but failed before a real model request, tool call, or fixture mutation.

## Evidence

- Authorization: `TERRA_HIGH_AUTHORIZED__GATE_2J_9I_SAFE_WRITE_SMOKE_V1`,
  hash `836ac0f78c9597639e831729bc29c0388b2dd2a45e0a72d2178cf38a768eb997`.
- Task manifest hash:
  `99d71256a044f1d2fbcc6f4f66b73147071a2fd9a732367b3d006eacebfc0bbe`.
- Model registry preflight: `qwen2.5-coder:14b`, Qwen2, `Q4_K_M`, digest
  `9ec8897f747e246e970bc5cfdda85d22f1123dc2e3d34978a010a75968716849`.
- Exact JCode binary hash:
  `2c59d30eeebc6d21e0a8a9a3b90af0022e4b92a7f3e6075db082cd256b3f8ef6`.
- The original fixture setup failure was repaired with a no-model preflight
  that reached exact JCode version `v0.58.51-dev (2444e7b6)`.
- Primary launch: JCode proposed unauthorized
  `anthropic/claude-sonnet-4`; the loopback compatibility bridge denied it
  before the real bridge and returned `400`. This was not an external request.
- One corrective retry used explicit `openai-compatible` and
  `qwen2.5-coder:14b` flags. The bridge then rejected JCode's oversized input
  against the sealed 256-token budget before calling Ollama.
- Totals: two contained JCode launches, two loopback compatibility requests,
  zero real-model requests, zero direct JCode-to-Ollama requests, zero tool
  calls, and zero fixture mutations. No further retry is authorized.
- Focused static regression after the remediation source change: `34 passed`;
  static launcher compilation passed with `gcc -static -O2 -Wall -Werror`.

The unresolved condition is JCode's oversized compatibility prompt relative to
the sealed input budget. A higher budget or any additional run requires a new
operator authorization. No mount, filesystem, network, model, provider, or
authority broadening was made.

Frozen benchmark changes: 0. Daily-runtime changes: 0. Gate 2-J.9J,
diagnostics, and the 80-run comparison remain unstarted.
