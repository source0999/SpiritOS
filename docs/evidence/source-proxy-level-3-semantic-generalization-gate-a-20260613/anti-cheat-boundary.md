# Anti-Cheat Boundary

## What Can Be Changed In Gate B

- Generic semantic routing rules in intake.
- Generic behavior contract coverage for synonym families.
- Generic first-pass generation checklist wording keyed by artifact family or probe id.
- Generic repair prompt structure and allowed output format.
- Additive trace instrumentation.
- Focused unit/regression tests and evidence-only diagnostics.

## What Cannot Be Changed In Gate B

- No Level 4.
- No new prompt batches.
- No scorer green-padding.
- No exact prompt branches for the five failed prompts.
- No cloud fallback.
- No backend-authored rescue content.
- No hidden deterministic scaffold.
- No mutation of generated artifacts after the fact except through the bounded repair loop under test.
- No weakening browser behavior probes to pass static artifacts.
- No changing behavior-probe, score, or receipt schemas in a breaking way.

## Generic Synonym Routing Vs Exact Prompt Tailoring

Generic synonym routing:

- Adds concept groups such as cost/share/fee/bill/split for calculator-splitter.
- Adds dusk/dawn/sunset/palette/switch as theme-control concepts.
- Adds phrase/passphrase/strength/gauge as password/passphrase feedback concepts.
- Applies to multiple prompts, including unseen variants.
- Is protected by negative controls for existing app/repo/component/path wording.

Exact prompt tailoring:

- Branches on `parking garage cost sharer`, `dusk dawn palette switch`, `secret phrase strength gauge`, `pretend balcony forecast tile`, or `finger paint doodle pad`.
- Emits canned artifact content for those prompts.
- Changes verdicts based on prompt id or evidence folder name.

Gate B must do the former and must not do the latter.

## Behavior Contract Strengthening Vs Scorer Cheating

Behavior contract strengthening:

- Makes the model packet and repair packet clearer before scoring.
- Requires generated artifacts to mutate visible DOM text or canvas pixels.
- Leaves browser probes and final PASS requirements intact.

Scorer cheating:

- Marks a static preview as PASS.
- Treats route GO, preview open, file existence, or model self-report as behavior PASS.
- Downgrades failure buckets to warnings.
- Adds false-positive corrections without browser evidence.

Gate B must strengthen generation and repair while preserving strict browser verification.

## Why Route Block Fixes Are Legitimate Only With Negative Controls

Fixing `route_blocked_no_preview` is legitimate only if standalone mini-app prompts route disposable while existing app/repo prompts still require explicit targets. Without negative controls, a broader resolver could silently route real production work into disposable artifacts and hide missing integration scope.

## Why Weather And Drawing Need Browser Proof

Weather and drawing already had route GO and preview open. That was not enough. Weather must prove a clicked local control changes visible city/temp/condition/forecast/status text. Drawing must prove pointer/mouse interaction mutates canvas pixels. Model self-report and static DOM are explicitly insufficient.
