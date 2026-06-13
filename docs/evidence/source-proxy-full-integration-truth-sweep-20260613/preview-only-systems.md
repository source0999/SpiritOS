# Preview-Only Systems

Preview-only means code intentionally says no live call, no worker start, or no authority.

- Model lane registry: `mode: metadata_only_no_model_calls`.
- Hermes sidecar verifier: `preview_future_only`.
- Gemma sidecar context/spec/verifier: `preview_future_only`.
- Verifier lane packet: `preview_only`, `advisory_only`, `model_calls_enabled: false`.
- Cartographer routing ownership: `preview_only`, `live_routing_enabled: false`, `worker_start_enabled: false`, `model_calls_enabled: false`, `memory_writes_enabled: false`.
- Cartographer lane registry/ownership locks: proposal/advisory only with false authority flags.

Preview metadata is useful for UI and receipts. It is not equivalent to invocation.
