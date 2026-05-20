# Scout v0.8 Closeout Summary

status: closed/manual-controlled

Status date: 2026-05-20

This closeout summarizes the Scout v0.7 review ergonomics lane, the Scout v0.8 next-lane decision record, and the live gate state after the backlog repair. It is documentation only. It does not implement Scout autonomy, run discovery, extract candidates, promote packets, call proxy intake, write proxy memory, write coding context, register workers, schedule writes, apply code, commit, or push.

## Executive Summary

Scout is parked as a stable manual-controlled intelligence center.

The v0.7 review ergonomics lane is complete and parked. The v0.8 decision record keeps Scout parked until a fresh operator decision chooses a new lane.

The live Scout gate is green:

- packet backlog: `0`
- packets: `45`
- verdicts: `45`
- packet synthesis: ready
- Level 1 soak: pass
- closeout: pass
- closeout mode: `dry_run_only`
- proxy memory writes: `false`
- coding context writes: `false`
- promotion finalization: `false`

## What Changed

### Scout Backlog Repair

One extracted artifact was stuck because the Ollama packet response included `...` inside `graph_relations`. The parser was hardened so malformed graph relation placeholders do not cause Scout to accept an inner relation object as the packet.

Files:

- `scout/src/scout/packets/synthesis.py`
- `scout/src/scout/tests/test_packet_synthesis_orchestrator.py`

Verification:

- focused synthesis tests passed
- the stuck artifact synthesized
- debugger processed the new packet
- packets and verdicts reached `45/45`
- backlog returned to `0`

This was operational repair, not autonomy.

### Scout Review Ergonomics

Read-only operator clarity improved:

- mutation-capable controls use manual gate copy
- dashboard and `/intelligence` show live Scout API refresh copy
- diagnostics summary copy shows backlog, packet synthesis, discovery execution, and memory write safety
- review evidence grouping was planned without adding mutation behavior

Files:

- `src/lib/scout-human-readable.ts`
- `src/components/dashboard/HomelabScoutIntelligenceWidget.tsx`
- `src/components/dashboard/ScoutIntelligenceCenter.tsx`
- `src/components/dashboard/__tests__/HomelabScoutIntelligenceWidget.test.tsx`
- `docs/scout-v0-7-diagnostics-summary-copy.md`
- `docs/scout-v0-7-review-ergonomics-stop-point.md`

### Scout v0.8 Decision

Scout v0.8 Phase 0.1 chose:

- **Option A: Stay Parked And Require A Fresh Operator Decision**

Files:

- `docs/scout-v0-8-next-lane-decision-record.md`
- `docs/scout-v0-8-closeout-summary.md`
- `docs/plan-index.md`

## Safety Boundary

Scout remains forbidden from:

- auto-approval
- auto-rejection
- auto-blocking
- auto source activation
- automatic discovery execution
- automatic candidate extraction
- automatic packet promotion
- proxy intake calls
- proxy memory writes
- coding context writes
- active context writes
- append-only evidence writes
- real receipt emission
- promotion finalization
- apply actions
- commits
- pushes
- service changes
- hidden background workers
- scheduled writes
- self-promotion to a higher autonomy level

## Current Grades

- manual-controlled intelligence center grade: strong, stable, operator-ready
- autonomy grade: parked, not autonomous
- autonomy foundation grade: good, bounded by explicit gates and live diagnostics

## Open Risks

- Live model output can still be malformed. Parser hardening now handles the observed ellipsis placeholder case, but synthesis should stay covered by focused tests.
- Several unrelated Cartographer and Coding files are dirty in the worktree. They were not part of this Scout closeout.
- Scout v0.8 has not selected a new implementation lane.

## Final Verified Gate

The final gate for this closeout must show:

- `git diff --check` clean
- backlog zero
- packet synthesis ready
- Level 1 soak pass
- closeout pass
- `read_only: true`
- `mutated: false`
- `mode: dry_run_only`
- proxy memory, coding context, and finalization remain `false`

## Manual Check

`cd /home/source/SpiritOS && grep -n "Scout v0.8 Closeout Summary\|status: closed/manual-controlled\|Option A: Stay Parked\|proxy memory writes: false\|coding context writes: false\|promotion finalization: false" docs/scout-v0-8-closeout-summary.md docs/plan-index.md && git diff --check && curl -s http://localhost:8077/v1/scout/overview?limit=5 | jq '{backlog,counts,packet_synthesis:(.packet_synthesis // .human_summary.packet_synthesis_status)}' && PYTHONPATH=. python3 -m source_proxy.testing.runner --profile scout-level-1-soak --json | jq '{result,mutated,checks,rank_fields:.summary.rank_fields,warnings:.summary.warnings}' && PYTHONPATH=. python3 -m source_proxy.testing.runner --profile scout-v0-5-closeout --json | jq '{result,read_only,mutated,ready:.closeout_summary.ready_for_next_increment,mode:.closeout_summary.mode,proxy_memory:.closeout_summary.would_write_proxy_memory,coding_context:.closeout_summary.would_write_coding_context,finalize:.closeout_summary.would_finalize_promotion,unexpected:.file_change_verdict.unexpected_status_delta,head_changed:.file_change_verdict.head_changed}'`

Expected outcome:

- closeout summary exists and is indexed
- `git diff --check` prints nothing
- backlog is zero
- packet synthesis is ready
- Level 1 soak returns `result: pass` and `mutated: false`
- closeout returns `result: pass`, `read_only: true`, `mutated: false`, `ready: true`
- `mode` is `dry_run_only`
- proxy memory, coding context, and finalization remain `false`
- `unexpected` is empty
- `head_changed` is `false`

## Rollback

```bash
git restore docs/plan-index.md
rm docs/scout-v0-8-closeout-summary.md
```

## Next Permission Gate

Scout is closed and parked at v0.8 Phase 0.1. Operator approval is required before any new Scout lane. The recommended next increment remains **Scout v0.8 Phase 0.2: Lane Selection**, docs-only, if Scout work continues.
