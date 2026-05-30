# Agent Factory Planning Package Closeout v0.1

## planning package status

The Agent Factory planning package is ready as a docs-only package.

It defines the Plan 1 through Plan 9 roadmap, dependency gates, safe timing map, sub-agent inventory, Plan 1 docs-only contracts, operating rules, and the new-chat start prompt for safe continuation.

## Docs that exist

- `docs/agent-factory-roadmap-v0.1.md`
- `docs/agent-factory-new-chat-handoff-v0.1.md`
- `docs/agent-factory-phase-1-docs-only-agent-contracts-v0.1.md`
- `docs/agent-factory-planning-package-closeout-v0.1.md`
- `docs/agent-factory-plan-1-new-chat-start-prompt-v0.1.md`

## What was already done accidentally or early

Plan 1 Phase 1 docs-only contracts and operating rules were already written in `docs/agent-factory-phase-1-docs-only-agent-contracts-v0.1.md`.

That file includes:

- Phase 1.1 contract source of truth.
- Authority Auditor contract.
- Receipt Scribe contract.
- Handoff Scribe contract.
- Prompt Pattern Librarian contract.
- Lane Guard contract.
- Phase 1.2 operating rules for dirty worktree handling, one-lane planning, authority crossings, and handoff readiness.

This early work is docs-only. It does not authorize runtime helpers, source edits, tests, implementation, commits, pushes, branches, worktrees, package installs, server restarts, external API calls, auth/config/env changes, or Plan 2.

## What is still only planning

Plans 2 through 9 are roadmap planning only.

Plan 2 must wait until Source Proxy apply/verify is stable.

Plans 3, 4, 5, and 6 must wait until the relevant Cartographer gates are proven.

Plans 7 and 8 must wait until Proxy and Cartographer are daily-driver stable.

Plan 9 must wait until daily-driver proof, worker coordination, product-helper gates, and trust-tier review.

## first real new-chat target

The first real new-chat target is:

Agent Factory Plan 1 review and ratification.

The new chat should:

- Start in `/home/source/SpiritOS`.
- Read the Agent Factory planning docs.
- Treat existing Plan 1 Phase 1 docs as already written.
- Review and ratify the existing contracts and operating rules.
- Not rewrite them unless something is missing.
- Proceed only to the next valid Plan 1 phase if the roadmap says it is allowed and Britton explicitly approves.

## What must not start

The next chat must not start Plan 2.

It must not write runtime helpers.

It must not touch implementation files.

It must not touch Source Proxy, Cartographer, Design, Scout, backend, frontend, tests, package, config, auth, environment, scripts, commits, pushes, branches, worktrees, stash, reset, clean, package installs, server restarts, or external API calls unless a later approved phase explicitly allows it.

## Short Spot Check

Britton should spot-check that:

- The roadmap names Plan 1 through Plan 9.
- The roadmap distinguishes what can run in parallel from what must wait until Proxy or Cartographer gates.
- The closeout admits Plan 1 Phase 1 docs-only content was already written.
- The new-chat prompt says to review and ratify existing Plan 1 Phase 1 docs before proceeding.

READY FOR HANDOFF PROMPT
