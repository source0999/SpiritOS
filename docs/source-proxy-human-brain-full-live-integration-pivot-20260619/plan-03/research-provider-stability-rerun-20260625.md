# Research Provider Stability Rerun - 2026-06-25

## Provider Health Before Rerun

- provider path: Scout + SearXNG through `run_current_research_for_task`
- Scout: skipped (`scout_research_disabled`)
- SearXNG: used
- provider URL: `http://127.0.0.1:8080`
- query: `Android Jetpack Compose share intent local task app receipt polling`
- direct helper result: `INTEGRATED_LIVE`
- source count: `6`
- retry count: `0`
- result counts: `[6]`
- classification: `SOURCES_AVAILABLE`

## Implementation Evidence

Provider-stability implementation:

- `run_current_research_for_task` now performs bounded retry/backoff for zero-source
  provider responses.
- Research packets now include provider attempts, result counts, retry count, max
  retries, backoff seconds, and provider failure classification.
- Set A runner receipts/debuggers now surface `research_provider_debug`,
  `research_provider_retry_count`, and `research_provider_failure_classification`.
- A3 now writes raw research variants/query-attempt evidence like A2/A9.

Guardrails preserved:

- zero sources still produce `BLOCKED_ENV`
- no stale cached sources are accepted
- no model-authored URLs are accepted as sources
- fake GO remains rejected by existing tests
- no A3-specific provider branch was added

## A3 Stability Rerun

The A3-only stability proof was run three times after the provider retry/debugger fix.

| Run | Receipt run_id | Final status | Source count | Retry count | Provider classification | Notes |
| --- | --- | --- | ---: | ---: | --- | --- |
| 1 | `run-20260625T104710Z` | `PASS` | 6 | 0 | `SOURCES_AVAILABLE` | SearXNG sources available on first attempt |
| 2 | `run-20260625T105325Z` | `BLOCKED_ENV` | 0 | 2 | `PROVIDER_ZERO_RESULTS` | Bounded retries exhausted with zero usable sources |
| 3 | `run-20260625T105845Z` | `PASS` | 6 | 0 | `SOURCES_AVAILABLE` | SearXNG sources available on first attempt |

A3 stable PASS: no.

The blocked run is now debuggable without guessing: the receipt records source count
`0`, retry count `2`, and provider failure classification `PROVIDER_ZERO_RESULTS`.

## Full Set A

Full Set A stability was not run because A3 did not produce stable `PASS / PASS /
PASS`.

- full Set A run 1: not run
- full Set A run 2: not run
- Set B/C: not run
- Plan 4: not started

## Receipt Handling

Append-only per-run receipts were preserved under:

- `docs/.../set-a-rerun/runs/run-20260625T104710Z/`
- `docs/.../set-a-rerun/runs/run-20260625T105325Z/`
- `docs/.../set-a-rerun/runs/run-20260625T105845Z/`

Tracked latest receipts/reports overwritten by the live A3 runs were restored by
exact path after the append-only receipts were preserved.

## Verdict

`PLAN3_BLOCKED_ENV_RESEARCH_PROVIDER`

The model contract was not changed in this task. The remaining blocker is provider
availability/reliability: the same A3 query can return six sources, then zero usable
sources after bounded retries, then six sources again.
