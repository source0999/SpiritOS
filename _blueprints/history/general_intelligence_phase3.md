---
blueprint_id: general-intelligence-phase3
title: General Intelligence Runtime Phase 3
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

# General Intelligence Runtime Phase 3

## Purpose

Phase 3 addresses the shallow-answer problem seen in manual testing. Phase 2 picked the right task policy, but Spirit could still answer with one or two thin sentences. Phase 3 adds reusable reasoning patterns with minimum answer shapes.

This is still a runtime-prompt phase only. It does not add tools, memory, repo reading, UI, routes, storage, telemetry, package scripts, or dependencies.

## What Changed

- Added a `spirit-reasoning-patterns` library.
- Added a `[REASONING PATTERN]` block to runtime after `[ACTIVE TASK POLICY]` and before `[SEMANTIC ROUTING]`.
- Each pattern includes:
  - purpose
  - answer shape
  - minimum bar
- The final answer should stay natural and should not name the pattern unless the user asks how Spirit is reasoning.

## Patterns

- Troubleshooting pattern
- Research pattern
- Paper and school help pattern
- Technical planning pattern
- Emotional-practical advice pattern
- Uncertainty pattern
- Source honesty pattern
- Direct answer pattern

## Why This Helps

For troubleshooting, Spirit should no longer stop at:

> That can be a sign of radiator issues, yes.

It should include:

- direct likelihood judgment
- symptom versus likely root cause
- missing evidence or measurement
- 3 to 5 plausible causes
- 1 to 3 next tests
- red flags or stop conditions

For deadline/emotional-practical prompts, Spirit should no longer stop at generic encouragement. It should include a usable schedule or ordered plan.

## Manual Prompts To Retry

```text
My car stalled and the engine was hot. Is it the radiator?
```

Look for: "not necessarily", missing evidence like temperature gauge/coolant/leaks/warning lights, ranked causes, next tests, and red flags.

```text
My app is slow and CPU is high. Is React broken?
```

Look for: not blaming React by default, profiling evidence, render loops, repeated effects, data fetching/server latency, bundle/hydration, and next tests.

```text
I'm overwhelmed and have a paper due tonight. I don't need therapy, I need a way through the next 4 hours.
```

Look for: brief validation, "submittable not perfect", time-boxed plan, what to skip, and the first action.

## How To Run

```bash
npx vitest run src/lib/spirit/__tests__/spirit-reasoning-patterns.test.ts src/lib/spirit/__tests__/spirit-task-policy.test.ts src/lib/spirit/__tests__/spirit-intelligence-contract.test.ts src/lib/spirit/__tests__/general-intelligence-eval.test.ts
npm run typecheck -- --pretty false
```
