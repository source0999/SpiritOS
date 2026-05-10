# localSearchPlan.md

## Purpose

Move SpiritOS web research away from an OpenAI-only web-search path and toward a free/local-first provider ladder.

This plan is intentionally incremental. Each section is small enough for Cursor, Codex, or another coding agent to complete without rewriting the whole chat runtime. The immediate checkpoint is not to build a full crawler platform. The immediate checkpoint is to make `/chat` Researcher, Teacher, `/api/research/web-search`, and the current Next server search path use a provider-agnostic local search router first, with paid OpenAI web search kept only as an explicit fallback.

## ARPA rule for this plan

- Analyze first.
- Research with references.
- Plan in small increments.
- Ask permission before writing a Cursor/Codex implementation prompt.
- Do not implement changes from this file until the user approves the next prompt/action.

## Current repo diagnosis

### Current dependency problem

The current search route is OpenAI-centered instead of provider-centered.

Known current paths to audit before touching code:

- `src/lib/server/openai-web-search.ts`
- `src/lib/server/spirit-web-research-guard.ts`
- `src/app/api/research/web-search/route.ts`
- `src/app/api/spirit/route.ts`
- `src/lib/spirit/spirit-route-decision.ts`
- `src/lib/spirit/research-source-enforcement.ts`
- `src/lib/server/spirit-search-telemetry.ts`
- `src/lib/spirit/spirit-search-response-headers.ts`
- `src/lib/server/__tests__/openai-web-search.test.ts`
- `src/lib/server/__tests__/openai-web-search-extract.test.ts`
- `src/lib/server/__tests__/spirit-web-research-guard.test.ts`
- `src/lib/server/__tests__/spirit-search-telemetry.test.ts`
- `src/lib/spirit/__tests__/spirit-route-decision.test.ts`
- `src/lib/spirit/__tests__/spirit-search-response-headers.test.ts`
- `src/app/api/spirit/__tests__/route.test.ts`
- `.env.example`
- `.env.local.example`
- `README.md`
- `proxyPlan.md`
- `backend/docker-compose.yml`

### Keep

Keep the good parts:

- Source enforcement.
- Verified HTTP URL filtering.
- No fake citation policy.
- Researcher and Teacher honesty rules.
- Response headers for search provider, search status, source count, and elapsed time.
- User/thread web-search toggles.
- Manual/API/local decision surface in the Source proxy.
- Existing OpenAI helper as a paid fallback provider, not as the default search architecture.

### Replace

Replace OpenAI-specific naming and coupling:

- `openai-web-search` route labels should become provider-neutral where appropriate.
- `OpenAiWebSearchResult` should become a generic `WebSearchResult`.
- `runOpenAiWebSearch` should not be the default call from app routes.
- OpenAI should be one provider inside a provider ladder, not the route itself.

## External references to consult during implementation

Use official docs first. Do not rely on random snippets.

- SearXNG docs: https://docs.searxng.org/
- SearXNG search API: https://docs.searxng.org/dev/search_api.html
- Crawl4AI docs: https://docs.crawl4ai.com/
- Crawl4AI quickstart: https://docs.crawl4ai.com/core/quickstart/
- Playwright docs: https://playwright.dev/docs/intro
- Robots Exclusion Protocol, RFC 9309: https://www.rfc-editor.org/rfc/rfc9309.html

## Design target

### Local-first provider ladder

The desired order:

1. Cache
2. Self-hosted SearXNG
3. Optional lightweight DuckDuckGo or other free provider adapter
4. Direct URL/page fetch and extraction
5. Optional heavy extraction through Source proxy later
6. Paid OpenAI web search only if explicitly enabled and explicitly approved

### Provider rule

The app should think:

> Use free/local verified web sources first. Only use paid API search when local search fails, paid fallback is enabled, and the user approves the spend.

### Non-goals for this checkpoint

Do not build all of these yet:

- Full Deep Research orchestration.
- Full crawler queue.
- Full browser agent that logs into websites.
- CAPTCHA bypass.
- Paywall bypass.
- Scraping private/authenticated pages.
- Source proxy `/v1/web/search` implementation.
- Crawl4AI production integration.
- Playwright dynamic browser fallback.

Those can come later.

## Safety and compliance boundaries

### Allowed

- Query a self-hosted SearXNG instance.
- Fetch public pages by URL.
- Extract readable content from normal public pages.
- Respect robots.txt.
- Use rate limits.
- Cache results to avoid hammering providers.
- Provide manual-search prompts when local search cannot verify sources.
- Use OpenAI only after paid fallback is enabled and the user approves.

### Not allowed

- Do not scrape Google directly as the default route.
- Do not bypass CAPTCHAs.
- Do not bypass paywalls.
- Do not ignore robots.txt.
- Do not scrape private/authenticated sessions unless the user explicitly implements a safe connector later.
- Do not make OpenAI web search the silent fallback.
- Do not claim search ran when every provider failed.

## New environment variables

Keep `WEB_SEARCH_ENABLED` as the global switch.

Add provider-specific variables:

