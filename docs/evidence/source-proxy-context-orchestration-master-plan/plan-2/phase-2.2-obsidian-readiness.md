# Plan 2 Phase 2.2 - Obsidian Readiness

Status: GO

## Increment 2.2.1 - Vault path/config truth

`build_obsidian_context_packet` wraps the existing `query_obsidian_context` diagnostics and reports:

- enabled state
- configured vault path state
- include/exclude globs
- max notes
- max chars per note
- read-only state

Decision: GO.

## Increment 2.2.2 - Disabled/missing config diagnostics

Disabled Obsidian returns:

- status: `skipped`
- reason: `disabled`
- diagnostics: `obsidian_context_used: false`

Missing or unavailable vaults return blocked statuses from the existing Obsidian diagnostics instead of silently skipping.

Test:

`test_obsidian_disabled_is_skipped_with_diagnostics`

Decision: GO.

## Increment 2.2.3 - Safe query behavior

The adapter calls the existing read-only Obsidian query function. It does not write notes, mutate memory, or start background work.

Decision: GO.

## Increment 2.2.4 - Task-specific notes

Task-specific selection is tested with `parser output contract`, matching a temp note containing those terms.

Test:

`test_obsidian_selects_safe_task_specific_excerpt`

Decision: GO.

## Increment 2.2.5 - Safe excerpts

Safe excerpt proof:

- secret-like `Token: sk-123456789012345` is not returned raw
- output contains `Token=[redacted]`

Decision: GO.

## Increment 2.2.6 - Production-ready read-only context behavior

Live Plan 2 packet against `/home/source/SpiritOS` records:

- `obsidian`: `skipped`
- reason: `disabled`

This is an explicit skipped state, not a silent bypass.

## Phase Closeout

Phase 2.2 GO. Obsidian produces task-specific safe context when configured, and explicit skipped/blocked diagnostics when disabled or unavailable.

