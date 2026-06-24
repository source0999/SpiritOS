# A1-Only Thin Research Fields Analysis - 2026-06-24

## Scope

- Branch: `integration/cleanup-plan3-debug-20260623`
- Starting HEAD: `d1edd343f355c71f8a074d1898386bbf0698e6d6`
- Prompt in scope: A1 only
- Set B/C: not run
- Plan 4: not started

## Current Failure

- Receipt: `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/continuation-3x10-dryrun/set-a-rerun/A1.json`
- Trace: `/home/source/spiritos-evidence/plan-03-3x10-dryrun/set-a-rerun/A1.task.final.raw.json`
- Status: `NEEDS_FIX`
- Failed gates: `research_materially_changed_output`, `research_change_fields_too_thin`
- Debugger adequacy: adequate. The receipt names the selected lane/model, local provider, model call status, failed gates, receipt path, trace path, and next bounded action.

## Evidence Readback

The raw A1 research packet contains concrete source facts:

- Reddit source says PKHeX is popular, expansive, PC-based, and customizable.
- Project Pokemon says PKHeX is a C# core-series save editor with support for core save files and related save formats.
- GitHub says PKHeX is an open-source Pokemon save file editor.
- PKHeX for Web says PKHeX can run across browser-supported platforms.

The latest A1 model attempts are not fake-source failures. They cite raw source titles/hosts, and they state concrete `Decision changed` text. Attempt 1 also contains `Why this changes the recommendation` text, but the model placed `Decision changed` and `Why` inline on the `Source:` line. Attempts 2 and 3 contain source-backed findings plus concrete decision text but omit the `Why` line.

## Root Cause

`ASSEMBLER_CAN_DERIVE_FIELDS_FROM_RAW_EVIDENCE`

The remaining failure is not a missing debugger and not a reason to weaken validation. The runner can safely normalize and complete the research-change block only when raw source linkage succeeds and the model supplied a concrete decision tied to that source-backed finding. This is a code-owned field assembly problem: the runner should split inline labels when present and, when a raw-source-backed block has a concrete decision but no `Why`, derive a bounded materiality sentence from the same raw finding and decision.

## Bounded Fix Strategy

- Parse inline `Decision changed:` and `Why this changes the recommendation:` labels even when the model puts them after `Source:`.
- Add a generic repair helper for internet-required live-model work products that can complete a missing `Why` field only from the same raw finding, source, and concrete decision.
- Keep fake-source and thin-field failures intact when raw source matching fails, a decision is absent, or the fields remain too thin.
- Do not add prompt-ID-specific A1 branches, fake sources, API/frontier calls, Set B/C execution, or Plan 4 work.
