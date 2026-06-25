# Research Provider Stability Analysis - 2026-06-25

## Scope

Plan 3 Set A stability follow-up after commit
`b16d068987081fe5e2cb3ab72c121d8dbe99af7d`.

This analysis is provider-path only. It does not change A3 decision wording, loosen
materiality/provenance gates, add API/frontier calls, start Set B/C, or start Plan 4.

## Latest A3 Stability Evidence

Final A3-only proof from the prior recovery:

- `run-20260625T041716Z`: `PASS`
- `run-20260625T042249Z`: `BLOCKED_ENV`
- `run-20260625T042819Z`: `PASS`

The `BLOCKED_ENV` receipt was:

- query: `Android Jetpack Compose share intent local task app receipt polling`
- selected lane: `generic_stabilized_research`
- source count: `0`
- query variant source counts: `[0]`
- blocked reason: `live research provider returned no sources`
- failed gates: `live_search_sources`, `research_materially_changed_output`,
  `research_change_source_not_from_raw_sources`
- failure classification: `ENV_BLOCKED`

The failure occurred before a useful model-backed research-to-decision product could
be accepted, because the research packet had no live sources. It was correctly not
treated as PASS.

## Provider Path

Current research uses:

- Scout diagnostics through `run_scout_research_diagnostics`
- SearXNG diagnostics through `run_searxng_research_diagnostics`
- source aggregation in `run_current_research_for_task`
- A3 runner query path through `run_research_with_variants`

At analysis time:

- Scout: skipped, `scout_research_disabled`
- SearXNG: used
- provider URL: `http://127.0.0.1:8080`
- A3 query result count: `6`
- top source examples:
  - `Send simple data to other apps | App data and files - Android Developers`
  - `Kotlin Multiplatform samples`
  - `Clipboard & Share in Compose: Copy, Paste & Intent Sharing Guide`
  - `Make your Android app a share target. Receive simple data from ...`

## Root Cause Classification

- `PROVIDER_ZERO_RESULTS`: the failed A3 receipt had zero sources for the only A3
  query attempt.
- `RETRY_MISSING`: the runner/research path performed only one provider attempt for
  A3, so an intermittent empty provider response immediately became `BLOCKED_ENV`.
- `SOURCE_COUNT_NOT_SURFACED`: A3 receipts exposed aggregate source counts and query
  counts, but not provider-attempt counts, retry counts, or per-attempt provider
  status/reason/error detail.

Not selected:

- `QUERY_TOO_NARROW`: the same query returned 6 sources during direct health checks.
- `BLOCKED_ENV_CORRECT_NO_FIX`: `BLOCKED_ENV` was correct, but bounded retry and
  provider diagnostics were missing.
- `UNKNOWN_NEEDS_HUMAN`: not needed; the provider path and missing retry were clear.

## Smallest Fix

Implemented a bounded provider-stability fix:

- add small retry/backoff in `run_current_research_for_task` when no sources are
  returned
- preserve `BLOCKED_ENV` when all attempts still return zero sources
- record provider attempt details, result counts, retry count, max retries, and
  provider failure classification in the research packet
- surface provider debug summary into Set A runner receipts/debugger
- write raw research query-attempt evidence for A3, not only A2/A9

The fix does not fabricate sources, does not accept zero-source research as PASS, and
does not change the generic model contract or A3 prompt content.
