# SearXNG Provider Stability Rerun - 2026-06-25

## Preflight

- branch: `integration/cleanup-plan3-debug-20260623`
- starting HEAD: `877f51fdef86e9f16349059323b9b8b9dec87a2f`
- preflight saved under `/tmp/spiritos-searxng-stability/`
- no staged files at preflight
- pre-existing SpiritFlix dirty files were not touched
- pre-existing plan-02 evidence deletions were not touched
- untracked generated/temp files were not staged

## Direct SearXNG 10x Before Fix

Query:

`Android Jetpack Compose share intent local task app receipt polling`

Provider URL:

`http://127.0.0.1:8080`

| Run | HTTP status | Raw result count | Error |
| ---: | ---: | ---: | --- |
| 1 | 200 | 20 | none |
| 2 | 200 | 20 | none |
| 3 | 200 | 20 | none |
| 4 | 200 | 20 | none |
| 5 | 200 | 20 | none |
| 6 | 200 | 20 | none |
| 7 | 200 | 20 | none |
| 8 | 200 | 20 | none |
| 9 | 200 | 20 | none |
| 10 | 200 | 20 | none |

Engine metadata from the direct JSON payload:

- result engines: `google`, `startpage`
- unresponsive engines: `brave: too many requests`, `duckduckgo: CAPTCHA`,
  `karmasearch: access denied`

## Adapter 10x Before Fix

The adapter probe used `create_plan3_durable_task` and
`run_current_research_for_task` with disposable task ids.

| Run | Status | Source count | Retry count | Classification |
| ---: | --- | ---: | ---: | --- |
| 1 | `INTEGRATED_LIVE` | 6 | 0 | `SOURCES_AVAILABLE` |
| 2 | `INTEGRATED_LIVE` | 6 | 0 | `SOURCES_AVAILABLE` |
| 3 | `INTEGRATED_LIVE` | 6 | 0 | `SOURCES_AVAILABLE` |
| 4 | `INTEGRATED_LIVE` | 6 | 0 | `SOURCES_AVAILABLE` |
| 5 | `INTEGRATED_LIVE` | 6 | 0 | `SOURCES_AVAILABLE` |
| 6 | `INTEGRATED_LIVE` | 6 | 0 | `SOURCES_AVAILABLE` |
| 7 | `INTEGRATED_LIVE` | 6 | 0 | `SOURCES_AVAILABLE` |
| 8 | `INTEGRATED_LIVE` | 6 | 0 | `SOURCES_AVAILABLE` |
| 9 | `INTEGRATED_LIVE` | 6 | 0 | `SOURCES_AVAILABLE` |
| 10 | `INTEGRATED_LIVE` | 6 | 0 | `SOURCES_AVAILABLE` |

## Service And Log Findings

- active container: `spirit-searxng`
- service status: healthy
- config file: `backend/searxng.yml`
- config mount: `/home/source/SpiritOS/backend/searxng.yml:/etc/searxng/settings.yml:ro`
- JSON format: enabled
- Scout: disabled by default, `scout_research_disabled`
- SearXNG: only active live research provider
- pre-fix log finding: repeated DuckDuckGo CAPTCHA exceptions
- pre-fix payload finding: Brave rate limit, DuckDuckGo CAPTCHA, Karmasearch
  access denied

## Fix Applied

Changed `backend/searxng.yml` only:

- disabled `brave`
- disabled `duckduckgo`
- disabled `karmasearch`

SearXNG was restarted with:

`docker compose --profile local-search restart searxng`

No A3 wording, model contract, gate, adapter, runner, stale cache, or source
fabrication behavior was changed.

## Post-Fix Direct SearXNG 10x

| Run | HTTP status | Raw result count | Unresponsive engines | Error |
| ---: | ---: | ---: | --- | --- |
| 1 | 200 | 20 | empty | none |
| 2 | 200 | 20 | empty | none |
| 3 | 200 | 20 | empty | none |
| 4 | 200 | 20 | empty | none |
| 5 | 200 | 20 | empty | none |
| 6 | 200 | 20 | empty | none |
| 7 | 200 | 20 | empty | none |
| 8 | 200 | 20 | empty | none |
| 9 | 200 | 20 | empty | none |
| 10 | 200 | 20 | empty | none |

## Post-Fix Adapter 10x

| Run | Status | Source count | Retry count | Classification |
| ---: | --- | ---: | ---: | --- |
| 1 | `INTEGRATED_LIVE` | 6 | 0 | `SOURCES_AVAILABLE` |
| 2 | `INTEGRATED_LIVE` | 6 | 0 | `SOURCES_AVAILABLE` |
| 3 | `INTEGRATED_LIVE` | 6 | 0 | `SOURCES_AVAILABLE` |
| 4 | `INTEGRATED_LIVE` | 6 | 0 | `SOURCES_AVAILABLE` |
| 5 | `INTEGRATED_LIVE` | 6 | 0 | `SOURCES_AVAILABLE` |
| 6 | `INTEGRATED_LIVE` | 6 | 0 | `SOURCES_AVAILABLE` |
| 7 | `INTEGRATED_LIVE` | 6 | 0 | `SOURCES_AVAILABLE` |
| 8 | `INTEGRATED_LIVE` | 6 | 0 | `SOURCES_AVAILABLE` |
| 9 | `INTEGRATED_LIVE` | 6 | 0 | `SOURCES_AVAILABLE` |
| 10 | `INTEGRATED_LIVE` | 6 | 0 | `SOURCES_AVAILABLE` |

## A3 Stability Rerun

A3 was rerun three times only after direct and adapter provider checks were healthy.

| Run | Receipt run_id | Final status | Source count | Retry count | Provider classification | Notes |
| ---: | --- | --- | ---: | ---: | --- | --- |
| 1 | `run-20260625T115624Z` | `PASS` | 6 | 0 | `SOURCES_AVAILABLE` | Provider healthy |
| 2 | `run-20260625T120218Z` | `NEEDS_FIX` | 6 | 0 | `SOURCES_AVAILABLE` | Failed `research_materially_changed_output`, `repo_context_used`, `research_change_source_not_from_raw_sources` |
| 3 | `run-20260625T120526Z` | `PASS` | 6 | 0 | `SOURCES_AVAILABLE` | Provider healthy |

A3 stable PASS: no.

The middle run was not provider-blocked. It had live sources and failed model/product
gates, so this task stops without patching A3/model contract logic.

## Full Set A

Full Set A was not run because A3 did not produce `PASS / PASS / PASS`.

- full Set A run 1: not run
- full Set A run 2: not run
- Set B/C: not run
- Plan 4: not started

## Evidence Files

- `/tmp/spiritos-searxng-stability/direct-searxng-10x.jsonl`
- `/tmp/spiritos-searxng-stability/adapter-research-10x.jsonl`
- `/tmp/spiritos-searxng-stability/searxng-json-engine-summary.json`
- `/tmp/spiritos-searxng-stability/service-config-log-audit.txt`
- `/tmp/spiritos-searxng-stability/spirit-searxng-logs-tail.txt`
- `/tmp/spiritos-searxng-stability/post-fix-direct-searxng-10x.jsonl`
- `/tmp/spiritos-searxng-stability/post-fix-adapter-research-10x.jsonl`
- `/tmp/spiritos-searxng-stability/post-fix-service-log-audit.txt`
- `/tmp/spiritos-searxng-stability/latest-a3-runs.json`

## Verdict

`PLAN3_NEEDS_FIX_WITH_GOOD_DEBUGGERS`

Provider zero-source intermittency was isolated and repaired for this evidence
window. A3 still did not reach stable PASS because one run failed model/product
gates despite live sources.
