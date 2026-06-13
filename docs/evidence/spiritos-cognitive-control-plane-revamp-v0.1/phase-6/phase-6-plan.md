# Phase 6 Plan - Behavior Verifier

## Authorization

Phase 6 is authorized as an evidence-only behavior verifier planning packet.

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
- no browser or Playwright reruns against generated artifacts in this phase

## Purpose

Define the verifier contract that prevents fake-green product claims. A product PASS must be tied to explicit acceptance criteria and direct behavior proof. Artifact existence, preview openability, static DOM presence, clean diffs, and worker recommendations are supporting signals only.

## PIVOT Increments

| Increment | Scope | Verdict |
| --- | --- | --- |
| 6.1 | Preflight and verifier surface inventory | GO |
| 6.2 | June 12 behavior fixture contract | GO |
| 6.3 | Verifier result schema | GO |
| 6.4 | Dry-run verifier examples | GO |
| 6.5 | Adapter map and Phase 7 handoff | GO |
| 6.6 | Phase 6 verification and closeout | GO |

## Non-Implementation Boundary

This phase does not create runtime verifier modules. Future implementation should wrap or extend existing Source Proxy verification, trial diagnostics, coding UI, and test runner surfaces rather than inventing a disconnected cognitive verifier stack.
