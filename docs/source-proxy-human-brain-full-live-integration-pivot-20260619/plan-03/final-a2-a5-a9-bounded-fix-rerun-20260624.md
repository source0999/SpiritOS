# Final A2/A5/A9 Bounded Fix Rerun - 2026-06-24

## Command

`PLAN3_STAGE4R_ONLY=A2,A5,A9 .venv/bin/python docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/continuation-3x10-dryrun/set-a-rerun/_stage4r_runner.py`

## Loop 1

- A2: `PASS`
- A5: `PASS`
- A9: `NEEDS_FIX`
- A9 remaining issue: model emitted exact `action_intent: "skip"` after `test later` was normalized successfully.
- Bounded loop action: mapped exact `skip` to existing controlled intent `reject`, with normalization recorded in the shell status.

## Loop 2

### A2

- Before failure: `research_change_source_not_from_raw_sources`
- Fix applied: research-change parsing now stops before repo/Mac evidence, preventing repo snippet `Source:` text from overwriting raw research source lines.
- Source linkage result: raw source registry present; source URLs remain code-owned.
- Packet validation result: valid
- Receipt path: `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/continuation-3x10-dryrun/set-a-rerun/A2.json`
- Trace path: `/home/source/spiritos-evidence/plan-03-3x10-dryrun/set-a-rerun/A2.task.final.raw.json`
- Verdict: `PASS`
- Debugger adequacy: adequate

### A5

- Before failure: `research_materially_changed_output`, `research_change_source_not_from_raw_sources`
- Fix applied: same source parser boundary and raw source registry handling.
- Source linkage result: raw source registry present; source URLs remain code-owned.
- Packet validation result: valid
- Receipt path: `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/continuation-3x10-dryrun/set-a-rerun/A5.json`
- Trace path: `/home/source/spiritos-evidence/plan-03-3x10-dryrun/set-a-rerun/A5.task.final.raw.json`
- Verdict: `PASS`
- Debugger adequacy: adequate

### A9

- Before failure: invalid action intent `test later`
- Fix applied: exact `test later` maps to `defer`; exact `skip` maps to `reject`; unrelated invalid intents still fail.
- Action intent result: normalizations recorded in `code_owned_packet_shell_status.action_intent_normalizations`.
- Packet validation result: valid
- Receipt path: `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/continuation-3x10-dryrun/set-a-rerun/A9.json`
- Trace path: `/home/source/spiritos-evidence/plan-03-3x10-dryrun/set-a-rerun/A9.task.final.raw.json`
- Verdict: `PASS`
- Debugger adequacy: adequate

## Slice Verdict

`A2/A5/A9 PASS`

Set B/C were not run. Plan 4 was not started.
