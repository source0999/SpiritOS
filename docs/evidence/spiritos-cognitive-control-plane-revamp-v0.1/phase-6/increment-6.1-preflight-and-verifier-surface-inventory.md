# Increment 6.1 - Preflight and Verifier Surface Inventory

## P - Preflight

Repo path:

- `\\10.0.0.186\SpiritOS\`

Allowed files:

- `docs/evidence/spiritos-cognitive-control-plane-revamp-v0.1/**`

Forbidden files/actions:

- source code edits outside the evidence root
- production UI changes
- Source Proxy behavior changes
- worker execution
- provider/model calls
- Obsidian writes
- git mutation
- generated benchmark artifact mutation

Commands run:

- `git status --short`
- `rg -n "behavior verifier|false-positive|fake-green|calculator|dark theme|habit tracker|timer|diff-preview|verification" C:\Users\smith\.codex\memories\MEMORY.md`
- `Get-Content docs\evidence\spiritos-cognitive-control-plane-revamp-v0.1\phase-index.md -Raw`
- `Get-Content docs\evidence\spiritos-cognitive-control-plane-revamp-v0.1\phase-5\phase-5-closeout.md -Raw`
- `Get-Content docs\evidence\spiritos-cognitive-control-plane-revamp-v0.1\phase-1\truth-fixture-requirements.json -Raw`
- `Get-Content source_proxy\verification\diff.py -Raw`
- `Get-Content source_proxy\verification\deterministic.py -Raw`
- `Get-Content source_proxy\api\diff_verification.py -Raw`
- `Get-Content source_proxy\api\coding_self_tests.py -Raw`
- `Get-Content source_proxy\cartographer\verification_runner.py -Raw`
- `Get-Content source_proxy\testing\runner.py -Raw`
- `Get-Content tests\ui-agent-trials\trial-result-schema.ts -Raw`
- `rg -n "PASS|FAIL|NEEDS_FIX|UNVERIFIED|artifact|preview|behavior|computed|timer|calculator" tests\ui-agent-trials source_proxy\tests src\components\coding -g "*.ts" -g "*.tsx" -g "*.py"`

## I - Implement

Created a read-only inventory of existing verifier-adjacent systems. No runtime behavior was changed.

## V - Verify

Static/manual checks:

- Existing verifier surfaces were inspected read-only.
- Existing Phase 1 fixture requirements were used as the source of truth for June 12 behavior cases.
- No browser, provider, worker, or generated artifact run was attempted.

## O - Observe

Changed files:

- `phase-6/increment-6.1-preflight-and-verifier-surface-inventory.md`
- `phase-6/behavior-verifier-surface-inventory.json`

Observed dirty tree at preflight:

- `?? docs/evidence/spiritos-brain-control-plane-preflight-audit-20260612/`
- `?? docs/evidence/spiritos-cognitive-control-plane-revamp-v0.1/`

## T - Triage

Verdict: GO

Reason:

- Phase 6 evidence root exists.
- Existing verifier surfaces are mapped for future reuse.
- No production files were edited.

Next authorized increment:

- Increment 6.2 - June 12 behavior fixture contract
