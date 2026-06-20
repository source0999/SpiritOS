# SpiritFlix S9 Smart Tags - relevant tags only

Date: 2026-06-20

## Scope

- Removed people-count scene tags from Smart Tags and recommended names: `solo`, `duo`, and `group`.
- Removed location-only scene tags from Smart Tags and recommended names: `indoor` and `outdoor`.
- Kept the visual tagger focused on descriptive content tags: body, apparel, activity, position, style, appearance details such as glasses/tattoos, and watermark.
- Forced stale reviewed metadata containing generic scene labels back to operator review.
- Did not rename, move, or delete any media files.

## Live selected-row proof

Final live forced refresh and preview were run against the four Aaliyah Yasan rows from the screenshots:

- `540598_720p.mkv` -> `curvy`, `lingerie`, `stockings`; proposed `Aaliyah Yasan - curvy lingerie stockings 1`
- `Aaliyah Yasin Has Unprotected Sex With A Stranger.mkv` -> `curvy`, `lingerie`, `stockings`; proposed `Aaliyah Yasan - curvy lingerie stockings 2`
- `Naughty Aaliyah Yasin Sucks A Big Cock While Smoking.mkv` -> `curvy`, `lingerie`, `stockings`; proposed `Aaliyah Yasan - curvy lingerie stockings 4`
- `Visit onlyshare.io for MORE 130.mkv` -> `curvy`, `lingerie`, `stockings`; proposed `Aaliyah Yasan - curvy lingerie stockings 10`

Raw proof:

- `raw/20-no-scene-refresh-selected.json`
- `raw/21-no-scene-preview-selected.json`
- `raw/22-no-scene-sidecar-frame-summary.json`

## Boundary

The tagger still does not infer protected race, ethnicity, nationality, religion, or identity from appearance. Visible clothing items, body/apparel descriptors, positions, and activities can be tagged when sampled frames support them.
