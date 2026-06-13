# Phase 3 Plan - Intake/Context Router Preview

## Authorization

Authorized phase: Phase 3 only.

Scope: evidence-only intake/context router preview contract and dry-run packet examples. No runtime behavior changes are made in this phase.

Do not begin Phase 4.

## PIVOT Increments

| Increment | Name | Output |
| --- | --- | --- |
| 3.1 | Preflight and existing intake/context surface inventory | `increment-3.1-preflight-and-intake-surface-inventory.md`, `intake-context-surface-inventory.json` |
| 3.2 | Intake classification contract | `increment-3.2-intake-classification-contract.md`, `intake-classification-contract.md`, `intake-classification-contract.json` |
| 3.3 | Context router preview packet schema | `increment-3.3-context-router-preview-schema.md`, `context-router-preview-schema.json` |
| 3.4 | Dry-run preview examples and truth/memory carry-forward | `increment-3.4-dry-run-preview-examples.md`, `dry-run-preview-examples.json` |
| 3.5 | Existing-system adapter map and Phase 4 handoff | `increment-3.5-adapter-map-and-phase-4-handoff.md`, `intake-context-adapter-map.json` |
| 3.6 | Phase 3 verification and closeout | `phase-3-closeout.md` |

## Hard Boundaries

- No Source Proxy behavior changes.
- No new runtime routes.
- No production UI changes.
- No provider/model calls.
- No live worker starts.
- No Obsidian writes.
- No automatic learning loop.
- No generated benchmark artifact mutation.
- No git mutation.
- No Phase 4 risk/permission implementation.

## Phase 3 GO Criteria

- Existing intake/context surfaces are inventoried.
- Intake classification fields and reason codes are defined.
- Context source selection rules preserve Phase 2 read-only boundaries.
- Preview packet schema includes source refs, privacy level, truth labels, unverified checks, and non-authority rules.
- Dry-run examples include safe, ambiguous, risky, and missing-context cases.
- Future adapter targets are mapped without duplicating existing systems.

