# Gate 2-J.9G Contained JCode No-Model Loop

## Verdict

PASS

## Binding

- Authorization: `TERRA_HIGH_AUTHORIZED__GATE_2J_9G_COMPLETION`
- Pinned binary: `2c59d30eeebc6d21e0a8a9a3b90af0022e4b92a7f3e6075db082cd256b3f8ef6`
- Provider route: contained loopback -> sibling relay -> inherited socketpair
  -> Proxy-owned sealed fake backend.

## Successful Loop

The fresh exact-binary task loop completed with exit `0` over the fake-only
route. JCode emitted start, request, response-wait, deterministic text delta,
message-end, and terminal done events. The relay recorded one 52,905-byte
request and the sealed fake backend recorded one identity-valid request and
response for `qwen2.5-coder:7b`.

## Supervision Evidence

Separate fresh-root slow-fake probes established both terminal controls. A
Proxy cancellation at two seconds and a five-second outer timeout each produced
SIGTERM exit `-15`, one fake request, and no surviving process group. The
descendant-aware resource sampler observed the JCode child peak at:

- RSS: 63,168,512 bytes
- Virtual memory: 367,951,872 bytes

The full observed process tree was reaped after termination. The bounded root
has a fresh tmpfs home, no session reuse, no telemetry, a read-only workspace,
and no host filesystem or external egress path.

## Integrity

- JCode launches: 4 in this gate (one successful loop, cancellation, timeout,
  descendant resource sampling).
- Successful fake requests: 1; controlled slow-fake requests: 3.
- Real model requests: 0.
- Direct Ollama requests: 0.
- Repository writes by JCode: 0.
- Frozen benchmark changes: 0.
- Daily-runtime changes: 0.
- Independent working-tree diff before the receipt: empty.

## Next Gate

Gate 2-J.9H may execute exactly one new read-only task only after a fresh
Proxy-side registry/digest observation and a model-attesting bridge are in
place. Gate 2-J.9I remains prohibited.
