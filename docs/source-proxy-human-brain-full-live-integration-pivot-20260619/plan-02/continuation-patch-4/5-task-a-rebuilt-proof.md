# Task A Rebuilt Proof

Task A status: PASS

Task A now requires live specialist/model plus verifier integration. Top-level status is not enough.

| Lane | Required | Invoked | Live output | Downstream consumed | Verification/failure result | Trace ID | Invocation Event | Consumer Event | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Gemma intent/spec | yes | yes | yes | yes | failure blocks GO | trace_e55fa84b8402437e | invocation_22275d16827a4cb9 | consumer_81bdb29517334132 | INTEGRATED_LIVE |
| Hermes critique/risk | yes | yes | yes | yes | failure blocks GO | trace_2e80e5b5e5dc4304 | invocation_421ba6e579c34d28 | consumer_886cee7579d848b0 | INTEGRATED_LIVE |
| Qwen coder | yes | yes | yes | yes | missing activation/consumer blocks GO | trace_2e80e5b5e5dc4304 | invocation_bd0a995eb5f94e91 | consumer_d50417e473824c54 | INTEGRATED_LIVE |
| Browser/functional verifier | yes | yes | VERIFIED | yes | UNVERIFIED/advisory/preview blocks GO | trace_2e80e5b5e5dc4304 | invocation_9378704e31ae47d3 | consumer_07ebf8bfe29b46fe | INTEGRATED_LIVE |

Failure proof:

- Unit tests reject non-activated Qwen.
- Unit tests reject metadata-only Qwen.
- Unit tests reject Qwen without downstream consumer.
- Unit tests reject advisory verifier.
- Unit tests reject preview verifier.
- Unit tests reject UNVERIFIED verifier.
- Unit tests reject verifier without downstream consumer.

Raw evidence:

/home/source/spiritos-evidence/plan-02-continuation-patch-4/task-a-live-specialist-proof.json
