# Plan 6 Partial-Candidate Targeted Fixes Addendum

Date: 2026-06-27

Status: `PLAN6_PARTIAL_CANDIDATE_ADDENDUM_SOAK_COMPLETE`

Starting status: `PARTIAL_DAILY_DRIVER_CANDIDATE`

Updated recommendation: `CONDITIONAL_DAILY_DRIVER_CANDIDATE`

Full daily-driver promotion: `NOT_APPROVED`

Plan 7: `NOT_STARTED / NOT_AUTHORIZED`

## Scope

Britton accepted the Plan 6 final closeout as `PARTIAL_DAILY_DRIVER_CANDIDATE`, did not approve full promotion, and authorized targeted fixes plus an additional supervised productive soak inside the Plan 6 partial-candidate boundary.

This addendum changed only Plan 6 docs/status/proof/operator-check artifacts. It did not touch source product code, package/env/secrets, generated XML packs, repomixes, SpiritFlix, media, Jellyfin, Mac optimizer, Obsidian, Plan 7, or external irreversible systems.

## Targeted Fixes

1. Externalized approval records: `plan6-addendum-approval-records-20260627.json` records one approval token per soak task, target paths, allowed action, apply window, forbidden paths, rollback instruction, and post-restore blocked-apply proof requirement.
2. Independent downstream authority strengthening: `plan6-additional-productive-soak-proof-20260627.json` contains a separate `independent_addendum_audit_records` section that verifies each task output hash, state fields changed, and downstream consumption after mutation.
3. Linux replay refresh: focused tests, Mac pytest lane, operator check, and JSON validation were rerun from `/home/source/SpiritOS`.
4. Status/handoff hygiene: `status.md`, `status.json`, `next-plan-handoff.md`, and `new-chat-start.md` now agree on conditional candidate status, full promotion not approved, and Plan 7 not authorized.

## Soak Tasks

| Task | Result | Target |
| --- | --- | --- |
| A | `GO_PRODUCTIVE_PLAN6_DOCS_PATCH` | Evidence index addendum refinement |
| B | `GO_TEST_ADJACENT_PLAN6_SCRIPT_PATCH` | Operator-check addendum validation |
| C | `GO_PRODUCTIVE_PLAN6_STATUS_PATCH` | Status and handoff consistency |
| D | `GO_ACCEPTANCE_HARNESS_OUTPUT_CONSUMED` | Acceptance harness output consumed into proof |
| E | `GO_DECISION_PACKET_COMPLETE` | Final addendum decision packet |

## Authority And Restore

Scoped apply authority was used through the official `central_gate_check("apply")` mechanism with a temporary gate state path and one fresh approval token per task. The repository `.gate/state.json` hash before the soak was `1f33f25264d315e0337f0bc0b0f8947a9aa2cf83fac96278a690128e8e4ca7e8` and after the soak was `1f33f25264d315e0337f0bc0b0f8947a9aa2cf83fac96278a690128e8e4ca7e8`.

Post-restore non-approved apply probes were blocked for every task without mutation.

## Decision

The addendum improves the recommendation from PARTIAL to CONDITIONAL because the approval record caveat and Linux replay caveat were directly addressed, and the independent addendum audit record strengthens downstream consumption evidence.

It does not justify full promotion because productive work remains Plan 6 docs/test-adjacent, no product-code readiness was proven, no Mac write occurred, and Plan 7 remains unauthorized.
