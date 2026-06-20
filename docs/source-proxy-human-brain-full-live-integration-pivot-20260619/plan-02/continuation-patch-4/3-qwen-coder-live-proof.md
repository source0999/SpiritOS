# Qwen Coder Live Proof

Goal: Qwen coder must be activated by the canonical specialist workflow, produce real parsed output, and be consumed downstream.

Implementation:

- Added `run_qwen_coder_lane` in `source_proxy/decision/model_lanes.py`.
- The lane uses local Ollama only.
- Model: `qwen2.5-coder:7b`.
- It receives upstream Gemma, Hermes, route, context, and research state.
- It returns schema-validated JSON with implementation summary, proposed action, acceptance notes, and risk notes.
- Timeout, missing model, missing inventory, bad JSON, or bad schema produces BLOCKED_ENV/NEEDS_FIX, not GO.

Live proof:

- task: task_9b6323805e3e
- status: INTEGRATED_LIVE
- activated: true
- live_invocation: true
- real_output: true
- downstream_consumed: true
- metadata_only: false
- trace_id: trace_2e80e5b5e5dc4304
- invocation_event_id: invocation_bd0a995eb5f94e91
- consumer_event_id: consumer_d50417e473824c54
- output_hash: a0a0aefafdcdf88ea7ad34b3b737c3279b9decd2889ad2fa94dc3d8b6c9d3fee

Raw evidence:

/home/source/spiritos-evidence/plan-02-continuation-patch-4/task-a-live-specialist-proof.json
