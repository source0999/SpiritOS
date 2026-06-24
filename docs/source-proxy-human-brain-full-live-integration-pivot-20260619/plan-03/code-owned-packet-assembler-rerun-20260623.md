# Code-Owned Packet Assembler Rerun - 2026-06-23

## Scope

- Branch: `integration/cleanup-plan3-debug-20260623`
- Runner: `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/continuation-3x10-dryrun/set-a-rerun/_stage4r_runner.py`
- Command: `PLAN3_STAGE4R_ONLY=A2,A5,A9 .venv/bin/python docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/continuation-3x10-dryrun/set-a-rerun/_stage4r_runner.py`
- Set B/C: not run
- Plan 4: not started

## Loop 1

- Change: moved A2/A5/A9 from model-authored final packet JSON to a code-owned packet shell assembled from in-run evidence.
- Result: A2 and A5 packet validation passed; A9 still failed packet validation on `garbled_or_fabricated_tokens_detected`.
- Debugger adequacy: adequate for packet shell ownership and lane/provider truth; A9 exposed a false positive from a real raw source URL containing `local_llm`.

## Loop 2

- Change: renderer research blocks now cite source-title-plus-finding from code-owned evidence; source refs rotate across decisions; garbled-token detection ignores URL text while preserving prose checks.
- Result: Set A remains `NEEDS_FIX`.
- Debugger adequacy: adequate. Receipts identify model-body status, code-owned shell status, provider/model/lane, validation errors, failure class, and next action.

## Prompt Results

### A2

- Receipt: `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/continuation-3x10-dryrun/set-a-rerun/A2.json`
- Trace: `/home/source/spiritos-evidence/plan-03-3x10-dryrun/set-a-rerun/A2.task.final.raw.json`
- Selected lane: `ollama_qwen2.5-coder_7b`
- Provider/model: `ollama` / `qwen2.5-coder:7b`
- Decision packet: valid
- Model body: valid, 5 decisions, parse status `ok`
- Code-owned shell: assembled; source URLs from code; local/API truth from lane metadata
- Result: `NEEDS_FIX`
- Remaining failure: `research_change_source_not_from_raw_sources`

### A5

- Receipt: `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/continuation-3x10-dryrun/set-a-rerun/A5.json`
- Trace: `/home/source/spiritos-evidence/plan-03-3x10-dryrun/set-a-rerun/A5.task.final.raw.json`
- Selected lane: `ollama_hermes4_latest`
- Provider/model: `ollama` / `hermes4:latest`
- Decision packet: valid
- Model body: valid, 3 decisions, parse status `ok`
- Code-owned shell: assembled; source URLs from code; local/API truth from lane metadata
- Result: `NEEDS_FIX`
- Remaining failures: `research_materially_changed_output`, `research_change_source_not_from_raw_sources`

### A9

- Receipt: `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/continuation-3x10-dryrun/set-a-rerun/A9.json`
- Trace: `/home/source/spiritos-evidence/plan-03-3x10-dryrun/set-a-rerun/A9.task.final.raw.json`
- Selected lane: `ollama_hermes4_latest`
- Provider/model: `ollama` / `hermes4:latest`
- Decision packet: invalid
- Model body: invalid, 3 decisions, parse status `wrapped_json_extracted`
- Code-owned shell: assembled; source URLs from code; local/API truth from lane metadata
- Result: `NEEDS_FIX`
- Remaining validation errors: `model_decision_body_invalid_action_intent:test later`, `model_decision_body_invalid_action_intent:test later:1`

## Stop Reason

The code-owned packet assembler fixed the original fake URL/local API/non-JSON wrapping class enough to expose narrower failures. A2/A5 now fail downstream research-block grading despite valid packets. A9 now clearly fails because the model chose an invalid controlled action intent. Per the bounded loop rule, stop with good debuggers instead of adding another semantic mapping or broad grader/renderer change.
