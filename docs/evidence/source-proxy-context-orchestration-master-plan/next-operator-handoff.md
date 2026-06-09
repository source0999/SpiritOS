# Next Operator Handoff: Source Proxy Context-Orchestrated Coding Readiness

Status: handoff for review only. Do not execute Plan 0 until Britton approves.

## Operator Boundary

You are in the SpiritOS repo. The current task created the master plan of plans under `docs/evidence/source-proxy-context-orchestration-master-plan/`.

Do not change runtime behavior. Do not run coder trials. Do not start Coder 50 or Coder 100. Do not execute Plan 0 unless Britton explicitly approves.

## Current Decision

Default coder route for the planned workflow is `qwen2.5-coder:7b`.

The 14B route remains comparison-only until it passes the same strict output-contract tests.

## Required First Question To Britton

Britton, do you approve executing Plan 0: Baseline, Model Route, and Workflow Law?

## If Britton Approves Plan 0

Start only Plan 0. Execute one increment at a time:

1. complete the increment
2. run safe read-only or docs-related checks for that increment
3. write evidence for that increment
4. decide GO/NO-GO
5. continue to the next increment only if GO

At Plan 0 closeout, stop and ask Britton before Plan 1.

## If Britton Does Not Approve

Do not execute. Capture the requested edits to the master plan, update only the docs in this evidence directory, run docs-only validation, and return for review.

## Absolute No-Start List

- Coder 50
- Coder 100
- complex multi-file feature tasks
- autonomous Cartographer queue work
- background workers
- 14B default switch
- hidden Scout memory writes
- hidden apply/commit/push
