# Plan 3 — Contaminated Agent Lab Proof Revert

**Date:** 2026-06-09  
**Actor:** Cursor revert task (Britton restart prep)  
**Scope:** Remove deterministic-correction proof layer only.

## What was removed

### Scripts (4)

- `scripts/agent-trials/run-plan3-visual-review.py`
- `scripts/agent-trials/run-plan3-real-visual-preview.py`
- `scripts/agent-trials/run-plan3-one-prompt-agent-lab.py`
- `scripts/agent-trials/run-plan3-agent-lab-calculation-followup.py`

These harnesses included deterministic correction helpers (`apply_prompt_1_correction`, `apply_prompt_2_correction`, `calculator_page`, `harness_corrected_preview`) that made previews look successful when raw Qwen output failed or was partial.

### Evidence dirs/files (6)

- `docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/visual-review/` (entire tree)
- `docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/visual-review-closeout.md`
- `docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/visual-preview/` (entire tree)
- `docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/real-visual-preview-closeout.md`
- `docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/one-prompt-agent-lab-preview/` (entire tree)
- `docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/agent-lab-calculation-followup/` (entire tree)

## What was preserved

### Core Source Proxy (not touched by this revert)

No `source_proxy/` files were modified or deleted during this revert. Pre-existing working-tree modifications remain as they were before this task.

### Plan 0 / 1 / 2 / core Plan 3 (not touched)

- Plan 0, Plan 1, Plan 2 evidence trees under `docs/evidence/source-proxy-context-orchestration-master-plan/` — unchanged.
- Core Plan 3 helper/subagent readiness artifacts retained:
  - `plan-3-helper-subagent-readiness-closeout.md`
  - `plan-3-helper-subagent-readiness-messy-round-results.json`
  - `plan-3-messy-stabilization-smoke.json`
  - `plan-3-messy-stabilization-results.json`
  - `plan-3-cleanup-stabilization-closeout.md`
- `scripts/agent-trials/run-plan3-messy-e2e.py` — retained (not part of contaminated proof layer).

## Confirmations

| Check | Result |
|-------|--------|
| Core Source Proxy files touched by revert | **No** |
| Plan 4 started | **No** |
| `git reset --hard` | **Not used** |
| `git clean` | **Not used** |
| `git stash` | **Not used** |
| `git commit` | **Not used** |
| `git push` | **Not used** |
| New raw Qwen test run | **Not started** |

## Post-revert verification

```text
$ git status --short --untracked-files=normal -- scripts/agent-trials docs/evidence/.../plan-3
?? docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/
?? scripts/agent-trials/run-plan3-messy-e2e.py

$ git diff --check -- scripts/agent-trials docs/evidence/.../plan-3
(clean — no whitespace errors)

$ node scripts/gate-status
status: RUNNING_INCREMENT
approved_increment: evaluation-round
last_completed_increment: 2.4
```

## Current git status summary (full tree)

**Modified (tracked, pre-existing — not changed by this revert):** 21 files across `.env.example`, `config/`, `package.json`, `source_proxy/`, `src/lib/coding/`, and `tests/ui-agent-trials/fixtures/`.

**Untracked (pre-existing unless noted):**

- `.codex-spiritflix-stable-3001.pid`, `.gate/`
- `docs/evidence/agent-runtime-trial-harness/qwen14b-local-coder-upgrade-plan/`
- `docs/evidence/source-proxy-context-orchestration-master-plan/` (includes cleaned Plan 3 evidence + this closeout)
- `scripts/agent-trials/run-plan3-messy-e2e.py`
- `scripts/gate-*` (approve, block, complete, lib, start, status)
- `source_proxy/approval/external_gate.py`, `source_proxy/context/source_readiness.py`, related tests
- `tests/agent-lab-demo/`

**Removed by this revert:** 4 contaminated scripts + 4 evidence directories + 2 closeout markdown files (all were untracked generated proof artifacts).

## Safest next steps (not executed)

Britton can restart Plan 3 Agent Lab preview work with a **raw Qwen-only** harness (no deterministic correction functions). When ready to commit, prefer splitting:

1. Core Source Proxy / gate / readiness changes (separate PR)
2. Plan 3 messy E2E + helper readiness evidence (separate PR)
3. New raw Agent Lab preview proof (after clean harness exists)

Do not commit the contaminated paths above — they are gone. Review remaining dirty tree before any commit.
