# Current Lane Inventory

status: `DESIGN_QUALIFICATION_ONLY`

| Component | Current role | Authority boundary |
|---|---|---|
| CodingOrchestrator | Canonical lifecycle and durable terminal truth | Sole task, approval, apply, verifier, and terminal authority |
| JCode adapter | Disabled Layer 4 qualification seam | Preview-only; no process dispatch or production import |
| JCode upstream | Pinned external CLI candidate | Exact commit `2444e7b6bc80d421ae3ee404081bdb41150a1830` only |
| Benchmark authority | Campaign 2 frozen gate | Immutable; JCode neither changes nor executes it |
| Terra High | Proposed implementation-work role | Specified only; no tracked runtime component |

No registered or visible component is evidence of causal runtime integration.
The JCode adapter may emit a constrained preview envelope only; it may not
choose a provider, mutate a task, approve, apply, or claim completion.
