# General Intelligence Runtime Phase 1

## Purpose

Phase 1 starts changing the engine, but only through a global runtime intelligence contract. The goal is to make Spirit choose better answer strategies before speaking while preserving the existing profile voices, tools, routes, UI, memory, and source enforcement.

## What Changed

- Added a global `[GENERAL INTELLIGENCE CONTRACT]` block to the model runtime prompt.
- The block treats model profiles as voice and tone, while task strategy comes from the user's actual request.
- Added task policies for troubleshooting, research/verification, school and paper help, technical planning, emotional-practical advice, uncertainty, and citation honesty.
- Added a private critic checklist inside the prompt. This is not a second model call and does not add an LLM judge.

## General Intelligence Contract

Before answering, Spirit privately classifies the user's task:

- troubleshooting / diagnosis
- research / verification
- school / paper help
- technical planning
- emotional-practical advice
- uncertainty check
- citation/source request
- casual direct answer

Then it chooses the answer strategy based on the task, not only the model profile voice.

Profiles control tone. Task policy controls reasoning shape. Evidence controls confidence. The critic pass checks for generic, unsupported, or overconfident answers.

## Example: Troubleshooting Misattributed Cause

This is not a hard-coded GPU or Palworld rule. It is a golden example of the broader troubleshooting policy.

For prompts like:

> My PC crashed when trying to play Palworld. It was buggy and loading slow. I took out the GPU and it is warm to touch. Is it overheating?

The general reasoning pattern Spirit should apply:

1. Do not accept the user's suspected cause as proven.
2. Separate the observed symptom from the likely root cause.
3. Identify what evidence is missing.
4. Rank likely causes from most to least plausible.
5. Mention red flags without causing panic.
6. Give the smallest useful next test.

For this specific example, a strong answer would explain that warm-to-touch after gaming can be normal, actual sensor temperatures matter more than touch, and the crash may be caused by game instability, RAM pressure, driver/DirectX issues, VRAM/storage/loading issues, power, or thermal shutdown only when evidence supports it.

This example exists to test general troubleshooting intelligence, not to special-case GPU questions.

## What It Does Not Change

- No new tools.
- No memory expansion.
- No repo-reading expansion.
- No route changes.
- No UI, dashboard, Oracle visuals, CSS, telemetry, voice, storage, or dependency changes.
- No package scripts or lockfile changes.

## How To Run

```bash
npx vitest run src/lib/spirit/__tests__/spirit-intelligence-contract.test.ts src/lib/spirit/__tests__/general-intelligence-eval.test.ts
npm run typecheck -- --pretty false
```

## Future Use

Phase 0 evals remain the measurement baseline. Phase 1 should improve future live answers against those evals, but these tests still avoid Ollama, OpenAI, network calls, and nondeterministic current-output checks.
