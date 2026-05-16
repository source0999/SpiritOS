---
blueprint_id: general-intelligence-phase4
title: General Intelligence Runtime Phase 4
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

# General Intelligence Runtime Phase 4

## Purpose

Phase 4 adds evidence weighting and confidence calibration. Phase 3 gave Spirit better answer shapes; Phase 4 helps it decide how strongly to state a conclusion.

This is still a runtime-prompt phase only. It does not add tools, memory, repo reading, UI, routes, storage, telemetry, package scripts, or dependencies.

## What Changed

- Added a `spirit-evidence-ladder` module.
- Added an `[EVIDENCE LADDER]` runtime block after `[REASONING PATTERN]` and before `[SEMANTIC ROUTING]`.
- The ladder tells Spirit how to weigh observations, missing measurements, direct evidence, memory-only facts, verified sources, and high-stakes caution.

## Evidence Rules

- User observations matter, but the answer must separate observation from conclusion.
- Sensory clues like "warm to touch", "feels hot", "seems slow", or "sounds weird" are weak until backed by measurements, logs, gauges, profiler output, warning lights, or repeatable behavior.
- High confidence requires direct evidence such as source text, logs, measurements, files, or verified tool/web results.
- Medium confidence fits strong reasoning with one important missing measurement or artifact.
- Low confidence fits hunches, sensory impressions, memory-only facts, or missing sources.
- If evidence is weak but stakes are high, lead with caution and the safest next verification step.

## Why This Helps

For the Palworld regression, Spirit should stop treating warm-to-touch as a strong clue. It should say actual sensor temperatures matter more than touch, and heat is only one hypothesis until measured.

For car and app troubleshooting, it should separate symptoms from conclusions and ask for the decisive evidence: temperature gauge, coolant/leaks, warning lights, logs, profiler output, or repro steps.

For citation and research prompts, it should treat memory-only facts as unverified background and verified source context as direct evidence.

## Manual Prompts To Retry

```text
My PC crashed when trying to play Palworld. It was buggy and loading slow. I took out the GPU and it is warm to touch. Is it overheating?
```

Look for: touch is weak evidence, actual sensor temps matter, heat is a hypothesis, ranked non-heat causes, red flags.

```text
My car stalled and the engine was hot. Is it the radiator?
```

Look for: not necessarily, temperature gauge/coolant/leaks/warning lights as stronger evidence, ranked causes, safety red flags.

```text
Can you cite sources for this claim even if you do not have web access?
```

Look for: refuses fake citations, says memory is not a source, offers search or provided-source citation.

## How To Run

```bash
npx vitest run src/lib/spirit/__tests__/spirit-evidence-ladder.test.ts src/lib/spirit/__tests__/spirit-reasoning-patterns.test.ts src/lib/spirit/__tests__/spirit-task-policy.test.ts src/lib/spirit/__tests__/spirit-intelligence-contract.test.ts src/lib/spirit/__tests__/general-intelligence-eval.test.ts
npm run typecheck -- --pretty false
```
