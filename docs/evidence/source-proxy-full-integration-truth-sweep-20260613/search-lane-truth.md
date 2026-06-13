# Search Lane Truth

## Findings

SearXNG is configured in repo:

- `backend/docker-compose.yml` defines `searxng` under profile `local-search`.
- `backend/searxng.yml` includes JSON output in `search.formats`.
- README documents `WEB_SEARCH_ENABLED=false` by default and optional SearXNG with `SEARXNG_URL=http://127.0.0.1:8080`.

SearXNG running state:

- Current Windows `docker ps --filter name=searxng` check could not prove running; Docker was unavailable or not running from this session.
- Existing Mac Plan 4 docs recorded past reachability from Mac to `http://10.0.0.186:8080/search?...&format=json`, but this sweep did not perform an external web call or live provider query.
- Current status for this sweep: configured and previously documented, not proven running now.

xersearch/xersearchd:

- `rg -n "xersearch|xersearchd"` returned no matches.
- Current status: MISSING as repo/service implementation.

Scout search:

- `source_proxy/decision/scout_research.py` can call a Scout packet search endpoint only when `SOURCE_PROXY_SCOUT_RESEARCH_ENABLED=1`.
- `source_proxy/api/scout_intake.py` exposes signed Scout promotion intake.
- `source_proxy/proxy_memory/scout_intake.py` can append approved Scout promotions when `SOURCE_PROXY_SCOUT_INTAKE_LOG` is configured.
- Current Source Proxy artifact path does not show Scout being called in Level 3/4 evidence.

Source Proxy search context:

- `source_proxy/decision/research.py` implements repo-first preview, optional Scout, then optional SearXNG via `SEARXNG_URL`.
- `source_proxy/decision/router.py` can mark `research_recommended`.
- `/v1/decisions/route` and `/v1/decisions/prompt-packet` call `enrich_route_decision_with_research`.
- Recent Level 3/4 artifact evidence did not show search use; inspected score files include `web_search_used: false`.

## Needed Wiring

Add a search-needed decision before model invocation:

- Detect current-info need, external factual dependency, docs/API lookup need, or user explicitly asks for web/search.
- Emit a search receipt even when search is skipped.
- If search is needed, choose repo-only, Obsidian, Scout, SearXNG, browser fetch, or handoff.
- Inject bounded, cited results into the context packet.

## Required Search Receipt Fields

- `search_needed`
- `search_decision`
- `provider_selected`
- `provider_running_proven`
- `query`
- `result_count`
- `sources_used`
- `search_context_chars`
- `used_in_model_prompt`
- `skip_reason`
- `errors`
- `receipt_path`

TinyFish or hosted search should remain future optional escalation, not current integration.
