# Integrated Level 6 Stop Boundaries

Date: 2026-06-15

Status: PLANNED_NOT_STARTED

No Level 6 implementation or matrix run was started.

## Current Stop Line

Stop after this Level 6 plan.

Do not implement Level 6 until Britton explicitly approves implementation.

Do not run the Level 6 matrix from this planning checkpoint.

## Hard Boundaries

Do not:

- edit runtime code during planning;
- mutate runtime files during planning;
- stage, commit, push, reset, clean, checkout, or revert;
- start TinyFish;
- create xersearch;
- promote Cartographer to routing owner;
- add model lanes;
- expand product features;
- run destructive prompts;
- run Level 6 matrix prompts before approval;
- create new runners before approval;
- modify model routing ownership;
- change Cartographer from advisory to owner;
- touch unrelated SpiritFlix/media work;
- delete stale duplicate FIP artifacts without explicit approval;
- claim final GO if lane truth, receipt truth, trace truth, or safety truth is degraded.

## Implementation Approval Prompt

Britton can approve the next step with this exact prompt:

```text
BRITTON GO SOURCE PROXY INTEGRATED LEVEL 6 IMPLEMENTATION ONLY

Purpose:
Implement the bounded Integrated Level 6 stress/soak runner and evidence reporting exactly from:
docs/evidence/source-proxy-integrated-level-6-stress-soak-plan-20260615/

Level 6 is a durability, stress, scoring, and evidence-hardening gate over the existing accepted Source Proxy stack. It is not a feature expansion.

Start by confirming:
1. git status is clean
2. latest commit hash
3. one Source Proxy uvicorn process for source_proxy.main:app on :8787
4. latest receipt endpoint returns HTTP 200
5. latest trace endpoint returns HTTP 200
6. latest trace matches latest receipt
7. local model availability truth is recordable
8. Scout/SearXNG availability truth is recordable
9. npm typecheck command
10. focused pytest command
11. git diff --check

If git status is not clean at start, stop with NEEDS_REVIEW and list exact dirty files.

Allowed implementation:
- create a Level 6 runner only if needed
- create Level 6 matrix JSON
- create Level 6 result JSON/raw/console evidence
- create a human-readable closeout
- add focused tests only for Level 6 scoring/evidence contract if implementation changes require them

Do not:
- add TinyFish
- create xersearch
- promote Cartographer to route owner
- add new model lanes
- expand product features
- tune benchmark-specific prompts
- weaken safety blocks
- hide degraded lane truth behind final GO
- allow hidden fallback
- allow hidden apply outside the approved target root
- stage, commit, push, reset, clean, checkout, or revert
- touch unrelated SpiritFlix/media work

Run the bounded 30-prompt Level 6 matrix only after preflight passes.

Required evidence:
- FIP-0 durable receipt for every posted row
- FIP-6 operator trace for every posted row
- matrix JSON
- results JSON
- raw response JSON
- console log
- human-readable closeout
- latest receipt endpoint check
- latest trace endpoint check
- trace matches receipt check
- no private reasoning leaked in trace
- no stale duplicate artifact accepted as latest truth
- mutation scope check
- typecheck result
- focused pytest result
- git diff --check result

Return:
- GO / NEEDS_REVIEW / NO-GO for Integrated Level 6
- exact counts for productive_go, expected_safety_block, expected_degraded_lane, lane_truth_warning, config_blocked, verifier_blocked, unexpected_no_go, trace_mismatch, receipt_missing, unauthorized_mutation
- latest run id and verdict
- files written
- tests run
- explicit stop line after Level 6
```

## Required Final Statement For This Planning Task

Any closeout for this planning checkpoint must state:

`No Level 6 implementation or matrix run was started.`
