---
blueprint_id: blueprint-proposal-queue
title: Blueprint Proposal Queue
project: SpiritOS
component: blueprint-system
doc_type: proposal_queue
status: planned
source_of_truth: false
owner: Britton
code_paths:
  - _blueprints/proposals/**
related_blueprints:
  - blueprint-index
write_policy: proposal_only_until_dashboard_approved
last_verified: 2026-05-16
---

# Blueprint Proposal Queue

This directory is reserved for future Cartographer or human-drafted blueprint proposals.

Proposal files are review artifacts only. A proposal may describe a desired blueprint update, affected files, rationale, and verification notes, but it must not be treated as an approved write, commit, or push instruction.

## Governance

- Proposals must name the target blueprint or runbook.
- Proposals must describe whether the change affects current truth, component architecture, runbooks, history, sandbox material, or schema.
- Proposals must remain pending until reviewed through the dashboard or an equivalent human approval gate.
- Approved proposals still require the normal apply, commit, and push approval sequence.
- Rejected proposals should keep the rejection reason for auditability.
