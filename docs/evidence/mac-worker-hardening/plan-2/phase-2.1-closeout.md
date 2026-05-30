# Phase 2.1 Closeout

Date: 2026-05-28

## Increments completed

- Increment 2.1.1: `docs/evidence/mac-worker-hardening/plan-2/increment-2.1.1-current-baseline.md`
- Increment 2.1.2: `docs/evidence/mac-worker-hardening/plan-2/increment-2.1.2-a-plus-gap-list.md`

Evidence exists for both increments.

## Baseline state confirmed

- Linux repo is on `main...origin/main` at `ac1c6ddf7cf2d71739801a13c46a3f1f3426ea26`.
- Linux working tree already had many modified and untracked files before Plan 2 evidence writes.
- Mac repo is on `main...origin/main` at `ac1c6ddf7cf2d71739801a13c46a3f1f3426ea26`.
- Mac repo still has untracked `scripts/mac-worker/`.
- Local API status endpoint `https://127.0.0.1:3000/api/coding/mac-worker` was not reachable during baseline capture; curl exited with code 7.
- Plan 1 evidence exists and confirms the Plan 1 GO state.

## Exact A+ gaps confirmed

| Gap | Classification |
| --- | --- |
| `scout_research_packet` not proven | proof gap |
| `browser_design_check` not proven | proof gap |
| `scripts/mac-worker/` overlay not formalized | blocker |
| Proxy may not yet call Mac smoothly in realistic active-task flows | proof gap |
| Web/search may not yet have end-to-end proof | proof gap |
| UI may not clearly distinguish proven vs untested Mac job types | polish gap |

## Checks and evidence

- Increment 2.1.1 required commands were run and captured.
- Increment 2.1.2 gap classification was written.
- Evidence files were verified with `ls -la`.

## Forbidden action review

- No implementation files were changed in Phase 2.1.
- No Mac write authority was changed.
- No hidden worker, daemon, launch agent, or persistent process was started.
- No Scout production data, Cartographer data, provider routing, secrets, or protected files were mutated.
- No fixes were applied.

## GO / NO-GO

GO for Phase 2.1 complete.

GO to Phase 2.2.

Next authorized increment: Increment 2.2.1, determine whether `scripts/mac-worker/` should be tracked.
