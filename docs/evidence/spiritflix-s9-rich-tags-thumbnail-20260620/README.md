# SpiritFlix S9 richer visual tags and batch thumbnails proof

Date: 2026-06-20

Scope:

- Remove the visible Quality/Technical section from the batch review panel.
- Add a video thumbnail to each batch row.
- Expand visual tags beyond generic scene tags.
- Prevent visual prompting from using generic `indoor`, `outdoor`, or `low-light` tags.
- Do not infer protected race, ethnicity, nationality, religion, or identity from appearance.

## Live proof

`raw/11-preview-540598.json` was captured from the live HTTPS admin API after refreshing:

- `/mnt/spirit-8tb/media/yes/models/aaliyah-yasan/540598_720p.mkv`

Observed row payload:

- smart tags: `solo`, `brunette`, `lingerie`
- recommended name: `Aaliyah Yasan - solo brunette lingerie 1`
- thumbnail URL: `/api/spiritflix/admin/thumbnail?path=%2Fmnt%2Fspirit-8tb%2Fmedia%2Fyes%2Fmodels%2Faaliyah-yasan%2F540598_720p.mkv`

Thumbnail route proof:

- `raw/12-thumbnail-540598.headers.txt`: `HTTP/1.1 200 OK`, `content-type: image/jpeg`
- `raw/12-thumbnail-540598.size.txt`: `11007` bytes

Quality/technical badges may still exist in the API for diagnostics and rename planning, but the operator batch panel no longer renders them as a visible section.

No media files were renamed, moved, or deleted.
