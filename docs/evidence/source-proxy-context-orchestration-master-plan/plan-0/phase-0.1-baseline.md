# Plan 0 Phase 0.1: Repo, Branch, and Dirty-Tree Baseline

Status: GO

Execution boundary: Plan 0 only. Read-only repo inspection plus evidence writes under `docs/evidence/source-proxy-context-orchestration-master-plan/plan-0/`. No runtime behavior changes. No coder trials. No staging, commit, push, stash, reset, checkout, clean, apply, or queue work.

## Increment 0.1.1: Repo Root, Branch, HEAD, Dirty Tree

Commands run:

- `git status --short --branch`
- `git rev-parse --show-toplevel`
- `git rev-parse --abbrev-ref HEAD`
- `git rev-parse HEAD`
- `git remote -v`

Observed repo truth:

- Repo root: `//10.0.0.186/SpiritOS`
- Interactive workspace root: `Z:\`
- Branch: `lane/coding-human-trial-runner-polish-20260530-112512`
- Upstream: `origin/lane/coding-human-trial-runner-polish-20260530-112512`
- Ahead of upstream: 19 commits
- HEAD: `081ab565eaae9531289dc3e9651ba7b42094f5d6`
- Remote: `git@github.com:source0999/SpiritOS.git`

Dirty tree summary:

- Modified tracked files: 20
- New untracked paths outside this master-plan directory include `.gate/`, `docs/evidence/agent-runtime-trial-harness/qwen14b-local-coder-upgrade-plan/`, `scripts/gate-*`, `source_proxy/approval/external_gate.py`, `source_proxy/tests/test_external_gate*.py`, and `tests/agent-lab-demo/`.
- New untracked master-plan files are limited to `docs/evidence/source-proxy-context-orchestration-master-plan/`.

Result: PASS. Baseline was captured without mutation beyond evidence writes.

## Increment 0.1.2: Dirty File Classification

Protected existing dirty tracked files:

- `.env.example`
- `config/source-proxy.example.env`
- `package.json`
- `source_proxy/api/chat.py`
- `source_proxy/api/decision.py`
- `source_proxy/cartographer/apply.py`
- `source_proxy/cartographer/autopilot_apply.py`
- `source_proxy/cartographer/clutter_proposals.py`
- `source_proxy/cartographer/level_2_apply.py`
- `source_proxy/planning/architect.py`
- `source_proxy/planning/plan.py`
- `source_proxy/planning/reviewer.py`
- `source_proxy/routing/litellm_router.py`
- `source_proxy/routing/ollama_route.py`
- `source_proxy/tasks/long_running.py`
- `source_proxy/tests/test_coder_agent_repomix_diff.py`
- `source_proxy/tests/test_coding_regression_pack.py`
- `source_proxy/tests/test_ollama_route.py`
- `src/lib/coding/dummy-coder-10-prompts.ts`
- `tests/ui-agent-trials/fixtures/coder-10-dummy-product-site-definition.json`

Classification:

- Relevant to future Source Proxy/coding readiness: yes, but protected from this Plan 0 docs-only execution unless explicitly inspected read-only.
- Runtime behavior files: protected; not edited.
- Tests/fixtures: protected; not edited.
- Local config/examples: protected; not edited.
- Existing untracked gate and trial paths: protected; not edited.
- This plan's evidence path: allowed docs-only write surface.

Result: PASS. Existing work is classified as protected and out of write scope for Plan 0.

## Increment 0.1.3: Safe Verification Surface

Safe during Plan 0:

- `git status --short --branch`
- `git rev-parse ...`
- `git diff --stat`
- `rg --files`
- `rg -n` read-only inventory searches
- `git diff --check -- docs/evidence/source-proxy-context-orchestration-master-plan`
- evidence docs under this plan directory

Unsafe during Plan 0 without separate approval:

- starting or restarting Source Proxy
- invoking model/provider routes
- running `/coding` coder trials
- Coder 50 or Coder 100
- Source Proxy apply or `execute-approved`
- background workers or queue continuation
- hidden Scout memory writes
- git mutation

Result: PASS. Safe verification surface is defined.

## Phase 0.1 Closeout

Checks passed:

- Repo identity captured.
- Branch and HEAD captured.
- Dirty tree classified.
- Existing dirty runtime work protected.
- Evidence-only write boundary preserved.

GO/NO-GO: GO to Phase 0.2 route inventory.

Next permitted phase: Phase 0.2 only.
