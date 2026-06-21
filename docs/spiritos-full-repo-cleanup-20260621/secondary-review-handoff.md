# Secondary Review Handoff (DRAFT — populated at F10 completion)

> **STATUS: NOT YET POPULATED.** This file is a required packet placeholder. It
> is filled in completely when the cleanup reaches `READY_FOR_SECONDARY_REVIEW`
> (final step of F10). Until then it records only that the handoff is pending.
> Do not treat the cleanup as complete if this file still says DRAFT.

## Pending content (to be filled at F10)
- cleanup branch and HEAD
- breakpoint HEAD
- planning commit
- every stage commit (F01–F10)
- frozen acceptance-contract hashes (per stage)
- frozen holdout-manifest hashes (per stage)
- stage verdicts (all must be `INTERNAL_GO_PENDING_SECONDARY_REVIEW`)
- changed files by subsystem
- compatibility evidence (the 12 preserved contracts)
- commands and exit codes (terminal battery)
- raw evidence root
- caveats by severity (minor only; major ⇒ not ready)
- protected paths proof (no protected path edited)
- rollback commands (per stage)
- remaining legacy code (what was intentionally not retired)
- exact Codex review request
- exact old-plan resume point (→ `resume-old-plan-handoff.md`)

## Current packet state
- `planning_packet`: GO (after P2 commit)
- `implementation_started`: false until F1 begins
- `current_stage`: see `cleanup-state.json`
- `ready_for_secondary_review`: false until F10 completes this handoff
