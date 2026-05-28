# Source Proxy Agent Integration Preflight Plan 1/12 Closeout v0.1

Status: Plan 1/12 complete.

Date: 2026-05-27.

Scope: inspection-only executable baseline and Plan 2 scope lock. No source, runtime, CSS, test, config, env, package, Scout, backend, or Cartographer runtime/evidence/receipt files were edited.

## Phase 1.1: Repo And Service Baseline

Result: GO.

- Dirty tree is docs-only and matches Plan 0 roadmap/index/old-chain classification artifacts plus this Plan 1 closeout.
- Source Proxy has `POST /v1/coding/bounded-diff-preview` in `source_proxy/api/codex_adapter.py`.
- Next App Router has `/v1/coding/bounded-diff-preview` proxy in `src/app/v1/coding/bounded-diff-preview/route.ts`.
- `/coding` renders `CodingCommandCenterShell` from `src/app/coding/page.tsx`.
- `CodingCockpitShell` still exists and includes approval/apply UI logic, but it is not the current `/coding` page entry.

## Phase 1.2: Agent Surface Baseline

Result: GO.

- Design Vault exists at `data/design-vault/` and is manual-first, no runtime integration, and no app UI write authority.
- Scout exists as a local read-only intelligence service under `scout/`; proxy intake exists at `source_proxy/api/scout_intake.py` and requires signature plus explicit promotion approval.
- Mac Mini state is documented as Scout migration/support context, not an active Plan 2 runtime dependency.
- Cartographer has many Source Proxy and Next route surfaces, including read-only/status endpoints and control-preview or apply-like endpoints. Plan 2 must not activate or consume Cartographer authority.

## Phase 1.3: Build Priority Map

Result: GO.

Real implementation blockers:

1. The active roadmap still names Plan 2 as the productive bounded-diff preview build, but the repo already contains a narrow CG-001 through CG-005 implementation and tests from prior work. Plan 2 should verify and repair this exact slice before expanding.
2. The current productive preview is hard-coded to one prompt family, one task-id range, and one target file: `src/lib/coding/workflow-progress-copy.ts`.
3. If that target already contains the replacement phrase, the route intentionally returns `backend_diff_generation_gap` instead of faking a no-op.
4. `/coding` has a command-center shell with extensive diagnostic/packet behavior. Plan 2 UI work must stay limited to bounded preview consumption and honest state display.
5. Design, Scout/Mac, and Cartographer surfaces are real but out of Plan 2's first implementation scope.

Exact allowed first source/test files for Plan 2:

- `source_proxy/api/codex_adapter.py`
- `source_proxy/tests/test_codex_cli_adapter.py`
- `src/app/v1/coding/bounded-diff-preview/route.ts`
- `src/app/v1/coding/bounded-diff-preview/__tests__/route.test.ts`
- `src/components/coding/CodingCommandCenterShell.tsx`
- `src/components/coding/__tests__/coding-command-center-shell.test.tsx`
- `src/lib/coding/workflow-progress-copy.ts`
- `src/lib/coding/proxy-trial-prompts.ts`

Plan 2 should not touch Design Vault, Scout, Mac Mini docs, Cartographer runtime/evidence/receipt files, CSS, package/config/env files, or broader `/coding` route/component files unless Britton explicitly expands scope.

## Final Executable Baseline Check

Result: GO.

```bash
cd /home/source/SpiritOS
git status --branch --short --untracked-files=normal
test -f docs/source-proxy-agent-integration-preflight-build-roadmap-v0.1.md
test -f docs/source-proxy-agent-integration-preflight-plan-0-closeout-v0.1.md
test -f docs/source-proxy-agent-integration-preflight-plan-1-closeout-v0.1.md
grep -n "Plan 1: Executable Baseline And Scope Lock" docs/source-proxy-agent-integration-preflight-build-roadmap-v0.1.md
grep -n "POST /v1/coding/bounded-diff-preview" docs/source-proxy-agent-integration-preflight-plan-1-closeout-v0.1.md
grep -n "CodingCommandCenterShell" src/app/coding/page.tsx
grep -n "@router.post(\"/bounded-diff-preview\")" source_proxy/api/codex_adapter.py
grep -n "BOUNDED_DIFF_PREVIEW_TARGET" source_proxy/api/codex_adapter.py
grep -n "No Source Proxy, Scout, or Cartographer authority changes" data/design-vault/README.md
grep -n "does not make autonomous promotion" scout/SCOPE.md
grep -n "@router.get(\"/live-state\")\\|@router.post(\"/safe-write\")\\|@router.get(\"/queue/run-next\")" source_proxy/api/cartographer.py
git diff --check -- docs/source-proxy-agent-integration-preflight-plan-1-closeout-v0.1.md
```
