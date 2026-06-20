# Specialist Truth Inventory

## Gemma Intent/Spec

- status: INTEGRATED_LIVE
- invoked by canonical workflow: yes
- real model call: yes, `gemma3n:e4b`
- output: schema-valid JSON with output hash
- downstream consumer: cartographer_specialist_packet_consumer
- causal invocation: invocation_22275d16827a4cb9
- causal consumer: consumer_81bdb29517334132
- failure behavior: required lane failure blocks aggregate specialist GO

## Hermes Critique/Risk

- status: INTEGRATED_LIVE
- invoked by canonical workflow: yes
- real model call: yes, `hermes4:latest`
- output: schema-valid JSON with output hash
- downstream consumer: cartographer_specialist_packet_consumer
- causal invocation: invocation_421ba6e579c34d28
- causal consumer: consumer_886cee7579d848b0
- failure behavior: required lane failure blocks aggregate specialist GO

## Qwen Coder

- status: INTEGRATED_LIVE
- activated by canonical workflow: yes
- real coder call: yes, `qwen2.5-coder:7b`
- output: parsed JSON, output hash `a0a0aefafdcdf88ea7ad34b3b737c3279b9decd2889ad2fa94dc3d8b6c9d3fee`
- downstream consumer: cartographer_specialist_packet_consumer
- causal invocation: invocation_bd0a995eb5f94e91
- causal consumer: consumer_d50417e473824c54
- failure behavior: missing activation, metadata-only state, timeout, bad schema, or missing consumer prevents specialist GO

## Browser/Functional Verifier

- status: INTEGRATED_LIVE
- live verification performed: yes
- result: VERIFIED
- result is VERIFIED or fails honestly: yes
- downstream consumer: cartographer_specialist_packet_consumer
- causal invocation: invocation_9378704e31ae47d3
- causal consumer: consumer_07ebf8bfe29b46fe
- failure behavior: advisory, preview, UNVERIFIED, missing target, missing behavior marker, or missing consumer prevents specialist GO

Raw live proof: /home/source/spiritos-evidence/plan-02-continuation-patch-4/task-a-live-specialist-proof.json
