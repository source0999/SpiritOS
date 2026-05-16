---
blueprint_id: blueprint-index
title: SpiritOS Blueprint Inventory
project: SpiritOS
component: blueprint-system
doc_type: index
status: active
source_of_truth: true
owner: Britton
code_paths:
  - _blueprints/**
related_blueprints: []
write_policy: proposal_only_until_dashboard_approved
last_verified: 2026-05-16
---

# SpiritOS Blueprint Inventory

Inventory created for Spirit Cartographer Increment 0.1 on 2026-05-15.

This index classifies the current `_blueprints` documents without rewriting their content. Each existing blueprint document is listed once.

## Directory Governance

| Directory | Purpose | Governance |
| --- | --- | --- |
| `current/` | Current project and dashboard state. | Canonical current truth; Cartographer may use these for drift checks. |
| `components/` | Component architecture and component roadmaps. | Active component blueprints may be source-of-truth; planned roadmaps are not canonical truth until promoted. |
| `runbooks/` | Manual QA, operating checks, and command recipes. | Operational guidance only; runbooks must not redefine architecture. |
| `history/` | Phase receipts and historical evidence. | Preserved for context; ignored for current drift authority. |
| `sandbox/` | Visual experiments and non-production concepts. | Explicitly non-production; cannot imply shipped behavior. |
| `proposals/` | Draft blueprint and governance update proposals. | Proposal queue only; no proposal applies without review and approval. |
| `_schema/` | Blueprint metadata and policy schema. | Governance reference for frontmatter and write policy rules. |

## Current Source Of Truth

| Document | Classification | Notes |
| --- | --- | --- |
| `current/system_state.md` | current truth | Current system architecture, Scout state, Source Proxy/coding workflow, safety boundaries, and known states. |
| `current/dashboard_state.md` | current truth | Dashboard redesign shipped status, architecture notes, and next-phase anchors. |

## Schema / Governance

| Document | Classification | Notes |
| --- | --- | --- |
| `_schema/blueprint-frontmatter.schema.md` | current truth | Frontmatter schema, allowed statuses, source-of-truth rules, and write policy definitions. |

## Component Blueprints

| Document | Classification | Notes |
| --- | --- | --- |
| `components/chat_runtime_architecture.md` | component blueprint | Chat runtime architecture, local-only persistence boundary, server-backed transport, Oracle reuse notes, and key files. |
| `components/cartographer_agent.md` | component blueprint | Spirit Cartographer operating contract, sub-role graph, approval lanes, onboarding, performance limits, and audit boundaries. |
| `components/design_system.md` | component blueprint | Spirit OS design language, palette, primitives, responsive targets, and chat workspace design notes. |
| `components/oracle_voice.md` | component blueprint | Oracle voice surface, hands-free loop, secure context, shared runtime/TTS systems, and deferred work. |

## Roadmaps

| Document | Classification | Notes |
| --- | --- | --- |
| `components/chat_workspace.md` | roadmap | Phased chat workspace rebuild roadmap and shipped/deferred chat capabilities. |
| `components/project_tracker.md` | roadmap | Planned Project Tracker capabilities and read-only/approval-gated safety contract. |

## Runbooks / Manual QA

| Document | Classification | Notes |
| --- | --- | --- |
| `runbooks/basic_chat_voice_qa.md` | manual QA/runbook | Manual checks for chat, voice, routes, LAN/Tailscale origins, and environment settings. |
| `runbooks/cartographer_dashboard_mobile_qa.md` | manual QA/runbook | Manual checks for Cartographer dashboard, LAN/Tailscale parity, mobile layout, and approval safety. |
| `runbooks/cartographer_manual_checks.md` | manual QA/runbook | Routine Cartographer operating checks for detection, approvals, onboarding, audit, rollback guidance, and regression commands. |

## History / Phase Receipts

| Document | Classification | Notes |
| --- | --- | --- |
| `history/general_intelligence_phase0.md` | history/phase receipt | Phase 0 eval scaffold receipt and measurement scope. |
| `history/general_intelligence_phase1.md` | history/phase receipt | Phase 1 runtime intelligence contract receipt. |
| `history/general_intelligence_phase2.md` | history/phase receipt | Phase 2 task policy runtime receipt. |
| `history/general_intelligence_phase3.md` | history/phase receipt | Phase 3 reasoning-pattern runtime receipt. |
| `history/general_intelligence_phase4.md` | history/phase receipt | Phase 4 evidence weighting and confidence calibration receipt. |

## Visual Sandbox

| Document | Classification | Notes |
| --- | --- | --- |
| `sandbox/design_demo.md` | visual sandbox | Visual-only design demo blueprint for `/design-demo`; explicitly not production rewiring. |

## Proposal Queue

| Document | Classification | Notes |
| --- | --- | --- |
| `proposals/README.md` | proposal queue placeholder | Explains where future reviewable blueprint proposals should live; contains no approved changes. |

## Deprecated / Parked Docs

No current `_blueprints` documents are classified as deprecated or parked in this inventory.
