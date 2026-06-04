# Phase 1 Closeout

Status: GO

Checks:

- Dry-run storage layout completed: GO
- `/mnt/spirit-8tb/media/movies` exists: GO
- `/mnt/spirit-8tb/media/tv` exists: GO
- `/mnt/spirit-8tb/media/music` exists: GO
- `/mnt/spirit-8tb/media/anime` exists: GO
- `/mnt/spirit-8tb/media/other` exists: GO
- `/mnt/spirit-8tb/services/jellyfin/config` exists: GO
- `/mnt/spirit-8tb/services/jellyfin/cache` exists: GO
- `/mnt/spirit-8tb/services/jellyfin/transcodes` exists: GO
- Ownership and permissions documented: GO
- No existing media files moved, renamed, deleted, or scanned deeply: GO
- `docs/media-server/jellyfin-folder-map.md` exists: GO

Verification summary:

- `/mnt/spirit-8tb` is mounted from `/dev/sda1` as ext4.
- Media and Jellyfin state directories are owned by `source:source`.
- Directory permissions are `drwxrwxr-x` / `775`.
- The folder map was added under `docs/media-server/jellyfin-folder-map.md`.

Final phase increment check:

```text
PHASE_1_INCREMENT_1_1_DRY_RUN_STYLE
TARGET /mnt/spirit-8tb/media/movies
TARGET /mnt/spirit-8tb/media/tv
TARGET /mnt/spirit-8tb/media/music
TARGET /mnt/spirit-8tb/media/anime
TARGET /mnt/spirit-8tb/media/other
TARGET /mnt/spirit-8tb/services/jellyfin/config
TARGET /mnt/spirit-8tb/services/jellyfin/cache
TARGET /mnt/spirit-8tb/services/jellyfin/transcodes

PHASE_1_INCREMENT_1_2_DIRS
/mnt/spirit-8tb /dev/sda1 ext4 rw,relatime
drwxrwxr-x source source /mnt/spirit-8tb/media
drwxrwxr-x source source /mnt/spirit-8tb/media/anime
drwxrwxr-x source source /mnt/spirit-8tb/media/movies
drwxrwxr-x source source /mnt/spirit-8tb/media/music
drwxrwxr-x source source /mnt/spirit-8tb/media/other
drwxrwxr-x source source /mnt/spirit-8tb/media/tv
drwxrwxr-x source source /mnt/spirit-8tb/services/jellyfin
drwxrwxr-x source source /mnt/spirit-8tb/services/jellyfin/cache
drwxrwxr-x source source /mnt/spirit-8tb/services/jellyfin/config
drwxrwxr-x source source /mnt/spirit-8tb/services/jellyfin/transcodes

PHASE_1_INCREMENT_1_3_FOLDER_MAP
docs/media-server/jellyfin-folder-map.md exists and matches the target paths.
```

Note:

- Jellyfin later created container-owned subdirectories under its config/cache paths after Phase 2 startup. The Phase 1 target mount directories remain present and writable by `source`.

Decision:

- Phase 1 is GO.
- Proceed to Phase 2 after the compose location decision.

Next safe step:

- Phase 2.1 compose location decision.