```env
# Global web-search gate.
WEB_SEARCH_ENABLED=false

# Free/local-first provider order.
# Default should not include openai unless explicitly enabled.
WEB_SEARCH_PROVIDER_ORDER=cache,searxng,fetch

# Optional self-hosted SearXNG.
SEARXNG_URL=http://127.0.0.1:8080
SEARXNG_MAX_RESULTS=8
SEARXNG_TIMEOUT_MS=10000

# Optional direct fetch/extraction.
WEB_SEARCH_FETCH_PAGE_ENABLED=true
WEB_SEARCH_FETCH_TIMEOUT_MS=10000
WEB_SEARCH_RESPECT_ROBOTS=true
WEB_SEARCH_USER_AGENT=SpiritOSLocalSearch/0.1

# Optional cache.
WEB_SEARCH_CACHE_ENABLED=true
WEB_SEARCH_CACHE_TTL_SECONDS=86400

# Paid fallback is disabled by default.
WEB_SEARCH_PAID_FALLBACK_ENABLED=false
WEB_SEARCH_REQUIRE_APPROVAL_FOR_PAID=true

# Existing paid fallback values, only used when paid fallback is enabled.
OPENAI_API_KEY=
WEB_SEARCH_MODEL=gpt-4o
WEB_SEARCH_TOOL_TYPE=web_search
WEB_SEARCH_MAX_RESULTS=8
```

Expected default behavior:

- Fresh installs do not need `OPENAI_API_KEY`.
- Existing users are not forced to run SearXNG.
- If `WEB_SEARCH_ENABLED=false`, search stays off.
- If `WEB_SEARCH_ENABLED=true` but no free provider is available, the app returns honest failure or manual-search guidance.
- OpenAI is never used unless fallback is enabled and approval is present.

## Proposed file structure

Add a provider-neutral folder:

```txt
src/lib/server/web-search/
  types.ts
  provider-router.ts
  provider-config.ts
  source-normalizer.ts
  cache-provider.ts
  searxng-provider.ts
  fetch-page-provider.ts
  openai-provider.ts
  research-context.ts
  telemetry.ts
  __tests__/
    web-search-provider-router.test.ts
    source-normalizer.test.ts
    searxng-provider.test.ts
    fetch-page-provider.test.ts
```

Keep the old file temporarily as a compatibility wrapper:

```txt
src/lib/server/openai-web-search.ts
```

Either leave it unchanged for one increment, or make it re-export the OpenAI provider implementation once the generic provider folder is stable.

## Provider result contract

Create a shared result shape.

```ts
export type WebSearchProvider =
  | "cache"
  | "searxng"
  | "ddgs"
  | "fetch"
  | "openai"
  | "manual";

export type WebSearchStatus =
  | "used"
  | "skipped"
  | "disabled"
  | "failed";

export type WebSearchSource = {
  title: string;
  url: string;
  snippet?: string;
  publishedAt?: string;
  provider?: WebSearchProvider;
};

export type WebSearchResult =
  | {
      ok: true;
      searched: true;
      provider: WebSearchProvider;
      sources: WebSearchSource[];
      answerPreview?: string;
      elapsedMs: number;
      providerTrace: WebSearchProviderTrace[];
    }
  | {
      ok: false;
      searched: boolean;
      provider: WebSearchProvider;
      error: string;
      detail?: string;
      elapsedMs: number;
      providerTrace: WebSearchProviderTrace[];
    };

export type WebSearchProviderTrace = {
  provider: WebSearchProvider;
  status: "skipped" | "attempted" | "used" | "failed";
  reason?: string;
  elapsedMs?: number;
  sourceCount?: number;
};
```

The trace matters because the UI and logs should show that Source tried cache, SearXNG, fetch, then stopped before paid fallback.

## Phase 0 - Baseline audit before code

### Increment 0.1 - Inventory current OpenAI search references

Objective: Find every OpenAI-specific web-search reference before changing architecture.

Files to inspect:

- `src/lib/server/openai-web-search.ts`
- `src/app/api/research/web-search/route.ts`
- `src/app/api/spirit/route.ts`
- `src/lib/server/spirit-web-research-guard.ts`
- `src/lib/spirit/spirit-route-decision.ts`
- `src/lib/server/spirit-search-telemetry.ts`
- `src/lib/spirit/spirit-search-response-headers.ts`
- `src/lib/spirit/research-source-enforcement.ts`
- `README.md`
- `.env.example`
- `.env.local.example`

Commands:

```bash
rg "openai-web-search|OpenAiWebSearch|runOpenAiWebSearch|WEB_SEARCH|OPENAI_API_KEY|web_search" src README.md .env.example .env.local.example proxyPlan.md backend -n
```

Manual checks:

- Confirm all current web-search entry points are known.
- Confirm Researcher and Teacher both use the same current paid path.
- Confirm there are tests expecting `openai-web-search`.

Expected output:

- A short implementation note listing all affected files.
- No files changed yet.

Possible errors:

- `rg` unavailable on Windows.
- Repomix path differs from live repo.
- Some references appear only in tests or docs.

Recommended fixes:

- Use `Select-String` in PowerShell if `rg` is unavailable.
- Do not start refactoring until the reference list is complete.

Next step:

- Proceed to Increment 0.2.

### Increment 0.2 - Record current behavior with tests

Objective: Run the current tests before changing search so failures are not blamed on the new provider work.

Commands:

```bash
npm run typecheck
npm run lint -- --quiet
npx vitest run src/lib/server/__tests__/openai-web-search.test.ts
npx vitest run src/lib/server/__tests__/openai-web-search-extract.test.ts
npx vitest run src/lib/server/__tests__/spirit-web-research-guard.test.ts
npx vitest run src/lib/spirit/__tests__/spirit-route-decision.test.ts
npx vitest run src/app/api/spirit/__tests__/route.test.ts
```

Manual checks:

- Save current pass/fail status.
- If existing tests fail, note that they are pre-existing.

Expected output:

- Baseline test report.
- Known failures separated from new search work.

Possible errors:

