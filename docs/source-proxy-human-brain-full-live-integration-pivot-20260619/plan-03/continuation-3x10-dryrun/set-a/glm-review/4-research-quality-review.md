# Stage 4 — Research Quality Review

Scope: research-heavy prompts A1, A2, A3, A4, A6, A9.

The rubric here has two independent axes:
1. **Was live research actually performed?** (provider invoked, sources fetched)
2. **Is the recommendation concrete and tied to specific findings?**

Axis 1 fails for all six because the generator hardcodes `SOURCES` and stamps `live_search_used=true` without calling any provider (see Stage 2). Axis 2 mostly passes on content quality. Both axes must pass for RESEARCH_ACCEPTED.

## Per-prompt

### A1 — Pokemon save editor (internet_required=true)
- `live_search_used=true` claimed, `source_count=4`, sources named (PKHeX, PKSM, PKHeX-Web, PKMDS).
- Provider proof: none. `route_decision.research_sources=[]`. Sources are a static list.
- Recommendation is specific and depends on a concrete finding ("do not build a parser; wrap PKHeX.Core; read-only inspector first").
- **RESEARCH_FAKE_OR_UNSUPPORTED** (content is good, but the live-research claim is unsupported).

### A2 — Browser extension -> Source Proxy task (internet_required=true)
- `live_search_used=true`, `source_count=3` (Chrome MV3, MDN native messaging, VS Code MCP).
- Provider proof: none.
- Recommendation is concrete and uses real repo anchors (`/v1/tasks/long-running`, CodingCockpitShell fields).
- **RESEARCH_FAKE_OR_UNSUPPORTED**.

### A3 — Android companion app (internet_required=true)
- `live_search_used=true`, `source_count=3` (Jetpack Compose, Compose architecture, Capacitor).
- Provider proof: none.
- Recommendation concrete (Kotlin Compose over Tailscale/LAN; native > Capacitor for a small companion).
- **RESEARCH_FAKE_OR_UNSUPPORTED**.

### A4 — Obsidian/notes -> AI context (internet_required=true)
- `live_search_used=true`, `source_count=3` (DuckDB RAG, local-first MCP, Analogy plugin).
- Provider proof: none.
- Recommendation concrete (sidecar index, chunk by heading, MCP exposure, no Obsidian mutation).
- **RESEARCH_FAKE_OR_UNSUPPORTED**.

### A6 — Media metadata cleanup (internet_required=true)
- `live_search_used=true`, `source_count=4` (tinyMediaManager, MusicBrainz Picard, TrueNAS forum, r/jellyfin).
- Provider proof: none.
- Recommendation concrete (staging-only, inventory -> preview -> human-approved; explicit no-DB/no-media boundary).
- **RESEARCH_FAKE_OR_UNSUPPORTED**.

### A9 — Current local LLM tools "this month" (internet_required=true)
- `live_search_used=true`, `source_count=4` (OpenHands local LLM docs, glukhov comparison, awesome-local-llm, Ollama Windows GUI article).
- Provider proof: none. Worse, the sources are **evergreen/general docs**, and the prompt specifically asks for what is worth using **this month** (June 2026). No source is dated to this month; the windowscentral pieces are undated consumer articles. The "this month" currency claim is unsupported even on the merits.
- Recommendation is reasonable (keep Ollama baseline; test LM Studio only as operator option; skip vLLM/SGLang) but not anchored to current evidence.
- **RESEARCH_FAKE_OR_UNSUPPORTED** (weakest of the six on currency).

## Summary

| Prompt | live_search_used (claimed) | provider proof | source_count | materially changed (claimed) | recommendation concrete | verdict |
|-------:|:--:|:--:|:--:|:--:|:--:|:--|
| A1 | true | none | 4 | true | yes | RESEARCH_FAKE_OR_UNSUPPORTED |
| A2 | true | none | 3 | true | yes | RESEARCH_FAKE_OR_UNSUPPORTED |
| A3 | true | none | 3 | true | yes | RESEARCH_FAKE_OR_UNSUPPORTED |
| A4 | true | none | 3 | true | yes | RESEARCH_FAKE_OR_UNSUPPORTED |
| A6 | true | none | 4 | true | yes | RESEARCH_FAKE_OR_UNSUPPORTED |
| A9 | true | none | 4 | true | partial (currency) | RESEARCH_FAKE_OR_UNSUPPORTED |

Research quality: **FAIL**. Zero prompts have provider proof of live search. The recommendations read well, but they could all have been written from prior knowledge without any search — which is precisely the "generic plan that could have been written without the claimed search/context" failure mode, dressed up with a source list. To earn RESEARCH_ACCEPTED, the proxy must actually invoke Scout/SearxNG (or `enrich_route_decision_with_research`) and the recommendation must visibly depend on a finding fetched in-run, with provider/response evidence captured to raw evidence.
