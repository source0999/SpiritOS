# Increment 7R.2 - Merge Individual Into Trial Runner

Date: 2026-06-08

## Changes

Updated `src/components/coding/CodingCockpitShell.tsx`.

Removed the separate sidebar section labelled:

```text
LumaCart prompt runner
```

The remaining single card is:

```text
Trial Runner
```

Subtitle:

```text
Run one dummy Coder prompt or a later benchmark. Coder 001 creates LumaCart first.
```

## Merged Controls

The Trial Runner now contains:

- Category select: existing Coder / Designer / Combined control.
- Count select: existing benchmark count control.
- Mode select:
  - Individual prompt
  - Benchmark count

Default mode is `Individual prompt`.

When in individual mode, the Trial Runner shows:

- Dummy Coder prompt dropdown.
- Coder 001 selected by default.
- Expected state chip.
- `dummy-product-site` target chip.
- `Run selected prompt` button.
- Compact selected-prompt status/result area.
- `Copy diagnostics` button.

When in benchmark mode, the existing benchmark run button is shown. Selection alone does not run a benchmark.

## Text Reduction

Long submitted prompt and boundaries moved behind collapsed details:

```text
View prompt + boundaries
```

The main card no longer shows all primary targets or the full forbidden list by default. Those details remain available in the collapsed details and via diagnostics copy.

## Acceptance

Source scan found no remaining standalone source labels for:

```text
LumaCart prompt runner
LumaCart single prompt runner
Run selected LumaCart
```

Existing manual composer remains separate and unchanged.

## Follow-Up: Run-All Button Restored

Britton reported that the default individual-prompt view removed the visible run-all-trials action.

Patch:

- Kept `Individual prompt` as the default Trial Runner mode.
- Restored a compact `Run all trials` button inside the same Trial Runner card.
- The button calls the existing reversible benchmark runner and still respects the existing run-block checks.
- No separate LumaCart panel was reintroduced.
- No selection auto-runs a benchmark.
