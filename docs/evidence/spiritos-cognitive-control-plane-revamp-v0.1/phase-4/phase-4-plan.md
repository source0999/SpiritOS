# Phase 4 Plan - Risk/Permission Executive Preview

## Authorization

Authorized phase: Phase 4 only.

Scope: evidence-only risk/permission executive preview contract and dry-run packet examples. No runtime behavior changes are made in this phase.

Do not begin Phase 5.

## PIVOT Increments

| Increment | Name | Output |
| --- | --- | --- |
| 4.1 | Preflight and existing permission/risk surface inventory | `increment-4.1-preflight-and-risk-surface-inventory.md`, `risk-permission-surface-inventory.json` |
| 4.2 | Risk taxonomy and permission decision contract | `increment-4.2-risk-taxonomy-and-permission-contract.md`, `risk-permission-contract.md`, `risk-permission-contract.json` |
| 4.3 | Executive preview packet schema | `increment-4.3-executive-preview-schema.md`, `executive-preview-schema.json` |
| 4.4 | Dry-run risk examples | `increment-4.4-dry-run-risk-examples.md`, `dry-run-risk-examples.json` |
| 4.5 | Existing-system adapter map and Phase 5 handoff | `increment-4.5-adapter-map-and-phase-5-handoff.md`, `risk-permission-adapter-map.json` |
| 4.6 | Phase 4 verification and closeout | `phase-4-closeout.md` |

## Hard Boundaries

- No permission is granted by Phase 4.
- No Source Proxy behavior changes.
- No runtime routes.
- No production UI changes.
- No provider/model calls.
- No live worker starts.
- No Obsidian writes.
- No automatic learning loop.
- No generated benchmark artifact mutation.
- No git mutation.
- No Phase 5 worker selector implementation.

## Phase 4 GO Criteria

- Existing permission/risk surfaces are inventoried.
- Risk taxonomy and permission decision states are defined.
- Preview packet schema is fail-closed and non-authoritative.
- Dry-run examples cover safe preview, human approval required, blocked, and fake-green risk cases.
- Existing central gate, spend gate, unsafe path, approval, and authority systems are mapped as future adapter targets.

