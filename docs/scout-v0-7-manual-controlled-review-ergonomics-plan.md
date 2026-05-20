# Scout v0.7 Phase 0.2 Manual-Controlled Review Ergonomics Plan

status: planning/manual-controlled

Status date: 2026-05-20

This document plans small Scout v0.7 review ergonomics work after Scout v0.6 was parked dry-run-only and Scout v0.7 Phase 0.1 decided to keep Scout-to-Proxy import parked. It is planning only. It does not call proxy intake, does not emit actual receipts, does not finalize promotions, does not write proxy memory, does not write coding context, does not register workers, does not schedule writes, does not apply code, does not commit, and does not push.

## Current Parked Boundary

Scout remains manual-controlled:

- Scout-to-Proxy import is parked
- import closeout mode is `dry_run_only`
- live parked dry-run is blocked without `SCOUT_PROMOTION_SIGNING_KEY`
- source approval remains manual
- source rejection remains manual
- source blocking remains manual
- source activation remains manual
- discovery execution remains manual
- candidate extraction remains manual
- packet promotion remains manual
- proxy memory writes remain off
- coding context writes remain off

## Review Ergonomics Goal

Improve operator review speed without increasing Scout authority.

Allowed ergonomics are passive:

- clearer labels for manual gates
- grouped review evidence
- better distinction between recommendation, queued action, and completed manual action
- concise diagnostics copy for mobile review
- read-only summaries of current Scout state
- tests that prove UI copy does not overclaim autonomy

## Forbidden Work

This plan does not authorize:

- proxy intake calls
- append-only intake writes
- actual receipt emission
- promotion finalization
- proxy memory writes
- coding context writes
- active context writes
- hidden background workers
- scheduled writes
- automatic packet promotion
- automatic source approval
- automatic source rejection
- automatic source blocking
- source activation
- discovery execution
- candidate extraction
- apply actions
- commits
- pushes
- self-promotion to a higher autonomy level

## Candidate Increments

### Phase 0.3: Manual Gate Copy Audit

Goal: audit `/intelligence` copy so every mutation-capable button reads as a manual operator action.

Likely files:

- `src/components/dashboard/HomelabScoutIntelligenceWidget.tsx`
- `src/components/dashboard/__tests__/HomelabScoutIntelligenceWidget.test.tsx`
- docs only if no copy change is needed

Implementation notes:

- Rename only labels or nearby passive helper text if current copy is ambiguous.
- Do not add new buttons.
- Do not change API calls.
- Do not change source, packet, discovery, or import behavior.

Manual checks:

- widget tests pass
- closeout compressed output stays `dry_run_only`
- no proxy memory write, coding context write, or promotion finalization

### Phase 0.4: Review Evidence Grouping Plan

Goal: define a small grouping model for review evidence before changing UI.

Likely files:

- docs only first

Implementation notes:

- Group existing read-only fields into operator-friendly buckets.
- Do not fetch new data.
- Do not mutate candidate, source, discovery, packet, memory, or coding context state.

Manual checks:

- doc grep confirms read-only grouping
- closeout compressed output passes

### Phase 0.5: Diagnostics Summary Copy

Goal: make diagnostics output easier to scan on mobile.

Likely files:

- docs first
- maybe `source_proxy/testing/runner.py` only if a later gate approves read-only summary fields

Implementation notes:

- Summary fields must derive from existing checks.
- No new writes.
- No background worker.
- No scheduled watch.

Manual checks:

- runner unit tests if runner output changes
- closeout compressed output passes

### Phase 0.6: Review Ergonomics Stop Point

Goal: park v0.7 review ergonomics after the smallest useful read-only improvement.

Likely files:

- docs only
- `docs/plan-index.md` if a stop-point row is needed

Implementation notes:

- Record what changed.
- Re-state that Scout remains manual-controlled and dry-run-only for import.
- Require a new operator decision before any further Scout increment.

Manual checks:

- stop-point doc exists
- plan index references the stop point if added
- closeout compressed output passes

## Acceptance Criteria

- Scout-to-Proxy import remains parked.
- Closeout mode remains `dry_run_only`.
- `read_only` remains `true`.
- `mutated` remains `false`.
- No proxy intake call occurs.
- No proxy memory write occurs.
- No coding context write occurs.
- No promotion finalization occurs.
- No source approval, rejection, blocking, or activation is automated.
- No discovery execution or candidate extraction is automated.
- UI copy does not overclaim autonomy.
- Any implementation is small enough for manual review from mobile.

## Manual Check

```bash
cd /home/source/SpiritOS && grep -n "Scout v0.7 Phase 0.2 Manual-Controlled Review Ergonomics Plan\|Manual Gate Copy Audit\|Review Evidence Grouping Plan\|Diagnostics Summary Copy\|Review Ergonomics Stop Point\|proxy memory writes remain off\|coding context writes remain off\|Next Permission Gate" docs/scout-v0-7-manual-controlled-review-ergonomics-plan.md docs/plan-index.md && git diff --check && PYTHONPATH=. python3 -m source_proxy.testing.runner --profile scout-v0-5-closeout --json | jq '{result,read_only,mutated,ready:.closeout_summary.ready_for_next_increment,mode:.closeout_summary.mode,blocked:.closeout_summary.parked_dry_run_blocked,proxy_memory:.closeout_summary.would_write_proxy_memory,coding_context:.closeout_summary.would_write_coding_context,finalize:.closeout_summary.would_finalize_promotion,unexpected:.file_change_verdict.unexpected_status_delta,head_changed:.file_change_verdict.head_changed}'
```

Expected outcome:

- plan doc exists
- plan lists the next small review-only increments
- plan index references the v0.7 ergonomics plan
- `git diff --check` prints nothing
- closeout compressed output returns `result: pass`
- `ready` is `true`
- `mode` is `dry_run_only`
- `proxy_memory`, `coding_context`, and `finalize` are `false`
- `unexpected` is empty
- `head_changed` is `false`

## Rollback

```bash
git restore docs/plan-index.md
rm docs/scout-v0-7-manual-controlled-review-ergonomics-plan.md
```

## Next Permission Gate

Operator approval is required before implementing Scout v0.7 Phase 0.3. The recommended next increment is **Scout v0.7 Phase 0.3: Manual Gate Copy Audit**, a small read-only UI-copy audit that must not change Scout authority or behavior.
