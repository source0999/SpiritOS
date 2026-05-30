# Increment 2.1.2 A+ Gap List

Date: 2026-05-28

## Scope

Allowed work for this increment was limited to creating a short A+ gap list from current evidence.

No implementation files were modified.

## Gap list

| Gap | Classification | Evidence | A+ requirement |
| --- | --- | --- | --- |
| `scout_research_packet` not proven | proof gap | Plan 1 closeout lists it as not tested. | Must be inspected, run through `/api/coding/mac-worker`, hardened if needed, and marked proven only if structured advisory data is returned. |
| `browser_design_check` not proven | proof gap | Plan 1 closeout lists it as not tested. | Must be inspected, run against a safe target, and marked proven only with honest screenshot/artifact evidence or clear dependency limitation. |
| `scripts/mac-worker/` overlay not formalized | blocker | Plan 1 closeout and Increment 2.1.1 Mac status both show `?? scripts/mac-worker/` on Mac; Linux also has untracked `scripts/mac-worker/`. | Must become tracked repo content or an explicitly documented approved overlay before A+ production-preflight. |
| Proxy may not yet call Mac smoothly in realistic active-task flows | proof gap | Plan 1 proved raw API/UI status truth, but did not prove a realistic active-task/proxy flow using Mac advisory support. | Must show Mac advisory/check support visible in a real task flow without granting autonomous write authority. |
| Web/search may not yet have end-to-end proof | proof gap | Plan 1 did not test `scout_research_packet`; no end-to-end web search packet evidence exists. | Must identify local-first provider boundary and prove web packet if provider is reachable; otherwise grade local-only honestly. |
| UI may not clearly distinguish proven vs untested Mac job types | polish gap | Plan 1 UI work exposed status truth, but the acceptance state for untested job types has not been reviewed in Plan 2. | UI should avoid presenting unproven jobs as production-ready and should surface success/failure/advisory-only state clearly. |

## Future lane items

These are not blockers for Plan 2 unless discovered to be required while proving the listed gaps:

- Expanding Mac into autonomous execution.
- Adding paid search providers.
- Persistent browser/session automation.
- Scout production packet ingestion or promotion.
- Provider routing changes.

Those items remain out of scope for the current advisory/check support lane.

## Safety confirmation

- No Mac write authority was changed.
- No hidden worker, daemon, launch agent, or persistent process was started.
- No Scout production storage was mutated.
- No Cartographer, provider routing, secrets, protected files, or design files were changed.
- No fixes were applied in this increment.

## GO / NO-GO

GO for Increment 2.1.2 complete.

Next authorized increment: Phase 2.1 closeout.
