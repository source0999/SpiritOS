# Operator Summary

S8.3 makes the readable S8.2 batch panel show better information.

What changed:

- `HD`, `full HD`, `mkv`, `mp4`, `long`, `short`, `unknown performer`, and `needs title cleanup` no longer appear as primary Smart Tags.
- Technical facts now show as Quality/technical badges or Advanced details.
- Model/performer identity appears as its own field.
- Recommended names display without `.mkv`, `.mp4`, or other extensions.
- Random/hash filenames fall back to `Model Name - Untitled 01` or `Unknown Model - Untitled 01`.
- Human-readable titles are preserved.
- Existing read-only face/performer evidence is used only when it safely matches the video path.
- The panel now explains that visual content tagging is not enabled yet.

What remains future work:

- True scene/body/action tags need a future approved local visual classifier, OCR, or VLM lane. S8.3 adds the contract but does not invent those tags from filenames.

Britton UI smoke:

- Run Preview folder and confirm rows are still clean.
- Run Analyze folder and confirm Smart Tags no longer show technical/status clutter.
- Confirm Quality/technical badges are separate from Smart Tags.
- Confirm random/hash filenames recommend model-based `Untitled 01` names.
- Confirm readable titles remain readable and extensionless in Recommended name.
