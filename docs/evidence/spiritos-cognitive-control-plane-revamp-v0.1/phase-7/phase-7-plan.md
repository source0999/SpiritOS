# Phase 7 Plan - Safe Execution Preview

## Authorization

Phase 7 is authorized as an evidence-only safe execution preview packet.

Allowed files:

- `docs/evidence/spiritos-cognitive-control-plane-revamp-v0.1/**`

Forbidden actions:

- no source code changes outside evidence docs
- no production UI changes
- no Source Proxy behavior changes
- no worker execution
- no provider/model calls
- no Obsidian writes
- no git mutation
- no generated benchmark artifact mutation
- no `execute-approved` route calls
- no sandbox terminal command execution
- no safe-write execution
- no workflow runner execution

## Purpose

Define the safe execution preview contract for the future control plane. Phase 7 prepares the action plan shape, authority gates, and reuse map for execution without executing anything.

## PIVOT Increments

| Increment | Scope | Verdict |
| --- | --- | --- |
| 7.1 | Preflight and execution surface inventory | GO |
| 7.2 | Safe execution preview contract | GO |
| 7.3 | Authority and forbidden action matrix | GO |
| 7.4 | Dry-run execution preview examples | GO |
| 7.5 | Adapter map and Phase 8 handoff | GO |
| 7.6 | Phase 7 verification and closeout | GO |

## Non-Implementation Boundary

This phase does not implement runtime modules, call existing execution routes, or grant approval authority. Future implementation must wrap existing Source Proxy action preview, diff preview, workflow state, safe write, sandbox terminal, and verification runner surfaces.
