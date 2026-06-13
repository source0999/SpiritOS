# Phase 2 Plan - Read-only Hippocampus Memory

## Authorization

Authorized phase: Phase 2 only.

Scope: evidence-only read-only memory contract for Obsidian, evidence docs, and durable run records. No runtime behavior changes are made in this phase.

Do not begin Phase 3.

## PIVOT Increments

| Increment | Name | Output |
| --- | --- | --- |
| 2.1 | Preflight and existing memory-source inventory | `increment-2.1-preflight-and-memory-source-inventory.md`, `memory-source-inventory.json` |
| 2.2 | Read-only memory contract | `increment-2.2-read-only-memory-contract.md`, `read-only-memory-contract.md`, `read-only-memory-contract.json` |
| 2.3 | Evidence selection and truth carry-forward rules | `increment-2.3-evidence-selection-rules.md`, `memory-selection-rules.json` |
| 2.4 | Existing-system adapter map | `increment-2.4-memory-adapter-map.md`, `memory-adapter-map.json` |
| 2.5 | Phase 2 verification and closeout | `phase-2-closeout.md` |

## Hard Boundaries

- No Obsidian writes.
- No automatic learning loop.
- No provider/model calls.
- No live worker starts.
- No Source Proxy behavior changes.
- No production UI changes.
- No git mutation.
- No generated benchmark artifact mutation.
- No Phase 3 intake/context router implementation.

## Phase 2 GO Criteria

- Existing memory-like systems are inventoried.
- Read-only boundaries are explicit.
- Secrets/private-path exclusion rules are preserved.
- Phase 1 truth labels are carried forward as memory metadata.
- Evidence docs and durable run records are mapped as read-only memory sources.
- Future adapter requirements are named without implementing them.

