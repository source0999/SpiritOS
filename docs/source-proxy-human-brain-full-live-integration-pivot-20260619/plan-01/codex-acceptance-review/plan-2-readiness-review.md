# Plan 2 Readiness Review

## Questions

Does Plan 1 produce a durable causal seam that Plan 2 can build on?

Yes. The seam persists causal events in the existing long-running task record and exposes a compact causal trace through task readback.

Is the consumer proof backend durable, not frontend-only?

Yes. The authoritative consumer is `long_running_status_observer`, persisted as a backend `consumer` event in `causal_events_json`. CodingCockpitShell is only display/acknowledgment.

Are there unresolved blockers before Plan 2?

No Plan 1 implementation blockers were found. The unrelated dirty tree should be isolated before Plan 2 work starts so Plan 2 staging/review does not get contaminated.

Should the raw evidence permission issue at `/mnt/spirit-8tb` be fixed before Plan 2?

Not required for Plan 2 approval, because the fallback raw evidence path is documented and usable. It should be fixed if Britton requires the exact `/mnt/spirit-8tb/spiritos-evidence/plan-01/` location for future evidence retention.

Are there unrelated dirty files that could contaminate Plan 2?

Yes. The current working tree includes unrelated dirty SpiritFlix/media/runtime files and older evidence directories. Plan 2 should use exact path staging and review.

Is the full cockpit Vitest failure a blocker for Plan 2 or a tracked known issue?

Not a Plan 2 blocker. The full cockpit file has unrelated existing UI expectation failures; the new causal trace parser test passes, and `npm run typecheck` passes.

## Readiness Verdict

Plan 2 may be considered for approval after Britton reviews this acceptance audit. Do not start Plan 2 until explicit approval.
