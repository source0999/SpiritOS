# Scout v0.7 Phase 0.1 Reopen Decision Record

status: decided/manual-controlled

Status date: 2026-05-20

This document records the Scout v0.7 reopen decision after Scout v0.6 was parked as a dry-run-only lane. It is documentation only. It does not call proxy intake, does not emit actual receipts, does not finalize promotions, does not write proxy memory, does not write coding context, does not register workers, does not schedule writes, does not apply code, does not commit, and does not push.

## Decision

Chosen path:

**Option A: Keep Scout-to-Proxy Import Parked**

Scout v0.7 does not reopen real Scout-to-Proxy import work.

The only Scout work allowed from this decision is read-only review ergonomics and diagnostics around the existing manual-controlled intelligence center.

## Rationale

Scout v0.6 closed cleanly:

- dry-run-only lane is parked/manual-controlled
- closeout returned `result: pass`
- `read_only: true`
- `mutated: false`
- `ready: true`
- `mode: dry_run_only`
- live parked dry-run remains blocked without `SCOUT_PROMOTION_SIGNING_KEY`
- no proxy intake call occurred
- no proxy memory write occurred
- no coding context write occurred
- no promotion finalization occurred
- unexpected status delta was empty
- head changed was false

The safest next Scout path is to improve review clarity without changing authority.

## Explicitly Not Reopened

Scout v0.7 does not reopen:

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
- source activation
- discovery execution
- candidate extraction
- apply actions
- commits
- pushes
- self-promotion to a higher autonomy level

## Allowed Work

Scout v0.7 may include small read-only review ergonomics:

- clearer diagnostics labels
- shorter manual check docs
- passive dashboard copy improvements
- read-only summaries of existing Scout state
- tests that prove Scout remains manual-controlled
- docs that keep the parked dry-run-only lane discoverable

Allowed work must keep:

- `read_only: true`
- `mutated: false`
- `mode: dry_run_only` for import closeout
- `would_call_proxy_intake: false`
- `would_write_proxy_memory: false`
- `would_write_coding_context: false`
- `would_finalize_promotion: false`

## Recommended Next Increment

**Scout v0.7 Phase 0.2: Manual-Controlled Review Ergonomics Plan**

Goal:

- identify small review-only improvements for `/intelligence`
- keep all Scout mutation gates manual
- keep import parked
- avoid source activation, discovery execution, packet promotion, proxy memory writes, and coding context writes

## Manual Check

```bash
cd /home/source/SpiritOS && grep -n "Scout v0.7 Phase 0.1 Reopen Decision Record\|Keep Scout-to-Proxy Import Parked\|does not reopen real Scout-to-Proxy import work\|would_write_proxy_memory: false\|would_write_coding_context: false\|would_finalize_promotion: false\|Scout v0.7 Phase 0.2" docs/scout-v0-7-reopen-decision-record.md docs/plan-index.md && git diff --check && PYTHONPATH=. python3 -m source_proxy.testing.runner --profile scout-v0-5-closeout --json | jq '{result,read_only,mutated,ready:.closeout_summary.ready_for_next_increment,mode:.closeout_summary.mode,blocked:.closeout_summary.parked_dry_run_blocked,proxy_memory:.closeout_summary.would_write_proxy_memory,coding_context:.closeout_summary.would_write_coding_context,finalize:.closeout_summary.would_finalize_promotion,unexpected:.file_change_verdict.unexpected_status_delta,head_changed:.file_change_verdict.head_changed}'
```

Expected outcome:

- decision record says Scout-to-Proxy import stays parked
- plan index references the v0.7 decision
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
rm docs/scout-v0-7-reopen-decision-record.md
```

## Next Permission Gate

Operator approval is required before implementing Scout v0.7 Phase 0.2. The next increment is planning only unless the operator explicitly approves a small read-only UI or diagnostics change.
