# Final Set A Stability Rerun - 2026-06-25

## Verdict

`PLAN3_SET_A_STABLE_GO_READY_FOR_HUMAN_DECISION`

Plan 3 Set A is stable after the SearXNG engine cleanup. The direct provider check returned live sources on every attempt, A3 passed three consecutive live reruns, and full Set A passed twice with all prompts green.

Set B/C were not run. Plan 4 was not started. No push or merge was performed.

## Direct SearXNG 10x Check

- query: `Android Jetpack Compose share intent local task app receipt polling`
- provider URL: `http://127.0.0.1:8080`
- evidence file: `/tmp/spiritos-final-set-a-stability/direct-searxng-10x.jsonl`
- attempts: 10
- HTTP 200 responses: 10
- zero-result runs: 0
- timeout/error runs: 0
- result counts: `20, 20, 20, 20, 20, 20, 20, 20, 20, 20`

The direct provider check was stable enough to run A3 and full Set A.

## A3 Stability 3x

| Run | Receipt run_id | Final status | Source count | Retry count | Provider classification | Failed gates |
| --- | --- | --- | ---: | ---: | --- | --- |
| 1 | `run-20260625T121016Z` | `PASS` | 6 | 0 | `SOURCES_AVAILABLE` | none |
| 2 | `run-20260625T121558Z` | `PASS` | 6 | 0 | `SOURCES_AVAILABLE` | none |
| 3 | `run-20260625T121858Z` | `PASS` | 6 | 0 | `SOURCES_AVAILABLE` | none |

A3 stable `PASS / PASS / PASS`: yes.

## Full Set A Stability 2x

### Full Set A Run 1

- receipt run_id: `run-20260625T122144Z`
- pass count: 10
- failed count: 0
- blocked count: 0
- Set B run: no
- Set C run: no
- Plan 4 work: no

| Prompt | Status | Source count | Retry count | Provider classification | Failed gates |
| --- | --- | ---: | ---: | --- | --- |
| A1 | `PASS` | 6 | 0 | `SOURCES_AVAILABLE` | none |
| A2 | `PASS` | 6 | 0 | `SOURCES_AVAILABLE` | none |
| A3 | `PASS` | 6 | 0 | `SOURCES_AVAILABLE` | none |
| A4 | `PASS` | 6 | 0 | `SOURCES_AVAILABLE` | none |
| A5 | `PASS` | 6 | 0 | `SOURCES_AVAILABLE` | none |
| A6 | `PASS` | 6 | 0 | `SOURCES_AVAILABLE` | none |
| A7 | `PASS` | 0 | 0 | `UNKNOWN_NEEDS_HUMAN` | none |
| A8 | `PASS` | 0 | 0 | `UNKNOWN_NEEDS_HUMAN` | none |
| A9 | `PASS` | 6 | 0 | `SOURCES_AVAILABLE` | none |
| A10 | `PASS` | 0 | 0 | `UNKNOWN_NEEDS_HUMAN` | none |

### Full Set A Run 2

- receipt run_id: `run-20260625T124450Z`
- pass count: 10
- failed count: 0
- blocked count: 0
- Set B run: no
- Set C run: no
- Plan 4 work: no

| Prompt | Status | Source count | Retry count | Provider classification | Failed gates |
| --- | --- | ---: | ---: | --- | --- |
| A1 | `PASS` | 6 | 0 | `SOURCES_AVAILABLE` | none |
| A2 | `PASS` | 6 | 0 | `SOURCES_AVAILABLE` | none |
| A3 | `PASS` | 6 | 0 | `SOURCES_AVAILABLE` | none |
| A4 | `PASS` | 6 | 0 | `SOURCES_AVAILABLE` | none |
| A5 | `PASS` | 6 | 0 | `SOURCES_AVAILABLE` | none |
| A6 | `PASS` | 6 | 0 | `SOURCES_AVAILABLE` | none |
| A7 | `PASS` | 0 | 0 | `UNKNOWN_NEEDS_HUMAN` | none |
| A8 | `PASS` | 0 | 0 | `UNKNOWN_NEEDS_HUMAN` | none |
| A9 | `PASS` | 6 | 0 | `SOURCES_AVAILABLE` | none |
| A10 | `PASS` | 0 | 0 | `UNKNOWN_NEEDS_HUMAN` | none |

Final Set A verdict: `PLAN3_SET_A_STABLE_GO_READY_FOR_HUMAN_DECISION`.

## Append-Only Receipt Evidence

Fresh A3-only receipts:

- `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/continuation-3x10-dryrun/set-a-rerun/runs/run-20260625T121016Z/`
- `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/continuation-3x10-dryrun/set-a-rerun/runs/run-20260625T121558Z/`
- `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/continuation-3x10-dryrun/set-a-rerun/runs/run-20260625T121858Z/`

Fresh full Set A receipts:

- `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/continuation-3x10-dryrun/set-a-rerun/runs/run-20260625T122144Z/`
- `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/continuation-3x10-dryrun/set-a-rerun/runs/run-20260625T124450Z/`

The tracked latest receipt/report churn produced by live reruns was restored by exact path after the append-only run directories were preserved. The append-only run directories are intentionally not staged by this task.

## Validation

- `git diff --check`: PASS after restoring generated latest receipt churn
- backend regression slice: PASS, `133 passed in 43.97s`
- `source_proxy/tests/test_plan3_stage4r_packet_runner.py`: PASS, `39 passed in 0.41s`
- `source_proxy/tests/test_research_preview.py`: PASS, `10 passed in 0.38s`
- `source_proxy/tests/test_scout_research_bridge.py`: PASS, `8 passed in 0.36s`
- frontend checks: SKIP, no frontend changed

## Scope Guardrails

- model contract changed: no
- validation loosened: no
- zero-source research accepted as PASS: no
- stale cached sources used as live proof: no
- fabricated sources used: no
- Set B/C run: no
- Plan 4 started: no
- SpiritFlix/media/Jellyfin touched: no
- pushed: no
- merged: no
