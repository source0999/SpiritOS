# Campaign 3 Decommission Registry

This registry prevents preview-only, duplicate, obsolete, or scope-diverged lanes from being counted as corrected Campaign 3 participants.

| Artifact Or Lane | Classification | Current Anchor | Reason | Required Gate 3.1 Action |
| --- | --- | --- | --- | --- |
| Historical design Campaign 3 | preserved historical, not corrected C3 | `refs/heads/codex/spiritos-campaign-3-core-design-lane-20260717` at `4aec510409e8bb82386190af9fa8f666efcbc63e` | `CAMPAIGN_3_SCOPE_DIVERGED_TO_DESIGN` | keep unchanged; never relabel as corrected C3 |
| `/v1/coding/helper-agents/preview` prompt-only helpers | duplicate or preview-only until proven | `src/app/v1/coding/helper-agents/preview/route.ts` | preview route is not production invocation | retain only entries with production caller and consumer |
| `/v1/coding/mac-advisory` advisory lane | compatibility-only until proven | `src/app/v1/coding/mac-advisory/route.ts` | advisory output alone does not affect verdict | integrate through Mac worker contract or keep advisory |
| Scout advisory/manual memory writes | compatibility-only until proven | `source_proxy/proxy_memory/scout_intake.py`, `source_proxy/api/scout_intake.py` | Scout must become canonical research lane, not a side write path | route through Source Proxy authority and context broker |
| SearXNG standalone authority | duplicate/obsolete as authority | docs and Scout references | provider must sit behind Scout | make provider-only, never lane authority |
| Design-agent implementation lanes | deferred/excluded | design-studio docs and routes | explicit exclusion from Campaign 3 | preserve behavior only |
| Coder 10 validation harness | deferred | existing Coder validation references | Campaign 5 scope | do not start in C3 |
| Full `/coding` UI wiring | deferred | `src/components/coding/**`, `src/app/coding/**` | Campaign 4 scope | backend contracts only |

Gate 3.1 must expand this table from actual source inventory and make ghost lanes non-selectable.
