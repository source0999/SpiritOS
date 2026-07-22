# Trace-event reconciliation status

The v1.1 names remain benchmark target terms, not names a harness may fabricate.
The production mapping is now recorded in
`benchmarks/coder-backend-100/v1.1/trace-event-contract-map.json` with status
`MAPPED_RUNTIME_CONFIRMED_PHASE_0`. Its twelve mappings identify a real
`source_proxy/` emitter, payload mapping, semantic-equivalence argument,
missing-field analysis, evidence record, amendment version, and independent
validator binding.

Runtime confirmation is scoped to the authenticated disposable LumaCart Phase 0
run at source head `59aba3dfe160ad6a3548e369800c970598943827`; its receipt is
`docs/evidence/campaign-3.5-integrated-coder-backend/phase-0-authenticated-run-20260719.json`.
That confirmation does not validate a direct adapter harness, the Core 30, the
Full 100, or a new source head. Those executions must still reconcile their own
real events to this map.

Validate the current map with:

```text
python3 scripts/validate-campaign-3-5-trace-event-map.py
python3 -m pytest -q source_proxy/tests/test_campaign_3_5_trace_event_map.py
```

Missing or ambiguous semantics still block scoring until a versioned amendment
is independently accepted. Task definitions remain immutable and cannot be
silently renamed or weakened.
