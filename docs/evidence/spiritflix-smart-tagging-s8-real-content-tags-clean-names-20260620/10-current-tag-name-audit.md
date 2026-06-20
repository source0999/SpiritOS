# Current Tag And Name Audit

## Bad Tag Sources

- `src/lib/spiritflix/admin/smart/heuristics.ts`
  - `inferQualityTags()` generated `HD`, `full HD`, `UHD`, and `vertical`.
  - `inferFormatTags()` generated container and duration tags such as `mkv`, `mp4`, `long`, and `short`.
  - `inferPerformerTags()` always generated `unknown performer`.
- `src/lib/spiritflix/admin/smart/suggestions.ts`
  - `buildSpiritFlixReviewSuggestions()` merged quality, format, source, and performer heuristics directly into `suggestedTags`.
  - Ambiguous filenames added `needs-title-cleanup` as a primary suggested tag.
- `src/lib/spiritflix/admin/smart/batch.ts`
  - `itemFromAnalysis()` sent every `analysis.suggestedTags` entry straight to the batch panel, so old sidecars polluted the operator UI.

## Name Sources

- `buildSuggestedFilename()` previously appended the original extension to every suggestion.
- `batch.ts` passed that suggestion through `buildSmartRenamePreviewDraft()` and used `draft.suggestedName` as `proposedFilename`, so display names included `.mkv` or `.mp4`.
- `rename-preview.ts` already preserves the original extension when building a future target path, so the operator display does not need extensions.

## Random Filename Detection

- Before S8.3, random/hash filenames were only weakly captured by `isAmbiguousSpiritFlixFilename()`.
- Numeric names, UUID-ish names, and mixed-case hash-like stems could still be preserved as recommended title text.

## Performer Identity Sources

- The model/person folder path can safely provide a weak identity fallback for paths like `/models/aaliyah-yasan/...`.
- Existing read-only face/performer evidence can be read from `scripts/media/performer_verification.json`.
- S8.3 uses only exact path matches from safe evidence sources such as manual/user-confirmed/face evidence. It does not mutate face DBs, enroll identities, or scan media.

## Visual Tagging Reality

- `scanner.ts` and `sampler.ts` create frame cache evidence and observations like `sampled frame`.
- No local visual classifier/VLM/OCR lane is integrated into the smart-tagging code for scene/body/action classification.
- S8.3 therefore adds an explicit `contentTagEvidence` contract and UI message instead of fabricating content tags.

## Patch Points

- `types.ts`: optional content tag evidence and performer identity contract.
- `heuristics.ts`: primary-content tag filter, technical/status classification, random filename detection, and model-folder identity helper.
- `suggestions.ts`: clean extensionless display names, random/hash fallbacks, read-only face evidence lookup, and technical metadata exclusion from primary `suggestedTags`.
- `batch.ts`: old-sidecar filtering, technical badge projection, model identity projection, clean display names, and visual-tagging message.
- `SpiritFlixSmartBatchPanel.tsx`: operator UI split between Model/performer, Smart Tags, Quality/technical, Recommended name, and Why this name.
- Focused tests in smart heuristics, suggestions, batch, and admin batch panel coverage.