- Vitest module resolution issue on mounted Windows paths.
- Existing lint warnings unrelated to search.
- Env-dependent tests behave differently locally.

Recommended fixes:

- Capture failures in the work log.
- Do not fix unrelated visual/chat UI issues during this search phase.

Next step:

- Proceed to Phase 1.

## Phase 1 - Provider-neutral web-search contract

### Increment 1.1 - Add generic web-search types

Objective: Introduce provider-neutral types without changing runtime behavior yet.

Files to add:

- `src/lib/server/web-search/types.ts`

Files to avoid changing in this increment:

- `src/app/api/spirit/route.ts`
- `src/app/api/research/web-search/route.ts`

Implementation notes:

- Define `WebSearchProvider`, `WebSearchResult`, `WebSearchSource`, and provider trace types.
- Include an adapter type like `WebSearchAdapter`.
- Use the generic result shape above.
- Keep names neutral. Do not call the generic type `OpenAiWebSearchResult`.

Manual checks:

```bash
npx tsc --noEmit
```

Expected output:

- Typecheck passes.
- No runtime behavior changes.
- No tests should need updates yet.

Possible errors:

- `server-only` import needed if files are server-only.
- Type exports conflict with existing `OpenAiWebSearchResult`.

Recommended fixes:

- Keep this as an additive change.
- Do not import generic types into old routes until Increment 1.2.

Next step:

- Proceed to Increment 1.2.

### Increment 1.2 - Add provider config reader

Objective: Centralize env parsing for the provider ladder.

Files to add:

- `src/lib/server/web-search/provider-config.ts`

Implementation notes:

- Read `WEB_SEARCH_ENABLED`.
- Read `WEB_SEARCH_PROVIDER_ORDER`.
- Read `SEARXNG_URL`, `SEARXNG_MAX_RESULTS`, `SEARXNG_TIMEOUT_MS`.
- Read `WEB_SEARCH_PAID_FALLBACK_ENABLED`.
- Read `WEB_SEARCH_REQUIRE_APPROVAL_FOR_PAID`.
- Default provider order should be `cache,searxng,fetch`.
- Do not include `openai` by default.

Manual checks:

```bash
npx vitest run src/lib/server/web-search/__tests__/web-search-provider-router.test.ts
```

Expected output:

- If the router test does not exist yet, this command can wait until Increment 1.4.
- Config helper can be manually exercised with a tiny test or temporary console only if needed.

Possible errors:

- Empty env strings accidentally become enabled providers.
- Provider order includes unknown names.
- `WEB_SEARCH_ENABLED` defaults unexpectedly to true.

Recommended fixes:

- Unknown providers should be ignored with trace reason `unknown_provider`.
- `WEB_SEARCH_ENABLED` should default false unless existing product decision requires otherwise.
- If keeping Researcher default ON at the thread level, still require the server global gate.

Next step:

- Proceed to Increment 1.3.

### Increment 1.3 - Add source normalizer

Objective: Ensure every provider returns the same verified, deduped, safe source list.

Files to add:

- `src/lib/server/web-search/source-normalizer.ts`
- `src/lib/server/web-search/__tests__/source-normalizer.test.ts`

Implementation notes:

- Use existing `resolveVerifiedHttpUrl` or `isVerifiedHttpUrl`.
- Remove invalid URLs.
- Deduplicate by normalized URL.
- Trim title and snippet.
- Cap sources to the requested max result count.
- Preserve provider label per source.

Manual checks:

```bash
npx vitest run src/lib/server/web-search/__tests__/source-normalizer.test.ts
```

Expected output:

- Invalid URLs are removed.
- Duplicate URLs are collapsed.
- Bare or malformed URLs do not reach final source headers.
- Source count matches verified sources only.

Possible errors:

- Provider returns relative URLs.
- Provider returns result objects without title.
- Provider returns `javascript:` or tracking redirect URLs.

Recommended fixes:

- Reject unsafe URLs.
- Default title to the hostname or `Untitled`.
- Keep redirect unwrapping as a later improvement unless easy and tested.

Next step:

- Proceed to Increment 1.4.

### Increment 1.4 - Add provider router skeleton and ladder test

Objective: Build the routing shell before adding real providers.

Files to add:

- `src/lib/server/web-search/provider-router.ts`
- `src/lib/server/web-search/__tests__/web-search-provider-router.test.ts`

Implementation notes:

- Accept a list of provider adapters.
- Try providers in configured order.
- Stop at the first provider with verified sources.
- Return a full provider trace.
- If all free providers fail, return honest failure.
- Do not call paid OpenAI unless paid fallback is enabled and approval is true.
- Include hard guard tests for no silent paid fallback.

Required test cases:

1. Cache hit stops before SearXNG.
2. Cache miss tries SearXNG next.
3. SearXNG verified results stop before fetch.
4. SearXNG failure falls through to fetch.
5. Empty verified sources count as failure and fall through.
6. OpenAI is skipped when `WEB_SEARCH_PAID_FALLBACK_ENABLED=false`.
7. OpenAI is skipped when paid fallback is enabled but approval is missing.
8. OpenAI is attempted only when enabled, approved, and earlier providers fail.
9. Provider trace records skipped, attempted, used, and failed states.
10. Unknown provider names do not crash the router.

Manual checks:

```bash
npx vitest run src/lib/server/web-search/__tests__/web-search-provider-router.test.ts
```

Expected output:

- The test proves the ladder order.
- There is no network access in this test.
- No OpenAI key is needed.

Possible errors:

- Test accidentally imports real provider modules.
- Test relies on environment state.
- Provider order is nondeterministic.

