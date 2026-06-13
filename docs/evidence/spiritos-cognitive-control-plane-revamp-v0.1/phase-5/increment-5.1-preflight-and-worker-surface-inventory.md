# Increment 5.1 - Preflight and Worker/Provider Surface Inventory

## P - Preflight

- Repo path: `\\10.0.0.186\SpiritOS\`
- Starting `git status --short`:
  - `?? docs/evidence/spiritos-brain-control-plane-preflight-audit-20260612/`
  - `?? docs/evidence/spiritos-cognitive-control-plane-revamp-v0.1/`
- Allowed Phase 5 write surface: `docs/evidence/spiritos-cognitive-control-plane-revamp-v0.1/**`
- Forbidden actions: worker dispatch/start, provider/model calls, runtime route changes, production UI changes, permission grants, Obsidian writes, generated artifact mutation, git mutation.
- Phase 4 risk/permission adapter map was inspected before editing.

## I - Implement

Created:

- `phase-5-plan.md`
- `increment-5.1-preflight-and-worker-surface-inventory.md`
- `worker-selector-surface-inventory.json`

Read-only inspected:

- `source_proxy/agents/registry.py`
- `source_proxy/cartographer/lane_registry.py`
- `source_proxy/cartographer/worker_contract.py`
- `source_proxy/self_status.py`
- `source_proxy/routing/litellm_router.py`
- `source_proxy/routing/ollama_route.py`
- `source_proxy/decision/advisory_broker.py`
- `/coding` worker-lane and authority display references
- Phase 4 risk/permission contract and handoff requirements

## V - Verify

- Agent/provider capability registry identified: PASS
- Cartographer lane registry identified: PASS
- Cartographer worker contract identified: PASS
- Model route/status surfaces identified: PASS
- Advisory broker and no-authority worker surfaces identified: PASS
- No production files changed: PASS

## O - Observe

Commands run:

- `git status --short`
- `Get-Content ... phase-4 ...`
- `rg ... MEMORY.md`
- `Get-Content source_proxy/agents/registry.py`
- `Get-Content source_proxy/cartographer/lane_registry.py`
- `Get-Content source_proxy/cartographer/worker_contract.py`
- `rg ... source_proxy src/components/coding src/lib/coding ...`

Skipped/unverified checks:

- Worker dispatch/start checks: SKIPPED, forbidden.
- Provider/model calls: SKIPPED, forbidden.
- Runtime route calls: SKIPPED, evidence-only Phase 5.

## T - Triage

Verdict: GO

Next authorized increment: Increment 5.2 - Worker selector decision contract.

