# Plan 0 Closeout: Baseline, Model Route, and Workflow Law

Status: GO

Stop gate: Do not start Plan 1 until Britton explicitly approves.

## Scope Completed

Plan 0 executed only:

- Phase 0.1: repo, branch, and dirty-tree baseline
- Phase 0.2: Source Proxy and `/coding` route inventory
- Phase 0.3: current model/provider route truth and 7B default correction
- Phase 0.4: workflow definitions and pivot law

Plan 0 did not execute:

- Plan 1 parser work
- coder trials
- Coder 50
- Coder 100
- complex feature tasks
- autonomous Cartographer queue work
- background workers
- hidden Scout memory writes
- hidden apply/commit/push

## Evidence Files

- `phase-0.1-baseline.md`
- `phase-0.2-route-inventory.md`
- `phase-0.3-model-truth.md`
- `phase-0.4-workflow-law.md`
- `plan-0-closeout.md`

## Key Findings

Baseline:

- Repo root is `//10.0.0.186/SpiritOS`.
- Interactive workspace is `Z:\`.
- Branch is `lane/coding-human-trial-runner-polish-20260530-112512`.
- HEAD is `081ab565eaae9531289dc3e9651ba7b42094f5d6`.
- Branch is ahead of origin by 19 commits.
- Existing dirty Source Proxy/coding work was present before Plan 0 and is protected from unrelated cleanup or revert.

Route inventory:

- Source Proxy backend routers are registered in `source_proxy/main.py`.
- `/coding` renders `CodingCockpitShell`.
- Preview/advisory surfaces exist for bounded diff preview, Cartographer preview, Design vault preview, helper-agents preview, research preview, Mac advisory, action preview, and gauntlet preview.
- Route existence is not accepted integration.
- Repomix is allowed only as fallback/source, not as the main context brain.

Model route:

- Plan 0 found the coder lane still defaulted to `qwen2.5-coder:14b` in examples, local env, and route resolver order.
- Plan 0 corrected the coder default to `qwen2.5-coder:7b`.
- 14B remains comparison/fallback only.
- 14B cannot become default until it passes the same output-contract tests and Britton approves.

Workflow law:

- Preview, advisory, integrated, and production-ready are defined.
- Every increment must be checked and evidenced before the next increment.
- Every phase closes before the next phase.
- Every plan closes before the next plan.
- Codex stops and asks Britton before starting the next plan.

## Files Changed During Plan 0

Evidence files:

- `docs/evidence/source-proxy-context-orchestration-master-plan/plan-0/phase-0.1-baseline.md`
- `docs/evidence/source-proxy-context-orchestration-master-plan/plan-0/phase-0.2-route-inventory.md`
- `docs/evidence/source-proxy-context-orchestration-master-plan/plan-0/phase-0.3-model-truth.md`
- `docs/evidence/source-proxy-context-orchestration-master-plan/plan-0/phase-0.4-workflow-law.md`
- `docs/evidence/source-proxy-context-orchestration-master-plan/plan-0/plan-0-closeout.md`

Route-truth correction files:

- `.env.example`
- `config/source-proxy.example.env`
- `.env.local`
- `source_proxy/routing/ollama_route.py`
- `source_proxy/tests/test_ollama_route.py`

## Checks Run

- `git status --short --branch`
- `git rev-parse --show-toplevel`
- `git rev-parse --abbrev-ref HEAD`
- `git rev-parse HEAD`
- `git remote -v`
- `git diff --stat`
- route inventory through `rg --files` and `rg -n`
- model truth inventory through `rg -n` and targeted file reads
- `.\\.venv-source-proxy-windows\\Scripts\\python.exe -m pytest source_proxy\\tests\\test_ollama_route.py`
- `git diff --check -- .env.example config/source-proxy.example.env source_proxy/routing/ollama_route.py source_proxy/tests/test_ollama_route.py docs/evidence/source-proxy-context-orchestration-master-plan`

Check results:

- Focused route tests: 14 passed.
- Diff hygiene: passed, with line-ending warnings only for existing Windows working-copy behavior.
- Required Plan 0 evidence files: present.

## GO/NO-GO

Plan 0 GO.

Plan 1 NO-GO until Britton approves starting it.

## Required Britton Gate

Britton, Plan 0 is closed with GO evidence. Do you approve starting Plan 1: Output Contract, Parser, and Repair Discipline?