Recommended fixes:

- Mock provider adapters as pure functions.
- Pass config directly into the router for tests.
- Keep env parsing tests separate from router behavior.

Next step:

- Proceed to Phase 2.

## Phase 2 - Local/free provider implementations in TypeScript

### Increment 2.1 - Add SearXNG provider in TypeScript

Objective: Add a TS/fetch provider for self-hosted SearXNG.

Files to add:

- `src/lib/server/web-search/searxng-provider.ts`
- `src/lib/server/web-search/__tests__/searxng-provider.test.ts`

Implementation notes:

- Use native `fetch`.
- Query `SEARXNG_URL`.
- Prefer `/search?q=...&format=json`.
- Accept max results and timeout.
- Parse result shapes defensively.
- Normalize through `source-normalizer.ts`.
- Return `provider: "searxng"`.
- Do not require SearXNG to be running for normal app startup.

Manual checks:

```bash
SEARXNG_URL=http://127.0.0.1:8080 npx vitest run src/lib/server/web-search/__tests__/searxng-provider.test.ts
```

Expected output:

- Mocked fetch tests pass without a real container.
- Provider returns verified sources from a mocked SearXNG JSON payload.
- Provider returns clear failure when SearXNG is unreachable.

Possible errors:

- Public SearXNG instances may disable JSON.
- SearXNG result object fields differ by engine.
- Local instance returns HTML if JSON format is not enabled.
- Timeout abort errors need clean handling.

Recommended fixes:

- In tests, mock known fields like `title`, `url`, and `content`.
- Support `content` as snippet fallback.
- Return `error: "searxng_unreachable"` or `error: "searxng_invalid_json"`.
- Do not make a missing SearXNG instance fatal.

Next step:

- Proceed to Increment 2.2.

### Increment 2.2 - Add direct fetch extraction provider

Objective: Add lightweight public-page extraction in TypeScript for URLs or search-result enrichment.

Files to add:

- `src/lib/server/web-search/fetch-page-provider.ts`
- `src/lib/server/web-search/__tests__/fetch-page-provider.test.ts`

Dependency options:

- Prefer TS-first extraction.
- Consider `node-html-parser`, `@mozilla/readability`, and `jsdom` only if already acceptable for the repo.
- If dependency weight is a concern, start with a minimal title/meta/paragraph extractor and defer heavier parsing.

Implementation notes:

- Use fetch with timeout.
- Respect `WEB_SEARCH_FETCH_PAGE_ENABLED`.
- Respect `WEB_SEARCH_RESPECT_ROBOTS=true` where feasible.
- Set a clear local user agent.
- Extract title, canonical URL, meta description, and first readable paragraph snippets.
- Do not execute JS.
- Do not use Playwright in this increment.

Manual checks:

```bash
npx vitest run src/lib/server/web-search/__tests__/fetch-page-provider.test.ts
```

Expected output:

- Static HTML fixture produces title, URL, and snippet.
- Invalid URL is rejected.
- Timeout returns clean failure.
- Robots-disallowed page returns skipped or failed with a clear reason.

Possible errors:

- Readability dependency pulls too much weight.
- Some pages require JS and return blank HTML.
- Robots parsing is more complex than expected.

Recommended fixes:

- Keep robots support conservative.
- If robots cannot be checked, skip direct fetch when strict mode is on.
- Defer JS-heavy pages to future Playwright or proxy route.

Next step:

- Proceed to Increment 2.3.

### Increment 2.3 - Keep OpenAI as explicit paid fallback provider

Objective: Preserve existing OpenAI web-search behavior, but move it behind paid fallback rules.

Files to add or modify:

- `src/lib/server/web-search/openai-provider.ts`
- `src/lib/server/openai-web-search.ts`

Implementation notes:

- Move or wrap the existing `runOpenAiWebSearch` logic.
- Provider should return generic `WebSearchResult`.
- It should still support existing env values:
  - `OPENAI_API_KEY`
  - `WEB_SEARCH_MODEL`
  - `WEB_SEARCH_TOOL_TYPE`
  - `WEB_SEARCH_MAX_RESULTS`
- It must not be called unless the provider router says paid fallback is allowed.
- Keep the old exported function as a compatibility wrapper temporarily.

Manual checks:

```bash
npx vitest run src/lib/server/__tests__/openai-web-search.test.ts
npx vitest run src/lib/server/web-search/__tests__/web-search-provider-router.test.ts
```

Expected output:

- Existing OpenAI tests still pass or are updated with minimal changes.
- Provider router test proves OpenAI is skipped unless explicitly enabled and approved.
- No OpenAI key is needed for normal test runs.

Possible errors:

- Existing tests assume OpenAI provider is the only provider.
- Old result type names still leak into generic code.
- Missing key errors show up in local-only route.

Recommended fixes:

- Keep compatibility wrapper until all app routes are migrated.
- Only update tests in the same increment where behavior changes.
- Add clear failure detail: `paid_fallback_disabled`, `paid_approval_required`, or `missing_key`.

Next step:

- Proceed to Increment 2.4.

### Increment 2.4 - Optional DDG/free provider adapter

Objective: Add a lightweight free provider only if it is stable and does not create legal or maintenance issues.

Files to add only if approved:

- `src/lib/server/web-search/ddgs-provider.ts`
- `src/lib/server/web-search/__tests__/ddgs-provider.test.ts`

Implementation notes:

- This is optional.
- Do not scrape Google directly.
- Prefer SearXNG as the main search aggregator.
- If using a library, inspect license and maintenance state first.
- Keep rate limits conservative.
- Provide a kill switch with env.

