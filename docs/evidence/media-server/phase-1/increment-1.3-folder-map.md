# Increment 1.3 Folder Usage Notes

Purpose:

- Write a short local usage note so category placement is obvious.

Allowed files changed:

- `docs/media-server/jellyfin-folder-map.md`
- `docs/evidence/media-server/phase-1/increment-1.3-folder-map.md`

Verification command:

```bash
sed -n '1,80p' docs/media-server/jellyfin-folder-map.md
```

Verification output:

```text
# Jellyfin Folder Map

Movies: /mnt/spirit-8tb/media/movies
TV Shows: /mnt/spirit-8tb/media/tv
Music: /mnt/spirit-8tb/media/music
Anime or Animation: /mnt/spirit-8tb/media/anime
Other: /mnt/spirit-8tb/media/other

Jellyfin config: /mnt/spirit-8tb/services/jellyfin/config
Jellyfin cache: /mnt/spirit-8tb/services/jellyfin/cache
Jellyfin transcodes: /mnt/spirit-8tb/services/jellyfin/transcodes
```

Manual check:

- Folder names match the Phase 1 target paths.
- The notes are simple user-facing placement guidance only.
- No source app files or production compose files were edited.

Rollback:

- Delete `docs/media-server/jellyfin-folder-map.md` if the folder map is wrong.

Status: GO
