# Increment 4.1 - Preflight and Risk/Permission Surface Inventory

## P - Preflight

- Repo path: `\\10.0.0.186\SpiritOS\`
- Starting `git status --short`:
  - `?? docs/evidence/spiritos-brain-control-plane-preflight-audit-20260612/`
  - `?? docs/evidence/spiritos-cognitive-control-plane-revamp-v0.1/`
- Allowed Phase 4 write surface: `docs/evidence/spiritos-cognitive-control-plane-revamp-v0.1/**`
- Forbidden actions: permission grants, runtime route changes, production UI changes, provider/model calls, live worker starts, Obsidian writes, automatic learning, generated artifact mutation, git mutation.
- Phase 3 preview schema and closeout were inspected before editing.

## I - Implement

Created:

- `phase-4-plan.md`
- `increment-4.1-preflight-and-risk-surface-inventory.md`
- `risk-permission-surface-inventory.json`

Read-only inspected:

- `source_proxy/approval/gate.py`
- `source_proxy/approval/external_gate.py`
- `source_proxy/safety/paths.py`
- `source_proxy/agents/registry.py`
- `source_proxy/self_status.py`
- `source_proxy/api/action_preview.py`
- `src/components/coding/approval-gate-binding.ts`
- Phase 1, Phase 2, and Phase 3 evidence contracts

## V - Verify

- Existing spend-before-send gate identified: PASS
- Existing central external gate identified: PASS
- Existing unsafe path detector identified: PASS
- Existing action preview classifier identified: PASS
- Existing agent/provider authority registry identified: PASS
- Existing `/coding` approval binding identified: PASS
- No production files changed: PASS

## O - Observe

Commands run:

- `git status --short`
- `Get-Content ... phase-3 ...`
- `rg ... MEMORY.md`
- `Get-Content source_proxy/approval/gate.py`
- `Get-Content source_proxy/approval/external_gate.py`
- `Get-Content source_proxy/safety/paths.py`
- `Get-Content source_proxy/agents/registry.py`
- `rg ... source_proxy src/components/coding src/lib/coding ...`

Skipped/unverified checks:

- Runtime gate checks: SKIPPED, Phase 4 is evidence-only.
- Provider/model calls: SKIPPED, forbidden.
- Worker starts: SKIPPED, forbidden.

## T - Triage

Verdict: GO

Next authorized increment: Increment 4.2 - Risk taxonomy and permission contract.

