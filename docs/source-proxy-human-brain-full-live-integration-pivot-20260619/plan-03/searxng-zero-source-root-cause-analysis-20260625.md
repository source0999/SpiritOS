# SearXNG Zero-Source Root Cause Analysis - 2026-06-25

## Scope

This task is provider reliability only. It does not patch A3 decision wording,
loosen materiality or provenance gates, accept zero-source research as PASS,
fabricate sources, use stale cached sources as live proof, add API/frontier calls,
introduce RouteLLM, run Set B/C, or start Plan 4.

## Prior Failure

The preceding Plan 3 provider diagnostic run ended with:

- verdict: `PLAN3_BLOCKED_ENV_RESEARCH_PROVIDER`
- query: `Android Jetpack Compose share intent local task app receipt polling`
- provider URL: `http://127.0.0.1:8080`
- Scout: skipped, `scout_research_disabled`
- active live provider: SearXNG
- A3 stability: `PASS`, `BLOCKED_ENV`, `PASS`
- blocked run source count: `0`
- blocked run retry count: `2`
- blocked run provider classification: `PROVIDER_ZERO_RESULTS`

Zero sources were correctly treated as `BLOCKED_ENV`.

## Direct Provider Evidence

The same A3 query was run directly against SearXNG ten times before the config
change:

| Check | Result |
| --- | --- |
| Direct SearXNG 10x | `10/10` HTTP 200 |
| Raw result count | `20/20/20/20/20/20/20/20/20/20` |
| Usable engines in successful payload | `google`, `startpage` |
| JSON unresponsive engines | `brave: too many requests`, `duckduckgo: CAPTCHA`, `karmasearch: access denied` |

The service was reachable and able to return sources, but the payload and logs
showed engine-level failures.

## Adapter Evidence

The Source Proxy current research adapter was run ten times using disposable
durable task records, without mutating Set A receipts:

| Check | Result |
| --- | --- |
| Adapter 10x | `10/10` `INTEGRATED_LIVE` |
| Normalized source count | `6` on every run |
| Retry count | `0` on every run |
| Provider classification | `SOURCES_AVAILABLE` on every run |
| Provider URL | `http://127.0.0.1:8080` |

This ruled out a current adapter parser bug for the observed query. Valid SearXNG
JSON sources were preserved and normalized.

## Service And Config Evidence

- container: `spirit-searxng`
- health before fix: healthy, running about seven days
- health after fix: healthy after SearXNG-only restart
- mounted tracked config: `backend/searxng.yml` to `/etc/searxng/settings.yml`
- JSON format enabled in config
- pre-fix logs showed repeated DuckDuckGo CAPTCHA exceptions
- pre-fix JSON reported Brave rate limiting, DuckDuckGo CAPTCHA, and Karmasearch
  access denied for the A3 query
- official SearXNG settings docs confirm engine settings are merged by `name` when
  `use_default_settings` is enabled, and `disabled` is a supported engine field:
  https://docs.searxng.org/admin/settings/settings.html

## Root Cause Classification

Primary classification: `SEARXNG_ENGINE_FLICKER`

Supporting classifications:

- `SEARXNG_RATE_LIMITED`: Brave returned `too many requests`.
- `SEARXNG_ENGINE_FLICKER`: DuckDuckGo returned CAPTCHA and Karmasearch returned
  access denied.
- `RETRY_BACKOFF_INSUFFICIENT`: the previous retry layer correctly retried
  zero-source packets, but retrying the same noisy engine set could still produce
  zero usable results.

Not selected:

- `SEARXNG_SERVICE_UNHEALTHY`: the container was healthy and direct calls returned
  results.
- `SEARXNG_TIMEOUT`: no timeout appeared in the direct or adapter 10x probes.
- `SEARXNG_PARSER_EMPTY`: direct JSON and adapter normalization both returned
  sources.
- `SOURCE_PROXY_ADAPTER_BUG`: adapter 10x preserved valid sources.
- `QUERY_TOO_FRAGILE`: the exact query returned sources repeatedly.
- `MULTI_PROVIDER_NEEDED`: not proven for this task because SearXNG returned stable
  sources once noisy engines were isolated.
- `UNKNOWN_NEEDS_HUMAN`: not needed; the failing engines were visible.

## Smallest Safe Fix

The smallest provider fix was to keep SearXNG and JSON enabled, keep default
settings, and disable only the engines proven unhealthy for this query:

- `brave`
- `duckduckgo`
- `karmasearch`

This does not hardcode the A3 query, does not fabricate sources, does not accept
stale cache, and does not alter A3/model contract logic.

## Post-Fix Provider Evidence

After the SearXNG-only restart:

- direct SearXNG 10x: `10/10` HTTP 200
- raw result count: `20` on every run
- unresponsive engines: empty on every run
- adapter 10x: `10/10` `INTEGRATED_LIVE`
- adapter normalized sources: `6` on every run
- adapter retry count: `0` on every run
- adapter classification: `SOURCES_AVAILABLE` on every run

The provider-zero-source condition was fixed for this evidence window.
