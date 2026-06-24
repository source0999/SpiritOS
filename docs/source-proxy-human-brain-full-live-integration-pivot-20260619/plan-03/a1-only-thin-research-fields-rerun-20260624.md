# A1-Only Thin Research Fields Rerun - 2026-06-24

## Command

`PLAN3_STAGE4R_ONLY=A1 .venv/bin/python docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/continuation-3x10-dryrun/set-a-rerun/_stage4r_runner.py`

## Fix Applied

- Added inline research-change label parsing for `Source: ... | Decision changed: ... | Why this changes the recommendation: ...`.
- Added a generic code-owned repair helper that can derive a missing `Why` only from a raw-source-backed finding plus concrete model-authored decision.
- Added receipt/debugger visibility through `research_change_field_repair_status`.
- Added focused tests for inline labels, code-owned `Why` derivation, and fake-source rejection.

## Result

- A1 result: `PASS`
- Failed gates: none
- Source count: 6
- Research materiality: true
- Receipt: `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/continuation-3x10-dryrun/set-a-rerun/A1.json`
- Trace: `/home/source/spiritos-evidence/plan-03-3x10-dryrun/set-a-rerun/A1.task.final.raw.json`

## Debugger Readback

- failure classification: `PASS`
- selected lane/model/provider: `ollama_default` / `gemma3n:e4b` / `ollama`
- model call attempted: true
- protected path block result: `not_required`
- receipt/trace paths present: yes
- next recommended action: `no action`

## Research-Change Fields

- Before: A1 failed with `research_materially_changed_output` and `research_change_fields_too_thin`.
- After: A1 had three accepted research-change blocks and no failed gates.
- Raw grounding: source facts came from the in-run A1 research packet; no fake/model-owned source was accepted.
- Repair use in the successful A1-only rerun: helper enabled, no derived fields needed because the live model emitted sufficient separate fields on the passing attempt.

## Safety

- Set B/C run: no
- Plan 4 started: no
- API/frontier call added: no
- Contract weakened: no
- Hardcoded A1 tailoring: no
- SpiritFlix/media/Jellyfin touched: no
