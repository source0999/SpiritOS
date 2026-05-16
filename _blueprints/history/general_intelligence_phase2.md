---
blueprint_id: general-intelligence-phase2
title: General Intelligence Runtime Phase 2
project: SpiritOS
component: general-intelligence
doc_type: phase_receipt
status: historical
source_of_truth: false
owner: Britton
code_paths: []
related_blueprints:
  - chat-runtime-architecture
write_policy: historical_read_only
last_verified: 2026-05-15
---

# General Intelligence Runtime Phase 2

## Purpose

Phase 2 makes the Phase 1 idea operational: profiles control voice, while a detected task policy controls the answer shape for the current turn.

This is still not a tool phase. It does not add memory, repo reading, UI, routes, storage, telemetry, package scripts, or dependencies.

## What Changed

- Added a deterministic `spirit-task-policy` module.
- Added broad task policy detection from the latest user message.
- Added an `[ACTIVE TASK POLICY]` runtime block after `[GENERAL INTELLIGENCE CONTRACT]` and before `[SEMANTIC ROUTING]`.
- Kept the selected model profile intact, so Sassy, Peer, Teacher, Researcher, and Brutal remain voice choices rather than reasoning limits.

## Task Policies

The active policy can be:

- troubleshooting / diagnosis
- research / verification
- school / paper help
- technical planning
- emotional-practical advice
- uncertainty check
- citation/source request
- casual direct answer

If detection is wrong, the prompt tells Spirit to adapt to the user's actual request.

## Troubleshooting Scope

The troubleshooting policy is intentionally general. It does not special-case GPU, Palworld, React, cars, or health-ish examples.

The shared pattern is:

1. Do not accept the user's suspected cause as proven.
2. Separate observed symptom from likely root cause.
3. Identify missing evidence or measurements.
4. Rank likely causes.
5. Give the smallest useful next test.
6. Mention red flags that change urgency.

## How To Run

```bash
npx vitest run src/lib/spirit/__tests__/spirit-task-policy.test.ts src/lib/spirit/__tests__/spirit-intelligence-contract.test.ts src/lib/spirit/__tests__/general-intelligence-eval.test.ts
npm run typecheck -- --pretty false
```

## Future Use

Phase 3 can expand this into a richer reasoning-pattern library. Phase 2 only selects a compact active policy so the model has a clear answer strategy before applying profile tone.