Manual checks:

```bash
npx vitest run src/lib/server/web-search/__tests__/ddgs-provider.test.ts
```

Expected output:

- Mocked provider returns normalized sources.
- Provider can be disabled.
- No live-network test is required.

Possible errors:

- Free provider blocks automated traffic.
- HTML shape changes.
- Library dependency becomes stale.

Recommended fixes:

- Keep this provider behind `WEB_SEARCH_PROVIDER_ORDER`.
- Do not include it by default until proven stable.

Next step:

- Proceed to Phase 3.

## Phase 3 - Optional SearXNG deployment story

### Increment 3.1 - Add disabled-by-default SearXNG service

Objective: Add local SearXNG deployment support without forcing every user to run another container.

Files to modify:

- `backend/docker-compose.yml`

Files to add:

- `backend/searxng.yml`

Implementation notes:

- Add service under a Docker Compose profile so it is disabled by default.
- Suggested profile name: `local-search`.
- Bind to localhost by default.
- Do not expose it on the LAN unless explicitly configured.
- Do not make Next or Source proxy depend on SearXNG.
- Existing `docker compose up` should behave the same as before.

Example direction for Cursor to implement, not final guaranteed syntax:

```yaml
services:
  searxng:
    image: searxng/searxng:latest
    profiles:
      - local-search
    ports:
      - "127.0.0.1:8080:8080"
    volumes:
      - ./searxng.yml:/etc/searxng/settings.yml:ro
    restart: unless-stopped
```

Simple config direction:

```yaml
use_default_settings: true

server:
  bind_address: "0.0.0.0"
  port: 8080
  secret_key: "change-this-local-dev-secret"

search:
  formats:
    - html
    - json
```

Manual checks:

```bash
cd backend
docker compose --profile local-search up -d searxng
curl "http://127.0.0.1:8080/search?q=spiritos&format=json"
```

Expected output:

- `docker compose up` without profile does not start SearXNG.
- `docker compose --profile local-search up -d searxng` starts SearXNG.
- Curl returns JSON search results.
- Existing backend services still work.

Possible errors:

- Port 8080 already in use.
- SearXNG config rejects default secret key.
- JSON output disabled.
- Engines return no results due rate limiting.
- Docker image config paths differ from current SearXNG docs.

Recommended fixes:

- Change host port with `SEARXNG_HOST_PORT` only if needed.
- Generate a local secret or document replacing it.
- Verify current SearXNG config path from official docs before final implementation.
- Keep failure non-fatal for the app.

Next step:

- Proceed to Increment 3.2.

### Increment 3.2 - Document SearXNG env setup

Objective: Make local search understandable without breaking existing users.

Files to modify:

- `.env.example`
- `.env.local.example`
- `README.md`

Implementation notes:

- Add `SEARXNG_URL`.
- Explain disabled-by-default Docker profile.
- Explain that OpenAI is now paid fallback only.
- Explain that `WEB_SEARCH_ENABLED=true` turns on the server search path, but free providers must be available or configured.
- Document that `OPENAI_API_KEY` is optional unless paid fallback is enabled.

Manual checks:

```bash
rg "SEARXNG_URL|WEB_SEARCH_PROVIDER_ORDER|WEB_SEARCH_PAID_FALLBACK_ENABLED|local-search" README.md .env.example .env.local.example backend/docker-compose.yml -n
```

Expected output:

- Docs show how to start SearXNG.
- Docs show how to set `SEARXNG_URL`.
- Docs make clear OpenAI is optional.
- Docs do not claim local search is always available if SearXNG is not running.

Possible errors:

- Docs imply SearXNG starts automatically.
- Docs still say OpenAI is required for Researcher/Teacher.
- Env examples conflict.

Recommended fixes:

- Use plain labels:
  - "Disabled by default"
  - "Optional local search"
  - "Paid fallback"
  - "Manual fallback"

Next step:

- Proceed to Phase 4.

## Phase 4 - Integrate with Next app routes and chat modes

### Increment 4.1 - Route `/api/research/web-search` through the provider router

Objective: Keep the same API route but make it provider-neutral.

Files to modify:

- `src/app/api/research/web-search/route.ts`

Implementation notes:

- Replace direct `runOpenAiWebSearch` call with `runWebSearch`.
- Preserve request body shape where possible.
- Preserve response source structure where possible.
- Add provider trace in response only if safe and useful.
- Response should say which provider won.

Manual checks:

```bash
curl -sS http://localhost:3000/api/research/web-search \
  -H "Content-Type: application/json" \
  -d '{"query":"latest Next.js release notes","maxResults":5}' | jq
```

Expected output with SearXNG running:

```json
{
  "ok": true,
  "searched": true,
  "provider": "searxng",
  "sources": [
    {
      "title": "...",
      "url": "https://...",
      "snippet": "..."
    }
  ],
  "providerTrace": [
    { "provider": "cache", "status": "skipped" },
    { "provider": "searxng", "status": "used" }
  ]
}
```

Expected output with no provider available:

```json
{
  "ok": false,
  "searched": false,
  "provider": "manual",
  "error": "no_local_provider_available",
  "detail": "No free/local web-search provider returned verified sources."
}
```

Possible errors:

- API route still imports `runOpenAiWebSearch`.
- Response shape breaks UI consumers.
- SearXNG failure returns 500 instead of clean JSON.
- Fetch runs from client side by mistake.

Recommended fixes:

