# General Intelligence Eval Phase 0

## Purpose

Phase 0 builds a ruler before changing the engine. It adds a deterministic eval scaffold for Spirit's general answer quality so later runtime upgrades can be measured against stable cases.

## What Phase 0 Measures

- Whether an answer handles the user's actual task instead of falling into a generic checklist.
- Whether it names uncertainty and missing evidence honestly.
- Whether it avoids fake citations, fake URLs, invented page numbers, and repo/file claims.
- Whether troubleshooting answers separate symptoms from likely causes and mention red flags.
- Whether writing, planning, school, and emotional-practical prompts get the right answer shape.

## What It Does Not Change

- No production answer behavior.
- No model prompts.
- No tools.
- No memory systems.
- No repo-reading expansion.
- No UI, dashboard, Oracle visuals, CSS, routes, telemetry, voice, storage, or package dependencies.
- No current Spirit output tests that depend on Ollama, OpenAI, network, or a local model.

## How To Run

Use the narrow deterministic Vitest target:

```bash
npx vitest run src/lib/spirit/__tests__/general-intelligence-eval.test.ts
```

The repo already has `npm test` for Vitest. No package script was added in Phase 0.

## Future Phase Use

Later phases can run these same cases against current and upgraded Spirit answers. The helper scores answers with string and regex trait checks only. It is intentionally simple: the goal is stable regression signal, not perfect grading or an LLM judge.

Future runtime changes should improve matched expected traits while avoiding forbidden traits. New cases can be added as failures are discovered.

## Example: Palworld

Weak answer pattern:

> Your GPU is probably overheating. Check fans, dust, airflow, and thermal paste.

Why it fails:

- Treats warm-to-touch as strong evidence.
- Collapses the crash cause and heat symptom.
- Skips actual sensor temperature.
- Misses likely causes like game instability, RAM pressure, driver/DirectX problems, VRAM/storage/loading issues.
- Pushes a generic hardware checklist too early.

Stronger answer pattern:

> Warm to the touch after gaming can be normal; actual sensor temps matter more than touch. The crash may be unrelated to heat, especially with Palworld loading slowly. Check GPU temperature under load, then consider game instability, RAM pressure, driver/DirectX issues, VRAM/storage/loading problems, and only treat thermal shutdown as likely if temperatures spike or the PC shuts down under load. Stop and inspect if there is smoke, a burning smell, artifacts, fan failure, or repeated shutdowns.

Why it passes:

- Leads with the best first correction.
- Separates symptom from cause.
- Requests the missing measurement.
- Ranks plausible causes.
- Names red flags without panic.
