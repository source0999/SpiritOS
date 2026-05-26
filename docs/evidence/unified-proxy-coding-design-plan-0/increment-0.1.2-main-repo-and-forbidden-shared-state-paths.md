# Increment 0.1.2: Record Main Repo Path And Forbidden Shared-State Paths

PLAN: Plan 0, Isolated Proxy Lane Baseline

PHASE: Phase 0.1, Lane Identity And Boundary Packet

INCREMENT: Increment 0.1.2, Record Main Repo Path And Forbidden Shared-State Paths

Lane name: unified-proxy-coding-design-plan-0

Evidence root: /home/source/SpiritOS/docs/evidence/unified-proxy-coding-design-plan-0/

Main repo path: /home/source/SpiritOS

Forbidden shared-state paths and systems:
- Cartographer runtime state
- Cartographer soak logs
- Cartographer live evidence
- Scout soak logs
- Production map state
- Production Source Proxy state
- Main repo execution path
- Background workers and queues
- Provider/model calls
- Apply or execute-approved routes
- Git mutation surfaces, including branch, worktree, stash, reset, clean, checkout, stage, commit, and push

Boundary declaration:
- All remaining Plan 0 work must remain inside the isolated proxy lane evidence root unless the increment is read-only inspection.
- No production source, runtime state, map state, Source Proxy runtime state, Cartographer state, Scout soak logs, or Cartographer evidence/logs may be modified.
- Cartographer soak dependency status: SAFE WHILE SOAK RUNS.

Required inspections performed:
- Confirmed current working directory: /home/source
- Confirmed expected main repo path exists: /home/source/SpiritOS
- Confirmed the authorized evidence root exists under docs/evidence.
- Did not create, edit, or write any runtime, soak, live evidence, production Source Proxy, production map, queue, provider, or git metadata path.

Manual validation:
- Main repo boundary is explicit.
- Evidence root is isolated under docs/evidence and is not runtime state.
- Forbidden shared-state categories are explicit.
- No production file, runtime file, soak log, or live evidence file was edited.

GO / NO-GO:
GO for Increment 0.1.2.

Next authorized increment only:
Plan 0, Phase 0.2, Increment 0.2.1: Capture Read-Only Git Status Snapshot Without Cleanup.
