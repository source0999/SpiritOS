# SpiritFlix S9 Smart Tags - no solo/indoor cleanup

Date: 2026-06-20

## Scope

- Suppressed stale/generic visual tags `solo` and `indoor` from Smart Tags and recommended names.
- Suppressed visual hair-color guesses (`brunette`, `black-hair`, `blonde`, `redhead`) after the reviewed screenshot showed an inconsistent `brunette` tag.
- Kept `outdoor` available when the sampled frame is clearly outside.
- Increased local visual model coverage from 4 to 8 sampled frames per video, so body/apparel tags have more frame evidence to work from.
- Did not rename, move, or delete any media files.

## Live selected-row proof

Final live forced refresh and preview were run against the four Aaliyah Yasan rows from the screenshots:

- `540598_720p.mkv` -> `duo`, proposed `Aaliyah Yasan - duo 1`
- `Aaliyah Yasin Has Unprotected Sex With A Stranger.mkv` -> `duo`, proposed `Aaliyah Yasan - duo 2`
- `Naughty Aaliyah Yasin Sucks A Big Cock While Smoking.mkv` -> `duo`, proposed `Aaliyah Yasan - duo 4`
- `Visit onlyshare.io for MORE 130.mkv` -> `duo`, proposed `Aaliyah Yasan - duo 10`

`Visit onlyshare.io for MORE 130.mkv` had stale reviewed metadata containing `solo indoor`; the forced retag cleared that review state and returned it to operator review.

Raw proof:

- `raw/20-refresh-selected.json` and `raw/21-preview-selected.json`
- `raw/40-eight-frame-refresh-selected.json`
- `raw/41-eight-frame-preview-selected.json`
- `raw/42-sidecar-frame-summary.json`

## Body/apparel tag boundary

The vocabulary includes visible body/apparel tags such as `curvy`, `busty`, `BBW`, `petite`, `slim`, `hijab`, `lingerie`, `stockings`, `tattoos`, and `glasses`.

The final live sidecars show the local visual model analyzed up to 8 frames for these clips but returned only `duo` observations. The app should not invent `curvy` or `BBW` without sampled-frame evidence. The prompt now explicitly asks the model to check for those visible supported tags when the frame clearly supports them.

The tagger still does not infer protected race, ethnicity, nationality, religion, or identity from appearance. A visible clothing item such as `hijab` can be tagged when clearly visible.
