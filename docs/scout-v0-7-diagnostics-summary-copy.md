# Scout v0.7 Phase 0.5 Diagnostics Summary Copy

status: active/manual-controlled

Status date: 2026-05-20

This document records the Scout v0.7 Phase 0.5 diagnostics summary copy increment. The change makes live Scout safety state easier to scan on mobile in the dashboard widget and `/intelligence` safety section. It does not change Scout authority, run discovery, extract candidates, promote packets, call proxy intake, write proxy memory, write coding context, register workers, schedule writes, apply code, commit, or push.

## Scope

The increment adds read-only copy derived from the existing live Scout overview payload:

- packet backlog status
- packet synthesis status
- discovery execution mode
- memory write safety state

## Files Touched

- `src/lib/scout-human-readable.ts`
- `src/components/dashboard/HomelabScoutIntelligenceWidget.tsx`
- `src/components/dashboard/ScoutIntelligenceCenter.tsx`
- `src/components/dashboard/__tests__/HomelabScoutIntelligenceWidget.test.tsx`
- `docs/scout-v0-7-diagnostics-summary-copy.md`
- `docs/plan-index.md`

## Safety Boundary

This increment does not authorize:

- proxy intake calls
- proxy memory writes
- coding context writes
- active context writes
- packet promotion
- promotion finalization
- source approval
- source rejection
- source blocking
- source activation
- discovery execution
- candidate extraction
- background workers
- scheduled writes
- apply actions
- commits
- pushes
- self-promotion to a higher autonomy level

## Acceptance Criteria

- Dashboard shows a compact diagnostics line derived from live Scout data.
- `/intelligence` Safety and Diagnostics shows packet backlog, packet synthesis, and discovery execution state.
- Copy says manual-controlled when discovery execution is manual.
- Copy does not claim autonomy.
- Existing manual action handlers remain manual.
- Widget tests pass.
- Scout Level 1 soak remains read-only and unmutated.
- Scout closeout remains ready and dry-run-only.

## Manual Check

`cd /home/source/SpiritOS && git diff --check && CI=1 npm run test -- HomelabScoutIntelligenceWidget && PYTHONPATH=. python3 -m source_proxy.testing.runner --profile scout-level-1-soak --json | jq '{result,mutated,checks,rank_fields:.summary.rank_fields,warnings:.summary.warnings}' && PYTHONPATH=. python3 -m source_proxy.testing.runner --profile scout-v0-5-closeout --json | jq '{result,read_only,mutated,ready:.closeout_summary.ready_for_next_increment,mode:.closeout_summary.mode,blocked:.closeout_summary.parked_dry_run_blocked,proxy_memory:.closeout_summary.would_write_proxy_memory,coding_context:.closeout_summary.would_write_coding_context,finalize:.closeout_summary.would_finalize_promotion,unexpected:.file_change_verdict.unexpected_status_delta,head_changed:.file_change_verdict.head_changed}'`

Expected outcome:

- `git diff --check` has no output
- widget tests pass
- `scout-level-1-soak` returns `result: pass` and `mutated: false`
- closeout returns `result: pass`, `ready: true`, `mode: dry_run_only`
- proxy memory, coding context, and promotion finalization remain `false`

## Next Permission Gate

Operator approval is required before implementing Scout v0.7 Phase 0.6. The recommended next increment is **Scout v0.7 Phase 0.6: Review Ergonomics Stop Point**, a parking document and final verification gate for this read-only ergonomics lane.
