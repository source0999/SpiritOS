# SpiritFlix Smart Batch UI Noise Audit

## Why Rows Became Unreadable

`SpiritFlixSmartBatchPanel` rendered each video as a two-column CSS grid: `minmax(0, 1fr) auto`. Only the first child and status pill fit that shape. The tag list, details grid, warning paragraphs, and action buttons were later siblings in the same grid, so they could be squeezed into narrow implicit columns next to the status pill. Long filenames also used ordinary `word-break: break-word`, which lets text collapse into one-character-per-line wrapping when the available column becomes tiny.

## Useful Operator Fields

Britton's default view needs:

- Video filename/title.
- Simple item status: candidate, analyzed, needs review, reviewed, or failed.
- Smart tag chips.
- Recommended/provisional filename.
- Clear approve/reject/review/refresh actions.

## Advanced-Only Fields

These fields are useful for diagnosis but noisy in the default operator path:

- Sidecar references.
- Target path internals.
- Analysis status and review status internals.
- Approved/rejected/pending count math.
- Raw rename blockers and warning paragraphs.
- Per-item diagnostic reason text.

## Preview vs Analyzed Mode

Preview mode should list candidate rows cleanly even when `Analyzed = 0`. It should say that tags and recommended names are unavailable until Analyze folder runs. Analyzed mode should show tag chips and recommended names or provisional names by default, with the final rename plan gated on review/approval.

## Why Recommended Names Are Unavailable Early

Preview-only candidate rows have not read or refreshed smart analysis sidecars, so they do not have smart tags or suggested filenames. Analyzed but unreviewed rows can expose provisional names, but final apply-ready rename preview requires reviewed/approved metadata. Unsafe names, duplicate targets, or existing target conflicts can still block final readiness.

## Patch Points

- `src/components/spiritflix/admin/SpiritFlixSmartBatchPanel.tsx`: replace diagnostic-first rows with operator-first cards and collapsed `Advanced details`.
- `src/styles/spiritflix.css`: make card layout single-column, give headers/actions stable wrapping, clamp long filenames, and prevent tiny implicit columns.
- `src/components/spiritflix/admin/__tests__/SpiritFlixSmartBatchPanel.test.tsx`: add focused tests for preview, analyzed, reviewed, advanced details, long names, and disabled real apply.
- `src/components/spiritflix/admin/__tests__/SpiritFlixAdminInteractions.test.tsx`: update integration expectations for the simpler default batch panel.
