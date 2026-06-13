# Local Qwen Limitations

## What Qwen handles well

The inspected diagnostics show Qwen can often create small disposable HTML/CSS/JS artifacts, follow a file bundle contract, and produce basic static demos for blunt prompts. It is useful for scoped local work where failure is cheap, the workspace is disposable, and Source Proxy preserves transcripts, diffs, receipts, and evidence packets.

## What Qwen currently fails

Qwen can produce plausible artifacts whose core interactions do not work. Examples include a calculator that opens but does not compute `2 + 3 = 5`, a dark theme switcher that changes class state without changing computed colors, and a habit tracker that renders static habits with no controls. It also sometimes misroutes app prompts into documents, as with notes, or produces no preview artifact for music player, password checker, and drawing pad prompts.

## Repeated failure types

- Plausible UI with broken or missing behavior.
- Static content where the prompt implies state change.
- Class or DOM mutation without visible/computed user effect.
- Missing preview/artifact output.
- App/document intent confusion.
- Source Proxy route GO that is weaker than product PASS.

## Why Source Proxy should coach and repair

Local Qwen is useful, but it should not be blindly trusted. Source Proxy needs to provide intent, behavior criteria, failure feedback, repair limits, path guards, and handoff logic. The model should receive a precise failure packet and one or two bounded chances to repair the disposable artifact, not an open-ended mandate.

## When Qwen is appropriate

- Small local artifacts.
- Disposable workspaces.
- Low-risk static or interactive demos.
- Tasks with clear behavior contracts and browser probes.
- Repairs where the observed failure is concrete and the allowed files are limited.

## When to hand off

Hand off when the task requires production source edits, paid/API/provider usage, high usage, hidden workers, real repo mutation, Obsidian write-back, external credentials, broad autonomous behavior, or repeated failed local repair. Hand off also when no artifact exists and the local route cannot safely generate one within approved scope.

## Avoiding overfitting

The diagnostic prompts should be used as real failure evidence, not as a hardcoded answer key. v0.2 should generalize from behavior categories: arithmetic output, visible theme change, stateful list mutation, editable notes, password feedback, pointer drawing, and preview readiness. Prompt-specific examples are fixtures for truth preservation; they are not special-case product patches.

## Expected conclusion

Qwen is useful as a local worker for scoped tasks, but Source Proxy must provide intent, behavior criteria, failure feedback, repair limits, and handoff logic.
