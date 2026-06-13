# Cartographer Lane Truth

## Existing Files

Cartographer has substantial code under:

- `source_proxy/cartographer/**`
- `source_proxy/api/cartographer.py`
- `source_proxy/decision/cartographer_routing.py`
- `source_proxy/cartographer/lane_registry.py`
- many `source_proxy/tests/test_cartographer_*`

## Current Role

Cartographer is not live route owner for Source Proxy artifact prompts.

`source_proxy/decision/cartographer_routing.py` states:

- `preview_only: True`
- `live_routing_enabled: False`
- `worker_start_enabled: False`
- `model_calls_enabled: False`
- `memory_writes_enabled: False`

`source_proxy/cartographer/lane_registry.py` also keeps lane records proposal/advisory only, with false authority flags.

Recent Level 3/4 evidence says:

- Level 3: `cartographer_live_route_ownership: false`
- Level 4: `cartographer_live_route_owner: false` in per-prompt traces
- Level 4 mini context: "Not invoked as live route owner; route traces are evidence sidecars."

## Route Ownership API

There are many Cartographer APIs for status, proposals, safe-write gates, approval tokens, queues, and proof models. They are not wired into the prompt-packet route as owner of model/context selection for artifact prompts.

## Needed for Live Ownership

- A Source Proxy pre-model routing hook that asks Cartographer for advisory routing/context recommendation.
- Cartographer returns model/context/verifier/search recommendation only.
- Source Proxy remains write/apply/approval authority.
- Receipts prove Cartographer request, response, decision, and whether Source Proxy accepted or overrode it.

## Receipt Fields

- `cartographer_consulted`
- `cartographer_live_route_owner`
- `cartographer_recommendation_id`
- `recommended_model_lane`
- `recommended_context_sources`
- `recommended_verifier`
- `source_proxy_decision`
- `override_reason`
- `cartographer_wrote_files: false`
