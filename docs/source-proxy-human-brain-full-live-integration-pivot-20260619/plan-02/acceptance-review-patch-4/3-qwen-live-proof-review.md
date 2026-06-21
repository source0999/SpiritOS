# Qwen Live Proof Review

## Evidence

Patch 4 evidence reports:

- task: task_9b6323805e3e
- status: INTEGRATED_LIVE
- activated: true
- live_invocation: true
- real_output: true
- downstream_consumed: true
- metadata_only: false
- model: qwen2.5-coder:7b
- output_hash: a0a0aefafdcdf88ea7ad34b3b737c3279b9decd2889ad2fa94dc3d8b6c9d3fee
- trace_id: trace_2e80e5b5e5dc4304
- invocation_event_id: invocation_bd0a995eb5f94e91
- consumer_event_id: consumer_d50417e473824c54
- consumer_subsystem: cartographer_specialist_packet_consumer

Raw evidence file exists:

`/home/source/spiritos-evidence/plan-02-continuation-patch-4/task-a-live-specialist-proof.json`

## Source Review

`run_qwen_coder_lane` is called by `run_specialists_for_task`, not merely listed as metadata. The Qwen lane receives upstream Gemma, Hermes, route, context, and research state. It returns parsed schema-validated JSON. Missing inventory/model, timeout, bad JSON, or bad schema blocks GO.

Tests explicitly reject metadata-only, non-activated, non-live, unconsumed, and missing-consumer Qwen proof.

Verdict: PASS.
