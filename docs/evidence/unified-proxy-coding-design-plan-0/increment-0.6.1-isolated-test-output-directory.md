# Increment 0.6.1: Define Isolated Test Output Directory

PLAN: Plan 0, Isolated Proxy Lane Baseline

PHASE: Phase 0.6, Test Sandbox And Evidence Directory Definition

INCREMENT: Increment 0.6.1, Define Isolated Test Output Directory

Objective:
Define an isolated test output directory for future proxy/design/coding work without creating or using it in Plan 0.

Isolated proxy lane scope:
unified-proxy-coding-design-plan-0

Allowed files or file zones:
- Evidence files inside /home/source/SpiritOS/docs/evidence/unified-proxy-coding-design-plan-0/
- Read-only inspection only when needed.

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
- Defined a future isolated test output directory as a boundary only.
- Did not create the test output directory.
- Did not run tests.

Required tests or inspections:
- Manual inspection of path boundary.
- Confirmed the proposed path is inside the isolated evidence root and does not overlap runtime/shared state.

Defined isolated test output directory:
/home/source/SpiritOS/docs/evidence/unified-proxy-coding-design-plan-0/test-output/

Plan 0 status of test output directory:
- Defined only.
- Not created.
- Not used.
- No tests run.

Future use constraints:
- Only isolated proxy-lane verification may write there.
- No Cartographer soak, Scout soak, production Source Proxy, production map, runtime queue, provider/model, or git mutation output may be written there.
- Tests that mutate shared soak state remain forbidden.

Required manual validation:
- The proposed test output directory is under the isolated evidence root.
- It does not overlap Cartographer, Scout, Source Proxy runtime state, map state, or git metadata.
- No test output directory was created in this increment.

Required evidence artifact:
This file.

Stop conditions:
- Any need to create output outside the evidence root.
- Any test would mutate shared state.
- Any output path overlaps forbidden runtime or soak state.

Rollback or recovery note:
No rollback action is authorized. Since no test output directory was created, recovery is to stop and report NEEDS OPERATOR REVIEW if the boundary is rejected.

GO / NO-GO exit rule:
GO only if the isolated test output directory is defined inside the evidence root and no tests or directory creation occurred.

GO / NO-GO:
GO for Increment 0.6.1.

Next authorized increment only:
Plan 0, Phase 0.6, Increment 0.6.2: Define Evidence Packet Naming Convention.

Cartographer soak dependency status:
SAFE WHILE SOAK RUNS.
