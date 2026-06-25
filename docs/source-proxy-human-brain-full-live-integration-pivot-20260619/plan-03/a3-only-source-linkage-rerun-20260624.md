# A3-Only Source Linkage Rerun - 2026-06-24

## Command

`PLAN3_STAGE4R_ONLY=A3 .venv/bin/python docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/continuation-3x10-dryrun/set-a-rerun/_stage4r_runner.py`

## Before Failure

- A3 status: `NEEDS_FIX`
- Failed gate: `research_change_source_not_from_raw_sources`
- Root cause: `MODEL_SOURCE_LEAKED_INTO_PACKET`

## Fix Applied

- Canonicalized matched research-change source refs to the raw research registry title, host, and URL.
- Dropped research-change blocks whose source cannot be proven from the raw research source registry.
- Kept the grader strict so insufficient remaining raw-source-backed blocks still fail.

## Raw Research Source Registry Result

- Source count: 6
- Accepted source refs were canonicalized to raw registry entries.
- Repo/Mac evidence did not become research provenance.

## Rerun Result

- A3 status: `PASS`
- Failed gates: none
- Research materiality: true
- Repair status: `canonicalized_source_refs=3`, `dropped_non_raw_source_blocks=0`
- Receipt: `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/continuation-3x10-dryrun/set-a-rerun/A3.json`
- Trace: `/home/source/spiritos-evidence/plan-03-3x10-dryrun/set-a-rerun/A3.task.final.raw.json`

## Debugger Adequacy

- failure classification: `PASS`
- selected lane/model/provider: `ollama_default` / `gemma3n:e4b` / `ollama`
- model call attempted: true
- protected path block result: `not_required`
- receipt/trace paths present: yes
- next recommended action: `no action`

## Set B/C

Set B and Set C were not run.