- Keep route server-only.
- Return clean 200/422 style JSON for search failure instead of crashing.
- Preserve backward-compatible fields while adding generic fields.

Next step:

- Proceed to Increment 4.2.

### Increment 4.2 - Route Researcher mode through provider router

Objective: Make Researcher use free/local search first.

Files to modify:

- `src/app/api/spirit/route.ts`
- `src/lib/server/spirit-web-research-guard.ts`
- `src/lib/server/web-search/research-context.ts`

Implementation notes:

- Replace direct OpenAI call with provider router call.
- `formatResearchContextForHermes` should accept generic `WebSearchResult`.
- Change wording from `OpenAI Responses + web_search` to provider-neutral wording.
- Keep no-fake-sources policy.
- Keep verified URL count.

Manual checks:

1. Start Next app.
2. Start SearXNG optional profile.
3. Turn Researcher web search on.
4. Ask:

```txt
Research the latest Vite release notes and give sources.
```

Expected output:

- Response says web search was used.
- Sources are real HTTP URLs.
- Headers show provider `searxng`, not `openai`.
- No OpenAI key is required.
- If SearXNG is not running, response says no verified external sources were available or suggests manual search.

Possible errors:

- Researcher still logs `route: openai-web-search`.
- Header provider still says `openai`.
- Context block says OpenAI even when SearXNG was used.
- Model invents sources when local search fails.

Recommended fixes:

- Update context wording.
- Update route lane label to `web-search` or `local-web-search`.
- Keep source enforcement strict.

Next step:

- Proceed to Increment 4.3.

### Increment 4.3 - Route Teacher web aids through provider router

Objective: Make Teacher mode source links use local/free search first too.

Files to modify:

- `src/app/api/spirit/route.ts`
- `src/lib/spirit/spirit-route-decision.ts`
- `src/lib/spirit/__tests__/spirit-route-decision.test.ts`
- `src/lib/spirit/research-source-enforcement.ts`

Implementation notes:

- Teacher can still trigger web aids for educational prompts.
- The lane should not be named `openai-web-search` anymore.
- If no search sources exist, Teacher should provide Study aids to search, not invented links.
- If sources exist, Teacher can include real links in Study aids.

Manual checks:

Ask Teacher mode:

```txt
Explain the latest peer-reviewed studies on sleep and cognition for my exam.
```

Expected output with local search running:

- Teacher gives simple explanation.
- Study aids includes real links from verified sources.
- Headers show `x-spirit-search-kind: teacher`.
- Provider is local/free when available.

Expected output with local search unavailable:

- Teacher still explains.
- Study aids gives search phrases.
- No fake links.

Possible errors:

- Existing tests expect `openai-web-search`.
- Teacher route decision lane mismatch.
- Teacher overuses search on casual chat.

Recommended fixes:

- Update tests to expect `web-search` or `local-web-search`.
- Keep existing trigger logic, only change provider implementation.
- Keep Teacher's educational phrasing guard.

Next step:

- Proceed to Increment 4.4.

### Increment 4.4 - Update telemetry and headers

Objective: Keep UI activity honest while removing OpenAI-only labels.

Files to modify:

- `src/lib/server/spirit-search-telemetry.ts`
- `src/lib/spirit/spirit-search-response-headers.ts`
- `src/lib/server/__tests__/spirit-search-telemetry.test.ts`
- `src/lib/spirit/__tests__/spirit-search-response-headers.test.ts`

Implementation notes:

- Keep existing headers:
  - `x-spirit-web-search`
  - `x-spirit-search-status`
  - `x-spirit-search-provider`
  - `x-spirit-source-count`
  - `x-spirit-search-query`
  - `x-spirit-search-elapsed-ms`
  - `x-spirit-search-kind`
  - `x-spirit-web-sources`
- Provider should be `searxng`, `fetch`, `openai`, or `manual`.
- Route lane should be generic:
  - `web-search`
  - `local-web-search`
  - `paid-web-search`
  - `local-chat`

Manual checks:

```bash
npx vitest run src/lib/server/__tests__/spirit-search-telemetry.test.ts
npx vitest run src/lib/spirit/__tests__/spirit-search-response-headers.test.ts
```

Expected output:

- Tests pass.
- Headers remain ByteString safe.
- UI can still parse old headers.
- Provider labels reflect actual provider.

Possible errors:

- Existing UI expects exactly `openai-web-search`.
- Header values contain non-ASCII.
- JSON sources header becomes too large.

Recommended fixes:

- Keep parser backward-compatible.
- Cap source header size.
- Use provider-neutral route labels but accept old labels in parser.

Next step:

- Proceed to Phase 5.

## Phase 5 - Tests and validation

### Increment 5.1 - Add provider router tests

Objective: Lock in the ladder order so future edits do not accidentally spend money.

Main file:

- `src/lib/server/web-search/__tests__/web-search-provider-router.test.ts`

Must assert:

- Free providers are tried before paid providers.
- Paid OpenAI provider is not called unless enabled and approved.
- Local success stops the ladder.
- Empty local results fall through.
- Provider trace is accurate.

Manual checks:

```bash
npx vitest run src/lib/server/web-search/__tests__/web-search-provider-router.test.ts
```

Expected output:

- All router tests pass.
- No network calls happen.

Possible errors:

- Test accidentally reads real env vars.
- Test calls real fetch.
- OpenAI mock gets called unexpectedly.

Recommended fixes:

- Inject config and providers directly.
- Use `vi.fn()` mocks.
- Assert call counts.

Next step:

- Proceed to Increment 5.2.

### Increment 5.2 - Update existing search tests

