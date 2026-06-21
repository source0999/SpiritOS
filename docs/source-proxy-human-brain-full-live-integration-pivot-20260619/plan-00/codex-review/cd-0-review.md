# CD-0 Review

CD-0 proposal reviewed from:

- `plan-00/artifacts/0.7-compression-decision.md`
- `plan-00/artifacts/0.5-mvi-contract-and-feasibility.md`
- `plan-00/artifacts/0.3-reuse-adapt-retire-matrix.md`

## Findings

1. Does CD-0 solve the exact causal proof gap?
   - Yes. It targets the missing `trace_id`, `invocation_event_id`, `consumer_event_id`, and `consumer_subsystem` fields on the existing long-running apply path, which is exactly the verified gap.

2. Does CD-0 avoid merging advisory routing into apply?
   - Yes. It explicitly says not to merge `/v1/decisions/route` into the apply path and preserves the advice/apply boundary.

3. Does CD-0 avoid a new state engine/framework?
   - Yes, with a condition. It says not to add a new event/state engine and to reuse a Cartographer ledger primitive if a ledger is needed.

4. Does CD-0 avoid authority expansion?
   - Yes. It keeps autonomous commit/push disabled and leaves operator approval in place.

5. Does CD-0 preserve the active route?
   - Yes. It keeps `/coding -> CodingCockpitShell -> v1 route -> Source Proxy handler` intact.

6. Does CD-0 avoid Obsidian/Mac writes?
   - Yes. It explicitly excludes Obsidian and Mac writes.

7. Is `CodingCockpitShell` as consumer-of-record reasonable?
   - Reasonable, but not my preferred proof anchor by itself. `CodingCockpitShell` is the active human-facing consumer and should display/acknowledge the event. For durable proof, Plan 1 should make the backend verifier/long-running status observer or a reused Cartographer ledger primitive the authoritative recorder, with `CodingCockpitShell` as the visible consumer. A browser-only consumer event would be easier to fake or miss in unattended verification.

8. Is CD-0 sufficient for Plan 1's first step?
   - Yes with notes. Plan 1 should tighten consumer-of-record wording before implementation: one authoritative backend event record, one visible shell observation, same `trace_id`, no new ledger engine.

## Recommendation

CD-0_RECOMMENDATION:
APPROVE_WITH_NOTES

Notes:

- Approve CD-0 as the minimal safe next architectural decision.
- Before Plan 1 implementation, specify the consumer-of-record as durable backend/ledger proof plus shell visibility, rather than relying solely on frontend observation.
- Do not add a parallel event store; reuse the long-running task store or Cartographer event ledger primitive.
