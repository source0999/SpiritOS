# Plan 3 3x10 Daily-Driver Dry-Run Stage Plan

Critical rule: no stage may execute the next stage in the same Codex run unless Britton explicitly approves that next stage.

## Stage 0 - Preflight and blocker readback

Status: this prompt

Purpose:
- Confirm repo state, staged files, dirty-tree scope, HEAD, Plan 2/3 commit reachability, raw evidence writability, and current Plan 3 blockers.

Human stop after Stage 0:
- Review preflight before trusting Stage 1 context.

## Stage 1 - Write dry-run battery and grading context

Status: this prompt

Purpose:
- Write compact battery, grading schema, runbook, staged plan, human checklist, and validation result files.
- Do not run prompts.
- Do not patch source.

Human stop after Stage 1:
- Review all dry-run context before approving Stage 2.

## Stage 2 - Patch Plan 3 acceptance blockers only

Purpose:
- Policy same-trace downstream consumer evidence.
- Recovery same-trace downstream consumer evidence.
- Repair failure/repair/reverify/consumer same-trace evidence.
- Operator fails when that evidence is missing.

Human stop after Stage 2:
- Review evidence before Stage 3.

## Stage 3 - Select/adapt canonical dry-run harness

Purpose:
- Use existing canonical Source Proxy workflow/task harness paths only.
- Do not create a new dry-run engine.
- Do not create a parallel test orchestration layer.
- Do not add new `source_proxy/tests` files or directories unless Britton explicitly approves after reviewing Stage 0-1.
- If no real harness exists, write NEEDS_FIX and stop for human review.

Special rule:
- Codex must provide evidence that the harness uses real Source Proxy routing/task paths.
- No Set A prompt may run until Britton approves the Stage 3 harness evidence.

Human stop after Stage 3:
- Review harness evidence before Set A.

## Stage 4 - Run Set A only, one prompt at a time

Purpose:
- Broad research/planning/architecture asks.
- Max 3 auto-fix attempts per prompt.
- Stop after Set A summary.

Human stop after Stage 4:
- Review Set A before Set B.

## Stage 5 - Run Set B only, one prompt at a time

Purpose:
- Safe patch/implementation asks.
- Max 3 auto-fix attempts per prompt.
- Stop after Set B summary.

Human stop after Stage 5:
- Review Set B before Set C.

## Stage 6 - Run Set C only, one prompt at a time

Purpose:
- Ambiguity/limits/mixed daily-driver asks.
- Max 3 auto-fix attempts per prompt.
- Stop after Set C summary.

Human stop after Stage 6:
- Review Set C before closeout.

## Stage 7 - Failure buckets and patch map

Purpose:
- Bucket failures.
- Identify root causes.
- List exact next patch targets.
- Do not claim GO unless all prompts pass.

Human stop after Stage 7:
- Review failure map before closeout.

## Stage 8 - Operators and focused tests

Purpose:
- Run Plan 2 operator.
- Run Plan 3 operator.
- Run focused tests.
- Document timeouts without hiding truth failures.

Human stop after Stage 8:
- Review test/operator output.

## Stage 9 - Battery closeout

Purpose:
- 30/30 PASS or honest NEEDS_FIX/BLOCKED.
- No fake GO.

Human stop after Stage 9:
- Approve closeout update.

## Stage 10 - Update Plan 3 closeout

Purpose:
- Only after human review of Stage 9.
- Update status/closeout JSON.

Human stop after Stage 10:
- Approve commit.

## Stage 11 - Commit

Purpose:
- Exact-path staging only.
- Commit Plan 3 continuation docs/implementation.
- No push.

Human stop after Stage 11:
- Review final commit and decide any later push separately.
