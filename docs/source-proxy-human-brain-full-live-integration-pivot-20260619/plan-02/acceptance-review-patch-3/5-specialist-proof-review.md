# Specialist Proof Review

## Evidence Reviewed

Patch 3 evidence files reviewed:

- 7-specialist-model-lane-proof.md
- 8-task-abc-proof.md

The review prompt referenced 7-specialist-unblock-loop.md and separate Task A/B/C files. The committed artifacts use the consolidated names above.

## What Passed

The specialist proof reports:

- status: INTEGRATED_LIVE
- task: task_1efd570e1a6e
- consumer: cartographer_specialist_packet_consumer
- consumer event: consumer_896ce3ad294b44f3
- Gemma model: gemma3n:e4b, used, JSON schema valid
- Hermes model: hermes4:latest, used, JSON schema valid
- cloud provider: false

A read-only task trace check during this review confirmed consumer_896ce3ad294b44f3 for task_1efd570e1a6e.

The local Ollama inventory includes gemma3n:e4b, hermes4:latest, and qwen2.5-coder:7b.

## Blocker

The claimed specialist integration does not satisfy the independent hardline GO standard.

The verifier lane is explicitly advisory/preview-shaped:

- preview_only: true
- advisory_only: true
- model_calls_enabled: false
- verdict: UNVERIFIED

The specialist integration code treats a non-empty verifier verdict as sufficient shape for integrated status, so UNVERIFIED can still contribute to INTEGRATED_LIVE. That is an advisory-go failure under this review prompt.

The Qwen coder lane is not live-activated in the proof:

- qwen_pre_coder_reasoning_used: false
- qwen_coder_activated: false
- fallback_to_qwen_attempted: false

Qwen is inventoried or classified as invokable, but the requested proof requires live invocation/consumption/failure-changing behavior if Qwen coder is a required lane. Metadata-only availability is not enough for GO.

## Specialist Verdict

FAIL / NEEDS_FIX. Gemma and Hermes look live and consumed, but Qwen coder and browser/functional verifier do not meet the hardline live-integration requirement.
