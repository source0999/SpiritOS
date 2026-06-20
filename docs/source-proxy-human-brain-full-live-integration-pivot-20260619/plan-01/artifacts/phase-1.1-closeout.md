# Phase 1.1 Closeout

Delivered:

- Added `causal_events_json` to the existing long-running task store.
- Added event helpers for event IDs, trace ID reuse, bounded event lists, and secret-shaped note redaction.
- Exposed `task.causal_events` and `task.causal_trace` on task readback.
- Added tests for unique event IDs, shared trace IDs, persistence, and secret-shaped strings not being emitted.

Verdict: GO
