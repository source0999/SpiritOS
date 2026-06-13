# Source Proxy Full Integration Truth Sweep Executive Summary

Date: 2026-06-13

Verdict: TRUTH_SWEEP_READY.

This sweep pauses the level ladder. Level 5 was not started, no new prompt batch was run, no scorer/verdict logic was patched, no real app files were mutated, and no git branch/stage/commit/push/clean/reset/stash/checkout action was taken.

The current live Product/artifact Source Proxy behavior is mostly the Qwen artifact lane:

human prompt -> artifact/task-shape intake -> disposable workspace decision -> Qwen/local model call -> tool-action file blocks -> disposable workspace writes -> preview path -> browser behavior probe -> bounded repair/retest evidence -> score/receipt/mini context pack.

What is actually live:

- Source Proxy FastAPI app and `/v1/decisions/prompt-packet` route.
- Product/artifact route and generic artifact resolver behavior.
- Qwen local coder lane for recent Level 3/4 artifact runs, evidenced by `qwen2.5-coder:7b` receipts and per-run transcripts.
- Disposable artifact workspace writes.
- Tool/action parsing and receipt writing.
- Browser/open behavior probes and Level 3/4 evidence wrappers.
- Repair loop for failed artifact behavior, still bounded to disposable workspaces.
- Route trace sidecars and mini context packs as evidence artifacts.

What is not live in recent Level 3/4 artifact runs:

- Gemma as a live context/spec/model lane.
- Hermes as a live verifier lane.
- Cartographer as live route owner.
- Obsidian context injected into coder prompts.
- Scout, SearXNG, xersearch, or local web search called by the artifact prompt path.
- Mac worker called by Source Proxy.
- Continue/Cursor lanes routed from live Source Proxy prompts.

Most named systems exist as code, documentation, preview endpoints, or advisory packets. That is useful groundwork, but it is not live integration unless a prompt receipt proves invocation.

Recommended next implementation step: add truth receipts first. Every Source Proxy prompt should emit an integration usage receipt with explicit booleans and evidence refs for model lane, context router, Obsidian, search, Cartographer, verifier, Mac worker, repair, browser, and external coder lanes. Only after that should one integration at a time be wired into live prompts.
