# Increment 0.5.1: Produce Allowed Path Matrix For Proxy/Design/Coding Work

PLAN: Plan 0, Isolated Proxy Lane Baseline

PHASE: Phase 0.5, Allowed/Forbidden Path Matrix

INCREMENT: Increment 0.5.1, Produce Allowed Path Matrix For Proxy/Design/Coding Work

Objective:
Define the allowed path matrix for current baseline/evidence work and future proxy/design/coding planning boundaries.

Isolated proxy lane scope:
unified-proxy-coding-design-plan-0

Allowed files or file zones:
- Current Plan 0 writable zone: /home/source/SpiritOS/docs/evidence/unified-proxy-coding-design-plan-0/
- Read-only repository inspection.

Forbidden files, paths, systems, and actions:
- Production source files.
- Source Proxy runtime files.
- Cartographer runtime files.
- Cartographer soak logs.
- Scout soak logs.
- Cartographer live evidence.
- Map state.
- Git mutations, including branch, worktree, stash, reset, clean, checkout, stage, commit, and push.
- Provider/model calls.
- Apply or execute-approved routes.
- Background worker or queue mutation.

Exact work performed:
- Inspected top-level repository directories read-only.
- Inspected Source Proxy directory structure read-only.
- Produced an allowed path matrix.

Required tests or inspections:
```text
$ find /home/source/SpiritOS -maxdepth 2 -type d | sort | sed -n '1,120p'
<read-only top-level directory inventory captured>

$ find /home/source/SpiritOS/source_proxy -maxdepth 2 -type d | sort | sed -n '1,120p'
<read-only Source Proxy directory inventory captured>
```

Allowed path matrix:

| Zone | Current Plan 0 write status | Current Plan 0 read status | Future use note |
| --- | --- | --- | --- |
| /home/source/SpiritOS/docs/evidence/unified-proxy-coding-design-plan-0/ | Allowed | Allowed | Only authorized evidence root for Plan 0. |
| /home/source/SpiritOS/docs/evidence/ | Restricted | Allowed | Parent evidence area; do not write outside the lane root. |
| /home/source/SpiritOS/docs/ | Forbidden except lane evidence root | Allowed | Documentation may be candidate-only for later plans with explicit authorization. |
| /home/source/SpiritOS/source_proxy/ | Forbidden | Allowed | Candidate proxy planning surface only; no runtime or production mutation in Plan 0. |
| /home/source/SpiritOS/source_proxy/tests/ | Forbidden | Allowed | Candidate isolated tests only in later plans; do not run soak-mutating tests. |
| /home/source/SpiritOS/src/ | Forbidden | Allowed | Candidate UI/design planning surface only; no production component/routes edits in Plan 0. |
| /home/source/SpiritOS/chatDesign/ | Forbidden | Allowed | Candidate design reference surface only; no edits in Plan 0. |
| /home/source/SpiritOS/_blueprints/ | Forbidden | Allowed | Candidate planning/reference surface only; no edits in Plan 0. |
| /home/source/SpiritOS/data/ | Forbidden | Allowed with caution | Treat runtime/shared state as forbidden unless a future plan explicitly authorizes isolated test output. |

Required manual validation:
- Only the isolated evidence root is writable in Plan 0.
- Candidate future paths are not self-authorized by this matrix.
- Runtime, soak, map, and production state remain forbidden.

Required evidence artifact:
This file.

Stop conditions:
- Any need to write outside the evidence root.
- Any path overlaps Cartographer soak state or production runtime state.
- Any ambiguity about future candidate path authorization.

Rollback or recovery note:
No rollback action is authorized. If a future path is unclear, stop and report NEEDS OPERATOR REVIEW before writing.

GO / NO-GO exit rule:
GO only if current writable scope remains limited to the evidence root and candidate paths are explicitly not authorized for Plan 0 mutation.

GO / NO-GO:
GO for Increment 0.5.1.

Next authorized increment only:
Plan 0, Phase 0.5, Increment 0.5.2: Produce Forbidden Path Matrix For Cartographer Soak And Shared State.

Cartographer soak dependency status:
SAFE WHILE SOAK RUNS.
