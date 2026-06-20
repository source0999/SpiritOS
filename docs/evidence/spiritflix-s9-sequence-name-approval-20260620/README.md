# SpiritFlix S9 sequence names and name approval proof

Date: 2026-06-20

Scope:

- Use model-folder video sequence numbers for visual-tag recommended names.
- Keep tag approval separate from name approval.
- Allow the operator to edit the recommended name directly in the batch panel.

## Live Aaliyah preview

`raw/20-preview-sequence-display.json` was captured from the live HTTPS admin API for:

- `/mnt/spirit-8tb/media/yes/models/aaliyah-yasan/540598_720p.mkv`
- `/mnt/spirit-8tb/media/yes/models/aaliyah-yasan/Visit onlyshare.io for MORE 62.mkv`
- `/mnt/spirit-8tb/media/yes/models/aaliyah-yasan/Visit onlyshare.io for MORE 79.mkv`

Observed names:

- `540598_720p.mkv` -> `Aaliyah Yasan - solo indoor 1`
- `Visit onlyshare.io for MORE 62.mkv` -> `Aaliyah Yasan - solo indoor 7`
- `Visit onlyshare.io for MORE 79.mkv` -> `Aaliyah Yasan - solo indoor 8`

All three rows still show content tags `solo`, `indoor` and remain unreviewed until the operator approves tags and/or name.

## Notes

The earlier force refresh in `raw/10-refresh-sequence.json` timed out on ffprobe for two larger items. The final preview proof recomputes provisional display names from existing visual-tag sidecars plus live model-folder sequence, so stale filename IDs are not shown just because a refresh is slow.

No media files were renamed, moved, or deleted.
