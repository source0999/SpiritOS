# Rename Preview Zero Audit

Question:

Why can the batch panel show `Rename previews: 0` after analysis?

Finding:

- In S8, `renamePreviewAvailable` was only true when an analysis sidecar had `reviewedMetadata` and `reviewStatus !== "unreviewed"`.
- The observed state has all items current and needing review, but still unreviewed.
- Therefore rename previews are 0 because the system intentionally blocks ready rename previews until tags/metadata are reviewed or approved.

Secondary issue:

- The batch API response was too thin for operator review.
- It included `suggestedTagCount`, `reviewStatus`, and `renamePreviewAvailable`, but not the actual tags, tag confidence/review state, proposed filename, blocker reason, warnings, sidecar reference, or target conflict details.
- The UI then rendered the thin response as a terse row, so Britton could not see what was found or which action unlocks rename previews.

Implementation decision:

- Keep the safety behavior: ready rename previews remain blocked until review/approval.
- Add a clearly labeled provisional preview when a safe filename suggestion exists before review.
- Add explicit blocker text: review or approve tags/metadata to unlock rename preview.
- Add item-level tags, review counts, proposed filename, rename status, blockers, warnings, target conflicts, duplicate target warnings, and sidecar references.
- Keep real rename/move apply disabled with the exact gate: `Real rename/move apply is disabled until Britton explicitly approves a future apply task.`

No-go items:

- No real media mutation is required or performed.
- No model/OCR/VLM work is required or performed.
- No Source Proxy work is involved.
