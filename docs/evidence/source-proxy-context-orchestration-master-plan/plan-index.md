# Source Proxy Context-Orchestration Master Plan Index

Status: master plan index only. Do not execute Plan 0 until Britton approves.

## Files

- `master-plan.md`: full Plan 0 through Plan 5 plan of plans.
- `acceptance-contract.md`: readiness definitions, packet requirements, output-contract gates, and evidence rules.
- `model-route-decision-7b-default.md`: 7B default decision with 14B comparison boundary.
- `no-preview-only-integration-policy.md`: policy against route-exists, preview-only, docs-only, and Repomix-only claims.
- `next-operator-handoff.md`: exact handoff for Britton and the next operator.

## Plan Sequence

| Plan | Title | Outcome | Stop Gate |
| --- | --- | --- | --- |
| 0 | Baseline, Model Route, and Workflow Law | Freeze repo truth, route truth, model default, definitions, and pivot workflow law. | Stop and ask Britton before Plan 1. |
| 1 | Output Contract, Parser, and Repair Discipline | Make malformed output rejection and one-pass repair reliable before adding context. | Stop and ask Britton before Plan 2. |
| 2 | Context Source Readiness | Polish Cartographer, Obsidian, Scout/Mac/Search, and Design into packet-producing or blocked/skipped sources. | Stop and ask Britton before Plan 3. |
| 3 | Helper/Subagent Readiness | Define visible advisory helper packets and no-hidden-mutation boundaries. | Stop and ask Britton before Plan 4. |
| 4 | Source Proxy Context Orchestration | Wire polished packet sources into the real `/coding` hot path and durable receipts. | Stop and ask Britton before Plan 5. |
| 5 | A+ Basic Coding Gauntlet | Prove three basic messy prompts through the full chain with 7B default before complex work. | Stop and ask Britton before any larger task lane. |

## Global Stop Rule

Codex must complete one increment, test it, write evidence, and continue only if GO. Each phase closes before the next phase. Each plan closes before the next plan. After every plan closeout, Codex stops and asks Britton for approval.

## Do Not Start Yet

- Coder 50
- Coder 100
- complex multi-file feature tasks
- autonomous Cartographer queue work
- background workers
- 14B default switch
- hidden Scout memory writes
- hidden apply/commit/push
