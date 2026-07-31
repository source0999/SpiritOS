# Gate 2-J.9G-B Sealed-Bridge Completion

## Verdict

PASS

## Binding

- Authorization: `TERRA_HIGH_AUTHORIZED__GATE_2J_9G_B_COMPLETION`
- Batch authorization hash: `df84e61f53d8cf10c592926c02276e0d494fd975d55a8036b142617856533b71`
- Pinned binary SHA-256: `2c59d30eeebc6d21e0a8a9a3b90af0022e4b92a7f3e6075db082cd256b3f8ef6`

## Completed Path

```text
Contained JCode
-> in-namespace loopback listener
-> inherited supervisor-owned Unix socketpair
-> Proxy-owned compatibility bridge
-> SealedFakeInferenceBridge
-> chunked SSE response
-> JCode NDJSON completion
```

The initial mounted Unix-socket design connected but failed with `EACCES` on
the sidecar's first read. A bounded `strace` confirmed the failure. The selected
correction is an inherited socketpair reserved for the relay sibling; the
launcher closes all nonstandard descriptors before JCode exec, so JCode itself
does not inherit the channel. This removes the LSM-mounted-socket failure
without exposing host networking or Ollama.

## Exact-Binary Evidence

The fresh-root exact-binary probe exited `0`. The host bridge recorded one
52,905-byte OpenAI-compatible request. It validated the bound task, run,
correlation, authorization, provider profile, model, route mapping, token
budget, and deterministic fake response before returning chunked SSE.

JCode emitted `sending request`, `waiting for response`, the deterministic
text delta, `message_end`, and terminal `done`. The bridge emitted one
`model_request.started` and one `model_request.completed` event with the exact
provider-reported model `qwen2.5-coder:7b`.

## Negative And Integrity Proof

- An unregistered model returns `400` before fake-backend use.
- The compatibility route is limited to `POST /v1/chat/completions` and maps
  internally to the sealed fake route only.
- Fake provider requests: 1 successful exact-binary cycle.
- Real model requests: 0.
- Direct Ollama requests: 0.
- Frozen benchmark changes: 0.
- Daily-runtime changes: 0.
- Repository writes by JCode: 0.

Focused compatibility, fake-bridge, and network tests passed `25/25`; the
socketpair regression adds direct proof that the Proxy bridge can operate from
the supervisor-owned channel.

## Next Gate

Gate 2-J.9G may use the same fake-only route for a supervised no-model task
loop. It must independently prove timeout, cancellation, resource measurement,
child cleanup, and zero repository diff.
