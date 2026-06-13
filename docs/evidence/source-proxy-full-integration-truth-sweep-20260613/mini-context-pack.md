# Mini Context Pack

Upload this file next: `docs/evidence/source-proxy-full-integration-truth-sweep-20260613/mini-context-pack.md`

Current verdict: TRUTH_SWEEP_READY.

What was audited: Source Proxy intake/router, Qwen coder lane, Hermes/Gemma/verifier lanes, Cartographer routing/context, Obsidian context, Scout/search, SearXNG/xersearch, Mac worker, browser fetch/research, Continue/Cursor references, model lane registry, route traces, repair loop, context packets, evidence receipts, and mini context packs.

Actually live today for recent Product/artifact runs: Source Proxy artifact intake/router, Qwen local coder via `qwen2.5-coder:7b`, disposable workspace writes, action/file-block parsing, preview selection, browser behavior probes, bounded repair/retest, score/receipt evidence, route trace sidecars, and mini context packs.

Not live in recent Level 3/4 artifact runs: Gemma, Hermes verifier, Cartographer route ownership, Obsidian selected-note context, Scout/search, SearXNG, xersearch, Mac worker, Continue lane, Cursor lane.

Preview-only: model lane registry sidecars, Gemma/Hermes sidecar metadata, verifier lane model packet, Cartographer routing ownership preview, Cartographer lane/ownership lock proposal models.

Docs-only or dormant: Mac worker Source Proxy integration, Continue/Cursor as Source Proxy routes, xersearch name, Cartographer context injection, Scout promotion-to-prompt context.

Search truth: SearXNG is configured in Docker compose and README but not proven running from this session. Source Proxy has repo/Scout/SearXNG research preview code, but recent artifact runs did not use search. `xersearch`/`xersearchd` was not found in repo search.

Obsidian truth: read-only query code and API exist. The coder path carries diagnostics, but diagnostics state Obsidian context is not used in prompt. Recent Level 3/4 runs did not use Obsidian.

Cartographer truth: substantial Cartographer code and APIs exist. Source Proxy Cartographer routing code is preview-only with live routing disabled. Recent Level 3/4 traces mark Cartographer live route owner false.

Gemma/Hermes/verifier truth: Qwen is the live primary local coder. Gemma/Hermes are preview/future sidecars. The verifier lane is advisory/model-call-disabled. Browser/deterministic behavior evidence is live; model verifier is not.

Mac worker truth: worker scripts and Mac support-node docs exist. No Source Proxy artifact prompt call to Mac worker was found.

Actual live Source Proxy artifact path: human prompt -> task/artifact intake -> disposable workspace decision -> Qwen local model call -> action/file-block parse -> workspace writes -> preview path -> browser behavior probe -> bounded repair/retest -> final verdict -> receipts/mini context pack.

Integration matrix summary: Qwen, repair loop, route traces, browser behavior, anti-tailoring/anti-cheat, and mini packs are live for artifact evidence. Obsidian, Scout, SearXNG, browser research are callable/conditional but unused in recent artifact runs. Gemma/Hermes/verifier/Cartographer ownership are preview-only. Mac worker is dormant. xersearch is missing.

Recommended next implementation: Priority 0 truth receipts. Every prompt should explicitly record which integrations were used or skipped before any Level 5 or multi-system claim. Priority 1 is a context-needed router. Priority 2 is one live integration at a time, likely Obsidian or Search first, then Cartographer advisory routing.
