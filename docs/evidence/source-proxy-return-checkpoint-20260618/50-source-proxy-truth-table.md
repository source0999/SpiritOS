# Source Proxy Truth Table

Generated from `raw/50-evidence-index.txt`, `raw/50-source-proxy-evidence-extracts.txt`, and current liveness probes.

| Area | Current status | Evidence | Confidence | Notes |
| --- | --- | --- | --- | --- |
| FIP-0 baseline/runtime | `PARTIAL-GO` | FIP-0 closeout existed; runtime currently up on `:8787`; post-Level-5 closeout names source-proxy-lan as runtime. | Medium | Current process is alive, but no fresh FIP run was allowed. |
| FIP-1 context packet | `PARTIAL-GO` | Claude 3x10 says real FIP-1..5 path was enabled. | Medium | Old GO, no fresh packet generation here. |
| FIP-2 research lanes | `PARTIAL-GO` | Claude audit says Scout/SearXNG honestly skipped when no current-info prompts; Level 5R2 says SearXNG was honestly used/blocked depending on results. | Medium | No fresh search calls. |
| FIP-3 Gemma/Hermes lanes | `PARTIAL-GO` | Claude model-lane audit: role separation correct; Gemma ~6 timeouts and Hermes critic one failure were non-gating. | High | Lane degradation should not vanish behind GO. |
| FIP-4 Qwen coding lane | `PARTIAL-GO` | Qwen used 30/30 in Claude battery; `/v1/models` coder alias is enabled now. | High | Coder quality still weak; no fresh coding call. |
| FIP-5 model inventory | `PARTIAL-GO` | Ollama has qwen/gemma/hermes models; `/v1/models` local/coder enabled, classifier missing. | High | No loaded models at capture time. |
| FIP-6 trace/receipt UI | `PARTIAL-GO` | Claude battery: 30/30 durable receipts/traces and trace match. Receipt trace audit flagged raw output excerpts. | High | Trace hygiene remains a concern. |
| FIP-7 integrated gauntlet status | `PARTIAL-GO` | Post-Level-5 stabilization says FIP-7R GO and Level 5R2 GO. | Medium | No broad gauntlet run allowed. |
| Claude 3x10 audit findings | `C / PARTIAL-GO` | 22 productive_go, 8 verifier_blocked_browser, 0 hard-fails; productive_go is structural only. | High | Most important caveat: not proof apps work. |
| GLM/ZCode audit findings | `PARTIAL-GO` | Exact GLM closeout exists; extraction was limited to available summaries. | Medium | Treat as newer audit evidence but not a runtime GO by itself. |
| Browser verifier | `PARTIAL-GO` | Claude audit says no real browser verifier and UI rows blocked; Level 5R2 says browser evidence passed in its matrix. | Medium | Contradiction needs reconciliation before browser-heavy claims. |
| Functional verifier | `NO-GO/PARTIAL` | Claude audit says deterministic verifier is structural only and does not prove behavior. | High | This is the main truth gap behind productive_go. |
| Repair loop | `UNKNOWN/PARTIAL` | Claude battery had 0 repair attempts; Level 5R2 says bounded repair loop visible, no recurrence. | Medium | Not proven organically under honest prompts. |
| productive_go definition | `NO-GO for behavior` | Claude audit: productive_go means structurally valid file, not working app. | High | Must be hardened before intelligence claims. |
| Trace hygiene/redaction | `PARTIAL-GO` | Claude audit flags raw Qwen output excerpt in traces. | High | Needs regression guard. |
| web/search/SearXNG/TinyFish/xersearch | `PARTIAL` | SearXNG can be honest used/blocked; TinyFish deferred; xersearch missing alias. | Medium | Do not claim full research stack ready. |
| Obsidian/context status | `PARTIAL` | `/v1/self/status` says configured not scanned; prior evidence says advisory/read-only. | High | Read-only advisory, not acceptance authority. |
| Cartographer routing | `PREVIEW` | `/v1/cartographer/status`: observing, write actions disabled, approval token missing, dirty package/config blocker. | High | Not a route owner for writes. |
| Mac advisory/design/source readiness | `UNKNOWN/PARTIAL` | Claude audit says Mac worker skipped stub; design context read-only. | Medium | Cosmetic/advisory only. |
| Source Proxy runtime process supervision | `PARTIAL-GO` | tmux session and listener exist; watchers active; no service manager for proxy itself proven. | High | Runtime health/status patch should come before more model work. |

## Reconciliation

The most current live runtime is up, but the authoritative source-of-truth is not a clean GO for implementation authority. Cleanup says proxy return readiness was GO; live Cartographer status now says the repo truth packet is blocked because package/config files are dirty. Both can be true: return-to-analysis is fine, but mutation authority should be explicitly approved and scoped.
