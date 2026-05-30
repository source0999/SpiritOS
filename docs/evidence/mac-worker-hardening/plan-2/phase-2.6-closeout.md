# Phase 2.6 Closeout

Date: 2026-05-28

## Increments completed

- Increment 2.6.1: `docs/evidence/mac-worker-hardening/plan-2/increment-2.6.1-proxy-flow-map.md`
- Increment 2.6.2: `docs/evidence/mac-worker-hardening/plan-2/increment-2.6.2-explicit-mac-advisory-opt-in.md`
- Increment 2.6.3: `docs/evidence/mac-worker-hardening/plan-2/increment-2.6.3-realistic-proxy-mac-flow-proof.md`

Evidence exists for all increments.

## Proxy smoothness grade

B

Rationale:

- Raw API proof exists for `source_proxy_context_discovery`.
- Agent-trial harness code has a natural Mac `trial_context_assist` integration path.
- An explicit advisory opt-in bridge was added to `CodingCommandCenterShell` and is covered by a component test.
- The active routed `/coding` page currently renders `CodingCockpitShell`, not `CodingCommandCenterShell`.
- The realistic harness run did not reach Mac because app navigation failed with `ERR_CONNECTION_REFUSED`.
- Active `/coding` UI smoothness is therefore not A+ proven.

## Checks and proof

Checks run in this phase:

- Harness help command: passed.
- Harness run `--agent coding --viewport desktop --limit 10 --profile britton-realistic`: completed with `go:false`; Mac not used due app navigation failure.
- Raw API `source_proxy_context_discovery`: passed and returned 5 candidate files.
- Focused component test for explicit Mac advisory opt-in: passed.
- Mac worker contract/API tests: passed.
- `npx --no-install tsc --noEmit --pretty false`: passed.
- `git diff --check`: passed.

Known test note:

- First broad component suite run failed because the new test assertion matched duplicate file text outside the Mac panel. The assertion was narrowed and the focused test passed. Full component suite remains scheduled for Increment 2.7.2.

## Forbidden action review

- No hidden automation was added.
- No default Mac routing was added.
- No autonomous Mac execution was added.
- No Mac write authority was granted.
- No apply, commit, push, provider change, Cartographer activation, or Scout production mutation occurred.
- The Mac remains advisory/check support only.

## Phase result

GO for Phase 2.6 complete as partial/B proxy smoothness proof.

NO-GO for A+ proxy smoothness until the explicit opt-in bridge is present in the active routed `/coding` shell or the harness proves Mac use end-to-end.

## GO / NO-GO

GO to Phase 2.7 for acceptance matrix and final verification.

Next authorized increment: Increment 2.7.1, update Mac worker acceptance matrix.
