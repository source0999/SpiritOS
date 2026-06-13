# Missing Wiring

The main missing part is a context orchestration step between route decision and model invocation.

Missing wiring:

- No universal integration receipt emitted for every prompt.
- No live context-needed router selecting from repo, Obsidian, search, Scout, Cartographer, verifier, or Mac worker.
- No positive/negative per-subsystem invocation receipt for recent artifact runs.
- No live Cartographer route ownership in prompt-packet execution.
- No Obsidian note excerpts injected into Qwen prompt.
- No SearXNG/Scout/xersearch search results injected into artifact prompts.
- No Hermes/Gemma live advisory call in repair or final verdict.
- No Mac worker job request path from Source Proxy artifact prompts.
- No external coder lane router for Continue/Cursor from the live prompt path.

The next implementation should start with receipts, not model swaps.
