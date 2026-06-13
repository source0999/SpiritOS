# Phase 5 Plan - Worker Selector and Handoff Preview

## Authorization

Authorized phase: Phase 5 only.

Scope: evidence-only worker/provider selector and handoff preview contract. No runtime behavior changes are made in this phase.

Do not begin Phase 6.

## PIVOT Increments

| Increment | Name | Output |
| --- | --- | --- |
| 5.1 | Preflight and existing worker/provider surface inventory | `increment-5.1-preflight-and-worker-surface-inventory.md`, `worker-selector-surface-inventory.json` |
| 5.2 | Worker selector decision contract | `increment-5.2-worker-selector-contract.md`, `worker-selector-contract.md`, `worker-selector-contract.json` |
| 5.3 | Handoff preview packet schema | `increment-5.3-handoff-preview-schema.md`, `handoff-preview-schema.json` |
| 5.4 | Dry-run selector examples | `increment-5.4-dry-run-selector-examples.md`, `dry-run-selector-examples.json` |
| 5.5 | Existing-system adapter map and Phase 6 handoff | `increment-5.5-adapter-map-and-phase-6-handoff.md`, `worker-selector-adapter-map.json` |
| 5.6 | Phase 5 verification and closeout | `phase-5-closeout.md` |

## Hard Boundaries

- No worker dispatch.
- No worker start.
- No provider/model calls.
- No Source Proxy behavior changes.
- No runtime routes.
- No production UI changes.
- No permission grants.
- No Obsidian writes.
- No generated benchmark artifact mutation.
- No git mutation.
- No Phase 6 behavior verifier implementation.

## Phase 5 GO Criteria

- Existing worker/provider/route/lane systems are inventoried.
- Worker selector output is explicitly recommendation-only.
- Handoff preview schema carries permission decision, risk classes, authority flags, evidence needs, and verifier handoff.
- Dry-run examples include safe recommendation, blocked selector, provider-spend block, and fake-green verifier handoff.
- Existing systems are mapped as future adapter targets without duplicating worker or provider registries.

