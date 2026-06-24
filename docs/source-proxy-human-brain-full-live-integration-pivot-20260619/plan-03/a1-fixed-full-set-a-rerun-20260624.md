# A1 Fixed Full Set A Rerun - 2026-06-24

## Commands

First full Set A rerun:

`.venv/bin/python docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/continuation-3x10-dryrun/set-a-rerun/_stage4r_runner.py`

Second bounded full Set A rerun after live search provider returned sources again:

`.venv/bin/python docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/continuation-3x10-dryrun/set-a-rerun/_stage4r_runner.py`

## First Full Rerun Result

- A1: `BLOCKED_ENV`
- A4: `BLOCKED_ENV`
- A5: `BLOCKED_ENV`
- Immediate provider check after the run returned sources for the same blocked query classes, so this was treated as a transient live-search no-result window and rerun once.

## Second Full Rerun Result

| Prompt | Result | Notes |
| --- | --- | --- |
| A1 | `PASS` | A1 thin research-change field failure fixed. |
| A2 | `PASS` | Prior packet path stayed passing. |
| A3 | `NEEDS_FIX` | `research_change_source_not_from_raw_sources` |
| A4 | `PASS` | Live sources returned and materiality passed. |
| A5 | `PASS` | Packet path passed. |
| A6 | `PASS` | Live sources returned and materiality passed. |
| A7 | `PASS` | Repo-only prompt. |
| A8 | `PASS` | Repo-only prompt. |
| A9 | `PASS` | Prior packet path stayed passing. |
| A10 | `PASS` | Repo-only prompt. |

## Current Full Set A Verdict

`NEEDS_FIX`

Full Set A is not GO because A3 surfaced a separate source-linkage failure in the full rerun. This A1-only task does not authorize patching A3.

## A3 Debugger Adequacy

- failure classification: `PRODUCTIVE_OUTPUT_GRADE_FAILURE`
- failed gate: `research_change_source_not_from_raw_sources`
- selected lane/model/provider: `ollama_default` / `gemma3n:e4b` / `ollama`
- source count: 6
- receipt: `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/continuation-3x10-dryrun/set-a-rerun/A3.json`
- trace: `/home/source/spiritos-evidence/plan-03-3x10-dryrun/set-a-rerun/A3.task.final.raw.json`
- next recommended action: inspect A3 source-linkage failure and make one bounded A3-only fix if Britton authorizes it.

## Set B/C

Set B and Set C were not run because full Set A is not honestly GO.
