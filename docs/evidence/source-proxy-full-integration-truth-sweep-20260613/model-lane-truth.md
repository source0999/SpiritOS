# Model Lane Truth

## Registry

`source_proxy/decision/model_lanes.py` defines:

- `qwen_local_coder`
- `hermes_sidecar_verifier_preview`
- `gemma_sidecar_context_preview`
- `manual_handoff`
- `cloud_or_api_route_future`

The registry declares:

- `mode: metadata_only_no_model_calls`
- `primary_coder_lane: qwen_local_coder`
- `sidecar_lanes_live: False`

## Current Live Lane

Qwen is the live primary artifact/coder lane in recent Level 3/4 evidence:

- `model_id: qwen2.5-coder:7b`
- `qwen_invoked: true`
- raw transcripts and receipts preserved per run

## Metadata / Preview Lanes

Hermes and Gemma exist as lane metadata:

- Hermes role: verifier/critic.
- Gemma role: intent/context/spec/verifier.
- Both have status `preview_future_only`.
- Both require future operator approval before live call.

## Hermes Truth

Hermes may be configured elsewhere in the repo and chat/local routing history, but recent Source Proxy artifact Level 3/4 evidence says Hermes verifier lane was NOT_INVOKED.

## Gemma Truth

Gemma appears in older comparison evidence and preview lane metadata. It was NOT_INVOKED in recent Level 3/4 artifact runs.

## Cloud/API Truth

Cloud/API route exists as future/approval route metadata. The task explicitly forbade cloud fallback. Recent Level 3/4 evidence did not claim cloud fallback and anti-cheat flags checked for it.

## Proof Required for Future Claims

- selected lane id
- provider
- exact model id
- call start/end timestamp
- transcript path
- prompt hash
- output hash
- whether output was injected into context, used for coding, or advisory only
- final authority owner
