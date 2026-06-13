# Diagnostic Lessons

## Calculator false positive and repeated fail

The original diagnostic treated the calculator as usable because it opened and matched plain intent. The revamped manifest also listed it as behavior PASS, but browser behavior evidence clicked `2 + 3 =` and observed display `0`, not `5`. v0.2 must require arithmetic behavior proof before PASS and should create a failure packet with the exact sequence, expected result, observed result, artifact path, and reason code.

## Dark theme false positive and repeated fail

Dark theme produced an artifact and toggled a class, but computed background and text colors did not change. v0.2 must test visible/computed state, not just class mutation or button existence.

## Habit tracker false positive and repeated fail

Habit tracker rendered static hard-coded habits with no inputs, buttons, checkboxes, or state-changing controls. v0.2 must require a behavior contract for state change: add, complete, edit, remove, or another prompt-appropriate habit action.

## Timer false negative

The original diagnostic marked timer FAIL, but later behavior proof showed start, wait, stop, and freeze working: `00:00` changed to `00:02` and stayed at `00:02` after Stop. v0.2 must preserve true passes as carefully as it catches false positives.

## Notes markdown-only failure

The notes prompt generated `notes_app.md` instead of an app. v0.2 needs better artifact intent resolution so "notes app" routes to an interactive app unless the user asks for a document.

## Missing preview/artifact failures

Music player mockup, password strength checker, and drawing pad produced no usable preview artifact in the inspected revamped diagnostic. v0.2 should fail artifact readiness, mark behavior unverified when no artifact exists, and produce handoff or repair only when the local disposable workspace can safely be used.

## Old corrected results vs new revamped results

The original 10-prompt summary showed several heuristic PASS rows. The revamped 11-prompt summary improved reason codes and preserved all run receipts, but separate browser review still corrected calculator, dark theme, and habit tracker. v0.2 should make that behavior review part of the final verdict path.

## Why behavior verification matters

Opening a page, creating files, and matching prompt words are not enough for app behavior. Users ask for working artifacts, so Source Proxy needs observable behavior probes that exercise the core interaction.

## Why a repair loop is now needed

v0.1 can tell the truth about failures. v0.2 should use that truth to coach local Qwen through a bounded repair attempt, then re-test and either PASS honestly or create a handoff packet.