Objective: Change old OpenAI-only expectations to provider-neutral expectations.

Files likely affected:

- `src/lib/server/__tests__/openai-web-search.test.ts`
- `src/lib/server/__tests__/openai-web-search-extract.test.ts`
- `src/lib/server/__tests__/spirit-web-research-guard.test.ts`
- `src/lib/spirit/__tests__/spirit-route-decision.test.ts`
- `src/app/api/spirit/__tests__/route.test.ts`

Manual checks:

```bash
npx vitest run src/lib/server/__tests__/openai-web-search.test.ts
npx vitest run src/lib/server/__tests__/spirit-web-research-guard.test.ts
npx vitest run src/lib/spirit/__tests__/spirit-route-decision.test.ts
npx vitest run src/app/api/spirit/__tests__/route.test.ts
```

Expected output:

- Tests pass with provider-neutral names.
- OpenAI-specific tests still validate OpenAI fallback only.
- Researcher and Teacher tests prove local provider path is preferred.

Possible errors:

- Test fixtures use old `OpenAiWebSearchResult`.
- Route test mocks the wrong module path.
- Old route lane assertions fail.

Recommended fixes:

- Add compatibility test for old labels only if needed.
- Update mock imports to `@/lib/server/web-search/provider-router`.
- Keep OpenAI tests scoped to `openai-provider`.

Next step:

- Proceed to Increment 5.3.

### Increment 5.3 - End-to-end manual checks

Objective: Prove the app works in real local mode.

Prerequisites:

```bash
cd backend
docker compose --profile local-search up -d searxng
cd ..
npm run dev
```

Env for local test:

```env
WEB_SEARCH_ENABLED=true
WEB_SEARCH_PROVIDER_ORDER=cache,searxng,fetch
SEARXNG_URL=http://127.0.0.1:8080
WEB_SEARCH_PAID_FALLBACK_ENABLED=false
OPENAI_API_KEY=
```

Manual checks:

1. Call `/api/research/web-search`.
2. Ask Researcher a current question.
3. Ask Teacher a study question.
4. Stop SearXNG and repeat.
5. Add fake OpenAI key and confirm OpenAI is still not used while fallback is false.
6. Enable paid fallback but do not approve, then confirm OpenAI is not used.
7. Approve paid fallback only in a controlled test, then confirm provider says `openai`.

Expected outputs:

- Local SearXNG produces sources.
- Researcher and Teacher show honest source status.
- App does not require `OPENAI_API_KEY`.
- OpenAI does not run silently.
- Failure path is honest and non-crashing.

Possible errors:

- SearXNG returns zero results for some queries.
- Local container starts but JSON format fails.
- Next app cannot reach container due host networking.
- App still says OpenAI in UI labels.
- Missing key error appears despite local provider.

Recommended fixes:

- Test with stable queries like `Next.js documentation` and `MDN fetch API`.
- Verify `curl "$SEARXNG_URL/search?q=test&format=json"`.
- Fix host URL for Docker Desktop vs Linux.
- Search for remaining `OpenAI` strings in UI and server context.

Next step:

- Proceed to Phase 6.

## Phase 6 - Documentation and user-facing behavior

### Increment 6.1 - Update README and env examples

Objective: Make the new behavior clear.

Files to modify:

- `README.md`
- `.env.example`
- `.env.local.example`

Required doc sections:

- Local-first web search.
- Optional SearXNG service.
- SearXNG profile startup command.
- `SEARXNG_URL`.
- Provider order.
- Paid OpenAI fallback.
- Manual fallback behavior.
- Troubleshooting.

Manual checks:

```bash
rg "Local-first web search|SearXNG|SEARXNG_URL|paid fallback|WEB_SEARCH_PROVIDER_ORDER" README.md .env.example .env.local.example -n
```

Expected output:

- New docs are discoverable.
- Existing OpenAI-only docs are removed or reframed as paid fallback docs.
- No docs imply automatic scraping of Google.

Possible errors:

- README has conflicting old Prompt 10B language.
- Env examples still say `OPENAI_API_KEY` required.
- Docker Compose docs do not mention disabled-by-default profile.

Recommended fixes:

- Rewrite old OpenAI section instead of adding another conflicting section.
- Mark OpenAI as optional paid fallback.

Next step:

- Proceed to Increment 6.2.

### Increment 6.2 - Add troubleshooting section

Objective: Make local search debuggable.

Add troubleshooting cases:

#### SearXNG not running

Command:

```bash
curl "http://127.0.0.1:8080/search?q=test&format=json"
```

Expected:

- JSON result.

Fix:

```bash
cd backend
docker compose --profile local-search up -d searxng
```

#### JSON disabled

Symptom:

- Response is HTML, not JSON.

Fix:

- Check `backend/searxng.yml`.
- Confirm `search.formats` includes `json`.
- Restart SearXNG.

#### No results

Symptom:

- SearXNG responds but returns empty results.

Fix:

- Try a broader query.
- Check SearXNG engine settings.
- Check if upstream engines are rate-limiting.

#### App still asks for OpenAI key

Symptom:

- Missing `OPENAI_API_KEY` error appears during local search.

Fix:

- Search for direct `runOpenAiWebSearch` calls.
- Confirm `/api/spirit` and `/api/research/web-search` use provider router.
- Confirm `WEB_SEARCH_PAID_FALLBACK_ENABLED=false`.

#### Fake citations

Symptom:

- Assistant gives sources when provider returned none.

Fix:

- Verify `research-source-enforcement` still receives verified source list.
- Verify `formatResearchSkippedBanner` is used on failure.
- Verify final model system context says no fake links.

