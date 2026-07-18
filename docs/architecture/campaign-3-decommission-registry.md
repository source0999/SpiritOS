# Campaign 3 Decommission Registry

| Artifact or lane | Classification | Anchor | Disposition / enforcement |
| --- | --- | --- | --- |
| Historical design Campaign 3 | preserved historical | `codex/spiritos-campaign-3-core-design-lane-20260717` at `4aec510409e8bb82386190af9fa8f666efcbc63e` | `CAMPAIGN_3_SCOPE_DIVERGED_TO_DESIGN`; never relabel or merge |
| `/v1/coding/helper-agents/preview` helpers | prompt-only / duplicate | `src/app/v1/coding/helper-agents/preview/route.ts` | nonselectable; only registered Source Proxy sub-agent invocation may participate |
| `/v1/coding/mac-advisory` | compatibility-only | `src/app/v1/coding/mac-advisory/route.ts` | cannot affect verdict; retained only as an advisory compatibility surface |
| Scout manual memory writes | compatibility-only | `source_proxy/proxy_memory/scout_intake.py`, `source_proxy/api/scout_intake.py` | not a research participant; canonical Scout contract and broker required |
| SearXNG standalone authority | duplicate / obsolete as authority | Scout/search configuration | provider-only behind Scout; no registry selection or evidence claim |
| web fetch/browser standalone lane | duplicate / obsolete as authority | Scout fetch/browser tooling | provider-only behind Scout; no independent participant claim |
| planning, critique, research, repository-analysis, helper, knowledge-writer aliases | callerless, consumerless, or labs-only | prompt catalogs and labs | disabled from production selection unless a contract-bound retained registry entry replaces it |
| design-agent implementation lanes | deferred / excluded | Design Studio roots | preserve behavior; no Campaign 3 implementation |
| Coder 10 validation harness | deferred | existing Coder references | do not start in Campaign 3 |
| Full `/coding` UI wiring | deferred | `src/components/coding/**`, `src/app/coding/**` | Campaign 4 only; Campaign 3 supplies backend contracts |

The runtime registry has no selectable entry for compatibility-only, duplicate,
obsolete, labs-only, callerless, consumerless, prompt-only, or permanent no-op lanes.
Preview-only routes and preview-only helper outputs are likewise nonselectable.
