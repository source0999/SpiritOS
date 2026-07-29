# Gate 2-J.9 Strict NDJSON Event Contract

status: `STRICT_EVENT_PROTOCOL_SPECIFIED`

schema: `source-proxy.gate-2j-9-ndjson-event-contract/v1`
extends: `source_proxy/jcode/evidence.py` (which enforces sequence + terminal sentinel + result fields).

## 1. Wire format

- Exactly one JSON object per line. UTF-8 only. No BOM. No embedded newlines.
- Maximum line length: 256 KiB (operator-sealed default; reject longer lines).
- Maximum event count per run: operator-sealed default (proposed 50,000).
- Strictly increasing integer `sequence` starting at 1; duplicates rejected.
- Trailing newline required; a final partial line (no newline) is a parse failure.
- Parser timeout: the supervisor's inactivity timeout bounds stream silence.

## 2. Per-event required fields

Every event object MUST include:

| Field | Type | Notes |
|---|---|---|
| `schema_version` | string | `source-proxy.jcode-event/v1` (to be sealed in 2-J.9A) |
| `event_id` | string | unique per event (uuid or run-scoped counter) |
| `sequence` | integer | strictly increasing from 1 |
| `timestamp` | string | RFC3339 UTC |
| `task_id` | string | matches envelope |
| `correlation_id` | string | matches envelope |
| `type` | string | one of the permitted types below |
| `source` | string | `jcode` or `proxy` |
| `payload` | object | type-specific |
| `prev_event_hash` | string | SHA-256 of canonical JSON of the previous event; `""` for the first (tamper-evident chain) |

## 3. Permitted event types

- `process.started`
- `jcode.version_attested`
- `environment.attested`
- `provider.configured`
- `model_request.started`
- `model_request.completed`
- `model_request.failed`
- `tool_call.proposed`
- `tool_call.allowed`
- `tool_call.denied`
- `tool_call.completed`
- `file.read`
- `file.write`
- `file.create`
- `file.delete`
- `command.started`
- `command.completed`
- `command.denied`
- `retry`
- `budget.warning`
- `timeout`
- `cancellation.requested`
- `cancellation.completed`
- `process.exited`
- `evidence.sealed`
- `run.completed` (terminal sentinel; carries the executor-claimed result)

An event whose `type` is not in this list is rejected (or quarantined under an explicit
operator decision). Unknown events never become terminal truth.

## 4. Parsing rules (enforced by the extended mapper)

- `ndjson_invalid_json:<line>` -> failure.
- `ndjson_blank_line:<line>` -> failure (no silent skipping).
- `ndjson_event_not_object:<line>` -> failure.
- `ndjson_sequence_invalid:<expected>` -> failure.
- `ndjson_type_missing:<seq>` -> failure.
- `ndjson_terminal_sentinel_missing` -> failure (no `run.completed`).
- `ndjson_prev_event_hash_chain_broken:<seq>` -> failure.
- `ndjson_unknown_event_type:<seq>` -> rejection/quarantine per operator.
- `ndjson_oversized_line:<line>` -> failure.
- `ndjson_partial_final_line` -> failure.
- Missing required result fields in the terminal event -> `jcode_result_field_missing:<field>`.

`map_jcode_ndjson_evidence` is extended to enforce the per-event schema, the prev-hash chain,
unknown-event handling, and stdout-contamination detection (see section 5). It still returns
`executor_claim_is_terminal_truth: False` and the independent-check list; JCode's claimed
success never becomes the Proxy terminal outcome.

## 5. stdout / stderr handling

- stdout is captured to `stdout.log`; stderr to `stderr.log`. Both are hashed.
- NDJSON is read from the event pipe / designated stream ONLY. Any non-NDJSON bytes on the
  event stream are `stdout_contamination` and cause failure.
- Oversized output (beyond `max_output_bytes`) is truncated for capture but recorded as a
  budget violation that maps to a non-`COMPLETED_VERIFIED` terminal class.

## 6. No silent loss

- No event may be dropped. A parser that cannot keep up must backpressure or fail, not skip.
- Required events for a `COMPLETED_VERIFIED` candidate include at minimum: `process.started`,
  `jcode.version_attested`, `environment.attested`, `provider.configured`, at least one
  `model_request.completed` (for model tasks), `process.exited`, `evidence.sealed`,
  `run.completed`. Missing required events -> no success.
