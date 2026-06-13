# Increment 8.1 - Preflight and Dry-Run Surface Inventory

## P - Preflight

Repo path:

- `Z:\`

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
- `execute-approved` route calls
- sandbox terminal command execution
- safe-write execution
- workflow runner execution
- browser/generated artifact behavior reruns

Commands run:

- `git status --short`
- `Get-Content docs\evidence\spiritos-cognitive-control-plane-revamp-v0.1\phase-index.md -Raw`
- `Get-Content docs\evidence\spiritos-cognitive-control-plane-revamp-v0.1\phase-7\phase-7-closeout.md -Raw`
- `Get-Content docs\evidence\spiritos-cognitive-control-plane-revamp-v0.1\phase-7\safe-execution-adapter-map.json -Raw`
- `Get-Content docs\evidence\spiritos-cognitive-control-plane-revamp-v0.1\phase-1\canonical-truth-contract.json -Raw`
- `Get-Content docs\evidence\spiritos-cognitive-control-plane-revamp-v0.1\phase-3\context-router-preview-schema.json -Raw`
- `Get-Content docs\evidence\spiritos-cognitive-control-plane-revamp-v0.1\phase-4\executive-preview-schema.json -Raw`
- `Get-Content docs\evidence\spiritos-cognitive-control-plane-revamp-v0.1\phase-5\handoff-preview-schema.json -Raw`
- `Get-Content docs\evidence\spiritos-cognitive-control-plane-revamp-v0.1\phase-6\behavior-verifier-result-schema.json -Raw`
- `Get-Content docs\evidence\spiritos-cognitive-control-plane-revamp-v0.1\phase-7\safe-execution-preview-contract.json -Raw`
- `Get-Content docs\evidence\spiritos-cognitive-control-plane-revamp-v0.1\phase-7\dry-run-execution-preview-examples.json -Raw`
- `rg -n "dry_run|self-tests|preview_only|would_execute|applied_anything|run_self_test_suite|phase-4e|proxy-smoke" source_proxy\testing source_proxy\tests source_proxy\api -g "*.py"`

## I - Implement

Created a read-only inventory of prior phase contracts and existing dry-run surfaces. No runtime endpoints were called.

## V - Verify

Static/manual checks:

- Phase 1, 3, 4, 5, 6, and 7 schemas were inspected as dry-run loop inputs.
- Existing dry-run/self-test surfaces were discovered without execution.
- No source files were modified.

Unavailable checks:

- Runtime integrated dry-run endpoint: UNVERIFIED because Phase 8 is evidence-only.
- Browser/generated artifact behavior rerun: UNVERIFIED by phase boundary.

## O - Observe

Changed files:

- `phase-8/increment-8.1-preflight-and-dry-run-surface-inventory.md`
- `phase-8/integrated-dry-run-surface-inventory.json`

Observed dirty tree at preflight:

- `?? docs/evidence/spiritos-brain-control-plane-preflight-audit-20260612/`
- `?? docs/evidence/spiritos-cognitive-control-plane-revamp-v0.1/`

## T - Triage

Verdict: GO

Reason:

- Phase 8 inputs and reuse surfaces are identified.
- No production files were edited.

Next authorized increment:

- Increment 8.2 - Integrated dry-run loop contract
