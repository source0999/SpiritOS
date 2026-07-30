# Gate 2-J.9D Strict NDJSON Event Bridge Receipt

status: `GATE_2J_9D_PASS_NO_MODEL`

authorization: `TERRA_HIGH_AUTHORIZED__GATE_2J_9D`

predecessors: `GATE_2J_9B_CONTAINMENT_RECEIPT.md`, `GATE_2J_9C_SUPERVISION_RECEIPT.md`

## Implemented contract

`source_proxy.jcode.event_schema` defines `source-proxy.jcode-event/v1` and validates
canonical per-event SHA-256 chains. Every accepted event is bound to task, run,
correlation, and gate identity and carries a schema version, unique event ID, ordered
sequence, UTC timestamp, known event type, source, payload, previous hash, and current
hash. `run.completed` is required as the final sentinel; an executor claim never becomes
Proxy terminal truth.

`source_proxy.jcode.evidence.map_strict_jcode_event_evidence` is the strict bridge entry
point. It rejects malformed or incomplete streams rather than silently dropping or
truncating input. Evidence sealing returns `EVIDENCE_INCOMPLETE` on a write failure.

## Focused proof

Focused strict-bridge plus legacy evidence tests: **20 passed**.

The deterministic fixture matrix covers valid reproducibility and controlled rejection of
malformed JSON, partial lines, invalid UTF-8, oversized lines, event-count and aggregate
limits, duplicate/skipped sequences, duplicate IDs, unknown event types and schemas,
missing fields, binding mismatch, previous/current hash tampering, missing terminal,
post-terminal bytes, stdout contamination, event inactivity, and evidence write failure.

## Advancement checks

- JCode executions: `0`
- Model requests: `0`
- Frozen benchmark changes: `0`
- Daily-runtime changes: `0`
- Next gate: `2-J.9E`, only after this receipt's explicit-path commit and push and the
  cumulative no-model regression run are verified.