Manual checks:

```bash
rg "Troubleshooting local search|JSON disabled|SearXNG not running|Fake citations" README.md -n
```

Expected output:

- README contains troubleshooting steps.
- Troubleshooting does not require the user to understand the codebase.

Possible errors:

- Too much README bloat.
- Troubleshooting mixes Source proxy and Next app too early.

Recommended fixes:

- Keep Source proxy P2 clearly separate.

Next step:

- Proceed to Phase 7.

## Phase 7 - Future Source proxy integration, P2 only

### Increment 7.1 - Document proxy P2, do not implement yet

Objective: Capture future proxy direction without expanding this checkpoint.

Files to modify:

- `proxyPlan.md`
- optionally `localSearchPlan.md` if this file lives in repo

Future files, not for this checkpoint:

- `source_proxy/api/web.py`
- `source_proxy/web/search.py`
- `source_proxy/web/providers/searxng.py`
- `source_proxy/web/providers/fetch.py`

P2 direction:

- Add `/v1/web/search` to Source proxy.
- Reuse same provider ladder concept.
- Let `/v1/decisions/*` recommend:
  - local SearXNG
  - manual browser search
  - paid API fallback
  - cancel
- Keep heavy Python extraction here if needed.
- Crawl4AI belongs here or behind a thin TS wrapper later, not in the first Next app checkpoint.

Manual checks:

```bash
rg "/v1/web/search|Source proxy web search|P2" proxyPlan.md localSearchPlan.md -n
```

Expected output:

- Proxy future is documented.
- No proxy implementation is required.
- No new Python dependencies are introduced in P1.

Possible errors:

- Cursor tries to implement P2 now.
- Crawl4AI gets added directly to Next app path.
- Proxy work distracts from local search migration.

Recommended fixes:

- Put a clear "P2 only, do not implement in this checkpoint" warning.
- Keep Crawl4AI as future proxy-heavy extraction.

Next step:

- Ask user permission before generating the Cursor prompt for Phase 1.

### Increment 7.2 - Future Crawl4AI route through proxy

Objective: Plan heavy extraction without forcing Python into the TS-first provider path.

Future behavior:

- Next app calls Source proxy for heavy crawl/extract only when needed.
- Source proxy owns Crawl4AI setup.
- TS provider router can include a future adapter like `proxy_extract`.
- SearXNG remains the first local search provider.
- Crawl4AI helps turn known URLs into clean markdown, not necessarily find search results.

Manual checks for future implementation:

```bash
curl -k https://127.0.0.1:8787/v1/web/search \
  -H "Content-Type: application/json" \
  -d '{"query":"test query","max_results":5,"prefer_free":true}'
```

Expected future output:

```json
{
  "ok": true,
  "provider": "searxng",
  "recommended_route": "local_route",
  "sources": [],
  "provider_trace": []
}
```

Possible errors:

- Proxy and Next provider routers drift apart.
- Python dependencies slow bootstrap.
- Crawl4AI browser setup fails on Windows or WSL.

Recommended fixes:

- Share the contract shape in docs.
- Keep Next TS provider router the P1 source of truth.
- Add proxy route only after P1 is stable.

Next step:

- P2 after local search P1 is shipped and tested.

## Phase 8 - Final acceptance checklist

A checkpoint is complete when all of these are true:

### Code

- `runOpenAiWebSearch` is no longer called directly by `/api/spirit`.
- `runOpenAiWebSearch` is no longer called directly by `/api/research/web-search`.
- Generic `runWebSearch` or equivalent provider router exists.
- SearXNG provider exists in TypeScript.
- OpenAI provider is paid fallback only.
- Provider trace exists.
- Source normalization rejects invalid URLs.
- Researcher and Teacher use generic web search.
- Source enforcement still prevents fake citations.

### Deployment

- `backend/docker-compose.yml` includes optional SearXNG service.
- SearXNG service is disabled by default using a Compose profile.
- `backend/searxng.yml` exists.
- `SEARXNG_URL` is documented.
- Existing users can run the app without SearXNG.

### Tests

- `web-search-provider-router.test.ts` exists.
- Router test proves the provider ladder.
- Tests prove OpenAI is not called silently.
- Researcher/Teacher route tests are updated.
- Telemetry/header tests are updated.
- Typecheck passes.
- Search-specific Vitest tests pass.

### Manual behavior

- With SearXNG running, Researcher returns real local/free sources.
- With SearXNG off, Researcher is honest about no verified sources.
- Teacher gives real Study aids links only when verified URLs exist.
- Teacher gives search phrases when no verified URLs exist.
- OpenAI is not required for local web search.
- OpenAI is not used unless paid fallback is enabled and approved.

## Recommended implementation order for Cursor

Use these small passes, one prompt at a time:

1. Add generic types, config, normalizer, and provider router test.
2. Add SearXNG provider with mocked tests.
3. Add optional SearXNG Docker Compose profile and docs.
4. Integrate `/api/research/web-search`.
5. Integrate Researcher mode.
6. Integrate Teacher mode.
7. Update telemetry and headers.
8. Update old tests.
9. Run end-to-end manual checks.
10. Document P2 proxy route only.

## Prompt permission gate

Stop here until the user approves the next action.

Do not write the Cursor implementation prompt automatically.

When approved, the first implementation prompt should target only:

- Phase 1
- Increment 1.1
- Increment 1.2
- Increment 1.3
- Increment 1.4

The first prompt should not modify `/api/spirit`, Docker Compose, README, or Source proxy yet.
