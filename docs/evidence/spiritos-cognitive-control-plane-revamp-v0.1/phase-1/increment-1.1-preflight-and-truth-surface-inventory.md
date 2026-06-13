# Increment 1.1 - Preflight and Truth-Surface Inventory

## P - Preflight

- Repo path: `\\10.0.0.186\SpiritOS\`
- Starting `git status --short`:
  - `?? docs/evidence/spiritos-brain-control-plane-preflight-audit-20260612/`
  - `?? docs/evidence/spiritos-cognitive-control-plane-revamp-v0.1/`
- Allowed Phase 1 write surface: `docs/evidence/spiritos-cognitive-control-plane-revamp-v0.1/**`
- Forbidden actions: production source changes, Source Proxy behavior changes, provider/model calls, live worker starts, Obsidian writes, git mutation, generated benchmark artifact mutation.
- Existing Phase 0 scope and allowed path matrix were inspected before editing.

## I - Implement

Created the Phase 1 plan and truth-surface inventory packet.

Read-only inspected truth-adjacent surfaces:

- `source_proxy/api/decision.py`
- `source_proxy/verification/diff.py`
- `source_proxy/verification/deterministic.py`
- `source_proxy/verification/contracts.py`
- `source_proxy/api/diff_verification.py`
- `source_proxy/api/coding_self_tests.py`
- `source_proxy/agents/registry.py`
- `src/components/coding/CodingAgentInterface.tsx`
- `src/components/coding/approval-gate-binding.ts`
- `tests/ui-agent-trials/trial-result-schema.ts`
- `tests/ui-agent-trials/*`
- `data/coding-runs.json`
- `docs/evidence/**`

## V - Verify

- Inventory file exists: PASS
- All inspected systems are read-only reuse candidates: PASS
- No production files changed: PASS

## O - Observe

Commands run:

- `git status --short`
- `rg -n ... C:\Users\smith\.codex\memories\MEMORY.md`
- `rg -n ... source_proxy src tests docs ...`
- `Get-Content ... phase-0 ...`

Skipped/unverified checks:

- Runtime route checks: SKIPPED, Phase 1 is evidence-only.
- Provider/model calls: SKIPPED, forbidden.
- Live workers: SKIPPED, forbidden.

## T - Triage

Verdict: GO

Next authorized increment: Increment 1.2 - Canonical truth label contract.

