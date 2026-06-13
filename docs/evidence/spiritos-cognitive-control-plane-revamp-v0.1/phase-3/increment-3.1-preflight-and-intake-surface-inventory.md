# Increment 3.1 - Preflight and Intake/Context Surface Inventory

## P - Preflight

- Repo path: `\\10.0.0.186\SpiritOS\`
- Starting `git status --short`:
  - `?? docs/evidence/spiritos-brain-control-plane-preflight-audit-20260612/`
  - `?? docs/evidence/spiritos-cognitive-control-plane-revamp-v0.1/`
- Allowed Phase 3 write surface: `docs/evidence/spiritos-cognitive-control-plane-revamp-v0.1/**`
- Forbidden actions: runtime route changes, production UI changes, provider/model calls, live worker starts, Obsidian writes, automatic learning, generated artifact mutation, git mutation.
- Phase 2 memory contract and adapter map were inspected before editing.

## I - Implement

Created:

- `phase-3-plan.md`
- `increment-3.1-preflight-and-intake-surface-inventory.md`
- `intake-context-surface-inventory.json`

Read-only inspected:

- `source_proxy/self_status.py`
- `source_proxy/context/inventory.py`
- `source_proxy/context/obsidian.py`
- `source_proxy/api/context_index.py`
- `source_proxy/api/context_inventory.py`
- `source_proxy/api/obsidian_context.py`
- `source_proxy/api/decision.py`
- `source_proxy/decision/router.py`
- `source_proxy/planning/architect.py`
- `source_proxy/safety/paths.py`
- `src/components/coding/approval-gate-binding.ts`
- Phase 1 and Phase 2 evidence contracts

## V - Verify

- Existing context index surface identified: PASS
- Existing context inventory surface identified: PASS
- Existing Obsidian query surface identified: PASS
- Existing prompt-packet/route decision surfaces identified: PASS
- Existing target/safety path helpers identified: PASS
- No production files changed: PASS

## O - Observe

Commands run:

- `git status --short`
- `Get-Content ... phase-2 ...`
- `rg ... MEMORY.md`
- `Get-Content source_proxy/self_status.py`
- `Get-Content source_proxy/context/inventory.py`
- `rg ... source_proxy src/components/coding src/lib/coding tests ...`

Skipped/unverified checks:

- Runtime route calls: SKIPPED, Phase 3 is evidence-only.
- Provider/model calls: SKIPPED, forbidden.
- Worker starts: SKIPPED, forbidden.

## T - Triage

Verdict: GO

Next authorized increment: Increment 3.2 - Intake classification contract.

