# Phase 8 Plan - Integrated Dry-Run Loop

## Authorization

Phase 8 is authorized as an evidence-only integrated dry-run loop packet.

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
- no browser/generated artifact behavior reruns

## Purpose

Define the integrated dry-run loop that composes Phases 1-7 into a single preview-only control-plane receipt:

`sense -> understand -> remember -> prioritize -> plan -> choose worker -> act -> verify -> learn`

The Phase 8 loop does not implement the runtime control plane. It describes the packet shape, gate aggregation rules, dry-run examples, and Phase 9 readiness handoff.

## PIVOT Increments

| Increment | Scope | Verdict |
| --- | --- | --- |
| 8.1 | Preflight and dry-run surface inventory | GO |
| 8.2 | Integrated dry-run loop contract | GO |
| 8.3 | Gate aggregation and verdict schema | GO |
| 8.4 | Dry-run loop examples | GO |
| 8.5 | Adapter map and Phase 9 handoff | GO |
| 8.6 | Phase 8 verification and closeout | GO |

## Non-Implementation Boundary

Phase 8 creates no runtime modules and calls no existing runtime endpoints. Future implementation must wrap existing Source Proxy and Cartographer preview surfaces and must keep Phase 6 product behavior truth separate from dry-run readiness.
